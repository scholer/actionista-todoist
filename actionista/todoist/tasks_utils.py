# Copyright 2018-2019 Rasmus Scholer Sorensen <rasmusscholer@gmail.com>

"""

Module for task-specific functionality, e.g. adding extra fields to tasks, etc.
Functions must operate on todoist.Item objects, or the equivalent dicts (or a list of tasks).


Note:
ISO 8601 also defines a format for durations: PnYnMnDTnHnMnS
e.g. P3Y6M4DT12H30M5S, or P2H35M - similar to just writing 2h30m, except the ISO8601 uses capitals for time.

The Todoist datetime string format is "almost" the "ctime" format:

except that Todoist has year before time of day, while ctime has year at the end.

"""

import sys
import datetime
import re
import dateutil.parser
import pytz
from dateutil import tz
from todoist.models import Item, Project, Label
from copy import deepcopy
from pprint import pprint

# Note: To get localized date formats, use the "Babel" package, c.f. https://stackoverflow.com/a/32785195/3241277
ISO_DATE_FMT = "%Y-%m-%dT%H:%M:%S"
DATE_TIME_FMT = "%Y-%m-%d %H:%M"  # Prettier format than ISO8601
DATE_NO_TIME_FMT = "%Y-%m-%d"
LABEL_REGEX = r"@\w+"
EXTRA_PROPS_REGEX = r"(?P<prop_group>\{(?P<props>(\w+:\s?[^,]+,?\s?)*)\})"
PROP_KV_REGEX = r"((?P<key>\w+):\s?(?P<val>[^,]+),?\s?)"
TASK_REGEX = r"^(?P<title>.*?)" + EXTRA_PROPS_REGEX + r"*\s*$"
# extra_props_regex = r"(?P<prop_group>\{(R|r)eward:\s?(?P<reward>.+)\})"
# extra_props_regex = r"(?P<prop_group>\{(?P<props>\w+:\s?[^,]+)*\})"
# prop_kv_regex = r"(?P<key>\w+):\s?(?P<val>[^,]+)"
# TASK_REGEX = r"^(?P<title>.*?)\s*(?P<reward_group>\{(R|r)eward:\s?(?P<reward>.+)\})?\s*$"
LOCAL_TIMEZONE = tz.tzlocal()
NO_DUEDATE_DATETIME = datetime.datetime(2099, 12, 31, 23, 59, 59).astimezone(LOCAL_TIMEZONE)
END_OF_DAY_TIME = datetime.time(23, 59, 59)
NO_DUE_DATE_PRETTY_STR = "(No due-date)"


def get_proper_priority_int(priority) -> int:
    """ Return a correct priority integer value for use with the API.

    The input priority can be either a string ("p1", "p2", "p3", or "p4") where "p1" is
    highest priority and "p4" is lowest priority. This is converted to one of the values
    (4, 3, 2, or 1), where priority=4 is highest priority.

    Alternatively, the input priority can be an integer, in which case we simply check that the
    integer is either 1, 2, 3, or 4, where priority=4 is highest priority.

    Examples:
        priority = "p3"
        priority = get_proper_priority_int(priority)
        assert priority == 2

        priority = 1
        priority = get_proper_priority_int(priority)
        assert priority == 1

        priority = 0
        priority = get_proper_priority_int(priority)
        ValueError: Argument `priority` must be between 1 and 4 (if int).

        priority = None
        priority = get_proper_priority_int(priority)
        TypeError: Argument `priority` must be str or int.
    """
    if isinstance(priority, str):
        # Priority in the form of "p1" to "p4".
        priority_str = priority
        priority_str_map = dict(p1=4, p2=3, p3=2, p4=1)
        try:
            priority = priority_str_map[priority]
        except KeyError:
            raise ValueError("Argument `priority` must be one of 'p1', 'p2', 'p3', or 'p4' (if str).")
    else:
        # Integer between 1 and 4:
        if not isinstance(priority, int):
            raise TypeError("Argument `priority` must be str or int.")
        if priority < 1 or 4 < priority:
            raise ValueError("Argument `priority` must be between 1 and 4 (if int).")
    return priority


def get_task_data(task, data_attr="_custom_data"):
    if isinstance(task, Item):
        # Try the "_custom_data" first (it should include original data as well), fall back to Item.data:
        return getattr(task, data_attr, task.data)
    else:
        return task


