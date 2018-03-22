
"""

INSTALLATION:
-------------

    pip install -U -e .



Examples, command line usage:
-----------------------------

    print-query command:
    * Note: --query defaults to "(overdue | today)"

    $ python -m rstodo.todoist print-query [--query <query>] [--task-fmt <task-format>]

    $ python -m rstodo.todoist print-query --print-fmt "* {due_date_time_opt_HHMM} > {title}"

    print-todays-completed-items:
    $ python -m rstodo.todoist print-todays-completed-items \
        --print-fmt "* {completed_date_local_dt:%H%M} > {content}" --sort-key completed_date_dt


Todoist Queries:
----------------

Refs:
* https://support.todoist.com/hc/en-us/articles/205248842-Setting-up-filters

API end point: /API/v7/query


Filter query:				What it does:
-------------				-------------
(overdue | today) & #Work	Shows all tasks that are overdue or due today that are in the “Work” project.
no date						Shows all tasks that don’t have a due date.
7 days & @waiting			Shows all tasks that are due in the next 7 days and are labelled @waiting.
created before: -365 days	Shows all tasks created more than 365 days ago.
assigned to: Allan			Shows all tasks assigned to Allan. A quick way to see what Allan’s working on.
assigned by: me				Shows all tasks you assigned to others. Handy for following up on delegated tasks.
shared & !assigned			Shows all tasks in shared project that haven’t been assigned to anyone.


Hmm... I seem to get vastly different results using API query vs web-app search/filter.
*
* However, neither seems to be correct!
* https://support.todoist.com/hc/en-us/articles/205248842-Filters






Todoist APIs:
-----------------

* https://github.com/Doist/todoist-python [installed] –
    Official python library from Doist. Has API module, object models, and managers.
    Documented at https://developer.todoist.com/.
* https://github.com/Garee/pytodoist [installed] –
    The second biggest Todoist library.
    Rolls its own API code using requests (`api` module), and object model (`todoist` module).


Todoist CLIs:
----------------
* https://github.com/ddksr/cliist -
    Another Todoist CLI, rather big,
    rolls its own API using urllib requests against https://api.todoist.com/API directly.
    Also has object model, and cache system. Uses optparse for command line parsing
* https://github.com/csu/todoist-cli –
    Very simple CLI, only supports adding tasks, does not use any "libraries",
    just makes manual GET requests to https://api.todoist.com/API/addItem?content=xxx URL.
    Uses the click library for command-line interface parsing. http://click.pocoo.org/5/
* https://github.com/Matael/pydoist -
    Uses the Pydoist api library,
    acts as a simple wrapper to parse "shortened/incomplete" project names using the Levenshtein (distance) library.
* https://github.com/Raytray/todoist-cli -
    "usage: todoist.py [-h] [-p PROJECT] [-c CONTENT] [-d DUE] [-u URL] function", e.g.
    `python todoist.py query -c "tomorrow"`.
    Manually queries the API api.todoist.com/API endpoints using requests library.
* https://github.com/KryDos/todoist-cli – [last update 2014]
    Terminal-like CLI, e.g. `todoist ls tod` to list today's items.
* https://github.com/bolasblack/todoistCli - Last update 2012.
    Looks pretty horrible..
* https://github.com/akramer/NextAction -
    GTD "next action" cli interface using Todoist, rolls its API code using urllib.
* https://github.com/emorisse/todoist-tools -
    Lots of example scripts using the official todoist library.
* https://github.com/deanmalmgren/todoist-tracker -
    Tracker.. but only python2?


Notes:
--------
* There are a bunch of other Todoist libraries on github, just sort the search by "recently updated":
    https://github.com/search?l=Python&o=desc&q=todoist&s=updated&type=Repositories&utf8=%E2%9C%93
* I'm surprised there are no Todoist packages for Sublime Text yet: https://packagecontrol.io/search/todoist



References:
--------------
  (has many examples using python or curl).
* Newest API version is v7: https://todoist.com/API/v7/sync
*


Date/time libraries:
--------------------
* Python built-in `datetime` library. [so many issues: constructor and objects are intermingled, timezone hell, etc.]
* Arrow, http://arrow.readthedocs.io/en/latest/
    "Fully implemented, drop-in replacement for datetime. Timezone-aware & UTC by default."
    "Formats and parses strings automatically. Humanizes and supports a growing list of contributed locales."
    a = arrow.get(<time stamp string>)
    a.to('US/Pacific')
    a.format('YYYY-MM-DD HH:mm:ss ZZ')
    a.humanize()  # e.g. 'an hour ago'
    Does not seem to parse "an hour ago" or "tomorrow".
* Pendulum, a very complex and precise library. https://pendulum.eustace.io/
    Although, pendulum has .today(), .tomorrow(), but .parse('tomorrow') fails despite docs saying it should work.
* Maya, https://github.com/kennethreitz/maya  - By Kenneth Reitz,
    Good for adding/subtracting datetimes and timedeltas/durations.
    Uses pendulum and dateparser libraries for parsing dates.
    tomorrow = maya.when('tomorrow')  # uses dateparser.parse('tomorrow')
    time = maya.parse('01/05/2016', date_first=False)  # Uses pendulum.parse(...)
* Moment, https://github.com/zachwill/moment.
* Zulu, https://github.com/dgilland/zulu - "all objects are UTC"
* Times, https://github.com/nvie/times [deprecated, recommends Arrow instead]
* delorean, "Delorean: Time Travel Made Easy", https://github.com/myusuf3/delorean, http://delorean.rtfd.org/
* pytz, for timezones.

Parsing human natural language time strings:
* for parsing "meta dates" like "tomorrow" or "in 1 hour":
* dateutil, dateparser, parsedatetime, and datefinder, metadate
* dateutil - "Useful extensions to the standard Python datetime features."
    # https://github.com/dateutil/dateutil
    dateutil.parser.parse("tomorrow")
* parsedatetime - Parse human-readable date/time strings::
    # https://github.com/bear/parsedatetime
    cal = parsedatetime.Calendar()
    cal.parseDT("tomorrow at 6am")
* dateparser - "python parser for human readable dates" - used by Maya for parsing natural date strings.
    https://github.com/scrapinghub/dateparser
    dateparser.parse('1 hour ago', languages=['en'])
    Supports: Gregorian calendar, Persian Jalali calendar, and Hijri/Islamic Calendar.
    "Development Status :: 2 - Pre-Alpha"
* datefinder, https://github.com/akoumjian/datefinder
    Uses regexes::
        matches = datefinder.find_dates(string_with_dates)
* recurrent - "Natural language parsing of dates and recurring events."
    https://github.com/kvh/recurrent
    recurrent.RecurringEvent(now_date=datetime.datetime(2010, 1, 1)).parse('every day starting next tuesday until feb')
* Chrono - "A natural language date parser. (Python version of chrono.js)"
    # https://github.com/wanasit/chrono-python
    Seems focused on en/jp/th (english, japan, thai)
* timeparser, https://github.com/thomst/timeparser
* pytimeparse - "A small Python module to parse various kinds of time expressions."
    https://github.com/wroberts/pytimeparse
    Is for parsing natural time deltas, e.g. "1 hour", not datetimes!
* bllip-parser, https://github.com/BLLIP/bllip-parser
    "BLLIP reranking parser (also known as Charniak-Johnson parser, Charniak parser, Brown reranking parser)".


Other date/time refs:
* http://strftime.org/ - how to use datetime.strftime()
*

Library refs and surveys:
* https://docs.google.com/spreadsheets/d/1dKt0R247B8Mx5sFXd7htSOQB-B5kMODM2ydmjp9cr80/edit#gid=0



Tips & Tricks:
---------------

If you want to see how the API works, just open the web interface in Chrome,
open the "Network" tab in the Developer Tools panel, set filter to "method:POST",
and start making changes.
You can see the endpoints queried as the ":path" under "Request Headers",
and the POST data under "Form data", particularly the "commands" key.


The Todoist v7 API:
-------------------

Refs:
* https://developer.todoist.com/?python#items

API v7 end points:
    /API/v7/sync
    /API/v7/query

    /API/v7/add_item
    /API/v7/quick/add

    /API/v7/activity/get
    /API/v7/completed
    /API/v7/completed/get_stats
    /API/v7/completed/get_all
    /API/v7/backups/get
    /API/v7/filters/get
    /API/v7/reminders/get

    templates/export_as_url
    templates/export_as_file
    templates/import_into_project

    uploads/add
    uploads/get
    uploads/delete


Requests to the /API/v7/sync endpoint:
* POST request data includes the main key 'commands', a list of dicts with commands to sync.
* A sync command is a dict (encoded as json string) with strings including
    ['type', 'args', 'uuid']

If you have a post request data, parse it as:
    d = urllib.parse.parse_qs(data)
    print(json.loads(d['commands'][0])[0].keys())


The Todoist web interface uses the Comet web application model:
* https://en.wikipedia.org/wiki/Comet_(programming)

Example Comet request URL:
    https://xcomet02.todoist.com/comet/1497916545644/?js_callback=CometChannel.scriptCallback&
    channel=user-111xxx28-41cxxx5e7faa8xxxxxxx&offset=-1&_client_id=_td_1497909186xxxx


"""

