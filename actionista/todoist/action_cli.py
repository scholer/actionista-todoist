# Copyright 2018-2019 Rasmus Scholer Sorensen <rasmusscholer@gmail.com>
"""

Actionista Action CLI for Todoist.

Manage your Todoist tasks from the command line, using powerful filters to
select, print, reschedule, and complete tasks in a batch-wise fashion.

Do you have dozens or even hundreds of overdue tasks on your agenda?
Clear up your task list in seconds, using the Actionista Action CLI for Todoist.
You can now take the rest of the day off with a clear conscience.

This Action CLI for Todoist (`todoist-action-cli`), operates sequentially on a list of tasks.
You start out with a list of *all* tasks, and then select tasks using one of the many
filters available. You can then sort, print, and reschedule the selected tasks.


The module uses the [official "Todoist Python API" package](https://pypi.org/project/todoist-python),
[github](https://github.com/Doist/todoist-python).


# TODO: Move all action commands (`print_tasks`, etc) to dedicated module to make this module a bit more manageable.

# TODO: Adopt the `update_date_complete`, and `close` action terminologies,
# c.f. https://developer.todoist.com/sync/v8/#close-item



"""

import sys
import shlex
import todoist
import shutil
from pprint import pprint

from actionista import binary_operators
from actionista.todoist import action_commands
from actionista.todoist.action_commands import ACTIONS
from actionista.todoist.tasks_utils import add_custom_task_fields
from actionista.todoist.config import get_config, get_token

NEWLINE = '\n'


def parse_argv(argv=None):
    """ Parse command line input.

    Args:
        argv: List of command line arguments, defaulting to `sys.argv`.

    Returns:
        (base_args, base_kwargs), action_groups
    where
        `(base_args and base_kwargs)` are args and kwargs given *before* the first `-command`,
    and
        `action_groups` is a list of `(action_name, action_args, action_kwargs)` tuples.


    Examples:

        >>> cmd = '-filter due_date_utc contains 2017-12-31 -add-task "Task 123" project=MyProject due=tomorrow priority=p1'
        >>> parse_argv(shlex.split(cmd))
        (
            [], {},
            [
                ('filter', ('due_date_utc', 'contains', '2017-12-31'), {}),
                ('add-task', ('Task123',), {'project': 'MyProject', 'due': 'tomorrow', 'priority': 'p1'}),
            ]
        )


    Old examples:

        # Print tasks due on New Year's Eve 2017 for the project named "Project1":
        >>> cmd = '-filter due_date_utc contains 2017-12-31 -filter project_name eq Project1 -print "{content}"'
        >>> parse_argv(shlex.split(cmd))
        [
            ('filter', ('due_date_utc', 'contains', '2017-12-31')),
            ('filter', ('project_name', 'eq', 'Experiments')),
            ('print', ('{content}')),
        ]

        # Print tasks starting with "RS123", mark them as complete, and sync the change to the server:
        >>> parse_argv(shlex.split('-filter content startswith RS123 -print "{content}" -mark-completed -sync'))
        [
            ('filter', ('content', 'startswith', 'RS123')),
            ('print', ('{content}')),
            ('mark_tasks_completed', (,)),
            ('sync', (,)),
        ]

    Note: Variable placeholders, e.g. "{today}" may be implemented later.

    """
    if isinstance(argv, str):
        argv = shlex.split(argv)
    if argv is None:
        argv = sys.argv

    action_groups = []  # List of (action, args) pairs.
    base_args = current_group_args = []
    base_kwargs = current_group_kwargs = {}
    for arg in argv:
        if arg[0] == "-":
            current_group_args, current_group_kwargs = [], {}  # Start new args group for action
            action_name = arg[1:]  # Truncate the leading '-' in '-action'.
            action_groups.append((action_name, current_group_args, current_group_kwargs))
        else:
            # Added support for key=value command line args:
            if '=' in arg:
                k, v = arg.split("=", 1)  # k=v pair
                current_group_kwargs[k] = v
            else:
                current_group_args.append(arg)
    return (base_args, base_kwargs), action_groups


def parse_action_args(action_groups):
    """ Parse action group args. E.g. if we need anything advanced like yaml parsing. """
    pass