def get_task_value(task, taskkey, default=None, coerce_type=None, data_attr="_custom_data"):
    """ Get a task data value from the task.
    This function combines a couple of features:

    1. Determine if task is a dict or Item, and extract the data dict using the given data attribute.
    2. Get the data value given by taskkey, defaulting to the given default value
        if `key` is not present in the data dict.
    3. coerce the value to a given type, e.g. coerce "1" to integer 1, or a date-string to datetime object.

    Args:
        task: Either a todoist.models.Item, or a task dict.
        taskkey: The key whose value you would like to get.
        default: Default value, if no value could be found.
        coerce_type: Coerce the value to this type before returning.
        data_attr: The attribute of task where data is stored.
            I am storing custom/derived data in task._custom_data, separate from the original
            data, to prevent the derived data from being cached to disk.

    Returns:
        Value, or <default>

    """
    task_data = get_task_data(task, data_attr=data_attr)
    try:
        task_value = task_data[taskkey]
    except KeyError:
        if taskkey.startswith("due_"):
            try:
                task_value = task_data['due'][taskkey.strip("due_")]
            except (KeyError, TypeError):  # TypeError if task_data['due'] is None
                task_value = default
        elif '.' in taskkey:
            # support dot-notation, task_data["due.date"] -> task_data["due"]["date"]
            basekey, childkey = taskkey.split('.', 1)
            try:
                task_value = get_task_value(task_data[basekey], childkey)
            except (KeyError, TypeError):
                task_value = default
        else:
            task_value = default
    if coerce_type is not None and task_value is not None and type(task_value) != coerce_type:
        print("NOTICE: `type(task_value) != coerce_type` - Coercing `task_value` to %s:" % type(coerce_type))
        task_value = coerce_type(task_value)
    return task_value


def is_recurring(task, data_attr='_custom_data'):
    """ Return whether task is recurring or not.
    This is super easy for new v8 Sync API tasks, but not so much for the older tasks.
    """
    task_data = get_task_data(task)
    try:
        return task_data['due']['is_recurring']
    except (KeyError, TypeError):  # TypeError if task_data['due'] is None
        due_string = task_data.get('date_string') or task_data.get('due_string') or ''
        return 'every' in due_string


def get_recurring_tasks(tasks: list, negate: bool = False) -> list:
    return [task for task in tasks if is_recurring(task) != negate]


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
    # Update: There was too many date fields, so now all timestamps and datetime objects are just in local time.
    'due_date',  # Due date (str), as listed by the API.
    'due_date_string',  # Human-readable due date, as listed by the API.
    'due_string_safe',  # Save due_string, is None if no due date.
    'due_date_dt',  # datetime object (local time)
    'due_date_iso',  # ISO str timestamp (local time)
    'due_date_safe_dt',  # Safe due date datetime - is always present (dummy value for no due date)
    'due_date_safe_iso',  # Safe due date ISO str - is always present (dummy value for no due date)
    # 'due_date_utc_iso',
    # 'due_date_local_dt',
    # 'due_date_local_iso',
    'date_added_dt',   # datetime object (local time)
    'date_added_iso',   # ISO str timestamp (local time)
    'date_added_safe_dt',
    'date_added_safe_iso',
    # 'date_added_utc_iso',
    # 'date_added_local_dt',
    # 'date_added_local_iso',
    'completed_date_dt',
    'completed_date_iso',
    'completed_date_safe_dt',
    'completed_date_safe_iso',
    # 'completed_date_utc_iso',
    # 'completed_date_local_dt',
    # 'completed_date_local_iso',
    'checked_str',
}


