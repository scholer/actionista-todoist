

Actionista Action-Chain CLI for Todoist (actionista-todoist)
============================================================

A ``find``-inspired "action chain" command line tool for managing your Todoist task list.

The successful ``find`` utility works by supplying a sequence of "actions"
(also known as "expressions" in the ``find`` manual).
Most actions are essentially filters, where you list criteria for the files to find.
However, the real usability of ``find`` is that is can not only print the matching files,
but also use the matching files for other actions, e.g. deleting the files,
or sending them to other command line tools.

The actionista action-chain CLI takes a similar approach.
Starting from the full list of tasks, you can apply filters to find exactly those tasks that you need.
Together with other actions, you can ``print``, ``reschedule``, ``rename``, ``mark-complete``, or ``delete``
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
but has now been separated into its own package, imported as: ``actionista.todoist_action_cli``.
It can be invoked with either of two commands::

    $ todoist-action-cli  [old name]


NOTE: This application is not created by, affiliated with, or supported by Doist.
It is a third-party command line utility that is making use of the official Todoist API,
as documented by https://developer.todoist.com/sync/v7/.


INSTALLATION:
-------------

To install distribution release package from the Python Packaging Index (PyPI)::

    $ pip install -U actionista-todoist


Alternatively, install the latest git master source by fetching the git repository from github
and install the package in editable mode (development mode)::

    $ git clonse git@github.com:scholer/actionista-todoist && cd actionista-todoist
    $ pip install -U -e .




USAGE:
------

Basic usage is::

    $ todoist-action-cli [actions]
    $ todoist-action-cli [-action [args]]

Where ``action`` is one of the following actions::

    # Sorting and printing tasks:

      -print                 Print tasks, using a python format string.
      -sort                  Sort the list of tasks, by task attribute in ascending or descending order.

    # Task selection (filtering):

      -filter                Generic task filtering method based on comparison with a specific task attribute.
      -has                   Generic task filtering method based on comparison with a specific task attribute.
      -is                    Special -is filter for ad-hoc or frequently-used cases, e.g. `-is not checked`, etc.
      -not                   Convenience `-not` action, just an alias for `-is not`. Can be used as e.g. `-not recurring`.
      -due                   Special `-due [when]` filter. Is just an alias for `-is due [when]`.
      -contains              Convenience filter action using taskkey="content", op_name="contains".
      -startswith            Convenience filter action using taskkey="content", op_name="startswith".
      -endswith              Convenience filter action using taskkey="content", op_name="endswith".
      -glob                  Convenience filter action using taskkey="content", op_name="glob".
      -iglob                 Convenience filter action using taskkey="content", op_name="iglob".
      -eq                    Convenience filter action using taskkey="content", op_name="eq".
      -ieq                   Convenience filter action using taskkey="content", op_name="ieq".
      -content               Convenience adaptor to filter tasks based on the 'content' attribute (default op_name 'iglob').
      -name                  Convenience adaptor to filter tasks based on the 'content' attribute (default op_name 'iglob').
      -project               Convenience adaptor for filter action using taskkey="project_name" (default op_name "iglob").
      -priority              Convenience adaptor for filter action using taskkey="priority" (default op_name "eq").
      -priority-eq           Convenience filter action using taskkey="priority", op_name="eq".
      -priority-ge           Convenience filter action using taskkey="priority", op_name="ge".
      -priority-str          Convenience adaptor for filter action using taskkey="priority_str" (default op_name "eq").
      -priority-str-eq       Convenience filter action using taskkey="priority_str", op_name="eq".
      -p1                    Filter tasks including only tasks with priority 'p1'.
      -p2                    Filter tasks including only tasks with priority 'p2'.
      -p3                    Filter tasks including only tasks with priority 'p3'.
      -p4                    Filter tasks including only tasks with priority 'p3'.

    # Updating tasks:

      -reschedule            Reschedule tasks to a new date/time.
      -mark-completed        Mark tasks as completed using method='close'.
      -mark-as-done          Mark tasks as completed using method='close'.

    # Synchronizing and committing changes with the server:

      -sync                  Pull task updates from the server to synchronize the local task data cache.
      -commit                Commit is a sync that includes local commands from the queue, emptying the queue. Raises SyncError.
      -show-queue            Show list of API commands in the POST queue.
      -delete-cache          Delete local todoist data cache.
      -print-queue           Show list of API commands in the POST queue.

    # Program behavior:

      -verbose, -v           Increase program informational output verbosity.
      -yes, -y               Disable confirmation prompt before enacting irreversible commands, e.g. -commit.
      -help, -h              Print help messages. Use `-help <action>` to get help on a particular action.




Installing this project (``actionista-todoist``) with ``pip`` will also give you some
"adhoc" command line interface entry points::

    $ todoist <command> <args>
    $ todoist print-query <query> [<print-fmt>]
    $ todoist print-completed-today [<print-fmt>]
    $ todoist print-today-or-overdue-items [<print-fmt>]

    # And a couple of endpoints with convenient defaults, e.g.:

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
    Uses the official ``todoist-python`` package.
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

For a detailed discussion about the official Todoist Web APIs, see ``todoist.py`` module docstring.


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