import datetime
from datetime import timedelta, timezone
import os
import re
import yaml
import todoist
# date/time packages:
import dateutil
import dateutil.parser
from dateutil.parser import parse as parse_date
# import pytz
# import pendulum
# import arrow
# import maya  # Kenneth's "Date and time for Humans" package.
# import moment
# import zulu


CONFIG_PATHS = [
    "~/.todoist_config.yaml"
]

TOKEN_PATHS = [
    "~/.todoist_token.txt"
]

TODOIST_DATE_FMT = ""
DAY_DATE_FMT = '%Y-%m-%d'

LABEL_REGEX = r"@\w+"
# extra_props_regex = r"(?P<prop_group>\{(R|r)eward:\s?(?P<reward>.+)\})"
# extra_props_regex = r"(?P<prop_group>\{(?P<props>\w+:\s?[^,]+)*\})"
# prop_kv_regex = r"(?P<key>\w+):\s?(?P<val>[^,]+)"
EXTRA_PROPS_REGEX = r"(?P<prop_group>\{(?P<props>(\w+:\s?[^,]+,?\s?)*)\})"
PROP_KV_REGEX = r"((?P<key>\w+):\s?(?P<val>[^,]+),?\s?)"
# TASK_REGEX = r"^(?P<title>.*?)\s*(?P<reward_group>\{(R|r)eward:\s?(?P<reward>.+)\})?\s*$"
TASK_REGEX = r"^(?P<title>.*?)" + EXTRA_PROPS_REGEX + "*\s*$"


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