def add_task_date_fields(
        input_dict, output_dict=None,
        date_keys=("date_added", "date_completed", "completed_date"),
        allday_time=END_OF_DAY_TIME,
        safe_date=NO_DUEDATE_DATETIME,
        datestrfmt="%Y-%m-%d %H:%M",
        allday_datestrfmt="%Y-%m-%d",
):
    """ Parse dates in `input_dict` and add custom date fields to `output_data`.

    Args:
        input_dict:
        output_dict:
        allday_time: If specified, "all-day" tasks (with a due date but no due time)
            will have their "due_time_dt" datetime object set to this value.
        safe_date: If a date is not specified (due date, date added, date completed),
            use this as the "safe value", e.g. typically a date really far into the future.

    Returns:
        output_dict

    Update, 2019: The new v8 Sync API builds on the combined `due` property that was introduced
    with v7.1.

    Examples:
        >>> task._custom_data = {}  # Create custom data dict.
        >>> output = add_task_date_fields(input_dict=task.data, output_dict=task._custom_data)

    """
    if output_dict is None:
        output_dict = {}

    # Parse due date:
    if input_dict.get('due'):
        # v8 (and v7.1) Sync API has separate 'due' child dict - expand these to the old v7.0 format:
        output_dict['due_date'] = input_dict['due']['date']
        output_dict['due_string'] = input_dict['due']['string']
        output_dict['due_string_safe'] = input_dict['due']['string']
        output_dict['date_string'] = input_dict['due']['string']  # v7.0 legacy attribute name
        output_dict['due_is_recurring'] = input_dict['due']['is_recurring']
        output_dict['is_recurring'] = input_dict['due']['is_recurring']
        # An all-day task in v8 API has a due date with no time specification:
        output_dict['is_allday'] = len(input_dict['due']['date']) <= len("YYYY-MM-DD")
        # Note: v8 due date is in RFC-3339/ISO8601 format!

        # Parse strings to datetime objects (denoted with a "_dt" postfix):
        # v8 API has two distinct ways of specifying due dates:
        # 1. "Floating", where the time is always the literal clock time, in-dependent of timezone.
        # 2. "Fixed timezone", where the time is in universal UTC time, and has a "timezone" property.
        #    The timezone attribute is used when re-parsing the due-string,
        # e.g. string="every day at 2pm", timezone="Europe/Copenhagen".
        # OBS: The datetime objects are always represented in the local timezone.
        output_dict['due_date_dt'] = dateutil.parser.parse(input_dict['due']['date'])
        if output_dict['is_allday'] and allday_time:
            # Force v7.0 behaviour for datetime objects:
            output_dict['due_date_dt'] = output_dict['due_date_dt'].replace(
                hour=allday_time.hour, minute=allday_time.minute, second=allday_time.second
            )
            output_dict['due_date_dt'] = output_dict['due_date_dt'].astimezone(tz.tzlocal())
        if not output_dict['due_date_dt'].tzinfo:
            if input_dict['due']['timezone']:  # Only check timezone if not all-day task:
                # OBS: Timezone calculation not needed for v7.1 legacy tasks, where [due][date] was UTC timestamp:
                # Convert from the given timezone to local timezone.
                # First create a "due-date local" timezone object, then use it to make a timezone-aware
                # datetime object using `localize()`, then convert that timezone-aware datetime to
                # computer-local time using `astimezone(tz.tzlocal())`:
                # print("Task '{content}': due: {due} => dt: {due_date_dt}".format(due_date_dt=output_dict['due_date_dt'], **input_dict))
                # Make it aware of the timezone:
                output_dict['due_date_dt'] = pytz.timezone(input_dict['due']['timezone']).localize(output_dict['due_date_dt'])
            # Convert from UTC (or whatever timezone it has) to local datetime:
            output_dict['due_date_dt'] = output_dict['due_date_dt'].astimezone(tz.tzlocal())
            # output_dict['due_date_dt'] = pytz.utc.localize()
        output_dict['due_date_pretty_safe'] = output_dict['due_date_dt'].strftime(
            DATE_NO_TIME_FMT if output_dict['is_allday'] else DATE_TIME_FMT)
    elif input_dict.get('due_date_utc'):
        # I have some old tasks where "due_date_utc" attribute is present but set to None. (weird)
        # print("Task '{content}': parsing due_date_utc: {due_date_utc}   (string: {date_string})".format(**input_dict))
        # Old v7 Sync API
        output_dict['due_date'] = input_dict['due_date_utc']
        output_dict['due_string'] = input_dict['date_string']
        output_dict['due_string_safe'] = input_dict['date_string']
        # xx:xx:59 = due date with no time (v7.0)
        output_dict['is_allday'] = (input_dict['due_date_utc'] or "59")[-2:] == "59"
        output_dict['due_date_dt'] = dateutil.parser.parse(input_dict['due_date_utc']).astimezone(LOCAL_TIMEZONE)
        output_dict['due_date_pretty_safe'] = output_dict['due_date_dt'].strftime(
            DATE_NO_TIME_FMT if output_dict['is_allday'] else DATE_TIME_FMT)
    else:
        # No due date specified:
        output_dict['is_allday'] = True
        output_dict['due_string_safe'] = input_dict.get('date_string', None)
        output_dict['due_date_pretty_safe'] = NO_DUE_DATE_PRETTY_STR

    # All datetime objects should have a timezone (either that, or none should have timezone)
    # Mixing timezone-aware with timezone-naive makes comparison impossible (TypeError)
    # At this point, all `due_date_dt` objects should have a timezone. If not, then something is wrong.
    if output_dict.get('due_date_dt') and not output_dict['due_date_dt'].tzinfo:
        print("Adding tzinfo to task (it should already have it at this point!):")
        pprint(input_dict)
        output_dict['due_date_dt'] = output_dict['due_date_dt'].astimezone(tz.tzlocal())

    # Add some "guaranteed", safe fields which are always present:
    output_dict['due_date_safe_dt'] = output_dict.get('due_date_dt', safe_date)
    output_dict['due_date_safe_iso'] = "{:%Y-%m-%dT%H:%M:%S}".format(output_dict.get('due_date_dt', safe_date))
    output_dict['due_date_safe'] = output_dict.get('due_date', "(No due-date)")

    # Parse additional date attributes to datetime objects (with local timezone):
    for key in date_keys:
        datestr = input_dict.get(key)
        # Old v7 date format was e.g. "Fri 23 Mar 2018 15:01:05 +0000" - ridiculous.
        # New v8 format is strictly RFC-3339/ISO1806 - nice.
        if datestr:
            # Create datetime object - datestr should be guaranteed to be UTC:
            dt_local = dateutil.parser.parse(datestr).astimezone(LOCAL_TIMEZONE)
            output_dict['%s_dt' % key] = dt_local
            output_dict['%s_iso' % key] = "{:%Y-%m-%dT%H:%M:%S}".format(dt_local)
        else:
            dt_local = safe_date.astimezone(LOCAL_TIMEZONE)

        # It is nice to have some "guaranteed", safe fields which are always present:
        output_dict['%s_safe_dt' % key] = dt_local
        output_dict['%s_safe_iso' % key] = "{:%Y-%m-%dT%H:%M:%S}".format(dt_local)

    # Also make "checked_str" field to quickly indicate the checked/completed status of a task:
    output_dict["checked_str"] = "[x]" if input_dict.get("checked", 0) else "[ ]"
    # Also make priority string, "p1", "p2". This is kind of weird, because p1 (high priority) is 4 not 1.
    # (The "priority strings" are used e.g. in the web app, where you type "p1" to make a high-priority task.)
    output_dict["priority_str"] = "p%s" % (5 - input_dict.get("priority", 1))
    return output_dict


