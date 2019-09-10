
USAGE
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

