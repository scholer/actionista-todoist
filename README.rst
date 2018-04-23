

Actionista Action-Chain CLI for Todoist (action-todoist)
=========================================================

A `find`-inspired "action chain" command line tool for managing your Todoist task list.

The successful `find` utility works by supplying a sequence of "actions"
(also known as "expressions" in the `find` manual).
Most actions are essentially filters, where you list criteria for the files to find.
However, the real usability of `find` is that is can not only print the matching files,
but also use the matching files for other actions, e.g. deleting the files,
or sending them to other command line tools.

The actionista action-chain CLI takes a similar approach.
Starting from the full list of tasks, you can apply filters to find exactly those tasks that you need.
Together with other actions, you can `print`, `reschedule`, `rename`, `mark-complete`, or `delete`
whatever tasks you need.
You can invoke as many actions as you need, both filters and other actions, in any order.
The actions are invoked in exactly the order you specify.

So if you want, you can filter tasks by e.g. project name, and print all tasks in a given project,
then filter by due date, and print again, then reschedule the tasks that were just printed,
then filter by exact name, then mark that (or those) remaining task(s) as complete,
and finally commit the changes to the server.
This example is mostly just to show what is possible,
and I personally wouldn't recommend having such a complex list of actions,
but you are basically free to list as many (or as few) actions as you want or need.
For the record, doing the described sequence of actions would look something like this::

    $ todoist-action-cli -project Wedding -print \
        -due before today -print -reschedule tomorrow
        -name startswith "Pick up tux" -rename "Ask Tommy to pick up tuxido"
        -commit




This package was formerly imported as rsenv.rstodo.todoist_action_cli,
but has now been separated into its own package, imported as: `actionista.todoist_action_cli`.
It can be invoked with either of two commands::

    $ todoist-action-cli  [old name]


NOTE: This application is not created by, affiliated with, or supported by Doist.
It is a third-party command line utility that is making use of the official Todoist API,
as documented by https://developer.todoist.com/sync/v7/.


INSTALLATION:
-------------

To install distribution release package from the Python Packaging Index (PyPI)::

    $ pip install -U action-todoist


Alternatively, install the latest git master source by fetching the git repository from github
and install the package in editable mode (development mode)::

    $ git clonse git@github.com:scholer/action-todoist && cd action-todoist
    $ pip install -U -e .




USAGE:
------

Basic usage is::

    $ todoist-action-cli [actions]
    $ todoist-action-cli [-action [args]]

Where `action` is one of the following actions::

    # Task selection (task filtering):

    'filter': filter_tasks,
    'has': filter_tasks,  # Undocumented alias, for now.
    'is': special_is_filter,  # Special cases, e.g. "-is incomplete" or "-is not overdue".
    'not': is_not_filter,
    'due': due_date_filter,
    # contains, startswith, glob/iglob, eq/ieq are all trivial derivatives of filter:
    # But they are special in that we use the binary operator name as the action name,
    # and assumes we want to filter the tasks, using 'content' as the task key/attribute.
    'contains': content_contains_filter,
    'startswith': content_startswith_filter,
    'endswith': content_endswith_filter,
    'glob': content_glob_filter,
    'iglob': content_iglob_filter,
    'eq': content_eq_filter,
    'ieq': content_ieq_filter,
    # Convenience actions where action name specifies the task attribute to filter on:
    'content': content_filter,  # `-content endswith "sugar".
    'name': content_filter,  # Alias for content_filter.
    'project': project_filter,
    'priority': priority_filter,
    # More derived 'priority' filters:
    'priority-eq': priority_eq_filter,
    'priority-ge': priority_ge_filter,
    'priority-str': priority_str_filter,
    'priority-str-eq': priority_str_eq_filter,
    'p1': p1_filter,
    'p2': p2_filter,
    'p3': p3_filter,
    'p4': p4_filter,

    # Sorting and printing actions:
    'sort': sort_tasks,
    'print': print_tasks,

    # Update task actions:
    'reschedule': reschedule_tasks,
    'mark-completed': mark_tasks_completed,
    'mark-as-done': mark_tasks_completed,

    # The following actions are overwritten when the api object is created inside the action_cli() function:
    'verbose': None, 'v': None,
    'delete-cache': None,
    'sync': None,
    'commit': None,
    'show-queue': None,


Installing this project (``action-todoist``) with ``pip`` will also give you some
"adhoc" command line interface entry points::

    $ todoist <command> <args>
    $ todoist print-query <query> [<print-fmt>]
    $ todoist print-completed-today [<print-fmt>]
    $ todoist print-today-or-overdue-items [<print-fmt>]

    # And a couple of endpoints with convenient defaults:
    $ todoist_today_or_overdue




Other python-based Todoist projects:
------------------------------------

**Other Todoist CLI packages that I know about:**

* [todoist-cli](https://pypi.org/project/todoist-cli/0.0.1/) -
    A command line interface for batch creating Todoist tasks from a file.
    Makes manual requests against the web API url (rather than using the official todoist-python package).
    No updates since January 2016.
* [todoicli](https://pypi.org/project/todoicli/) - A rather new project (as of April 2018).
    Focuses on pre-defined queries for listing tasks, e.g. "today and overdue", "next 7 days", etc.
    Lots of other functionality, pretty extensive code base.
    Uses the official `todoist-python` package.
* {pydoist}(https://pypi.org/project/Pydoist/) - A basic CLI to add Todoist tasks from the command line.

**Other general python Todoist packages:**

* python-todoist - The official python 'Todoist' package from Doist (the company behind Todoist).
    Is currently using the version 7.0 "Sync" API.
* [pytodoist](https://pypi.org/project/pytodoist/) - An alternative Todoist API package.
    Also uses the v7 Sync API.
    A rather different approach to API wrapping, perhaps more object oriented.
    Focused on modelling individual Users/Projects/Tasks/Notes,
    where the official todoist-python package has *managers* as the central unit
    (ItemsManager, ProjectsManager, NotesManager).







TODOIST web APIs:
-----------------

For a detailed discussion about the official Todoist Web APIs, see `todoist.py` module docstring.


## TODOIST SYNC API v7 notes:


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