def get_input_output_dicts(task, output_attr="_custom_data", deepcopy_data=True):
    if isinstance(task, Item):
        input_data = task.data
        if output_attr:
            try:
                output_data = getattr(task, output_attr)
            except AttributeError:
                output_data = deepcopy(task.data) if deepcopy_data else {}
                setattr(task, output_attr, output_data)
        else:
            output_data = task.data
    else:
        assert isinstance(task, dict)
        input_data = output_data = task
    return input_data, output_data


def add_custom_task_fields(
        tasks,
        api,
        inject_derived_task_fields=1,
        inject_task_date_fields=1,
        inject_task_project_fields=1,
        inject_task_labels_fields=1,
        *,
        verbose=0,
        **kwargs
):
    """ Add custom data fields to each task.
    Alternative version of `inject_tasks_custom_data()`, this version is intended to
    be called with values taken directly from the command line, hence why input arguments are
    being cast to int, as the input may likely be e.g. str '0' or '1'.

    Args:
        tasks:
        api:
        inject_derived_task_fields:
        inject_task_date_fields:
        inject_task_project_fields:
        inject_task_labels_fields:
        verbose:
        **kwargs:

    Returns:
        List of tasks, for chaining.
    """
    if int(inject_derived_task_fields):

        if int(inject_task_date_fields):
            # Inject custom date fields, e.g. `due_date_iso`, `due_date_dt`, and `checked_str`:
            if verbose >= 2:
                print("Parsing dates and creating ISO strings...", file=sys.stderr)
            inject_tasks_date_fields(tasks=tasks, strict=False)

        if int(inject_task_project_fields):
            # Inject project info, so we can access e.g. task['project_name']:
            if verbose >= 1:
                print("Injecting project info...", file=sys.stderr)
            inject_tasks_project_fields(tasks=tasks, projects=api.projects.all())

        if int(inject_task_labels_fields):
            # Inject project info, so we can access e.g. task['project_name']:
            if verbose >= 1:
                print("Injecting project info...", file=sys.stderr)
            inject_tasks_labels_fields(tasks=tasks, labels=api.labels.all())

    return tasks


