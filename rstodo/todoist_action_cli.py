# Copyright 2018 Rasmus Scholer Sorensen


"""

This is my experimentation with creating a more powerful API.

I've previously created a basic `todoist` module, with basic examples on how to use the Todoist API,
including notes and discussions.

This is my attempt at making a more extensive CLI.

The goal is to have something where I can make a long list of actions, e.g.:

    $ todoist -filter <filter_name> -print "\nBEFORE RESCHEDULING:" -reschedule "today" -print "\nAFTER RESCHEDULING:"

Note how this has an order. It is more like `find` CLI than traditional ArgParser or Click CLI.
I therefore don't think we can create it with argparse or click, but it should be easy to roll manually.


Note: Python datetime libraries:
* datetime stdlib
* maya - By Kenneth Reitz
* arrow (not to be confused with apache-arrow) - by Chris Smith.
* moment - port of moment.js
* 


Complex Filtering:
------------------

Regarding complex filtering operations with more than one expression,
e.g. "-filter (due_date_utc gt 2017-12-24 and due_date_utc lt 2017-12-13) or priority eq 1".

Why would we want to do this?
* The "and" is equivalent to applying two sequential filters.
* So it is only useful to implement "or",
* which is just a join of two separate queries.
* I really don't think it is worth the complexity to achieve this!

This probably requires a proper parser, e.g:
* recursive descent parser. ("The hard way")
* s-expression (sexp) parser in Python
* pyparsing
* PLY
* YACC / Bison / ANTLR

Which makes for rather complicated code:
* https://gist.github.com/adamnew123456/0f45c75c805aa371fa92 - Pratt-style parser, 700+ LOCs for a simple calculator.
* https://github.com/louisfisch/Mathematical-Expressions-Parser/

Although maybe this can be done easily with a parser generator based on parsing expression grammars (PEGs):
* https://github.com/orlandohill/waxeye
* https://github.com/scottfrazer/hermes

See also:
* Dragon Book
* Boost Spirit (C++)
* https://en.wikipedia.org/wiki/Operator-precedence_parser
* https://en.wikipedia.org/wiki/S-expression
*



"""

import sys
import os
import shlex
import operator
import builtins
from todoist.models import Item, Project
import dateparser

from rstodo import binary_operators
from rstodo.todoist_tasks_utils import parse_task_dates, inject_project_info, human_date_to_iso
from rstodo.todoist import get_todoist_api


