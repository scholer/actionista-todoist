import datetime
import re
import dateutil.parser
from dateutil import tz
from todoist.models import Item

"""

Module for task-specific functionality, e.g. adding extra fields to tasks, etc.
Functions must operate on todoist.Item objects, or the equivalent dicts (or a list of tasks).


Note: 
ISO 8601 also defines a format for durations: PnYnMnDTnHnMnS
e.g. P3Y6M4DT12H30M5S, or P2H35M - similar to just writing 2h30m, except the ISO8601 uses capitals for time.

The Todoist datetime string format is "almost" the "ctime" format:

except that Todoist has year before time of day, while ctime has year at the end.

"""

# https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
# Note: To get localized date formats, use the "Babel" package, c.f. https://stackoverflow.com/a/32785195/3241277
TODOIST_DATE_FMT = "Ridiculous"  # e.g. "Fri 23 Mar 2018 15:01:05 +0000"
LABEL_REGEX = r"@\w+"
EXTRA_PROPS_REGEX = r"(?P<prop_group>\{(?P<props>(\w+:\s?[^,]+,?\s?)*)\})"
PROP_KV_REGEX = r"((?P<key>\w+):\s?(?P<val>[^,]+),?\s?)"
TASK_REGEX = r"^(?P<title>.*?)" + EXTRA_PROPS_REGEX + "*\s*$"
# extra_props_regex = r"(?P<prop_group>\{(R|r)eward:\s?(?P<reward>.+)\})"
# extra_props_regex = r"(?P<prop_group>\{(?P<props>\w+:\s?[^,]+)*\})"
# prop_kv_regex = r"(?P<key>\w+):\s?(?P<val>[^,]+)"
# TASK_REGEX = r"^(?P<title>.*?)\s*(?P<reward_group>\{(R|r)eward:\s?(?P<reward>.+)\})?\s*$"


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


CUSTOM_FIELDS = {
    'due_date',
    'due_date_dt',
    'due_date_utc_iso',
    'due_date_local_dt',
    'due_date_local_iso',
    'due_date_safe_dt',
    'due_date_safe_iso',
    'date_added_dt',
    'date_added_utc_iso',
    'date_added_local_dt',
    'date_added_local_iso',
    'date_added_safe_dt',
    'date_added_safe_iso',
    'completed_date_dt',
    'completed_date_utc_iso',
    'completed_date_local_dt',
    'completed_date_local_iso',
    'completed_date_safe_dt',
    'completed_date_safe_iso',
    'checked_str',
}


def parse_task_dates(tasks, date_keys=("due_date", "date_added", "completed_date"), strict=False):
    """ Parse date strings and create python datetime objects. """
    endofday = datetime.time(23, 59, 59)
    localtz = tz.tzlocal()
    for task in tasks:
        # 'due_date' has been permanently renamed to 'due_date_utc'. (Which is ridiculous, btw).
        if isinstance(task, Item):
            task = task.data

        if 'due_date_utc' in task:  # May still be `None`!
            task['due_date'] = task['due_date_utc']
            # xx:xx:59 = due date with no time (v7.0)
            task['is_allday'] = (task['due_date_utc'] or "59")[-2:] == "59"
        elif task.get('due'):
            # v7.1 Sync API has separate 'due' child dict - expand these to the old v7.0 format:
            task['due_date_utc'] = task['due_date'] = task['due']['date']
            task['date_string'] = task['due']['string']
            task['is_recurring'] = task['due']['is_recurring']
            task['is_allday'] = len(task['due']['date']) <= len("2018-12-31")
            # Note: v7.1 due date is in ISO8601 format (unlike v7.0).
        else:
            task['is_allday'] = True

        # print("Parsing dates in Task:")
        # print(task)
        for key in date_keys:
            # changed: `due_date` is now `due_date_utc`
            # `completed_date` is typically NOT going to be present unless task has been completed.
            datestr = task[key] if strict else task.get(key)  # E.g. ""Fri 23 Mar 2018 15:01:05 +0000" - ridiculous.
            if datestr:
                # Date time object instance:
                dtobj = task['%s_dt' % key] = dateutil.parser.parse(datestr)
                dt_local = task['%s_local_dt' % key] = dtobj.astimezone(localtz)
                if task['is_allday']:
                    # Force v7.0 behaviour for datetime objects:
                    dt_local.replace(hour=23, minute=59, second=59)
                # CUSTOM_FIELDS.add('%s_dt' % key)
                assert '%s_dt' % key in CUSTOM_FIELDS
                # Note: These dates are usually in UTC time; you will need to convert to local timezone
                task['%s_utc_iso' % key] = "{:%Y-%m-%dT%H:%M:%S}".format(dtobj)
                # CUSTOM_FIELDS.add('%s_utc_iso' % key)
                assert '%s_utc_iso' % key in CUSTOM_FIELDS
                # The time strings below is what you normally see in the app and what you probably want to display:
                # CUSTOM_FIELDS.add('%s_local_dt' % key)
                assert '%s_local_dt' % key in CUSTOM_FIELDS
                task['%s_local_iso' % key] = "{:%Y-%m-%dT%H:%M:%S}".format(dt_local)
                # CUSTOM_FIELDS.add('%s_local_iso' % key)
                assert '%s_local_iso' % key in CUSTOM_FIELDS
                # task['due_time_local'] = task['due_date_local_dt'].time()
                # Local time (without date):
                # due_time_local = dt_local.time()
                # task['%s_local_time' % key] = "{:%H:%M}".format(due_time_local)  # May be "23:59:59" if no time is set
                # In Todoist, if task has due date without specified time, the time is set to "23:59:59".
                # due_time_opt: Optional time, None if due time is "end of day" (indicating no due time only due day).
                # task['%s_time_opt' % key] = time_opt = due_time_local if due_time_local != endofday else None
                # task['%s_time_opt_HHMM' % key] = "{:%H:%M}".format(time_opt) if time_opt else ""
            else:
                # Just create datetime object for "guaranteed" / "safe" fields:
                # Note: The v7.1 Sync API just specifies due date with no time as '2018-04-15', i.e. without time info.
                # Unfortunately, datetime objects have no way to specify "all day" or "no time spec".
                # See comments in this thread by pvkooten (author of metadate): https://goo.gl/3ZNdW3
                dtobj = datetime.datetime(2099, 12, 31, 23, 59, 59)
                dt_local = dtobj.astimezone(localtz)

            # It is nice to have some "guaranteed", safe fields which are always present:
            task['%s_safe_dt' % key] = dt_local
            task['%s_safe_iso' % key] = "{:%Y-%m-%dT%H:%M:%S}".format(dt_local)
            # CUSTOM_FIELDS.add('%s_safe_dt' % key)
            # CUSTOM_FIELDS.add('%s_safe_iso' % key)
            assert '%s_safe_dt' % key in CUSTOM_FIELDS
            assert '%s_safe_iso' % key in CUSTOM_FIELDS

            assert not any('%s' in k for k in task)  # Make sure we've replaced all '%s'

        # Also make "checked_str"
        task["checked_str"] = "[x]" if task.get("checked", 0) else "[ ]"
        # Also make priority string, "p1", "p2". This is kind of weird, because p1 (high priority) is 4 not 1.
        task["priority_str"] = "p%s" % (5 - task.get("priority", 1))

    # CUSTOM_FIELDS.add('checked_str')
    assert 'checked_str' in CUSTOM_FIELDS


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