def get_config():
    # for cand in CONFIG_PATHS:
    #     if os.path.isfile(cand):
    #         config_fn = cand
    #         break
    # else:
    #     return None
    fn_cands = map(os.path.expanduser, CONFIG_PATHS)
    # fn_cands = (os.path.expanduser(pth) for pth in CONFIG_PATHS)
    try:
        config_fn = next(cand for cand in fn_cands if os.path.isfile(cand))
    except StopIteration:
        return None
    with open(config_fn) as fp:
        config = yaml.load(fp)
    return config


def get_token():
    """

    Returns:
        str token, or None if no token was found.

    How to obtain and install a token:
        1. Log into your todoist.com account,
        2. Place the token string either in a single file in one of the paths listed in `TOKEN_PATHS`,
            or put the token in the configuration file keyed under 'token'.

    """
    fn_cands = map(os.path.expanduser, TOKEN_PATHS)
    try:
        fn = next(cand for cand in fn_cands if os.path.isfile(cand))
    except StopIteration:
        config = get_config()
        return None if config is None else config['token']
    with open(fn) as fp:
        token = fp.read().strip()
    return token


def get_todoist_api(token=None):
    if token is None:
        token = get_token()
    api = todoist.TodoistAPI(token=token)
    return api


def parse_task_dates(tasks, date_keys=("due_date", "date_added", "completed_date"), strict=False):
    endofday = datetime.time(23, 59, 59)
    from dateutil import tz
    localtz = tz.tzlocal()
    if strict:
        get = lambda task, key: task[key]
    else:
        get = lambda task, key: task.get(key)
    for task in tasks:
        if 'due_date_utc' in task:
            task['due_date'] = task['due_date_utc']

        for key in date_keys:
            # changed: `due_date` is now `due_date_utc`
            datestr = get(task, key)
            task['%s_dt' % key] = dateutil.parser.parse(datestr) if datestr is not None else None
            if datestr:
                # Note: These dates are usually in UTC time; you will need to convert to local timezone
                task['%s_local_dt' % key] = task['%s_dt' % key].astimezone(localtz)
                # task['due_time_local'] = task['due_date_local_dt'].time()
                due_time_local = task['%s_local_dt' % key].time()
                task['%s_time_HHMM' % key] = "{:%H:%M}".format(due_time_local)  # May be "23:59:59" if no time is set
                # due_time_opt: Optional time, None if due time is "end of day" (indicating no due time only due day).
                task['%s_time_opt' % key] = time_opt = due_time_local if due_time_local != endofday else None
                task['%s_time_opt_HHMM' % key] = "{:%H:%M}".format(time_opt) if time_opt else ""
                assert not any('%s' in k for k in task)  # Make sure we've replaced all '%s'