def inject_tasks_custom_data(
        tasks, output_attr="_custom_data", deepcopy_data=True,
        add_dates=True,
        parse_content=False, task_regex=TASK_REGEX,
        add_project_info=True, projects=None,
        add_label_fields=True, labels=None, label_fmt="@{name}", labels_sep=" ",
):
    """ Parse task data (e.g. dates) and inject custom data fields.

    This an "all-in-one" function that performs all parsing/extraction steps.
    (Not sure this is better that just doing them sequentially.)

    By default, the custom data is added to a separate `task._custom_data` property,
    which will be a deep copy of `task.data`.

    Args:
        tasks:
        output_attr: The task attribute to inject data to.
        deepcopy_data:
        add_dates:
        parse_content:
        task_regex:
        add_project_info:
        projects:
        add_label_fields: Whether to add custom task-label fields.
        labels: The full list of labels from the API, so we can map LabelID to Label.
        label_fmt: The format of each label (e.g. prefix @).
        labels_sep: The separator to use when making "labels_str".

    Returns:
        None; tasks are updated in-place.
    """
    for task in tasks:
        # Get the input_data and output_data objects to read from and write to:
        input_data, output_data = get_input_output_dicts(
            task=task, output_attr=output_attr, deepcopy_data=deepcopy_data)

        if add_dates:
            # Custom date fields (and "checked_str" and "priority_str"):
            add_task_date_fields(input_dict=input_data, output_dict=output_data)
            # output_data.update(custom_fields)

        if parse_content:
            parse_task_content(task, output_data, task_regex)

    # Adding project info requires having the projects data:
    if add_project_info:
        assert projects is not None
        inject_tasks_project_fields(tasks=tasks, projects=projects)

    if add_label_fields:
        inject_tasks_labels_fields(tasks, labels, output_attr=output_attr, label_fmt=label_fmt, labels_sep=labels_sep)


def inject_tasks_date_fields(
        tasks,
        date_keys=("date_added", "date_completed", "completed_date"),
        strict=False,
        output_attr='_custom_data', deepcopy_data=True,
        verbose=0
):
    """ Parse date strings and create python datetime objects.


    """
    if verbose:
        print(f"Parsing and adding additional date information to tasks {output_attr if output_attr else ''}...",
              file=sys.stderr)
    for task in tasks:
        # Get the input_data and output_data objects to read from and write to:
        input_data, output_data = get_input_output_dicts(
            task=task, output_attr=output_attr, deepcopy_data=deepcopy_data)

        # Add custom date fields (and "checked_str" and "priority_str"):
        added_fields = add_task_date_fields(
            input_dict=input_data, output_dict=output_data, date_keys=date_keys)
        # print(f"Task {input_data['content']} aded date fields:", added_fields)
        # output_data.update(added_fields)