def parse_argv(argv=None):
    """ Parse command line input.

    Args:
        argv: List of command line arguments, defaulting to `sys.argv`.

    Returns:
        action_groups: List of (action_name, action_args) pairs.

    Examples:

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
    for arg in argv:
        if arg[0] == "-":
            current_group_args = []
            action_name = arg[1:]  # Truncate the leading '-'.
            action_groups.append((action_name, current_group_args))
        else:
            current_group_args.append(arg)

    return action_groups


def parse_action_args(action_groups):
    """ Parse action group args. E.g. if we need anything advanced like yaml parsing. """
    pass


def print_tasks(tasks, print_fmt="{project_name:15} {due_date_dt:%Y-%m-%d %H:%M  } {content}", header=None,  sep="\n"):
    """

    Args:
        tasks:
        print_fmt:
        header:
        sep:

    Returns:

    Frequently-used print formats:
        "* {content}"
        "{project_name:15} {due_date_dt:%Y-%m-%d %H:%M  } {content}  ({checked})"

    """
    if header:
        print(header)
    task_dicts = [task.data if isinstance(task, Item) else task for task in tasks]
    if print_fmt == 'repr' or print_fmt == 'pprint':
        import pprint
        pprint.pprint(task_dicts)
    else:
        print(sep.join(print_fmt.format(**task) for task in task_dicts))
    return tasks


def sort_tasks(tasks, keys="project_name,item_order", order="ascending"):
    """ Sort list of tasks.
    Frequently-used sortings:
        project_name,item_order
        due_date,priority,item_order

    """
    if isinstance(keys, str):
        keys = keys.split(',')
    itemgetter = operator.itemgetter(*keys)
    tasks = sorted(tasks, key=itemgetter, reverse=(order == "descending"))
    return tasks


def filter_tasks(tasks, taskkey, op_name, value, missing="exclude", default=None, value_transform=None, negate=False):
    """

    Args:
        tasks:
        taskkey:
        op_name:
        value:
        missing:
        default:
        value_transform:
        negate: Can be used to negate (invert) the filter.
            Some operators already have an inverse operator, e.g. `eq` vs `ne`, `le` vs `gt`.
            But other operators do not have a simple inverse operator, e.g. `startswith`.
            So, if you want to remove/exclude tasks starting with 'Email', use:
                -filter content startswith Email exclude _ _ True
            Note: Negate applies to the transform, but not to tasks included/excluded due to missing value.

    Returns:

    The `missing` parameter controls what to do if `taskkey` is not present in a task:
        "raise" -> raise a KeyError.
        "include" -> include the task (task passes filter evaluation).
        "exclude" -> exclude the task (task fails filter evaluation).
        "default" -> Use a default value in leiu of the missing value.

    What if task[taskkey] is None?
        * Since we can't really use None for any comparison, it should be considered as missing,
            exactly the same as if the key was missing.

    """
    # First, check values and print helpful warnings about frequent pitfalls:
    if op_name == 'le' and (taskkey.startswith('date') or taskkey.startswith('due')):
        print("\nWARNING: You are using the less-than-or-equal-to (`le`) operator with a data value, "
              "which can be tricky. Consider using the less-than (`lt`) operator instead. If you do use the "
              "less-than-or-equal-to (`le`) operator, make sure to specify full time in comparison.\n")
    if taskkey == 'due_date_utc':
        print("\nNOTICE: You are using 'due_date_utc' as filter taskkey. This has the rather-unhelpful "
              "format: 'Mon 26 Mar 2018 21:59:59 +0000'.\n")
    # We often use "_" as placeholeder on the command line, because we cannot enter e None value:
    if default == '_' or default == '__None__':
        default = None
    if value_transform == '_' or value_transform == '__None__':
        value_transform = None
    if isinstance(negate, str) and negate.lower() in ('false', '_', '__none__', '0'):
        negate = False

    negate = bool(negate)
    op = getattr(binary_operators, op_name)
    # I'm currently negating explicitly in the all four 'missing' cases,
    # but I could also just have re-defined `op` as: `def op(a, b): return _op(a, b) != negate`

    if value_transform:
        if isinstance(value_transform, str):
            # It is either 'int' or a custom eval statement:
            if value_transform in builtins.__dict__:
                value_transform = getattr(builtins, value_transform)  # e.g. 'int'
                # print(f"Using `value_transform` {value_transform!r} from `builtins`...")
            elif value_transform in locals():
                value_transform = locals()[value_transform]
                # print(f"Using `value_transform` {value_transform!r} from `locals()`...")
            elif value_transform in globals():
                value_transform = globals()[value_transform]
                # print(f"Using `value_transform` {value_transform!r} from `globals()`...")
            else:
                # print(f"Creating filter value transform by `eval({value_transform!r})`...")
                t = eval(value_transform)
                if hasattr(t, '__call__'):
                    value_transform = t
                else:
                    # Was a one-off eval transform intended as: `value = eval('value*2')`.
                    value = t
                    value_transform = None  # Prevent further transformation
    if value_transform:
        # custom callable:
        value = value_transform(value)
        if default and missing == "default":  # Only try to transform task default value if we actually need it
            default = value_transform(default)
    # Perhaps transform value?
    # For certain types and ops we may want to customize the binary operator to account for special cases.
    # For instance, if taskkey is a date type, then we generally want to convert both
    # Although, maybe just as compare them as strings, e.g. `'2018-02-01' > '2018-01-31'` ?
    # Only case then is the "None" case, in which case just use '2099-12-31T23:59' ?
    # * Edit: Better to have a generic `missing` parameter.
    # Still, we may want to use one of the advanced date/time libraries, so we can interpret
    # stuff like "today", "tomorrow", "5 days from now", etc.
    # print("OP:", op)
    # if taskkey in ('due_date', 'due_date_utc'):
    #     # Tasks without due date may have None; we use a distant due date instead to simplify date comparisons:
    #     def itemgetter(task):
    #         return task[taskkey] or '2099-12-31T23:59'  # No due date (None) defaults to end of the century.
    # else:
    #     itemgetter = operator.itemgetter(taskkey)

    def get_value(task, default_=None):
        nonlocal value
        task = task.data if isinstance(task, Item) else task
        # return taskkey not in task or op(itemgetter(task), value)
        task_value = task.get(taskkey, default_)
        if task_value is not None and type(task_value) != type(value):
            print("NOTICE: `type(task_value) != type(value)` - Coercing `value` to %s:" % type(task_value))
            value = type(task_value)(value)
        return task_value

    if missing == "raise":
        def filter_eval(task):
            task_value = get_value(task)
            if task_value is None:
                raise ValueError(f"Key {taskkey!r} not present (or None) in task {task['id']}: {task['content']}")
            return op(task_value, value) != negate  # This comparison with negate will negate if negate is True.
    elif missing == "include":
        def filter_eval(task):
            # return taskkey not in task or op(itemgetter(task), value)
            task_value = get_value(task)
            return task_value is None or (op(task_value, value)  != negate)
    elif missing == "exclude":
        def filter_eval(task):
            # return taskkey in task and op(itemgetter(task), value)
            task_value = get_value(task)
            return task_value is not None and (op(task_value, value) != negate)
    elif missing == "default":
        def filter_eval(task):
            task_value = get_value(task, default)
            return op(task_value, value) != negate
        if default is None:
            print('\nWARNING: filter_tasks() called with missing="default" but no default value given (is None).\n')
    else:
        raise ValueError("`missing` value %r not recognized." % (missing,))
    tasks = [task for task in tasks if filter_eval(task)]
    return tasks


def special_is_filter(tasks, *args):
    """  Special -is filter for ad-hoc or frequently-used cases, e.g. -is not checked, etc.

    These are generally implemented on an as-needed basis.

    Args:
        tasks:
        *args:

    Returns:
        tasks: Filtered list of tasks.
    """
    if args[0] == 'not':
        negate = True
        args = args[1:]
    else:
        negate = False
    if args[0] == 'due':
        taskkey = 'due_date_utc_iso'
        if len(args) > 1:
            pass
    elif args[0] in ('checked', 'unchecked', 'complete', 'incomplete'):
        # -is not checked
        pass


def reschedule_tasks(tasks, new_date):
    """

    Args:
        tasks:
        new_date:

    Returns:

    """
    for task in tasks:
        continue
    return tasks


def mark_tasks_completed(tasks):
    """

    Note: The Todoist v7 Sync API has two command types for completing tasks:
        'item_complete' - used by ?
        'item_uncomplete' - Mark task as uncomplete.
        'item_update_date_complete' - used to mark recurring task completion.
        'item_close' - does exactly what official clients do when you close a task:
            regular task is completed and moved to history,
            subtasks are checked (marked as done, but not moved to history),
            recurring task is moved forward (due date is updated).


    See: https://developer.todoist.com/sync/v7/#complete-items

    Args:
        tasks:

    Returns:

    """
    for task in tasks:
        task.close()
    return tasks


def fetch_completed_tasks(tasks):
    """ This will replace `tasks` with a list of completed tasks dicts. May not work nicely. Only for playing around.

    You should probably use the old CLI instead:
        $ todoist print-completed-today --print-fmt "* {title}"
    """
    from rstodo.todoist import completed_get_all
    # This will use a different `api` object instance to fetch completed tasks:
    tasks, projects = completed_get_all()
    inject_project_info(tasks, projects)
    return tasks


def sync(tasks):
    try:
        task = next(iter(tasks))
    except StopIteration:
        print("\nWARNING: `tasks` list is empty; cannot sync.\n")
    else:
        task.api.sync()
    return tasks


# Probably not needed:
# def unmark_tasks_completed(tasks):
#     pass


# Defined ACTIONS dict AFTER we define the functions.
# OBS: ALL action functions MUST return tasks, never None.
ACTIONS = {
    'print': print_tasks,
    'sort': sort_tasks,
    'filter': filter_tasks,
    'reschedule': reschedule_tasks,
    'mark-completed': mark_tasks_completed,
    'sync': sync,
    'fetch-completed': fetch_completed_tasks,  # WARNING: Not sure how this works, but probably doesn't work well.
}


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

    -Note: -sync is currently implied as the first action.-  (Edit: No, using cache for while testing.)

    Available actions include:
        -filter
        -sort
        -print
        -reschedule
        -mark-completed
        -sync

    You can chain as many operations as you need, but you cannot fork the pipeline.
    There is also no support for "OR" operators (or JOIN, or similar complexities).


    Filter:
    -------

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


    Print:
    ------

    Printing takes three optional positional arguments:
        1. print_fmt: How to print each task. Every task field can be used as variable placeholder, e.g. {due_date_utc}.
        2. header: A header to print, e.g. "TASKS DUE TODAY:\n-----------"
        3. sep: A separator between each task. Is usually just "\n".

        Note: Since backslash has special meaning on the command prompt, in order to insert a tab character from
        the command line, you need to do the following (OS dependent):
            linux/bash: Ctrl+V, then Tab - or use $'\t'.
            windows:
                (a) Start cmd with: `cmd.exe /F:OFF` (disables tab-completion).
                (b)


    Other commands:
    ---------------

    Rescheduling takes a single argument, the new date, in the proper Todoist date-time format.

    Sync and mark-complete does not take any additional arguments.


    """
    action_groups = parse_argv(argv=argv)

    # print("Action groups:")
    # print("\n".join(str(group) for group in action_groups))

    api = get_todoist_api()
    # api.sync()  # Sync not always strictly needed; can load values from cache, e.g. for testing.

    # print()
    # return
    # The Todoist v7 python API is a bit of a mess:
    # api.items is not a list of items, but the ItemsManager.
    # To get actual list of items, use `api.state['items']`.
    items_manager = api.items
    # api._update_state creates object instances from the data as defined in `resp_models_mapping`,
    # so we should have `todoist.model.Item` object instances (not just the dicts received from the server):
    tasks = api.state['items']

    # Inject project info, so we can access e.g. task['project_name']:
    if verbose >= 1:
        print("Injecting project info...")
    inject_project_info(tasks=tasks, projects=api.projects.all())
    if verbose >= 2:
        print("Parsing dates and creating ISO strings...")
    parse_task_dates(tasks, strict=False)

    # print("Tasks:", len(tasks))
    # print(tasks)

    def increment_verbosity(tasks):
        # If you modify (reassign) an immutable type within a closure, it is by default considered a local variable.
        # To prevent this, declare that the variable is non-local:
        nonlocal verbose
        verbose += 1
        return tasks
    ACTIONS['v'] = ACTIONS['verbose'] = increment_verbosity

    def print_help(tasks):
        # import re
        # print(repr(action_cli.__doc__))  # Nope, escapes proper line breaks.
        # print(re.escape(action_cli.__doc__))  # Nope, escapes whitespace.
        print(action_cli.__doc__)  # Works, if you are using r""" for your docstrings (which you probably should).
        return tasks
    ACTIONS['h'] = ACTIONS['help'] = print_help

    # For each action in the action chain, invoke the action providing the (remaining) tasks as first argument.
    for action_key, action_args in action_groups:
        n_tasks = len(tasks)
        if verbose >= 2:
            print(f"\nInvoking '{action_key}' action on {n_tasks} with args:", action_args)
        action_func = ACTIONS[action_key]
        tasks = action_func(tasks, *action_args)
        assert tasks is not None


if __name__ == '__main__':
    action_cli()