def print_todays_tasks(
        token=None, print_fmt="{content}", sort_key="default"
):
    """Print all tasks that are due today."""
    return print_query_result(query="today", token=token, print_fmt=print_fmt, sort_key=sort_key)


def print_overdue_tasks(
        token=None, print_fmt="{content}", sort_key="default"
):
    """Print all overdue tasks."""
    return print_query_result(query="overdue", token=token, print_fmt=print_fmt, sort_key=sort_key)


def print_today_or_overdue_tasks(
        token=None, print_fmt="{content}", sort_key="default"
):
    """Print all tasks that are either overdue or due today."""
    # OBS: If you return anything from a CLI entry point, the returned value is printed to stdout.
    ret = print_query_result(query="overdue | today", token=token, print_fmt=print_fmt, sort_key=sort_key)


def todoist_query(query, token=None):
    # if sort_key is None:
    #     sort_key=lambda t: t["due_date_dt"]
    api = get_todoist_api(token)
    # api.sync()  # updates and returns api.state.
    # If you are going to use any of the object models, you should always start by invoking api.sync()
    # If you are just going to use api.query(queries), then you don't need to sync.

    # TODO: Consider using the official todoist.managersfilters.FilterManager

    query_res = api.query(queries=[query])  # sequence of queries
    tasks = query_res[0]["data"]
    return tasks


def filter_tasks(tasks, filter):
    if isinstance(filter, dict):
        filter = list(filter.items())
    if isinstance(filter, list):
        print(filter)
        def filter_func(task):
            # print(filter)
            return all(task[k] == v for k, v in filter)
    else:
        filter_func = filter
    tasks = [task for task in tasks if filter_func(task)]
    return tasks


def sort_tasks(tasks, sort_key="default"):
    if sort_key == "default":
        # changed: `due_date` is now `due_date_utc`
        sort_key_func = lambda t: t["due_date_dt"] or datetime.datetime(2100, 1, 1)
    elif isinstance(sort_key, str):
        # Note: do not do `sort_key = lambda t: t[sort_key]` because the lambda function is only evaluated
        # after `sort_key` is updated (to be the lambda function) - weird result of Python's closure mechanism.
        sort_key_func = lambda t: t[sort_key]
    elif isinstance(sort_key, (list, tuple)):
        sort_key_func = lambda t: tuple(t[k] for k in sort_key)
    else:
        sort_key_func = sort_key
    tasks.sort(key=sort_key_func)
    return tasks


def parse_tasks(tasks, task_regex=None):
    """Tasks are parsed and updated in-place."""
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


