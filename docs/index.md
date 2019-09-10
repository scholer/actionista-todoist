
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
Together with other actions, you can `print`, `reschedule`, `rename`, `close`, or `delete`
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

