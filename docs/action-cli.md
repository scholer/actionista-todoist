
`todoist-action-cli` usage
===========================

Actionista Action CLI for Todoist.

Manage your Todoist tasks from the command line, using powerful filters to
select, print, reschedule, and complete tasks in a batch-wise fashion.

Do you have dozens or even hundreds of overdue tasks on your agenda?
Clear up your task list in seconds, using the Actionista Action CLI for Todoist.
You can now take the rest of the day off with a clear conscience.

This Action CLI for Todoist (`todoist-action-cli`), operates sequentially on a list of tasks.
You start out with a list of *all* tasks, and then select tasks using one of the many
filters available. You can then sort, print, and reschedule the selected tasks.



Examples
---------

> OBS: In all examples, a code line starting with `$ ` means that it should be run from
> the terminal / command prompt.

### Basic actions:

The basic actions are:

* `-sync` - make sure you have the latest updates from the Todoist server.
* `-print` - used to print tasks out (in the terminal).
* `-commit` - used to submit any changes that you've made.

Almost all examples starts with a `-sync` action,
followed by one or more task selection (filtering) actions,
followed by a `-sort` action to sort the selected tasks,
then a `-print` action to print the selected tasks out.

If you want to make changes, e.g. close or reschedule the selected tasks,
you just add the desired action command (e.g. `-close` or `-reschedule "tomorrow"),
followed by `-commit` to submit your changes to the server.

*Please make sure to remember the `-commit` action, if you want your changes to have any effect!*




### Selecting tasks

You typically use the following actions for selecting (filtering) tasks:

* `-name "task-content"` - select tasks by the task name ("content").
* `-project "project-name"` - select tasks in a given project.
* `-due [before/after "date"]` - select tasks by due date.
* `-is [not] recurring` - select recurring or non-recurring tasks.

You can use "glob patterns" when selecting tasks by task name or project.
For instance, `-project "Dev*"` will select tasks for all projects that begin with "Dev".

For more info on "glob pattern matching", see e.g. [this](https://facelessuser.github.io/wcmatch/glob/)
or [wikipedia](https://en.wikipedia.org/wiki/Glob_(programming)).

Additional convenience actions to filter/select tasks by task name:

* `-contains "text"` - the same as `-name "*text*"`.
* `-startswith "text"` - the same as `-name "text*"`.
* `-endswith "text"` - the same as `-name "*text"`.


#### Task selection examples

Print all tasks in your "Work" project.

	$ todoist-action-cli -sync -project "Work" -sort -print

To select tasks in both "Work", as well as "Work-dev" and "Work-admin",
just add an asterix after "Work". This will use "glob-style" pattern matching:

	$ todoist-action-cli -sync -project "Work*" -sort -print


### Sorting tasks

Sort overdue tasks by due date:

	$ todoist-action-cli -due before today -sort "due_date_safe_dt" -print

Sort overdue tasks by priority, then due date, then project:

	$ todoist-action-cli -due before today -sort "priority_str,due_date_safe_dt,project_name" -print

* Note: We sort by "priority_str" (p1, p2, ...), since we are sorting in "ascending" mode by default,
  and priority_str gets the highest-priority tasks at the top.
  We could sort by "priority", but for "priority", higher values means "higher priority",
  while for "priority_str", a "p1" priority is higher than "p3".


### Closing/completing tasks

Close (complete) a task starting with "Write" from project "Personal" (and also print the task):

	$ todoist-action-cli -sync -project "Personal" -startswith "Write" -print -close -commit

After invoking the command above, you should now see the task as being "checked off" when you print it:

	$ todoist-action-cli -sync -project "Personal" -startswith "Write" -sort -print

You can re-open the task again, if you need to:

	$ todoist-action-cli -sync -project "Personal" -startswith "Write" -print -reopen -commit


### Rescheduling tasks

Reschedule task "Task123" (and also print the task):

	$ todoist-action-cli -sync -name "Task123" -print -reschedule "tomorrow" -commit

After invoking the command above, you should see that the task due day has changed when you print it:

	$ todoist-action-cli -sync -name "Task123" -print

You can generally specify dates and times the same way you would in Todoist,
e.g. using "2 days from now", "Wednesday 3 pm", "next monday", "2019-12-31 15:00", etc.


### Adding new tasks

To add a new task, use the `-add-task` action:


You can add labels like you normally would using `@label`:

	$ todoist-action-cli -sync -add-task "Test task 005 @devtest #Dev-personal <date tomorrow> p2" -commit

However, as you can see, using "#project" and the normal ways of specifying due date and priority doesn't work.

You can provide information on `project`, `due` date, `priority`, and `labels` explicitly using `key=value` notation:

	$ todoist-action-cli -sync -add-task "Test task 006" project=Work due=tomorrow priority=p1 \
	  labels=awaiting,devtest -commit -filter content startswith "Test" -print "{content}"


### Rename a task

To rename an existing task, first select it using one or more filters, then use the `-rename` action.
For example:

	$ todoist-action-cli -label devtest -content "Test task 1435" -sort -print -rename "Test task 1850" -commit

Then check that it has been renamed:

	$ todoist-action-cli -label devtest -content "Test task *" -sort -print


### Showing changes before they are submitted

If you are curious about what changes will be submitted to the server, you can see them before you `-commit`,
using `-show-queue` action:

	$ todoist-action-cli -sync -name "Task123" -print -reschedule "tomorrow" -show-queue -commit

	$ todoist-action-cli -sync -add-task "Test task 006" project=Work due=tomorrow priority=p1 labels=awaiting,devtest -show-queue fmt=json -commit


### Resetting cached data

You may encounter a state that does not allow you to continue using `todoist-action-cli` or the todoist-python package.
If that happens, you can run the following command to delete the cache, thereby resetting the local state:

	$ todoist-action-cli inject_task_date_fields=0 inject_task_project_fields=0 -delete-cache

*OBS: If this happens, it may be due to a bug in this program.
If so, please consider submitting an issue at https://github.com/scholer/actionista-todoist/issues.
If you are technically proficiency and you have managed to fix a bug in this program,
I welcome you to submit a pull-request at https://github.com/scholer/actionista-todoist/pulls.*



Detailed usage description:
---------------------------

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


#### Action arguments

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


