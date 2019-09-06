
Actionista Action CLI for Todoist
==================================


Actionista Action CLI for Todoist.

Manage your Todoist tasks from the command line, using powerful filters to
select, print, reschedule, and complete tasks in a batch-wise fashion.

Do you have dozens or even hundreds of overdue tasks on your agenda?
Clear up your task list in seconds, using the Actionista Action CLI for Todoist.
You can now take the rest of the day off with a clear conscience.

This Action CLI for Todoist (`todoist-action-cli`), operates sequentially on a list of tasks.
You start out with a list of *all* tasks, and then select tasks using one of the many
filters available. You can then sort, print, and reschedule the selected tasks.


Configuration:
--------------

In order to use the Todoist API, you need to configure an API access token.
You can use the `actionista-todoist-config` CLI to set this up.

You can run the full interactive configuration using:

	$ actionista-todoist-config --interactive

Alternatively, if you just need to update your API token, you can run:

	$ actionista-todoist-config --check-token --token 41f1c812be19cc3bcee6c6c2a569c545f7bfd7e1

(Replace `41f1c812be19cc3bcee6c6c2a569c545f7bfd7e1` with your actual API token.)

You can find your API token in the Todoist web app, under 'Settings' -> 'Integrations',
or by browsing directly to this page: https://todoist.com/prefs/integrations
(working directions as of September 2019).


Examples:
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




### Selecting tasks:

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


#### Task selection examples:

Print all tasks in your "Work" project.

	$ todoist-action-cli -sync -project "Work" -sort -print

To select tasks in both "Work", as well as "Work-dev" and "Work-admin",
just add an asterix after "Work". This will use "glob-style" pattern matching:

	$ todoist-action-cli -sync -project "Work*" -sort -print


### Sorting tasks:

Sort overdue tasks by due date:

	$ todoist-action-cli -due before today -sort "due_date_safe_dt" -print

Sort overdue tasks by priority, then due date, then project:

	$ todoist-action-cli -due before today -sort "priority_str,due_date_safe_dt,project_name" -print

* Note: We sort by "priority_str" (p1, p2, ...), since we are sorting in "ascending" mode by default,
  and priority_str gets the highest-priority tasks at the top.
  We could sort by "priority", but for "priority", higher values means "higher priority",
  while for "priority_str", a "p1" priority is higher than "p3".


### Closing/completing tasks:

Close (complete) a task starting with "Write" from project "Personal" (and also print the task):

	$ todoist-action-cli -sync -project "Personal" -startswith "Write" -print -close -commit

After invoking the command above, you should now see the task as being "checked off" when you print it:

	$ todoist-action-cli -sync -project "Personal" -startswith "Write" -sort -print

You can re-open the task again, if you need to:

	$ todoist-action-cli -sync -project "Personal" -startswith "Write" -print -reopen -commit


### Rescheduling tasks:

Reschedule task "Task123" (and also print the task):

	$ todoist-action-cli -sync -name "Task123" -print -reschedule "tomorrow" -commit

After invoking the command above, you should see that the task due day has changed when you print it:

	$ todoist-action-cli -sync -name "Task123" -print

You can generally specify dates and times the same way you would in Todoist,
e.g. using "2 days from now", "Wednesday 3 pm", "next monday", "2019-12-31 15:00", etc.


### Adding new tasks:

To add a new task, use the `-add-task` action:


You can add labels like you normally would using `@label`:

	$ todoist-action-cli -sync -add-task "Test task 005 @devtest #Dev-personal <date tomorrow> p2" -commit

However, as you can see, using "#project" and the normal ways of specifying due date and priority doesn't work.

You can provide information on `project`, `due` date, `priority`, and `labels` explicitly using `key=value` notation:

	$ todoist-action-cli -sync -add-task "Test task 006" project=Work due=tomorrow priority=p1 \
	  labels=awaiting,devtest -commit -filter content startswith "Test" -print "{content}"


### Showing changes before they are submitted:

If you are curious about what changes will be submitted to the server, you can see them before you `-commit`,
using `-show-queue` action:

	$ todoist-action-cli -sync -name "Task123" -print -reschedule "tomorrow" -show-queue -commit

	$ todoist-action-cli -sync -add-task "Test task 006" project=Work due=tomorrow priority=p1 labels=awaiting,devtest -show-queue fmt=json -commit


### Resetting cached data:

You may encounter a state that does not allow you to continue using `todoist-action-cli` or the todoist-python package.
If that happens, you can run the following command to delete the cache, thereby resetting the local state:

	$ todoist-action-cli inject_task_date_fields=0 inject_task_project_fields=0 -delete-cache

*OBS: If this happens, it may be due to a bug in this program.
If so, please consider submitting an issue at https://github.com/scholer/actionista-todoist/issues.
If you are technically proficiency and you have managed to fix a bug in this program,
I welcome you to submit a pull-request at https://github.com/scholer/actionista-todoist/pulls.*


Alternative Todoist CLI:
========================

This package also provides a more "traditional" CLI for Todoist.

The traditional CLI currently provides the following features:

* `add-task` - which can be used to add a new task to Todoist.
* `print-projects` - which can be used to print your Todoist projects.



Examples:
---------

### Example: Add a new task:

Add a task:

	$ todoist-cli add-task "Test task 1234"

Add a task, specifying due-date, project, labels, priority, and a note:

	$ todoist-cli add-task "Test task 1235 @devtest" --due "tomorrow 2 pm" --project "Todoist-playground" --label "playground" --priority p4 --note "This is a third note"

As you can see, you can add labels using "@label" as you do in the Todoist web-app,
or using `--label <label>`. The following three commands are all equivalent:

	$ todoist-cli add-task "Test task 1235" --label "playground" --label devtest
	$ todoist-cli add-task "Test task 1235 @devtest" --label "playground"
	$ todoist-cli add-task "Test task 1235 @devtest @playground"

Note that `todoist-cli add-task` is equivalent to `todoist-add-task`.
You can use whichever format you prefer.


### Example: Print projects

You can use the `print-projects` CLI command to print your Todoist projects:

	$ todoist-cli print-projects

