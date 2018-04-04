import datetime
import re
import dateutil.parser
from dateutil import tz
import dateparser
from todoist.models import Item, Project

"""

Note: 
ISO 8601 also defines a format for durations: PnYnMnDTnHnMnS
e.g. P3Y6M4DT12H30M5S, or P2H35M - similar to just writing 2h30m, except the ISO8601 uses capitals for time.

"""

TODOIST_DATE_FMT = "Ridiculous"  # "Fri 23 Mar 2018 15:01:05 +0000"
DAY_DATE_FMT = '%Y-%m-%d'
ISO_8601_FMT = '%Y-%m-%dT%H:%M:%S'
LABEL_REGEX = r"@\w+"
EXTRA_PROPS_REGEX = r"(?P<prop_group>\{(?P<props>(\w+:\s?[^,]+,?\s?)*)\})"
PROP_KV_REGEX = r"((?P<key>\w+):\s?(?P<val>[^,]+),?\s?)"
TASK_REGEX = r"^(?P<title>.*?)" + EXTRA_PROPS_REGEX + "*\s*$"
# extra_props_regex = r"(?P<prop_group>\{(R|r)eward:\s?(?P<reward>.+)\})"
# extra_props_regex = r"(?P<prop_group>\{(?P<props>\w+:\s?[^,]+)*\})"
# prop_kv_regex = r"(?P<key>\w+):\s?(?P<val>[^,]+)"
# TASK_REGEX = r"^(?P<title>.*?)\s*(?P<reward_group>\{(R|r)eward:\s?(?P<reward>.+)\})?\s*$"


def human_date_to_iso(human_date, fmt=ISO_8601_FMT):
    """ Convert natural language / contextual dates, e.g. 'today', to iso date string.
    Note: This is a little bit finicky. For instance, "in 2 weeks" works, but none of the following variations do:
        "in two weeks", "2 weeks from now", "two weeks", "in 2 weeks from now", etc.

    The returned datetime object does not by default have any timezone information,
    so the iso datestring is basically local time.
    """
    dt = dateparser.parse(human_date)
    if dt is None:
        print(f"\nERROR: FAILED to parse human input date {human_date!r}.\n")
        raise ValueError(f"FAILED to parse human input date {human_date!r}.")
    return dt.strftime(fmt)


def use_task_data_dict(func):
    pass


def extract_labels(content):
    labels = re.findall(LABEL_REGEX, content)
    cleaned = re.sub(LABEL_REGEX, "", content).rstrip()
    return labels, cleaned


def extract_props(content):
    props_match = re.search(EXTRA_PROPS_REGEX, content)
    if not props_match:
        return None, content
    props_str = props_match.groupdict()['props']
    props_pairs = re.findall(PROP_KV_REGEX, props_str)
    props_dict = dict(tuple(mgroup[1:3]) for mgroup in props_pairs)

    cleaned = re.sub(EXTRA_PROPS_REGEX, "", content).rstrip()
    return props_dict, cleaned


def parse_task_dates(tasks, date_keys=("due_date", "date_added", "completed_date"), strict=False):
    """ Parse date strings and create python datetime objects. """
    endofday = datetime.time(23, 59, 59)
    localtz = tz.tzlocal()
    for task in tasks:
        # 'due_date' has been permanently renamed to 'due_date_utc'. (Which is ridiculous, btw).
        if isinstance(task, Item):
            task = task.data
        if 'due_date_utc' in task:
            task['due_date'] = task['due_date_utc']

        # print("Parsing dates in Task:")
        # print(task)
        for key in date_keys:
            # changed: `due_date` is now `due_date_utc`
            # `completed_date` is typically NOT going to be present unless task has been completed.
            datestr = task[key] if strict else task.get(key)  # E.g. ""Fri 23 Mar 2018 15:01:05 +0000" - ridiculous.
            if datestr:
                # Date time object instance:
                dtobj = task['%s_dt' % key] = dateutil.parser.parse(datestr) if datestr is not None else None
                # Note: These dates are usually in UTC time; you will need to convert to local timezone
                task['%s_utc_iso' % key] = "{:%Y-%m-%dT%H:%M:%S}".format(dtobj)
                # dt_local = task['%s_local_dt' % key] = dtobj.astimezone(localtz)
                # task['%s_local_iso' % key] = "{:%Y-%m-%dT%H:%M:%S}".format(dt_local)
                # task['due_time_local'] = task['due_date_local_dt'].time()
                # Local time (without date):
                # due_time_local = dt_local.time()
                # task['%s_local_time' % key] = "{:%H:%M}".format(due_time_local)  # May be "23:59:59" if no time is set
                # In Todoist, if task has due date without specified time, the time is set to "23:59:59".
                # due_time_opt: Optional time, None if due time is "end of day" (indicating no due time only due day).
                # task['%s_time_opt' % key] = time_opt = due_time_local if due_time_local != endofday else None
                # task['%s_time_opt_HHMM' % key] = "{:%H:%M}".format(time_opt) if time_opt else ""
                assert not any('%s' in k for k in task)  # Make sure we've replaced all '%s'


