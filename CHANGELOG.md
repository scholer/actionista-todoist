


Version 2019.09.09:
-------------------


### `todoist-action-cli` changes:

* NEW: Label names are now added to tasks as derived custom data fields 'label_names' and 'labels_str'.
	Note that 'label_names' is a list, and must be used accordingly.
	The derived label fields can be used e.g. for printing, sorting, or filtering:
	* `todoist-action-cli -sync -filter label_names contains habit -sort "labels_str,project_name" -print "{content} ({labels_str})"
	* Please notice the order of operands for the `-filter` command: `filter <key> <op> <value>`.

* NEW: Added convenience **`-label`** filter action, which will filter tasks based on the given label.
 	`-label <label>` is equivalent to `-filter label_names icontains <label>`.
	* Note the use of `icontains`, making the comparison case-insensitive.

* NEW: Added support for negative-filtering using exclamation marks.
  Using negative filtering was already possible using `-filter <key> not <op> <value>`,
  or one of the many "negative-filtering" convenience filter actions.
  But this adds support for using "!value" to negate the filter,
  e.g. `-label !habit` to filter out tasks with the "habit" label.

* NEW: Added support to disable injecting 'label_names' and 'labels_str' derived fields, using:
	* `todoist-action-cli inject_task_labels_fields=0`.

* NEW: Added support for disabling all injections of derived data fields using:
	* `todoist-action-cli inject_derived_task_fields=0`.


### Other code changes:

* The "case-insensitive" operators in `actionista.binary_operators` now work for lists, sets, and dicts.
	Before, the case-insensitive operators would just use `a.lower()` (or occationally `str(a).lower()`).
	But now, the elements in a list/set/dict are converted to lowercase, recursively.
	For dicts, the keys are converted to lowercase as well.


*For developer-relevant code changes, please check the git commit log.*



Version 2019.09.06:
-------------------

### New `todoist-cli` CLI command:

* Added alternative `todoist-cli`, a more traditional, Click-enabled CLI.
  `todoist-cli` is a command group with sub-commands `add-task` and `print-projects`.
    * The `todoist-cli` CLI superseds the old, argparse-based `todoist-adhoc-cli` CLI 
      (which will probably be renamed to `todoist-argparse-cli`).
* Added `add-task` sub-command to `todoist-cli` CLI.
  You can use `todoist-cli add-task` to add a new task to Todoist.
  You can also invoke this command directly using `todoist-add-task`.
* Added `print-projects` sub-command to `todoist-cli` CLI.
  You can use `todoist-cli print-projects` to print/list your Todoist projects.
  This is useful if you need to e.g. add a task, but you can't remember the Todoist project names.

### New `actionista-todoist-config` CLI command:

* Added `actionista-todoist-config` CLI, which can be used to update the API token and create default config file.
  You can now configure Actionista for Todoist by invoking `actionista-todoist-config`
  from the command line.
   

### Other changes:

* All Actionista for Todoist CLI commands will now append "Actionista-Todoist" info the HTTP User-Agent header
  to `python-requests/<requests version> Actionista-Todoist/<actionista version>`.
  The User-Agent will appear in your activity list, making it more obvious what changes you've 
  made using the Actionista for Todoist CLIs.


*For developer-relevant code changes, please check the git commit log.*



Version 2019.09.04:
-------------------


* Switched to using the new v8 Sync API version.
    * Major differences from v7: (1) How due dates are stored - now under a dedicated `due` attribute, 
    and using "floating", rather than "fixed" timezones; times are, by default, in the user's timezone,
    rather than UTC). And (2) projects and tasks are now using an actual "parent-child" tree, rather than 
    simply using "indent" and "order" attributes. Tasks and projects still have an "order", but it is relative 
    to it  siblings under the same parent. There is also still "day_order" (the order on the "today" page),
    that haven't changed.

* Now storing derived fields (e.g. "due_date_safe_dt", "project_name", and "checked_str") 
  in separate attribute (`_custom_data`, by default), instead of contaminating the 
  primary `.data` attribute.


### Added `todoist-action-cli` features:

* Added **-add-task** action, which can be used to add a new task. 
  The task's project, priority, and due date is specified using `due=when` notation.
  If you want to perform additional actions after adding a new task (e.g. `-print` or `-sort`), 
  please make sure to `-commit` after adding the the new task before doing so.

* Added **`-close`** action, which can be used to close (complete) the selected task(s):

    `$ todoist-action-cli -sync -name "Task to complete" -close -commit`

* Added **`-reopen`** action, which can be used to reopen (uncomplete) the selected task(s):

    `$ todoist-action-cli -sync -name "Task to uncomplete" -reopen -commit`

* Added **`-archive`** action, which can be used to archive the selected task(s):

    `$ todoist-action-cli -sync -is completed -name "Starts-with-this*" -archive -commit`

* Added **`-delete`** action, which can be used to delete the selected task(s):

    `$ todoist-action-cli -sync -project "Delete-tasks-in-this-project" -delete -commit`

* Fixed `-reschedule` command so it is cleaner and compliant with v8 Sync API.

* Added option to skip parsing and injection of derived date and project fields, 
  using `todoist-action-cli inject_task_date_fields=0 inject_task_project_fields=0`.
  This is useful if your cache is corrupted and you need to delete the cache without doing any 
  parsing tasks:

      $ todoist-action-cli inject_task_date_fields=0 inject_task_project_fields=0 -delete-cache

* Moved all tasks action commands to separate module, `action_commands`.

*For developer-relevant code changes, please check the git commit log.*





2019-09-03: Move to Todoist Sync API v8
----------------------------------------

### What has changed between v7 and v8 of the Sync API?

Task `due` property changes:

* Task items not have a dedicated `due` dict property, instead of the `due_date_utc` and friends.
	* This change, with a dedicated `due` property, was actually already present in the Sync API v7.1.
* This affect these methods:
	* The `items.add()` and `items.update()` methods now expect a `due` parameter,
	  instead of the `date_string`, `date_lang` and/or `due_date_utc` parameters.
	* The `items.update_date_complete()` method now expects a `due` parameter,
	  instead of `new_date_utc`, `date_string` and/or `is_forward` parameters.
* The new `due` property has the following:
	* `date` (str): RFC-3339 date, either "YYYY-MM-DD" or "YYYY-MM-DDTHH:MM:SS".
		If `date` is YYYY-MM-DD, it is considered an "all day" item with no specified time.
		This is different from the v7 API, where a time of 23:59:59 was used to indicate an "all day" task.
	* So, a major difference is that an "all-day" task in v7 API had a time of 23:59:59,
		while an "all day" task in v8 API does not have a time.
	* `timezone` (str): Always set to null, unless you want the task due time to really be at a given timezone.
		If timezone is not given, then the time is always "in the user's current timezone".
		That is, if I specify a task to happen at 10:00:00, and I change timezone, the task is still due
		at 10:00:00 in the new timezone.
	* `string` (str): A human-readable due date, e.g. "10 am every monday".
	* `lang` (str): The language used to parse the `string` attribute.
	* `is_recurring` (bool): Whether the task is recurring. If it is, then completing a task
		will simply move the task's due date by re-parsing the `string`.

Reminders:

* The `date_string`, `date_lang`, `due_date_utc` properties of reminders were
  replaced by the `due` object.
* The `reminders.add()` and `reminders.update()` methods now expect a `due`
  parameter, instead of the `date_string`, `date_lang` and/or `due_date_utc`
  parameters.

Date format changes:

* Date formats must be RFC-3339, i.e. "YYYY-MM-DD" or "YYYY-MM-DDTHH:MM:SS" or (maybe?) "YYYY-MM-DD HH:MM:SS"
	* From the RFC-3339 specs: [RFC-3339 is] "a profile of the ISO 8601 standard".

Other method changes:

* Most of the `items` methods are now intended to be invoked on just *a single*
	item, rather than a list of items.
* For example, the `items.complete()` method now expects the `id` parameter, instead of
  the `ids` parameter, and it completes the item and all the item's
  descendants.  In addition the new `date_completed` parameter can also be
  specified.


Refs:

* https://developer.todoist.com/sync/v8/#changes
* https://developer.todoist.com/sync/v8/#full-day-dates
* https://github.com/Doist/todoist-python/blob/29864f6b390f64b560fad891fdb9d3c26ca5237f/CHANGELOG.md
* https://github.com/Doist/todoist-python/commit/29864f6b390f64b560fad891fdb9d3c26ca5237f


Copy/paste of official Todoist CHANGELOG.md:

* All arguments expecting a date/time must be formatted according to [RFC
  3339](https://tools.ietf.org/html/rfc3339), and all return values are also
  using the same format.
* The `item_order` and `indent` properties of projects, that denoted a visual
  hierarchy for the projects (the order of all the projects and the level of
  indent of each one of them), were replaced by `parent_id` and `child_order`,
  which denote a real hierarchy (the parent project of a project and the order
  of all children of a specific parent project).
* The `projects.add()` method now expects a `parent_id` and `child_order`
  parameter, instead of the `item_order` and `indent` parameters.
* The `projects.update()` method doesn't expect an `item_order` and `indent`
  parameters anymore, but it doesn't accept the new `parent_id` and
  `child_order` parameters as well, as the way to change the hierarchy is now
  different (see the `projects.move()` and `projects.reorder()` methods).
* The new `projects.move()` method must be used to move a project to become
  the child of another project or become a root project.
* The new `projects.reorder()` method must be used to reorder projects in
  relation to their siblings with the same parent.
* The `projects.delete()` method now expects only an `id` parameter, instead
  of the `ids` parameter, and it deletes the project and all the projects's
  descendants.
* The `projects.archive()` method now expects the `id` parameter, instead of
  the `ids` parameter, and it archives the project and all the project's
  descendants.
* The `projects.uncomplete()` method now expects an `id` parameter, instead
  of the `ids` parameter, and it restores the project as a root project.
* The `projects.update_orders_indents()` method was removed.
* The `date_string`, `date_lang`, `due_date_utc` properties of items were
  replaced by the `due` object.
* The `item_order` and `indent` properties of items, that denoted a visual
  hierarchy for the items (the order of all the items and the level of indent
  of each one of them), were replaced by `parent_id` and `child_order`, which
  denote a real hierarchy (the parent item of an item and the order of all
  children of a specific parent item).
* The `items.add()` method now expects a `parent_id` and `child_order`
  parameter, instead of the `item_order` and `indent` parameters.
* The `items.add()` and `items.update()` methods now expect a `due` parameter,
  instead of the `date_string`, `date_lang` and/or `due_date_utc` parameters.
* The `items.update()` method doesn't expect an `item_order` and `indent`
  parameters anymore, but it doesn't accept the new `parent_id` and
  `child_order` parameters as well, as the way to change the hierarchy is now
  different (see `item_move` and `item_reorder`).
* The `items.move()` method does not accept the `project_items` and
  `to_project` parameters, but a new set of parameters specifically `id`, and
  one of `project_id` or `parent_id`.  Another difference stemming from this is
  that only a single item can be moved at a time, and also that in order to
  move an item to become the child of another parent (or become a root level
  item) the `item_move` command must be used as well.
* The `items.update_orders_indents()` method was removed.
* The new `items.reorder()` method must be used to reorder items in relation
  to their siblings with the same parent.
* The `items.delete` method now expects only an `id` parameter, instead of
  the `ids` parameter, and it deletes the item and all the item's descendants.
* The `items.complete()` method now expects the `id` parameter, instead of
  the `ids` parameter, and it completes the item and all the item's
  descendants.  In addition the new `date_completed` parameter can also be
  specified.
* The `items.uncomplete()` method now expects an `id` parameter, instead of
  the `ids` parameter, and it uncompletes all the item's ancestors.
* The new `items.archive()` method can be used to move an item to history.
* The new `items.unarchive()` method can be used to move an item out of
  history.
* The `items.update_date_complete()` method now expects a `due` parameter,
  instead of `new_date_utc`, `date_string` and/or `is_forward` parameters.
* The possible color values of filters changed from `0-12` to `30-49`.
* The `date_string`, `date_lang`, `due_date_utc` properties of reminders were
  replaced by the `due` object.
* The `reminders.add()` and `reminders.update()` methods now expect a `due`
  parameter, instead of the `date_string`, `date_lang` and/or `due_date_utc`
  parameters.
* The state now includes an additional new resource type called
  `user_settings`.
* The user object now includes the `days_off` property.
* The `since` and `until` parameters of the `activity/get` method are
  deprecated, and are replaced by the new `page` parameter.