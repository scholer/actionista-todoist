# Copyright 2017–2018 Rasmus Scholer Sorensen

"""

This module contains a set of pre-defined todoist command line actions.

It is NOT a wrapper around the todoist api or any todoist library.
It is intended to be used from the comand line, or as reference examples for how to use the existing Todoist
libraries. It is not intended to be used in other code as a general Todoist library.


INSTALLATION:
-------------

1. Install this package in editable mode with pip:
    pip install -U -e .

2. Obtain a login token from the todoist website:
    Log into your todoist.com account, go to Settings → Integrations → Copy the API token.

3a. Create a file `~/.todoist_token.txt` and place your token in here, or
3b. Alternatively, create a file `~/.todoist_config.yaml` and add token as a yaml-entry:

    token: <token>



Examples, command line usage:
-----------------------------

`print-query` command:
* Note: --query defaults to "(overdue | today)"

    $ python -m actionista.todoist.adhoc_cli print-query [--query <query>] [--task-fmt <task-format>]

    $ python -m actionista.todoist.adhoc_cli print-query --print-fmt "* {due_date_time_opt_HHMM} > {title}"


`print-todays-completed-items` command:

    $ python -m actionista.todoist.adhoc_cli print-completed-today \
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



Todoist web APIs:
------------------

* Currently, the main Todoist API is the "Sync v7" API,
    available at https://todoist.com/api/v7/ (or https://api.todoist.com/API/v7/)

* Since the Sync API is a bit complicated for basic tasks, it seems Doist is also developing a basic REST API,
    available at https://developer.todoist.com/rest/v8/.
    This currently supports: Authorization and create/read/update/delete of projects/tasks/comments/labels/.



Todoist API packages:
---------------------

* https://github.com/Doist/todoist-python [installed] –
    Official python library from Doist, using requests (Session).
    Uses the Sync v7 API at 'https://todoist.com/api/v7/'.
    Has a main API object, which is synced with the server.
    Data (items/projects/notes/etc) is represented by thin model objects, which are controlled/manipulated by managers.
    Advanced functionality is delegated to the managers, e.g. ActivityManager.
    Documented at https://developer.todoist.com/.

* https://github.com/Garee/pytodoist [installed] –
    The second biggest Todoist library.
    Also uses the Sync v7 API - 'TodoistAPI.URL = https://api.todoist.com/API/v7/'
    Rolls its own API code using requests (`api` module), and object model (`todoist` module).


### About the official `python-todoist` package:

This is a little weird.
For instance, you cannot do a simple `for project in api.projects:`,
since `api.projects` is a ProjectsManager, which is not iterable.
The same goes for `api.items` and everything else that you would expect to be iterable.
You have to do `for task in api.state['items']`, or `for project in api.state['projects']`


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


The Todoist Sync v7 API:
-------------------------

Available at: https://todoist.com/api/v7/

Refs:
* https://developer.todoist.com/?python#items

Sync API v7 end points:
    /API/v7/sync
    /API/v7/query  (NOTE: DEPRECATED! Use sync API instead.)

    /API/v7/add_item
    /API/v7/quick/add

    /API/v7/activity/get
    /API/v7/completed
    /API/v7/completed/get_stats - Karma, etc.
    /API/v7/completed/get_all - Completed tasks.
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


### Activity log ('activity/get') vs Completed ('completed/get_all')

Example activity log event::

    {
      "id" : 955333384,
      "object_type" : "item",
      "object_id" : 101157918,
      "event_type" : "added",
      "event_date" : "Fri 01 Jul 2016 14:24:59 +0000",
      "parent_project_id" : 174361513,
      "parent_item_id" : null,
      "initiator_id" : null,
      "extra_data" : {
        "content" : "Task1",
        "client" : "Mozilla/5.0; Todoist/830"
      }
    }


Example completed/get_all response::

    {
      "items": [
        { "content": "Item11",
          "meta_data": null,
          "user_id": 1855589,
          "task_id": 33511505,
          "note_count": 0,
          "project_id": 128501470,
          "completed_date": "Tue 17 Feb 2015 15:40:41 +0000",
          "id": 33511505
        }
      ],
      "projects": {
        # All projects with items listed above.
      }
    }



Todoist v7.1 Sync API:
----------------------

I've started preparing to upgrade to v7.1 Sync API, because I realized there was no way to
reliably determine if a task is recurring in the v7.0 API.
Unfortunately, supporting both versions adds a bit of complexity.
Specifically, the v7.1 API deals with due dates differently.
Due dates are saved as a child dict attribute, rather than just a simple string,
The format has also changed to ISO8601, and instead of using "23:59:59" as "all day" due time,
it now just sets due.date to 'YYYY-MM-DD' with no time spec.
When this is transformed to datetime objects, the time is defaulted to 0:00:00,
which would make it difficult to filter and sort due dates.
I've thus directed `parse_task_dates()` to keep the old behaviour,
setting the datetime's local time to 23:59:59.

I'm not sure how task updating work in the v7.1 Sync API.




Todoist REST API v8:
--------------------

Currently available at https://beta.todoist.com/API/v8/
* Note: This is strikingly similar to the Sync v7 API: https://todoist.com/api/v7/

> "Our original API, named Sync API, provides an easy way to deal with full and partial syncs,
> but it’s not so simple for individual calls. REST API aims to provide API developers a friendly
> way to deal with the most basic features of Todoist API."

Refs/docs:
* https://developer.todoist.com/rest/v8/


Other notes:
-------------

The Todoist web interface uses the Comet web application model:
* https://en.wikipedia.org/wiki/Comet_(programming)

Example Comet request URL:
    https://xcomet02.todoist.com/comet/1497916545644/?js_callback=CometChannel.scriptCallback&
    channel=user-111xxx28-41cxxx5e7faa8xxxxxxx&offset=-1&_client_id=_td_1497909186xxxx


"""

