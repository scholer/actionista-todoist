

Actionista Action-Chain CLI for Todoist (actionista-todoist)
============================================================

Actionista Action CLI for Todoist.

Manage your Todoist tasks from the command line, using powerful filters to
select, print, reschedule, and complete tasks in a batch-wise fashion.

Do you have dozens or even hundreds of overdue tasks on your agenda?
Clear up your task list in seconds, using the Actionista Action CLI for Todoist.
You can now take the rest of the day off with a clear conscience.

This Action CLI for Todoist (`todoist-action-cli`), operates sequentially on a list of tasks.
You start out with a list of *all* tasks, and then select tasks using one of the many
filters available. You can then sort, print, and reschedule the selected tasks.

*Actionista* Action-Chain CLI for Todoist (actionista-todoist)
is inspired by the powerful `find` command line tool. It takes the "chain of actions"
approach that `find` uses to find and select files on your harddisk,
and applies it for managing your Todoist task list.

The successful `find` utility works by supplying a sequence of "actions"
(also known as "expressions" in the `find` manual).

Most actions are essentially filters, where you list criteria for the files to find.
However, the real usability of `find` is that it can not only print the matching files,
but also use the matching files for other actions, e.g. deleting the files,
or sending them to other command line tools.

The *actionista* action-chain CLI takes a similar approach.
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
For the record, doing the described sequence of actions would look something like this:

    $ todoist-action-cli -project Wedding -print \
        -due before today \
        -print \
        -reschedule tomorrow \
        -name startswith "Pick up the rings" \
        -rename "Remind Tommy to pick up the rings" \
        -commit


Usually, for your own sanity, command line usage would be a little more simple, and have only a single "purpose"
with each invocation:

    # Basic example: Find tasks containing the string "rings":

    $ todoist-action-cli -sync -name "*rings*" -sort -print



The generalized command line usage is:

    $ todoist-action-cli [-action [args]] [-action [args]] [...]


You can also import the package from python:

    >>> import actionista.todoist
    >>> import actionista.todoist.action_cli

Note: This package was formerly imported as ``rsenv.rstodo.todoist_action_cli``,
but has now been separated into its own package, imported as: ``actionista.todoist_action_cli``.


NOTE: This application is not created by, affiliated with, or supported by Doist.
It is a third-party command line utility that is making use of the official Todoist API,
as documented by https://developer.todoist.com/sync/v8/.



INSTALLATION:
-------------


### Installation with ``pipx``:

For regular end-users, I recommend using ``pipx`` to install the Actionista-Todoist command line apps:

	$ pipx install actionista-todoist