def print_query_result(
        query, token=None, print_fmt="{content}", sort_key="default", filter=None,
        parse_task=True, task_regex=None,
):
    """Perform a search using a single query string and print the results.

    Args:
        query:
        token:
        task_fmt:
        sort_key:
        task_regex: Parse task['content'] and add

    Returns:
        List of results

    Examples:
        >>> token = get_token()
        >>> res = print_query_result("@reward", print_fmt="{content} - {checked}")  # print all task with rewards

        >>> res = print_query_result(
        >>>     "@reward", print_fmt="{title}\t{reward}}",
        >>>     task_regex="^(?P<title>.*?)\s*(?P<reward_group>\{reward:\s?(?P<reward>.+)\})?\s*$")

    ^(?P<title>.*?)\s*(?P<reward_group>\{reward:\s?(?P<reward>.+)\})
    (?P<title>.*)\s*(?P<reward_group>\{reward:\s?(?P<reward>.+)\})
    ^(?P<title>.*?)\s*(?P<reward_group>\{reward:\s?(?P<reward>.+)\})?\s*$
    ^(?P<title>.*?)\s*(?P<reward_group>\{(R|r)eward:\s?(?P<reward>.+)\})?\s*(?P<labels>(@\w+\s?)*\s?)*$
    ^(?P<title>.*?)\s*(?P<prop_group>\{(R|r)eward:\s?(?P<reward>.+)\})?\s*(?P<labels>(@\w+\s?)*)\s*$

    Check DFCI email {reward: 0.25h W} @Habit @Reward
    Check DFCI email @Habit @Reward {reward: 0.25h W}
    @Habit @Reward Check DFCI email {reward: 0.25h W}


    If you do this manually using the TodoistAPI class:
    todoist.TodoistAPI(token=token)

    """
    tasks = todoist_query(query, token)
    # Returns filtered, sorted task list
    tasks = print_tasks(tasks, print_fmt=print_fmt, sort_key=sort_key,
                        filter=filter, parse_task=parse_task, task_regex=task_regex)

    return tasks


def print_tasks(
        tasks, print_fmt="{content}", sep="\n",
        sort_key="default", filter=None,
        parse_task=True, task_regex=None,
    ):

    parse_task_dates(tasks)  # create datetime objects (*_dt) from string dates.

    if filter:
        filter_tasks(tasks, filter=filter)

    if sort_key:
        sort_tasks(tasks, sort_key=sort_key)

    if parse_task:
        parse_tasks(tasks, task_regex=task_regex)

    if print_fmt:
        print(sep.join(print_fmt.format(**task) for task in tasks))

    return tasks


def get_overdue_items(token=None, query="overdue", incl_time=False):
    api = get_todoist_api(token)
    api.sync()
    now = datetime.datetime.now(timezone.utc)
    # today = datetime.fromordinal(now.toordinal())  # ordinal only includes date not time.
    today = datetime.datetime(*now.timetuple()[:3])
    cut_date = now if incl_time else today
    # items = (item for item in api.items.all() if item['due_date_utc'])
    # overdue = [item for item in items if arrow.get(parse_date(item['due_date_utc'])) < cut_date]
    # overdue = [item for item in items if parse_date(item['due_date_utc']) < cut_date]
    # overdue = [item for item in items if arrow.get(parse_date(item['due_date_utc'])) < today]  # Using arrow
    # use timestamp (seconds from epoch):
    # overdue = [item for item in items if parse_date(item['due_date_utc']).timestamp() < cut_date.timestamp()]
    overdue = [item for item in api.items.all()
               if item['due_date_utc'] is not None
               and parse_date(item['due_date_utc']).timestamp() < today.timestamp()]
    return overdue


def get_todays_completed_events(token=None):
    api = get_todoist_api(token)
    # https://developer.todoist.com/?python#get-activity-logs
    # api.activity.get()  # will get all activity
    # keys are:
    # * object_type: e.g. item, note, etc.
    # * object_id: Only show for a particular object, but only if `object_type` is given.
    # * event_type: e.g. added, updated, completed, deleted,
    # * object_event_types: Combination of object_type and event_type.
    # * parent_project_id: Only show events for items or notes under a given project.
    # * parent_item_id: Only show event for notes under a given item.
    # * initiator_id: ?
    # * since, until: return event after/before these time (formatted as 2016-06-28T12:00).
    # * limit, offset: Maximum number of events to return, and paging offset.
    kwargs = dict(
        since="{:%Y-%m-%dT06:00}".format(datetime.date.today()),
        object_type='item',
        event_type='completed',
        limit=40,
    )
    events = api.activity.get(**kwargs)
    return events