def action_cli(argv=None, verbose=0):
    r""" Start the "Action CLI", in which sequential actions are invoked, starting from the full set of Todoist tasks.

    Note: This is only for dealing with active tasks; printing, filtering, rescheduling, completing.
    These all use Task objects from `api.state['items']` (managed ItemsManager).
    For other uses, e.g. listing completed tasks, use my old todoist cli, found in the `todoist` module,
    e.g. for printing today's completed items:
        $ todoist print-completed-today --print-fmt "* {title}"

    NOTE: Actually, the list of tasks will include both completed/checked and active/unchecked tasks!
    It doesn't include all tasks, though, so there must be a limit to how much data is fetched from the server.

    Examples:

        Tasks due today (today being 2018-03-10):
            $ todoist_action_cli -filter due_date_utc startswith 2018-03-10 -print

        Filter out completed tasks:
            $ todoist_action_cli -filter checked eq 0 default 0 int -print

        Tasks due today or overdue:
            $ todoist_action_cli -filter due_date_utc lt 2018-03-11 -print

        Tasks in project "Dev-personal":
            $ todoist_action_cli -filter due_date_utc lt 2018-03-11 -print

        Tasks in "Expriments" project starting with "RS52" and priority of at least 2:
            $ todoist-action-cli -filter project_name ieq experiments \
                                 -filter content istartswith rs52 \
                                 -filter priority ge 2 default 1 int
                                 -print

        High-priority tasks with no due date:
            $ todoist-action-cli -filter priority ge 2 default 1 int \
                                 -filter due_date_utc gt Z include \  # (*)
                                 -print "{project_name:15} {due_date_utc} {content}"
        (*) We expect the binary operator to evaluate False, relying on missing="include" to include tasks w/o due date.

        Sorting tasks before printing:
            $ todoist-action-cli -filter priority ge 2 default 1 int \
                                 -sort project_name,item_order descending \  # (*)
                                 -print "{project_name:15} {due_date_utc} {content}"
        (*) This is now the default sort order, you can just invoke `-sort` action with no further arguments.

        Example of how to print with a header:
            $ todoist-action-cli
                -filter content istartswith rs52
                -print "{project_name:15} {due_date_dt:%Y-%m-%d   } {content}" "Project:        Due_date:     Task:"

        Using "human dates" as the input value (e.g. for scripts, or if you just don't want to type the date).

        Find tasks that were due more than two weeks ago:
            $ todoist-action-cli \
                -filter due_date_utc_iso lt "2 week ago" exclude today human_date_to_iso \
                -print "{project_name:15} {due_date_dt:%Y-%m-%d %H:%M  } {content}" \
                       "Project:        Due_date:          Task:"
        Note how we used 'today' as default value. The default value would also have been transformed,
        if we had used missing="default" instead of missing="exclude" (which just excludes tasks with no due date).
        Note that using human language dates is a little bit finicky.
            For instance, "in 2 weeks" works, but none of the following variations do:
            "in two weeks", "2 weeks from now", "two weeks", "in 2 weeks from now", etc.

        More examples:

            $ todoist-action-cli -due before tomorrow -not recurring -project not Personal-* \
                -sort "project_name,priority_str,due_date_local_iso" -print

    -Note: -sync is currently implied as the first action.-  (Edit: No, using cache for while testing.)

    Available actions include:
        -sync:          Sync changes with the server. NOTE that sync will reset all previous task filters!
        -filter         filter the task list.
        -due            shorthand for filtering by due date.
        -sort           sort the task list.
        -print          print the task list.
        -reschedule     reschedule all tasks in the current task list, usually after filter-selecting.
        -mark-completed mark all tasks in the tasks list as completed.
        -commit:        Commit local changes. Will ask for confirmation if `-y` has not been given beforehand.
        -y, -yes:       Skip all confirmation prompts.

    For a full list of commands, refer to the `action_cli.ACTIONS` module attribute.
    (Is also printed when invoking `todoist-action-cli --help`).

    You can chain as many operations as you need, but you cannot fork the pipeline.
    There is also no support for "OR" operators (or JOIN, or similar complexities).

    To get help on each action, use:
        `$ todoist-action-cli -help <action>`


    Task attributes/keys:
    ---------------------

    The following task attributes can be used when filtering, sorting, and printing tasks:

    * content - the task name/title/text.
    * project_name
    * priority_str - a string indicating prioritiy, e.g. p1-p4.
    * checked_str - String indicating if task is completed "[x]" or not "[ ]".
    * due_date_utc_iso - due date, UTC time, in ISO8601 formatted string.
    * due_date_local_iso - due date, local time zone, in ISO8601 formatted string.
    * due_date_safe_dt - "safe", i.e. not None, datetime object.
    * date_string - due date, text string, as written by user (before being parsed by the computer).
        This is actually the primary way in which task due dates are defined,
        and can be used to specify e.g. recurring tasks, 'every monday at 13:00'.


    Filtering tasks: `-filter`
    --------------------------

    Filtering is always done as: <task field> <binary operator> <value>,
    e.g. "project_name eq Experiments".

    The full call-signature for filter tasks is:
         taskkey, op_name, value, missing="exclude", default=None, value_transform=None

    See `filter_tasks()` for details. In short:

        `taskkey` is transformed to `task[taskkey]`, e.g. 'due_date_utc_iso' or 'priority'.
        `op_name` is the name of the binary operator to use.
        `value`   is the provided value to compare against, e.g. '2018-03-10' or '1'.
        `missing` is "what to do if the key/value is missing in the task (or None)". Default is to exclude the task.
        `default` is the default task value used if missing="default", i.e. if the value is missing in the task.
        `value_transform` is a transformation of the comparison value,
            and is only needed because everything is a string on the terminal.
            Can be either (a) a function/type from `builtins`, or (b) an expression to be evaluated with `eval`.

    Unfortunately, since we haven't implemented complex parameter passing,
    you have to provide all action arguments as positional arguments.
    (That is, we haven't implemented the following:  -filter priority le 2 missing=exclude,value_transform=int
     - but that would probably also be overkill right now.)


    Filtering examples:
        -filter priority le 2 default 1 int

    Binary operators that can be used for filtering include:

        eq, lt, gt, le, ge: Equal-to, less-than, greater-than, less-than-or-equal-to, greater-than-or-equal-to.
            E.g. "project_name eq Experiments", but also "due_date_utc ge 2017-12-24" and "due_date_utc le 2017-1-31"
            where the latter two can be combined to find tasks due between Christmas and New Year's Day 2017.
        contains, in_, startswith: .
        glob, re: Glob-style and regex-style string pattern matching.

        Notes, binary operators:
        * Most binary operators have a 'case-insensitive' equivalent, prefixed with 'i', e.g. 'ieq', 'istartswith', etc.
        * Many binary operators only work for string comparison, but most task fields are strings, e.g. due_date_utc.
        * The default Todoist `due_date_utc` format is not very helpful: 'Mon 26 Mar 2018 21:59:59 +0000'
            * For this reason, we provide `due_date_utc_iso`, which can be sorted and compared smoothly.
        * Regarding dates, the `le` operator may be tricky to use (e.g. for the upper limit on date ranges):
            While:
                >>> "2017-12-24T14:55" >= "2017-12-24"
                >>> "2017-12-30T14:55" <= "2017-12-31"
            are both `True`, but:
                >>> "2017-12-31T14:55" <= "2017-12-31"
            is `False` (even though the task falls on the given date) - because we are using string comparisons!
            Thus, always use `lt` to specify the upper limit of date ranges, to avoid mistakes.
            (Note that all-day events uses "23:59:59" as due date time.)


    Value transform:
        The `value_transform` filter parameter can be used to transform the input comparison value.
        E.g.
            -filter due_date_utc lt "two weeks from now" exclude _ human_date_to_iso
        Here, 'human_date_to_iso' is the name of a function (accessible from the scope of `filter_tasks`),
        which will convert "two weeks from now" to an iso-formatted datetime string.

        Note: Parsing human dates seems to be a little bit finicky.
            For instance, "in 2 weeks" works, but none of the following variations do:
            "in two weeks", "2 weeks from now", "two weeks", "in 2 weeks from now", etc.

    ## Task filter, shorthand commands:

    Since the "full" `-filter` command is a little verbose,
    the todoist-action-cli offers a range of "shorthand" convenience actions for filtering tasks.
    These include:

        -content        Shorthand for filtering by task content.
        -name           Alias for `-content`.
        -contains       Filter tasks that contains the given string.
        -startswith     Filter tasks that starts with the given string.
        -endswith       Filter tasks that ends with the given string.
        -glob, -iglob   Filter tasks that match a given glob pattern (case sensitive / insensitive).
        -eq, -ieq       Filter tasks that matches a given string (case sensitive / insensitive).
        -has            Unofficial alias for `-filter`.

    Some filtering mechanics require a little bit of extra care. This is implemented through the `-is` operator:
    Examples:

        `-is recurring`         - Only include tasks that are recurring.
        `-is checked`           - Only include tasks that have been marked as complete ("checked off").
        `-is due`               - Only include tasks that are not completed and have a due date.
        `-is due before today`  - Only include overdue tasks (excluding completed tasks).
        `-is due before [day/date]`

    Again, we have a few shorthand convenience commands for using the `-is` command:

        -is             Special filter for filtering by e.g. due date or whether an action is completed or recurring.
        -not            Shorthand for `-is not`.
                        Example: `-not recurring` to filter out recurring tasks.
        -due            Shorthand for `-is due [when]`.


    Sorting tasks: `-sort`
    ----------------------

    Sorting the list of tasks is useful for display purposes.
    The command takes the form:

        -sort <comma,separated,list,of,attributes> <sort-order>

    Examples:

        `-sort project_name,priority_str,item_order` - sort tasks by project, then priority, then manual order.
        `-sort "project_name,priority" descending`  to sort tasks by project, then by priority, in descending order.
        `-sort "project_name,content" ascending     to sort tasks by project, then by task content/name.

    Default sort order is currently "project_name,priority_str,item_order", in ascending order.


    Printing tasks: `-print`
    ------------------------

    Printing takes three optional positional arguments:
        1. print_fmt: How to print each task. Every task field can be used as variable placeholder, e.g. {due_date_utc}.
            You can print the full task data using "{task}", or the special "repr" or "pprint" keywords.
        2. header: A header to print, e.g. "TASKS DUE TODAY:\n-----------"
        3. sep: A separator between each task. Is usually just "\n".

        Note: Since backslash has special meaning on the command prompt, in order to insert a tab character from
        the command line, you need to do the following (OS dependent):
            linux/bash: Ctrl+V, then Tab - or use $'\t'.
            windows:
                (a) Start cmd with: `cmd.exe /F:OFF` (disables tab-completion).
                (b)

    Default print format: (as specified by module attribute `DEFAULT_TASK_PRINT_FMT`)

    {project_name:15} {due_date_safe_dt:%Y-%m-%d %H:%M} {priority_str} {checked_str} {content} (due: {date_string!r})


    Other commands:
    ---------------

    Rescheduling takes a single argument, the new date, in the proper Todoist date-time format.

    Sync and mark-complete does not take any additional arguments.

    """
    (base_args, base_kwargs), action_groups = parse_argv(argv=argv)

    config = get_config() or {}
    config.update(base_kwargs)
    token = get_token(raise_if_missing=True, config=config)
    api = todoist.TodoistAPI(token=token)
    if config.get('api_url'):
        # Current default: 'https://api.todoist.com/sync/v8/' (including the last '/')
        assert config.get('api_url').endswith('/')
        print("NOTICE: USING NON-STANDARD API BASE URL:", config.get('api_url'))
        api.api_endpoint = None  # Make sure this is not used.
        api.get_api_url = lambda: config.get('api_url')
    # Regarding caching:
    # By default, TodoistAPI.__init__ will load cache files (.json and .sync) from path given by `cache` parameter.
    # api.sync() will invoke `_write_cache()` after `_post()` and `_update_state()`.
    # api.sync()  # Sync not always strictly needed; can load values from cache, e.g. for testing.

    # The Todoist v7 python API is a bit of a mess:
    # api.items is not a list of items, but the ItemsManager.
    # To get actual list of items, use `api.state['items']`.
    # api._update_state creates object instances from the data as defined in `resp_models_mapping`,
    # so we should have `todoist.model.Item` object instances (not just the dicts received from the server):
    task_items = api.state['items']

    add_custom_task_fields(tasks=task_items, api=api, verbose=verbose, **base_kwargs)

    def increment_verbosity(tasks, **kwargs):
        """ Increase program informational output verbosity. """
        # If you modify (reassign) an immutable type within a closure, it is by default considered a local variable.
        # To prevent this, declare that the variable is non-local:
        nonlocal verbose
        verbose += 1
        return tasks
    ACTIONS['v'] = ACTIONS['verbose'] = increment_verbosity

    ask_before_commit = True

    def disable_confirmation_prompt(tasks, **kwargs):
        """ Disable confirmation prompt before enacting irreversible commands, e.g. -commit. """
        nonlocal ask_before_commit
        ask_before_commit = False
        return tasks

    ACTIONS['y'] = ACTIONS['yes'] = ACTIONS['no-prompt'] = disable_confirmation_prompt

    # Better to define sync here rather than relying on getting api from existing task
    def sync(tasks, **kwargs):
        """ Pull task updates from the server to synchronize the local task data cache.
        Note: api.sync() without arguments will just fetch updates (no commit of local changes).
        """
        # Remove custom fields (in preparation for JSON serialization during `_write_cache()`:
        n_before = len(tasks)
        print("\nSyncing... (fetching updates FROM the server; use `commit` to push changes!)")
        # Removing custom fields is no longer needed, now custom/derived data is stored in separate attribute.
        # for task in api.state['items']:
        #     for k in CUSTOM_FIELDS:
        #         task.data.pop(k, None)  # pop(k, None) returns None if key doesn't exists, unlike `del task[k]`.
        api.sync()
        tasks = api.state['items']
        n_after = len(tasks)
        print(f" - {n_after} tasks after sync ({n_before} tasks in the task list before sync).")
        add_custom_task_fields(tasks=tasks, api=api, verbose=verbose, **base_kwargs)
        return tasks

    ACTIONS['sync'] = sync

    def commit(tasks, *, raise_on_error=True, verbose=0):
        """ Commit is a sync that includes local commands from the queue, emptying the queue. Raises SyncError. """
        # Prompt if needed:
        if ask_before_commit:
            answer = input(f"\nPROMPT: About to commit {len(api.queue)} updates. Continue? [Y/n] ") or 'Y'
            if answer[0].lower() == 'n':
                print(" - OK, ABORTING commit.")
                return tasks
        if verbose > -1:
            print(f"\nCommitting {len(api.queue)} local changes and fetching updates...")
        # Removing custom fields is no longer needed, now custom/derived data is stored in separate attribute.
        # for task in api.state['items']:
        #     for k in CUSTOM_FIELDS:
        #         task.data.pop(k, None)  # pop(k, None) returns None if key doesn't exists, unlike `del task[k]`.
        # Commit changes (includes an automatic sync), and re-parse task items:
        api.commit(raise_on_error=raise_on_error)
        tasks = api.state['items']
        add_custom_task_fields(tasks=tasks, api=api, verbose=verbose, **base_kwargs)
        return tasks

    ACTIONS['commit'] = commit

    # Better to define sync here rather than relying on getting api from existing task
    def show_queue(tasks, *, fmt="json", width=200, indent=2, verbose=0):
        """ Show list of API commands in the POST queue. """
        def get_obj_data(obj):
            return obj.data
        # Remove custom fields (in preparation for JSON serialization during `_write_cache()`:
        print("\n\nAPI QUEUE:\n----------\n")

        if fmt == "pprint":
            pprint(api.queue, width=width, indent=indent)
        elif fmt == "yaml":
            import yaml
            print(yaml.safe_dump(api.queue, width=width, indent=indent))
        elif fmt == "yaml-unsafe":
            import yaml
            print(yaml.dump(api.queue, width=width, indent=indent))
        elif fmt == "json":
            import json
            # This is actually the best, since it can use `default=get_obj_data` to represent model objects.
            print(json.dumps(api.queue, indent=indent, default=get_obj_data))
        else:
            raise ValueError(f"Argument `fmt` value {fmt} not recognized. Should be one of 'pprint', 'yaml', or 'json'.")
        return tasks

    ACTIONS['show-queue'] = show_queue
    ACTIONS['print-queue'] = show_queue

    def delete_cache(tasks, *, verbose=0):
        """ Delete local todoist data cache.
        Should be done periodically, and especially if you start to experience any unusual behaviour.
        """
        if api.cache is not None:
            print("Deleting cache dir:", api.cache)
            shutil.rmtree(api.cache)  # Is a directory containing .json and .sync files
        else:
            print("delete_cache: API does not have any cache specified, so cannot delete cache.")
        return tasks

    ACTIONS['delete-cache'] = delete_cache

    def print_help(tasks, cmd=None, *, verbose=0):
        """ Print help messages. Use `-help <action>` to get help on a particular action. """
        # import re
        # print(repr(action_cli.__doc__))  # Nope, escapes proper line breaks.
        # print(re.escape(action_cli.__doc__))  # Nope, escapes whitespace.
        if cmd is None:
            print(action_cli.__doc__)  # Works, if you are using r""" for your docstrings (which you probably should).
            print("    Complete list of available actions:")
            print("    -------------------------------------\n")
            print("\n".join(
                f"      -{action:20} {(func.__doc__ or '').split(NEWLINE, 1)[0]}"
                for action, func in list(ACTIONS.items())))
            print("\n")
        elif cmd == "operators":
            print("""
Binary comparison operators are used to compare two values:

    valueA  operator  valueB

For example: "1 eq 2" returns False ("no match"), while "2 eq 2" returns True ("match").

Tasks where the two operands compare to true are included/kept in the list, while non-matching items are discarted.
""")
            print("\nAvailable operators include:")
            print(", ".join(sorted(op for op in dir(binary_operators) if not op.startswith('_'))))
            print("""
Some operators expect strings (e.g. "abcdefg startswith abc"), 
while others are mostly type-agnostic, e.g. "123 greaterthan 100".

For `todoist-action-cli`, most arguments are assumed to be strings, and you have to use the 'value_transform' 
argument to convert input values to e.g. integers. 

""")
            print(binary_operators.__doc__)
        else:
            if cmd not in ACTIONS:
                print(f"\nERROR: {cmd!r} command not recognized.\n")
                return print_help(tasks)
            else:
                print(ACTIONS[cmd].__doc__)
        return tasks

    ACTIONS['h'] = ACTIONS['help'] = ACTIONS['-help'] = print_help

    def add_task(tasks, task_content, *, project=None, due=None, priority=None, labels=None,
                 auto_reminder=True, auto_parse_labels=True, verbose=0):
        """ Forward arguments to action_commands.add_task, injecting the `api` object. """
        print("add_task function invoked with args:")
        pprint(dict(
            tasks=f"[{len(tasks)} tasks]", task_content=task_content, project=project,
            due=due, priority=priority, labels=labels,
            auto_reminder=auto_reminder, auto_parse_labels=auto_parse_labels,
        ))
        return action_commands.add_task(
            tasks=tasks, api=api, task_content=task_content,
            project=project, due=due, priority=priority, labels=labels,
            auto_reminder=True, auto_parse_labels=auto_parse_labels, verbose=verbose
        )

    ACTIONS['add-task'] = ACTIONS['-add-task'] = add_task

    unrecognized_actions = [agroup[0] for agroup in action_groups if agroup[0] not in ACTIONS]
    if unrecognized_actions:
        print("\nERRROR, the following actions were not recognized:", unrecognized_actions)
        return

    if len(action_groups) == 0:
        # Print default help
        action_groups.append(('help', [], {}))

    # For each action in the action chain, invoke the action providing the (remaining) tasks as first argument.
    for action_key, action_args, action_kwargs in action_groups:
        n_tasks = len(task_items)
        if verbose >= 1:
            print(f"\nInvoking '{action_key}' action on {n_tasks} tasks with args: {action_args!r}", file=sys.stderr)
        action_func = ACTIONS[action_key]
        # TODO: Pass `config=config` to all action commands (or move from functional to object-oritented flow).
        task_items = action_func(task_items, *action_args, verbose=verbose, **action_kwargs)
        assert task_items is not None


if __name__ == '__main__':
    action_cli()