import datetime
from datetime import timezone
import dateutil.parser
from dateutil.parser import parse as parse_date
from pprint import pprint

from todoist.models import Project

from actionista.todoist.tasks_utils import parse_task_dates, parse_tasks_content, inject_project_info
from actionista.todoist.utils import get_todoist_api


def todoist_query(query, token=None):
    """ Get tasks matching the given query.

    Note: This currently uses the `query` endpoint at https://todoist.com/API/v7/query, which has been deprecated.
    Apparently the `query` API endpoint had quality issues,
    c.f. https://github.com/Doist/todoist-api/issues/22 and https://github.com/Doist/todoist-python/issues/37.
    They currently recommend "client side filtering" after obtaining all todoist data via the Sync API.
    It seems they are building a new REST API ("v8") which allows for simple task queries using a filter string.

    Args:
        query: Filter/query string to search for tasks.
        token: Login token. If not provided, will try to load token from file or config.

    Returns:
        tasks: list of task dicts

    """
    api = get_todoist_api(token)
    # If you are going to use any of the object models, you should always start by invoking `api.sync()`,
    # which fetches and caches the whole Todoist state (and also returns it).
    # If you are just going to use api.query(queries), then you don't need to sync.
    # Note that the query endpoint was deprecated due to quality issues, sometimes returning unexpected results.
    # TODO: The `qyery` endpoint on the v7 "Sync" API has been deprecated.
    # TODO: Consider using saved filters via todoist.managers.filters.FilterManager,
    # TODO: Or alternatively use the new v8 "REST" API.
    # Edit: FiltersManager is only to create/read/update/delete filters, not applying filters. Same for models.Filter.
    query_res = api.query(queries=[query])  # `api.query` expects a sequence of queries
    tasks = query_res[0]["data"]
    return tasks


def filter_tasks(tasks, filter):
    """ Filter a list of tasks. Reference function.

    Args:
        tasks: List of task dicts.
        filter: Either
            (a) A dict or list of (key, filter_value) pairs used as `task[key] == filter_value`, or
            (b) a function that returns True for all elements that passes the filter.

    Returns:
        Filtered list of tasks.

    Examples:
        >>> filter_tasks(tasks, filter={'content': "My task", "checked": 0, })
    """
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
    """ Sort a list of tasks. Reference function. Default currenltly means "Sort by due date".

    The only noteworthy code here is the default sort by due date, where we use "2100-01-01"
    instead of None (because datetime and None cannot be compared).

    Args:
        tasks: A list of task dicts.
        sort_key: Sorting key(s) or function. Either:
            (a) A single key to sort by, or
            (b) a sequence of multiple keys to sort by, or
            (c) a key function (in which case, just use `tasks.sort(key=keyfunc)` directly?).

    Returns:
        Sorted list of tasks.
    """
    if sort_key is None or sort_key == "default":
        # changed: `due_date` is now `due_date_utc`
        sort_key_func = lambda task: task["due_date_dt"] or datetime.datetime(2100, 1, 1)
    elif isinstance(sort_key, str):
        # Note: do not do `sort_key = lambda task: task[sort_key]` because the lambda function is only evaluated
        # after `sort_key` is updated (to be the lambda function) - weird result of Python's closure mechanism.
        sort_key_func = lambda task: task[sort_key]
    elif isinstance(sort_key, (list, tuple)):
        sort_key_func = lambda task: tuple(task[k] for k in sort_key)
    else:
        sort_key_func = sort_key
    tasks.sort(key=sort_key_func)
    return tasks