If you don't have pipx installed, you can refer to the
[pipx installation guide](https://pipxproject.github.io/pipx/installation/).
Briefly:

	$ pip install pipx
	$ pipx ensurepath

The last step will add `~/.local/bin` to the PATH environment variable.
Please make sure to close and restart your terminal/command prompt after
installing pipx for the first time.


Known installation errors:

* If you are using ``conda``, there is a known issue where you receive an error,
  "Error: [Errno 2] No such file or directory:", when trying to install packages with ``pipx``.
  If you get this error, please update your ``conda`` python and make sure you are only using
  the "defaults" channel, *not* "conda-forge".


### Installation with ``pip``:

To install distribution release package from the Python Packaging Index (PyPI):

    $ pip install -U actionista-todoist


Alternatively, install the latest git master source by fetching the git repository from github
and install the package in editable mode (development mode):

    $ git clone git@github.com:scholer/actionista-todoist && cd actionista-todoist
    $ pip install -U -e .



CONFIGURATION:
--------------

Once ``actionista-todoist`` package is installed, you need to obtain a login token from the todoist website:
Log into your todoist.com account, go to ``Settings -> Integrations``, and copy the API token.
(You can also go directly to the page: https://todoist.com/prefs/integrations).

Now run:

	$ actionista-todoist-config

to set up the login token with your Actionista-Todoist installation.
The API token is stored in ``~/.todoist_token.txt``.
The ``actionista-todoist-config`` command will also create a default config file,
``~/.todoist_config.yaml``, which you can edit to change default sorting and printing format.

If you re-set your Todoist API token, you can update it either by running:

	$ actionista-todoist-config --token <your-token-here>

or by manually editing the file ``~/.todoist_token.txt`` and place your token in here.



USAGE:
------

The ``actionista-todoist`` package contains several command line apps (CLIs):

* ``todoist-action-cli`` - also available as ``actionista-todoist``.
* ``todoist-cli``.
* ``actionista-todoist-config``.


The ``todoist-action-cli`` CLI program uses the "action chain" approach, where you specify a sequence
of "actions", which are used to filter/select tasks from Todoist and then sort, print, or reschedule
the selected tasks in a batch-wise fashion.

The ``todoist-cli`` CLI program is used mostly for things that doesn't fit the "action chain" philosophy.
For instance, if you want to add a new task, that doesn't really fit into the ``todoist-action-cli``
workflow.(*) Instead, you can use ``todoist-cli add-task`` command to add a new task to Todoist.
The ``todoist-cli`` is also used for other things, e.g. printing a list of your projects, etc.
You can run ``todoist-cli --help`` to see all available commands.

Finally, the ``actionista-todoist-config`` CLI program is used to set up Actionista-Todoist,
configuring your API login token, and creating a default configuration file.


(*) The ``todoist-action-cli`` can technically be used to add tasks to Todoist, using the
``-add-task`` action command - however, this is not the recommended approach.




### `todoist-action-cli` usage:


The general command line usage is:

    $ todoist-action-cli [actions]
    $ todoist-action-cli [-action [args]]

Where ``action`` is one of the following actions:

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

To see how to use each filter, type:

    $ todoist-action-cli -help <action_name>

E.g.:

    $ todoist-action-cli -help project
    $ todoist-action-cli -help filter
    $ todoist-action-cli -help reschedule



As you can see, typical usage is:

    $ todoist-action-cli -sync [one or more filter actions to select the tasks] -sort -print

The filter actions could be e.g. filtering by ``-name`` (same as ``-content``),
``project``, ``due_date_local_iso``, etc.
The ``-sync`` action is optional; if you do not specify ``-sync``, the program will just re-use the old cache,
from last time you invoked ``-sync``. You must invoke ``-sync`` at least once, when you first install this package,
and you should always ``-sync`` if you have made any changes (e.g. from your phone) since your last sync.
Finally, the ``-sort`` and ``-print`` commands will sort and print the selected tasks.

If you need to refine your filters, just run the command again. The data is cached locally,
so if you omit the ``-sync`` action, commands can be executed in rapid succession.


Another example, to reschedule the due date for a bunch of tasks, would look like:

    $ todoist-action-cli [-sync] [filter actions] [-sort] [-print] -reschedule "Apr 21" -commit


*NOTE: I **strongly** recommend that you ``-print`` the filtered tasks before you
``-rename`` or ``-reschedule`` the tasks. When you invoke ``-commit``, the changes cannot be undone automatically,
so you may easily end up with a bunch of identically-named tasks with the same due date, if you forgot to
apply the correct selection filters before renaming or rescheduling the tasks!
For this reason, the program will, by default, ask you for confirmation before every `-commit`.*


#### Action arguments:

Each action can be provided a set of arguments which are listed sequentially, separated by space.
If one argument contains spaces, e.g. you are filtering by tasks in the project "Meeting notes",
then you need to quote the argument as such:

    $ todoist-action-cli -sync -project "Meeting notes" -sort "project_name,content" ascending -print

Here, we provided one argument to the ``-project`` action (``"Meeting notes"``),
and two arguments to the ``-sort`` action (``"project_name,content"`` and ``ascending``).

Some of the actions attempts to be "clever" when interpreting the arguments given.
For instance, when filtering by project, you can do either:

    $ todoist-action-cli -project "Wedding*"
    $ todoist-action-cli -project glob "Wedding*"
    $ todoist-action-cli -project startswith Wedding

The general signature for the ``-project`` action is:

    $ todoist-action-cli -project [operator] value

Here, ``[operator]`` is the name of one of the many registered binary operators.
These are used to compare the tasks against a given value.
In the example above, if you do not specify any operator, then the "glob" operator is used.
The "glob" operator allows you to use wild-cards for selecting tasks, the same way you select files on the command line.
In our case, we "glob" against tasks with project name starting with the string "Wedding*".
We could also have used the "startswith" operator, and omit the asterisk:  ``startswith Wedding``.

For more info on how to use operators, see:

    $ todoist-action-cli -help operators





Ad-hoc CLI:
------------

Installing this project (``actionista-todoist``) with ``pip`` will also give you some
"ad-hoc" command line interface entry points:

    $ todoist-adhoc <command> <args>
    $ todoist-adhoc print-query <query> [<print-fmt>]
    $ todoist-adhoc print-completed-today [<print-fmt>]
    $ todoist-adhoc print-today-or-overdue-items [<print-fmt>]

    # And a couple of endpoints with convenient defaults, e.g.:

    $ todoist_today_or_overdue




Prior art: Other python-based Todoist projects
-----------------------------------------------

#### Other Todoist CLI packages that I know about:

* [todoist-cli](https://pypi.org/project/todoist-cli/0.0.1/) -
    A command line interface for batch creating Todoist tasks from a file.
    Makes manual requests against the web API url (rather than using the official todoist-python package).
    No updates since January 2016 (except `setup.py` and `requirements.txt`).
    This probably doesn't work, given that it uses an old, obsolete API endpoint URL.

* [todoicli](https://pypi.org/project/todoicli/) - A rather new project (as of April 2018).
    Focuses on pre-defined queries for listing tasks, e.g. "today and overdue", "next 7 days", etc.
    Lots of other functionality, pretty extensive code base.
    Has integration with the toggl.com time tracking service.
    Uses the official ``todoist-python`` package, but still uses the 
    "universal UTC" time format from the old v7 Sync API, and the v7 due-date structure.
    That means it probably won't work anymore, given that the v7 Sync API has been deprecated,
    and the `todoist-python` package has switched to Sync API v8.
    For instance, the `list td` and `list n7` uses `item['due_date_utc']`, which will raise 
    a `KeyError` with the new v8 data structure.
    The CLI also expects `IDs` (`task_id`, `label_id`, `project_id`), rather than text names,
    making it rather difficult to use for the end user.

* [pydoist](https://pypi.org/project/Pydoist/) - A basic CLI to add Todoist tasks from the command line.
    Uses the official `todoist-python` python API from Todoist.
    Lastest release was November 2016, so may not work with the new v8 Sync API.


#### Other general python Todoist packages:

* [python-todoist](https://pypi.org/project/todoist-python/) - The official python 
    'Todoist' package from Doist (the company behind Todoist).
    Is currently using the version 8.0 "Sync" API.

* [pytodoist](https://pypi.org/project/pytodoist/) - An alternative Todoist API package.
  Also uses the v7 Sync API.
  A rather different approach to API wrapping, perhaps more object oriented.
  Focused on modelling individual Users/Projects/Tasks/Notes,
  where the official todoist-python package has *managers* as the central unit
  (ItemsManager, ProjectsManager, NotesManager).

  * Last update November 2016 - will be obsolete when the v7 Sync API is removed.