def get_todays_completed_items(token=None):
    api = get_todoist_api(token)
    # https://developer.todoist.com/?python#get-all-completed-items
    # Only available for Todoist Premium users.
    # keys are:
    # * project_id: Only return completed items under a given project.
    # * annotate_notes: Return notes together with the completed items (a true or false value).
    # * since, until: return event after/before these time (formatted as 2016-06-28T12:00).
    # * limit, offset: Maximum number of events to return, and paging offset.
    kwargs = dict(
        # TODO: This is bit of a hack; only works for timezones near or west of UTC.
        since="{:%Y-%m-%dT06:00}".format(datetime.date.today()),
        limit=40,  # default=30, max=50.
    )
    res = api.completed.get_all(**kwargs)
    return res['items'], res['projects']


def inject_project_info(tasks, projects):
    for task in tasks:
        pid = task['project_id']
        # Todoist API sometimes returns string ids and sometimes integer ids.
        project = projects[pid if pid in projects else str(pid)]
        for k, v in project.items():
            task["project_%s" % k] = v


def print_todays_completed_items(
        token=None, print_fmt="{content}", sort_key="default",
        add_project_info=True,
):
    """Print all tasks that were completed today."""
    tasks, projects = get_todays_completed_items(token=token)
    # from pprint import pprint
    # pprint(tasks)
    # print()
    # pprint(projects)
    if add_project_info:
        inject_project_info(tasks, projects)
    tasks = print_tasks(tasks, print_fmt=print_fmt, sort_key=sort_key)
    return tasks


def reschedule_items(items, new_date='today'):
    """

    Args:
        items:

    Returns:

    How should this be done?

    Recurring tasks:
        Update `due_date_utc`, changing the date part to today but keeping the original time part.
        Keep `date_string` as-is.

    Non-recurring tasks:
        Update `due_date_utc`, changing the date part to today but keeping the original time part.
        Update `date_string` to "%m %d %H:%M" if date_string has a time, otherwise just "%m %d".
        Note: If due_date_utc does not have a time but is date-only, then the time will be 23:59:59, not 00:00.
        Which makes sense: task is due by the end of the day. OBS: The 59 seconds matter, 23:59:58 doesn't work.

    Example of request command to reschedule a task with id=2233091342 to Thur 22 Jun 2017 14:00:00 (EST; 18:00:00 UTC)
        [{
            "type":"item_update",
            "args":{"id":2233091342,"due_date_utc":"2017-6-22T18:00:00"},
            "uuid":"c51c443e-1316-9830-fa67-57aafd2815b1"
        }]
    (uuid is used to prevent executing duplicate or old requests)

    We can use ItemManager.update_date_complete() which uses the 'item_update_date_complete' command type:
        [{
            'type': 'item_update_date_complete',
            'uuid': 'a4663f86-5539-11e7-9273-38c9863570b9',
            'args': {'id': 2233091342, 'new_date_utc': '2017-06-21T00:00', 'date_string': 'every day at 10 pm'}
        }]
    Note: According to the docs this is mostly to mark recurring tasks as complete.

    If `new_date_utc` is wrong, you will get a SyncError:
        SyncError: (
            '87b2186e-5538-11e7-b699-38c9863570b9', {
                'error_extra': {'expected': 'date: YYYY-MM-DDTHH:MM', 'argument': 'new_date_utc'}, 
                'error_tag': 'INVALID_ARGUMENT_VALUE', 'error': 'Invalid argument value', 
                'command_type': 'item_update_date_complete', 'error_code': 20, 'http_code': 400})
    """
    # Expected date format: YYYY-MM-DDTHH:MM  (in UTC time!)
    if isinstance(new_date, datetime.datetime):
        new_date = new_date.strftime()
    else:
        try:
            datetime.datetime.strptime(new_date, "YYYY-MM-DDTHH:MM")
        except ValueError:
            # Assume new_date is in some kind of "natural language" format.
            import pendulum
            import maya
            import arrow
            import dateutil
            new_date = maya.parse(new_date)
            # Make sure the new due date is in UTC!
            new_date = "{:%y-%m-%dT%H:%M".format(new_date)
    # all_day_time = datetime.time
    # import maya
    for item in items:
        item['due_date_utc'] = new_date