def process_tasks(tasks, sort_key="default", filter=None, parse_task=True, task_regex=None):
    """ Parse dates, parse content, filter, sort -
    Args:
        tasks:
        sort_key:
        filter:
        parse_task:
        task_regex:

    Returns:
        Processed list of tasks.
    """

    # Parse date strings and create datetime objects (*_dt):
    parse_task_dates(tasks)

    # Parse custom metadata from task content (using `TASK_REGEX` regular expression):
    if parse_task:
        parse_tasks_content(tasks, task_regex=task_regex)

    if filter:
        tasks = filter_tasks(tasks, filter=filter)

    if sort_key:
        tasks = sort_tasks(tasks, sort_key=sort_key)

    return tasks


def print_tasks(
        tasks, print_fmt="{content}", sep="\n",
        sort_key="default", filter=None,
        parse_task=True, task_regex=None,
    ):
    """ Parse dates, parse content, filter, sort, and finally print a list of tasks.

    Returns:
        The processed (parsed/filtered/sorted) list of tasks.
    """

    if print_fmt:
        print(sep.join(print_fmt.format(**task) for task in tasks))

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

    If you do this manually using the TodoistAPI class:
        todoist.TodoistAPI(token=token)

    """
    tasks = todoist_query(query, token)
    # Returns filtered, sorted task list
    tasks = print_tasks(tasks, print_fmt=print_fmt, sort_key=sort_key,
                        filter=filter, parse_task=parse_task, task_regex=task_regex)
    return tasks


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


def get_overdue_items(token=None, query="overdue", incl_time=False):
    """ Get overdue tasks.
    Currently, this just invokes `api.sync()` and then filtering the response manually.

    It may be more appropriate to either:
        (a) Use a filter, either a saved filter (using `api.filters), or
        (b) Use the (now deprecated) `query/` endpoint, or
        (c) Use the REST API at https://beta.todoist.com/API/v8/

    """
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
               and parse_date(item['due_date_utc']).timestamp() < today.timestamp()]  # Timestamp is epoch float
    return overdue


def completed_get_all(token=None, project_id=None, since=None, until=None, limit=None, offset=None, annotate_notes=None):
    """ Get completed items, using the 'completed/get_all' endpoint (via CompletedManager).

    This endpoint is more specific than the Activity Log endpoint.
    It still returns a dict with "items" and "projects",
    but the data keys are more descriptive and specific (e.g. "completed_date" instead of "event_date").

    Note: This API endpoint is only available for Todoist Premium users.

    Refs/docs:
    * https://developer.todoist.com/?python#get-all-completed-items

    Available filter parameters/keys/kwargs for the 'completed/get_all' endpoint includes:
    * project_id: Only return completed items under a given project.
    * since, until: return event after/before these time (formatted as 2016-06-28T12:00).
    * limit, offset: Maximum number of events to return, and paging offset.
    * annotate_notes: Return notes together with the completed items (a true or false value).

    Note that while the regular Sync API uses ridiculous time format, the 'completed' API takes sane
    ISO-8601 formatted datetime strings for `since` and `until` params.

    Returns:
        A two-tuple of (items, projects).
        * Although maybe it is better to just return the response dict
            which contains two keys, "items" and "projects"?

    Note:
        * I'm having issues with the project_id for tasks not matching any projects.
        * The projects returned are good; it is indeed an issue with the project_id value. Maybe it is an old value?
        * This issue doesn't seem to be present for the `activity/get` endpoint.
        * This issue is NOT described in the docs, https://developer.todoist.com/sync/v7/#get-all-completed-items
        * The documented example makes it appear that item['project_id'] should match projects[id]['id'] .

    """
    api = get_todoist_api(token)
    kwargs = dict(
        project_id=project_id,
        since=since,
        until=until,
        limit=limit,
        offset=offset,
        annotate_notes=annotate_notes,
    )
    kwargs = {k: v for k, v in kwargs.items() if v is not None}
    print("\nRetrieving completed tasks from Todoist server...")
    res = api.completed.get_all(**kwargs)
    from pprint import pprint; pprint(res)
    return res['items'], res['projects']


def activity(
        token=None,
        object_type=None, object_id=None, event_type=None, object_event_types=None,
        parent_project_id=None, parent_item_id=None, initiator_id=None,
        since=None, until=None,
        limit=None, offset=None,
):
    """ Search using the activity log ('activity/get') endpoint.

    This endpoint can be used to retrieve all recent activity, all activity for a given project, etc.

    Refs/docs:
    * https://developer.todoist.com/?python#get-activity-logs

    Note: api.activity.get() without parameters will get all activity (limited to 30 entries by default).

    Endpoint parameters/keys are:
    * object_type (str): e.g. 'item', 'note', 'project', etc.
    * object_id (int): Only show for a particular object, but only if `object_type` is given.
    * event_type (str): e.g. 'added', 'updated', 'completed', 'deleted',
    * object_event_types: Combination of object_type and event_type.
    * parent_project_id: Only show events for items or notes under a given project.
    * parent_item_id: Only show event for notes under a given item.
    * initiator_id: ?
    * since, until: return event after/before these time (formatted as 2016-06-28T12:00).
    * limit, offset: Maximum number of events to return, and paging offset.

    Returns:
        events: A list of event dicts.

    """
    api = get_todoist_api(token)
    kwargs = dict(
        object_type=object_type, object_id=object_id, event_type=event_type, object_event_types=object_event_types,
        parent_project_id=parent_project_id, parent_item_id=parent_item_id, initiator_id=initiator_id,
        since=since, until=until,
        limit=limit, offset=offset,
    )
    kwargs = {k: v for k, v in kwargs.items() if v is not None}
    events = api.activity.get(**kwargs)
    return events


def get_todays_completed_events(token=None):
    """ Get all today's completed events using ActivityManager (against the 'activity/get' endpoint).
    See `activity()` for info.
    Since only tasks can be completed, this is basically just another way to get completed tasks.
    Better alternative: Use `get_todays_completed_items()`, which uses the CompletedManager.
    """
    api = get_todoist_api(token)
    kwargs = dict(
        since="{:%Y-%m-%dT06:00}".format(datetime.date.today()),
        object_type='item',
        event_type='completed',
        limit=40,
    )
    events = api.activity.get(**kwargs)
    return events


def get_todays_completed_items(token=None):
    """ Get todays completed items, using CompletedManager against the 'completed/get_all' endpoint.
    See `completed_get_all()` for info.
    Note: The completed/get_all endpoint seems to return tasks with wrong project_id values.
    Perhaps use activity/get endpoint via get_todays_completed_events() instead?
    """
    # TODO: Specifying since 'today' this way is bit of a hack; only works for timezones near or west of UTC.
    # TODO: Make proper, generic way of dealing with time and time strings!
    since="{:%Y-%m-%dT06:00}".format(datetime.date.today())
    print("Returning all completed tasks since UTC:", since)
    return completed_get_all(since=since)


def print_todays_completed_items(
        token=None, print_fmt="{content}", sort_key="default",
        add_project_info=False,
):
    """ Print all tasks that were completed today. """
    # tasks, projects = get_todays_completed_items(token=token)  # currently gives tasks with erroneous project_id.
    events = get_todays_completed_events(token=token)  # Use activity/get instead of completed/get_all.
    # This is just very generic, and instead of returning task items, it returns generic events.
    # The task name/content is available as event['extra_data']['content'], and
    # the task project_id is available as event['parent_project_id'].
    # So we cannot use the event directly; we would have to transform them.
    print("Events:")
    pprint(events)
    return
    # from pprint import pprint
    # pprint(tasks)
    # print()
    # pprint(projects)
    if add_project_info:
        # Disabling by default, since the project_id and projects returned by api.completed.get_all()
        # (at the completed/get_all endpoint) don't match up. The task's project_id is wrong, it seems!
        # http://todoist.com/API/v7/completed/get_all
        # Maybe they are just using old project_id values, but still.
        # Is the api.activity.get() endpoint at https://todoist.com/API/v7/activity/get any better?
        # Yes, it seems this gives correct project_id values for the returned tasks.
        inject_project_info(tasks, projects)
    tasks = print_tasks(tasks, print_fmt=print_fmt, sort_key=sort_key)
    return tasks


def reschedule_items(items, new_date='today'):
    """

    Args:
        items:

    Returns:

    How should task rescheduling be done?

    Rescheduling recurring tasks:
        Update `due_date_utc`, changing the date part to today but keeping the original time part.
        Keep `date_string` as-is.

    Rescheduling non-recurring tasks:
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

    date_string, due_date_utc, datetime_obj = dateutil.parser.parse(new_date)

    # api.items.all() is same as api.state['items']
    for item in api.items.all():
        # Yes, these are actual `model.Item` objects. Made during `api._update_state()` with::
        #    newobj = model(remoteobj, self); self.state[datatype].append(newobj)  # self = api
        item.update(date_string=date_string, due_date_utc=due_date_utc)

    api.commit()


def print_projects(print_fmt="pprint-data", sort_key=None, sync=True, sep="\n"):

    api = get_todoist_api()
    if sync:
        print("\nSyncing data with server...")
        api.sync()
    projects = api.state['projects']  # Not api.projects, which is a non-iterable ProjectsManager. Sigh.
    if print_fmt == "pprint":
        pprint(projects)
    elif print_fmt == "pprint-data":
        pprint([project.data for project in projects])  # Convert to list of dicts which prints better.
    else:
        for project in projects:
            fmt_kwargs = project.data if isinstance(project, Project) else project
            print(print_fmt.format(**fmt_kwargs), end=sep)


def parse_args(argv=None):
    import argparse
    ap = argparse.ArgumentParser(prog="RS Todoist python CLI")
    subparsers = ap.add_subparsers(dest='command')
    # There are two ways to describe which subcommand to invoke depending on the subparser argument passed by the user.
    #  a. Capturing the subparser argument explicitly using the `dest` argument in ap.add_subparsers().
    #  b. Let the sub-parser set the subcommand function using sp.set_defaults(func=foo).

    # TODO: Use the method from `pptx-downsizer` to get default arguments from functions. (Or, use click.)
    sp = subparsers.add_parser('print-query')
    sp.set_defaults(func=print_query_result)
    sp.add_argument('--query', default="(overdue | today)")  # "(overdue | today) & #Work"

    # print_todays_completed_items
    sp = subparsers.add_parser('print-completed-today')
    sp.set_defaults(func=print_todays_completed_items)

    # print_todays_completed_items
    sp = subparsers.add_parser('print-today-or-overdue')
    sp.set_defaults(func=print_today_or_overdue_tasks)

    # Add shared args for task commands:
    for cmd, sp in subparsers.choices.items():
        sp.add_argument('--print-fmt', default="{content}")
        sp.add_argument('--sort-key', default="default")

    # print_projects
    sp = subparsers.add_parser('print-projects')
    sp.set_defaults(func=print_projects)
    sp.add_argument('--print-fmt', default="pprint")
    sp.add_argument('--sort-key', default="default")

    # OBS: Do not make special switches, just use print-fmt and the regex-parsed variables.
    argns = ap.parse_args(argv)

    return argns


def main(argv=None):
    """ Main CLI entry point.

    Args:
        argv: Command line arguments (default: sys.argv)

    Returns:
        None

    Examples:
        $ todoist print-today-or-overdue --print-fmt "* {title}"
        $ todoist print-completed-today --print-fmt "* {title}"

    """

    argns = parse_args(argv)
    args = vars(argns)
    command, func = args.pop('command'), args.pop('func')  # command is the subparser name; func is the function obj.
    res = func(**args)
    # print_todays_tasks()
    # print_query_result(query="(overdue | today) & #Work")  # Note: 'query' endpoint deprecated because weird results.
    # print_query_result(query="no date")


if __name__ == '__main__':
    main()