def inject_tasks_project_fields(tasks, projects, strict=False, na='N/A', output_attr='_custom_data', verbose=0):
    """ Inject project information (name, etc) for each task, using the task's project_id.
    This makes it considerably more convenient to print tasks, when each task has the project name, etc.
    Information is injected as `getattr(task, output_attr, task.data)["project_%s" % k"] = v`
    for all key-value pairs in the task's project, e.g. project_name, project_color, project_indent,
    project_is_archived, etc.

    Args:
        tasks: A list of tasks.
        projects: A list of projects, or a dict of projects keyed by `project_id`.
        strict: If True, raise an error if a task's project_id is not found in the projects dict.
        na: If, in non-strict mode, a task's project_id is not found, use this value instead.
            It can be either a single value, which is used for the most common project fields,
            or it can be a dict where we just do `task.update(na)`.
        output_attr: Instead of updating task directly, update the dict found
            in `getattr(task, output_attr)`.

    Returns:
        None; the task dicts are updated in-place.
    """
    if verbose:
        print(f"Adding additional project information to tasks {output_attr if output_attr else ''}...",
              file=sys.stderr)
    if not isinstance(projects, dict):
        # If projects is e.g. a list of projects, create a dict mapping project_id to project:
        projects_by_pid = {project['id']: project for project in projects}
        projects = projects_by_pid
    # I think it should be OK to add non-standard fields to task Items
    for task in tasks:
        # Update either `task.data` or `task._custom_data`:
        input_data, output_data = get_input_output_dicts(task, output_attr=output_attr, deepcopy_data=True)
        pid = input_data['project_id']
        # Todoist API sometimes returns string ids and sometimes integer ids.
        try:
            project = projects[pid if pid in projects else str(pid)]
        except KeyError as exc:
            if strict:
                raise exc
            else:
                if isinstance(na, dict):
                    output_data.update(na)
                else:
                    output_data['project_name'] = na
        else:
            # Add all the project info to task, using "project_" prefix.
            # If project is a Model instance, then the data dict is in the 'data' attribute
            # (otherwise just project is already a dict and can be used directly).
            # (the todoist.model.Model class does not support the dict interface).
            for k, v in getattr(project, 'data', project).items():
                output_data["project_%s" % k] = v


def inject_tasks_labels_fields(
        tasks, labels, output_attr='_custom_data', label_fmt="@{name}", labels_sep=" ", verbose=0):
    """ Inject labels information for each task, using the task's 'labels' attribute.
    This makes it considerably more convenient to print tasks, when each task has the label name,
    rather than just the label id.

    Args:
        tasks: A list of tasks.
        labels: A list of labels, or a dict of labels keyed by `label_id`.
        output_attr: Instead of updating task directly, update the dict found
            in `getattr(task, output_attr)`.
        label_fmt: How to format each label when creating `labels_str`.
        labels_sep: How to join the labels when creating `labels_str`.

    Returns:
        None; the task dicts are updated in-place.
    """
    if verbose:
        print(f"Adding additional labels information to tasks {output_attr if output_attr else ''}...",
              file=sys.stderr)
    if not isinstance(labels, dict):
        # If projects is e.g. a list of projects, create a dict mapping project_id to project:
        labels_by_id = {int(label['id']): label for label in labels}
    else:
        labels_by_id = labels
    # I think it should be OK to add non-standard fields to task Items
    del labels
    for task in tasks:
        # Update either `task.data` or `task._custom_data`:
        input_data, output_data = get_input_output_dicts(task, output_attr=output_attr, deepcopy_data=True)
        task_labels = [labels_by_id[lid] for lid in input_data['labels']]
        label_dicts = [label.data if isinstance(label, Label) else label for label in task_labels]
        output_data['label_names'] = [label['name'] for label in label_dicts]
        # if lowercase_label_names:
        #     output_data['label_names'] = [label_name.lower() for label_name in output_data['label_names']]
        output_data['labels_str'] = labels_sep.join(label_fmt.format(**label) for label in label_dicts)


def parse_task_content(task, output_dict, task_regex):
    try:
        output_dict.update(re.match(task_regex, task['content']).groupdict())
        labels, cleaned = extract_labels(task['content'])
        props, cleaned = extract_props(task['content'])
        output_dict['cleaned'] = cleaned
        output_dict['ext_labels'] = labels
        output_dict['ext_props'] = props or {}
    except AttributeError as e:
        print("WARNING: Error while matching regex `{}` to task['content'] `{}`: %s".format(
            task_regex, task['content'], repr(e)))
    return output_dict


def parse_tasks_content(tasks, task_regex=None, output_attr='_custom_data', verbose=0):
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
    if verbose:
        print(f"Adding additional content-parsed information to tasks {output_attr if output_attr else ''}...",
              file=sys.stderr)
    if task_regex is None:
        task_regex = TASK_REGEX
    if isinstance(task_regex, str):
        task_regex = re.compile(task_regex)
    for task in tasks:
        # Update either `task.data` or `task._custom_data`:
        if output_attr:
            try:
                output_data = getattr(task, output_attr)
            except AttributeError:
                output_data = {}
                setattr(task, output_attr, output_data)
        else:
            output_data = task
        parse_task_content(task, output_data, task_regex)
    return tasks
