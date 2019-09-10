

Alternative Todoist CLI
========================

This package also provides a more "traditional" CLI for Todoist.

The traditional CLI currently provides the following features:

* `add-task` - which can be used to add a new task to Todoist.
* `print-projects` - which can be used to print your Todoist projects.



Examples
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