# def parse_date_string(date_str, iso_fmt=None):
#     """Return (informal_date, iso_date_str, datetime_obj) tuple."""
#     import dateutil.parser
#     dt = dateutil.parser.parse(date_str)  # returns datetime object
#     return dt


def inject_project_info(tasks, projects):
    """ Inject project information (name, etc) for each task, using the task's project_id.
    This makes it considerably more convenient to print tasks, when each task has the project name, etc.
    Information is injected as `task["project_%s" % k"] = v` for all key-value pairs in the task's project,
    e.g. project_name, project_color, project_indent, project_is_archived, etc.

    Args:
        tasks: A list of tasks.
        projects: A dict of projects, keyed by `project_id`.

    Returns:
        None; the task dicts are updated in-place.
    """
    if not isinstance(projects, dict):
        projects_by_pid = {project['id']: project for project in projects}
        projects = projects_by_pid
    # I think it should be OK to add non-standard fields to task Items
    for task in tasks:
        pid = task['project_id']
        # Todoist API sometimes returns string ids and sometimes integer ids.
        project = projects[pid if pid in projects else str(pid)]
        # If projects are Model instances, then the data dict is in the 'data' attribute (otherwise just project):
        for k, v in getattr(project, 'data', project).items():
            task["project_%s" % k] = v


def parse_tasks_content(tasks, task_regex=None):
    """ Parse tasks using the task-parsing regular expressions. Tasks are parsed and updated in-place.
    This is only for use with my custom metadata scheme where I use `{reward: 1h}` in the task content
    to define key-value metadata pairs.

    ^(?P<title>.*?)\s*(?P<reward_group>\{reward:\s?(?P<reward>.+)\})
    (?P<title>.*)\s*(?P<reward_group>\{reward:\s?(?P<reward>.+)\})
    ^(?P<title>.*?)\s*(?P<reward_group>\{reward:\s?(?P<reward>.+)\})?\s*$
    ^(?P<title>.*?)\s*(?P<reward_group>\{(R|r)eward:\s?(?P<reward>.+)\})?\s*(?P<labels>(@\w+\s?)*\s?)*$
    ^(?P<title>.*?)\s*(?P<prop_group>\{(R|r)eward:\s?(?P<reward>.+)\})?\s*(?P<labels>(@\w+\s?)*)\s*$

    Check DFCI email {reward: 0.25h W} @Habit @Reward
    Check DFCI email @Habit @Reward {reward: 0.25h W}
    @Habit @Reward Check DFCI email {reward: 0.25h W}

    """
    if task_regex is None:
        task_regex = TASK_REGEX
    if isinstance(task_regex, str):
        task_regex = re.compile(task_regex)
    for task in tasks:
        try:
            task.update(re.match(task_regex, task['content']).groupdict())
            labels, cleaned = extract_labels(task['content'])
            props, cleaned = extract_props(task['content'])
            task['cleaned'] = cleaned
            task['ext_labels'] = labels
            task['ext_props'] = props or {}
        except AttributeError as e:
            print("WARNING: Error while matching regex `{}` to task['content'] `{}`: %s".format(
                task_regex, task['content'], repr(e)))
    return tasks