def parse_date_string(date_str, iso_fmt=None):
    """Return (informal_date, iso_date_str, datetime_obj) tuple."""
    import dateutil
    date = dateutil.parser.parse(date_str)  # returns datetime object


def reschedule_cmd(query, new_date='today'):
    """

    Args:
        query:
        new_date:

    Returns:


    Discussion:


    Example POST request form data using the web interface to "reschedule" a single item:
        resource_types:["all"]
        commands: [{
            "type": "item_update",
            "args": {"date_string":"Aug 7", "date_lang":"en", "id":2235317410, "due_date_utc": "2017-8-8T03:59:59"},
            "uuid":"9b5ba425-7dcf-db4d-5a2a-d870bf731xxx"
        }]
        day_orders_timestamp:1502140199.43
        collaborators_timestamp:
        sync_token:xxxx
        with_web_static_version:true
        limit_notes:1
        max_notes:5
        with_dateist_version:1
        _client_id:_td_1501792xxxxx

    OBS: To see how the web interface uses the sync api, just open the "Network" tab in Chrome's developer tools
    and look for form data for requests to the /API/v7/sync endpoint.

    """
    # Q: Do we need an actual ISO date-string, or can we use the Todoist API to parse `new_date`?
    # Q: If we need an ISO date-string, can we use e.g. maya/arrow/pendulum to parse `new_date`?
    # Q: Which is better, to use the full "sync" API, or to reschedule individual tasks?
    # Q:
    # tasks = todoist_query(query)
    api = get_todoist_api()
    query_res = api.query(queries=[query])  # sequence of queries
    tasks = query_res[0]["data"]
    reschedule_items(tasks, new_date=new_date)
    api.sync()
    # Workflow:
    # 1. Sync:
    #   api.sync() -> api._update_state() -> populates api.state['items']
    # 2. Update:
    #   api.items.update(item_id, **kwargs) -> api.queue.append(cmd)
    # 3. Commit:
    #   api.commit() -> api.sync(commands=api.queue) -> api._post()

    date_string, due_date_utc, datetime_obj = parse_date_string(new_date)

    # api.items.all() is same as api.state['items']
    for item in api.items.all():
        # Yes, these are actual `model.Item` objects. Made during `api._update_state()` with::
        #    newobj = model(remoteobj, self); self.state[datatype].append(newobj)  # self = api
        item.update(date_string=date_string, due_date_utc=due_date_utc)

    api.commit()



def parse_args(argv=None):
    import argparse
    ap = argparse.ArgumentParser(prog="RS Todoist python CLI")
    subparsers = ap.add_subparsers(dest='command')
    # There are two ways to describe which subcommand to invoke depending on the subparser argument passed by the user.
    #  a. Capturing the subparser argument explicitly using the `dest` argument in ap.add_subparsers().
    #  b. Let the sub-parser set the subcommand function using sp.set_defaults(func=foo).

    # TODO: Use the method from `pptx-downsizer` to get default arguments from functions.
    sp = subparsers.add_parser('print-query')
    sp.set_defaults(func=print_query_result)
    sp.add_argument('--query', default="(overdue | today)")  # "(overdue | today) & #Work"

    # print_todays_completed_items
    sp = subparsers.add_parser('print-completed-today')
    sp.set_defaults(func=print_todays_completed_items)

    # print_todays_completed_items
    sp = subparsers.add_parser('print-today-or-overdue')
    sp.set_defaults(func=print_today_or_overdue_tasks)

    for cmd, sp in subparsers.choices.items():
        sp.add_argument('--print-fmt', default="{content}")
        sp.add_argument('--sort-key', default="default")

    # OBS: Do not make special switches, just use print-fmt and the regex-parsed variables.
    argns = ap.parse_args(argv)

    return argns


def main(argv=None):
    """

    Args:
        argv:

    Returns:


    Examples:
        $ todoist print-today-or-overdue --print-fmt "* {title}"

    """

    argns = parse_args(argv)
    args = vars(argns)
    command, func = args.pop('command'), args.pop('func')
    res = func(**args)
    # print_todays_tasks()
    # print_query_result(query="(overdue | today) & #Work")
    # print_query_result(query="no date")


if __name__ == '__main__':
    main()

