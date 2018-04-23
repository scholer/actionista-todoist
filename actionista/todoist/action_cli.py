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
import shlex
import operator
import builtins
from dateutil import tz
import todoist
from todoist.models import Item
import dateparser
import parsedatetime  # Provides better information about the accuracy of the parsed date/time.
import shutil

from actionista import binary_operators
from actionista.todoist.tasks_utils import parse_task_dates, inject_project_info, CUSTOM_FIELDS
from actionista.date_utils import local_time_to_utc, end_of_day, start_of_day
from actionista.date_utils import ISO_8601_FMT, DATE_DAY_FMT
from actionista.todoist.utils import get_config, get_token

NEWLINE = '\n'
DEFAULT_TASK_PRINT_FMT = (
    "{project_name:15} "
    "{due_date_safe_dt:%Y-%m-%d %H:%M}  "
    "{priority_str} "
    "{checked_str} "
    "{content} "
    "(due: {date_string!r})"
)
# print_fmt="{project_name:15} {due_date_safe_dt:%Y-%m-%d %H:%M  } {content}",
# print_fmt="{project_name:15} {due_date_safe_dt:%Y-%m-%d %H:%M}  {checked_str} {content}",
# print_fmt="{project_name:15} {due_date_safe_dt:%Y-%m-%d %H:%M}  {priority_str} {checked_str} {content}",


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


def get_task_value(task, taskkey, default=None, coerce_type=None):
    task = task.data if isinstance(task, Item) else task
    # return taskkey not in task or op(itemgetter(task), value)
    if 'due' in task and taskkey in ('due_date', 'due_date_utc'):
        # Support for v7.1 Sync API with separate 'due' dict attribute:
        # Although this may depend on how `parse_task_dates()` deals with v7.1 tasks.
        due_dict = task.get('due') or {}
        task_value = due_dict.get()
    else:
        task_value = task.get(taskkey, default)
    if coerce_type is not None and task_value is not None and type(task_value) != coerce_type:
        print("NOTICE: `type(task_value) != coerce_type` - Coercing `task_value` to %s:" % type(coerce_type))
        task_value = coerce_type(task_value)
    return task_value


def print_tasks(
        tasks,
        print_fmt=DEFAULT_TASK_PRINT_FMT,
        header=None,  sep="\n"
):
    """ Print tasks, using a python format string.

    Examples:
        `-print`
        `-print "{project_name:15} {due_date_safe_dt:%Y-%m-%d %H:%M  } {content}"`
        `-print "{project_name:15} {content}" "Project name:   Task:`

    Args:
        tasks: List of tasks or task dicts to print.
        print_fmt: How to print each task.
            Note: You can use print_fmt="pprint" to just print all tasks using pprint.
        header: Print a header before printing the tasks.
        sep: How to separate each printed task. Default is just "\n".

    Returns: List of tasks.

    Frequently-used print formats:
        "* {content}"
        "{project_name:15} {due_date_safe_dt:%Y-%m-%d %H:%M  } {content}"
        "{project_name:15} {due_date_safe_iso}    {content}  ({checked})"
        "{project_name:15} {due_date_safe_dt:%Y-%m-%d %H:%M}  {checked}  {content}"
        "{project_name:15} {due_date_safe_dt:%Y-%m-%d %H:%M}  {checked_str}  {content}"

    Frequently-used headers:
        "Project:        Due_date:          Task:"
        "Project:        Due_date:          Done: Task:"
        "Project:        Due_date:        Done: Task:"
        "Project:        Due_date:        P:   Done: Task:"

    See `parse_task_dates()` for available date fields. In brief:
        due_date_utc
        due_date_utc_iso
        due_date_dt
        due_date_local_dt
        due_date_local_iso
        due_date_safe_dt   # These two '_safe_' fields are guaranteed to be present, even if the task
        due_date_safe_iso  # has no due_date, in which case we use the end of the century. (Note: local time!)
        # We also have the same above fields for `date_added` and `completed_date`.

    """
    if header:
        print(header)
    task_dicts = [task.data if isinstance(task, Item) else task for task in tasks]
    if print_fmt == 'repr' or print_fmt == 'pprint':
        import pprint
        pprint.pprint(task_dicts)
    else:
        print(sep.join(print_fmt.format(task=task, **task) for task in task_dicts))
    return tasks


def sort_tasks(tasks, keys="project_name,priority_str,item_order", order="ascending"):
    """ Sort the list of tasks, by task attribute in ascending or descending order.

    Examples:

        Sort tasks by project_name, then priority, in descending order:
            -sort "project_name,priority" descending
            sort_tasks(tasks, keys="project_name,priority", order="descending")

    Frequently-used sortings:

        project_name,priority_str,item_order
        project_name,item_order
        due_date,priority,item_order

    """
    if isinstance(keys, str):
        keys = keys.split(',')
    itemgetter = operator.itemgetter(*keys)
    tasks = sorted(tasks, key=itemgetter, reverse=(order == "descending"))
    return tasks


def filter_tasks(tasks, taskkey, op_name, value, missing="exclude", default=None, value_transform=None, negate=False):
    """ Generic task filtering method based on comparison with a specific task attribute.

    CLI signature:
        $ todoist-action-cli -filter <taskkey> <operator> <value> <missing> <default> <transform> <negate>
    e.g.
        $ todoist-action-cli -filter project_id eq 2076120802 exclude none int

    Args:
        tasks: List of tasks (dicts or todoist.Item).
        taskkey: The attribute key to compare against, e.g. 'due_date_local_iso' or 'project'.
        op_name: Name of the binary operator to use when comparing the task attribute against the given value.
        value: The value to compare the task's attribute against.
        missing: How to deal with tasks with missing attributes, e.g. "include", "exclude", or default to a given value.
        default: Use this value if a task attribute is missing and missing="default".
        value_transform: Perform a given transformation of the input value, e.g. `int`, or `str`.
        negate: Can be used to negate (invert) the filter.
            Some operators already have an inverse operator, e.g. `eq` vs `ne`, `le` vs `gt`.
            But other operators do not have a simple inverse operator, e.g. `startswith`.
            So, if you want to remove/exclude tasks starting with 'Email', use:
                -filter content startswith Email exclude _ _ True
            Note: Negate applies to the transform, but not to tasks included/excluded due to missing value.

    Returns:
        Filtered list of tasks passing the filter criteria (attribute matching value).

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
    if op_name == 'le' and 'date' in taskkey and value[-2:] != '59':
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

    print(f" - Filtering {len(tasks)} tasks with: {taskkey!r} {op_name} {value!r} "
          f"(missing={missing!r}, default={default!r}, value_transform={value_transform!r}, negate={negate!r})\n")

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
        if 'due' in task and taskkey in ('due_date', 'due_date_utc'):
            # Support for v7.1 Sync API with separate 'due' dict attribute:
            # Although this may depend on how `parse_task_dates()` deals with v7.1 tasks.
            due_dict = task.get('due') or {}
            task_value = due_dict.get(taskkey.replace('due_', ''))  # items in the 'due' dict don't have 'due_' prefix
        else:
            task_value = task.get(taskkey, default_)
        if task_value is not None and type(task_value) != type(value):
            # Note: We are converting the *comparison value*, not the task value:
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
            return task_value is None or (op(task_value, value) != negate)
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


def generic_args_filter_adaptor(tasks, taskkey, args, *, default_op='iglob', **kwargs):
    """ A generic adaptor for filter_tasks(), accepting custom *args list.

    Typical use case is to be able to process both of the following action requests
    with a single function:
        `-content RS123*` and `-content startswith RS123`.
    This adaptor function just uses the number of args given to determine if a
    binary operator was provided with the action request.

    Args:
        tasks: List of tasks, passed to filter_tasks.
        taskkey: The task attribute to filter on.
        default_op: The default binary operator to use, in the case the user did not specify one in args.
        *args: User-provided action args, e.g. ['RS123*"], or ['startswith', 'RS123']

    Returns:
        Filtered list of tasks.

    """
    assert len(args) >= 1
    if args[0] == 'not':
        negate = True
        args = args[1:]
    else:
        negate = False
    if len(args) == 1:
        # `-content RS123*`
        op_name, value, args = default_op, args[0], args[1:]
    else:
        # `-content startswith work`
        op_name, value, *args = args
    print(f"generic_args_filter_adaptor: args={args}")
    return filter_tasks(tasks, taskkey=taskkey, op_name=op_name, value=value, negate=negate, *args, **kwargs)


def special_is_filter(tasks, *args):
    """ Special -is filter for ad-hoc or frequently-used cases, e.g. `-is not checked`, etc.

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
    if args[0] == 'due' or args[0] == 'overdue':
        # Note: "-is due" is alias for "due today or overdue" which is equivalent to "due before tomorrow".
        if args[0:2] == ["due", "or", "overdue"] or args[0:2] == ["overdue", "or", "due"]:
            args[0:2] = ["due", "before", "tomorrow"]
        timefmt = ISO_8601_FMT
        taskkey = 'due_date_utc_iso'
        convert = None
        if args[0] == 'overdue':
            op_name = 'lt'
            convert = start_of_day
            when = "today"
        elif len(args) > 1:
            if args[1] in ('before', 'on', 'after'):
                when = args[2]
                if args[1] == 'before':
                    op_name = 'lt'
                    convert = start_of_day
                elif args[1] == 'on':
                    op_name = 'startswith'
                    timefmt = DATE_DAY_FMT
                else:  # args[2] == 'after':
                    op_name = 'gt'
                    convert = end_of_day
            else:
                # "-is due today", same as "-is due on today"
                when = args[1]
                op_name = 'startswith'
                timefmt = DATE_DAY_FMT
        else:
            # "-is due":
            when = "today"
            op_name = 'le'
            convert = end_of_day
        # Using dateparser.DateDataParser().get_date_data() instead of dateparser.parse() we get a 'period' indication:
        # date_data = dateparser.DateDataParser().get_date_data(when)
        # if date_data is None:
        #     raise ValueError("Could not parse due date %r" % (when,))
        # dt, accuracy = date_data['date_obj'], date_data['period']  # Max 'period' precision is 'day' :(
        # Using parsedatetime, since dateparser has a poor concept of accuracy:
        # parsedatetime also understands e.g. "in two days", etc.
        cal = parsedatetime.Calendar()
        # Note: cal.parse returns a time.struct_time, not datetime object,
        # use cal.parseDT() to get a datetime object. Or just dt = datetime.datetime(*dt[:6])
        dt, context = cal.parseDT(when, version=2)  # provide `version` to get a context obj.
        if not context.hasDate:
            raise ValueError("Could not parse due date %r" % (when,))
        if convert and not context.hasTime:
            # Only perform conversion, i.e. snap to start/end of day, when no time indication was provided:
            dt = convert(dt)
        utc_str = local_time_to_utc(dt, fmt=timefmt)
        # date_value_iso = dt.strftime(timefmt)
        # When we request tasks that are due, we don't want completed tasks, so remove these first:
        tasks = filter_tasks(tasks, taskkey="checked", op_name="eq", value=0, missing="include")
        # Then return tasks that are due as requested:
        return filter_tasks(tasks, taskkey=taskkey, op_name=op_name, value=utc_str, negate=negate)
    elif args[0] in ('checked', 'unchecked', 'complete', 'incomplete', 'completed', 'done'):
        # -is not checked
        if args[0][:2] in ('in', 'un'):
            checked_val = 0
        else:
            checked_val = 1
        taskkey = "checked"
        op_name = "eq"
        return filter_tasks(tasks, taskkey=taskkey, op_name=op_name, value=checked_val, negate=negate)
    elif args[0] == 'in':
        taskkey = "project_name"
        op_name = "eq"
        value = args[1]
        return filter_tasks(tasks, taskkey=taskkey, op_name=op_name, value=value, negate=negate)
    elif args[0] == 'recurring':
        """ `-is [not] recurring` filter.
        NOTE: The 'is_recurring' attribute is not officially exposed and "may be removed soon",
        c.f. https://github.com/Doist/todoist-api/issues/33.
        Until then, perhaps it is better to filter based on whether the date_string starts with the word "every". 
        """
        # taskkey = "is_recurring"
        # op_name = "eq"
        # value = 1
        # return filter_tasks(tasks, taskkey=taskkey, op_name=op_name, value=value, negate=negate)
        # -is not recurring : for recurring task : negate==True, startswith('every')==True => startswith == negate
        print(f" - Filtering {len(tasks)} tasks, excluding {'' if negate else 'non-'}recurring tasks...\n")
        return [task for task in tasks
                if str(get_task_value(task, 'date_string')).lower().startswith('every') is not negate]
    else:
        raise ValueError("`-is` parameter %r not recognized. (args = %r)" % (args[0], args))


def is_not_filter(tasks, *args):
    """ Convenience `-not` action, just an alias for `-is not`. Can be used as e.g. `-not recurring`."""
    args = ['not'] + list(args)
    return special_is_filter(tasks, *args)


def due_date_filter(tasks, *when):
    """ Special `-due [when]` filter. Is just an alias for `-is due [when]`. """
    args = ['due'] + list(when)  # Apparently *args is a tuple, not a list.
    return special_is_filter(tasks, *args)


def content_filter(tasks, *args):
    """ Convenience adaptor to filter tasks based on the 'content' attribute (default op_name 'iglob'). """
    return generic_args_filter_adaptor(tasks=tasks, taskkey='content', args=args)


def content_contains_filter(tasks, value, *args):
    """ Convenience filter action using taskkey="content", op_name="contains". """
    return filter_tasks(tasks, taskkey="content", op_name="contains", value=value, *args)


def content_startswith_filter(tasks, value, *args):
    """ Convenience filter action using taskkey="content", op_name="startswith". """
    return filter_tasks(tasks, taskkey="content", op_name="startswith", value=value, *args)


def content_endswith_filter(tasks, value, *args):
    """ Convenience filter action using taskkey="content", op_name="endswith"."""
    return filter_tasks(tasks, taskkey="content", op_name="endswith", value=value, *args)


def content_glob_filter(tasks, value, *args):
    """ Convenience filter action using taskkey="content", op_name="glob". """
    return filter_tasks(tasks, taskkey="content", op_name="glob", value=value, *args)


def content_iglob_filter(tasks, value, *args):
    """ Convenience filter action using taskkey="content", op_name="iglob". """
    return filter_tasks(tasks, taskkey="content", op_name="iglob", value=value, *args)


def content_eq_filter(tasks, value, *args):
    """ Convenience filter action using taskkey="content", op_name="eq". """
    return filter_tasks(tasks, taskkey="content", op_name="eq", value=value, *args)


def content_ieq_filter(tasks, value, *args):
    """ Convenience filter action using taskkey="content", op_name="ieq". """
    return filter_tasks(tasks, taskkey="content", op_name="ieq", value=value, *args)


def project_filter(tasks, *args):
    """ Convenience adaptor for filter action using taskkey="project_name" (default op_name "iglob"). """
    return generic_args_filter_adaptor(tasks=tasks, taskkey='project_name', args=args)


def project_iglob_filter(tasks, value, *args):
    """ Convenience filter action using taskkey="content", op_name="iglob". """
    return filter_tasks(tasks, taskkey="project_name", op_name="iglob", value=value, *args)


def priority_filter(tasks, *args):
    """ Convenience adaptor for filter action using taskkey="priority" (default op_name "eq"). """
    return generic_args_filter_adaptor(tasks=tasks, taskkey='priority', args=args, default_op='eq', value_transform=int)


def priority_ge_filter(tasks, value, *args):
    """ Convenience filter action using taskkey="priority", op_name="ge". """
    value = int(value)
    return filter_tasks(tasks, taskkey="priority", op_name="ge", value=value, *args)


def priority_eq_filter(tasks, value, *args):
    """ Convenience filter action using taskkey="priority", op_name="eq". """
    value = int(value)
    return filter_tasks(tasks, taskkey="priority", op_name="eq", value=value, *args)


def priority_str_filter(tasks, *args):
    """ Convenience adaptor for filter action using taskkey="priority_str" (default op_name "eq"). """
    # return filter_tasks(tasks, taskkey="priority_str", op_name="eq", value=value, *args)
    return generic_args_filter_adaptor(tasks=tasks, taskkey='priority_str', args=args, default_op='eq')


def priority_str_eq_filter(tasks, value, *args):
    """ Convenience filter action using taskkey="priority_str", op_name="eq". """
    return filter_tasks(tasks, taskkey="priority_str", op_name="eq", value=value, *args)


def p1_filter(tasks, *args):
    """ Filter tasks including only tasks with priority 'p1'. """
    return priority_str_eq_filter(tasks, value="p1", *args)


def p2_filter(tasks, *args):
    """ Filter tasks including only tasks with priority 'p2'. """
    return priority_str_eq_filter(tasks, value="p2", *args)


def p3_filter(tasks, *args):
    """ Filter tasks including only tasks with priority 'p3'. """
    return priority_str_eq_filter(tasks, value="p3", *args)


def p4_filter(tasks, *args):
    """ Filter tasks including only tasks with priority 'p3'. """
    return priority_str_eq_filter(tasks, value="p4", *args)


def reschedule_tasks(tasks, new_date, timezone='date_string', update_local=False):
    """ Reschedule tasks to a new date/time.

    Example: Reschedule overdue tasks for tomorrow
        $ todoist-action-cli -sync -due before today -reschedule tomorrow
    Will reschedule overdue tasks using:
        reschedule_tasks(tasks, 'tomorrow')

    Args:
        tasks: List of tasks.
        new_date:
        timezone:
        update_local:

    Returns:
        List of tasks.

    WOOOOOT:
    When SENDING an updated `due_date_utc`, it must be in ISO8601 format!
    From https://developer.todoist.com/sync/v7/?shell#update-an-item :
    > The date of the task in the format YYYY-MM-DDTHH:MM (for example: 2012-3-24T23:59).
    > The value of due_date_utc must be in UTC. Note that, when the due_date_utc argument is specified,
    > the date_string is required and has to specified as well, and also, the date_string argument will be
    > parsed as local timestamp, and converted to UTC internally, according to the user’s profile settings.

    Maybe take a look at what happens in the web-app when you reschedule a task?
    Hmm, the webapp uses the v7.1 Sync API at /API/v7.1/sync.
    The v7.1 API uses task items with a "due" dict with keys "date", "timezone", "is_recurring", "string", and "lang".
    This seems to make 'due_date_utc' obsolete. Seems like a good decision, but it makes some of my work obsolete.

    Perhaps it is easier to just only pass `date_string`, especially for non-recurring tasks.

    Regarding v7.1 Sync API:
        * The web client doesn't send "next sunday" date strings any more. The client is in charge of parsing
            the date and sending a valid date. The due.string was set to "15 Apr".
    """
    print("\n\nRescheduling %s tasks for %r..." % (len(tasks), new_date))
    print(" - Remember to use `-commit` to push the changes (not `-sync`)!\n\n")
    if timezone == 'date_string':  # Making this the default
        # Special case; instead of updating the due_date_utc, just send `date_string` to server.
        # Note: For non-repeating tasks, this is certainly by far the simplest way to update due dates.
        for task in tasks:
            if 'due' in task.data:
                # Support v7.1 Sync API with dedicated 'due' dict attribute.
                new_due = {'string': new_date}
                task.update(due=new_due)
            else:
                task.update(date_string=new_date)
        return tasks
    if isinstance(new_date, str):
        new_date_str = new_date  # Save the str
        new_date = dateparser.parse(new_date)
        if new_date is None:
            raise ValueError("Could not parse date %r." % (new_date_str,))
        # Hmm, dateparser.parse evaluates "tomorrow" as "24 hours from now", not "tomorrow at 0:00:00).
        # This is problematic since we typically reschedule tasks as all day events.
        # dateparser has 'tomorrow' hard-coded as alias for "in 1 day", making it hard to re-work.
        # Maybe it is better to just reschedule using date_string?
        # But using date_string may overwrite recurring tasks?
        # For now, just re-set time manually if new_date_str is "today", "tomorrow", etc.
        if new_date_str in ('today', 'tomorrow') or 'days' in new_date_str:
            new_date = new_date.replace(hour=23, minute=59, second=59)  # The second is the important part for Todoist.
        # For more advanced, either use a different date parsing library, or use pendulum to shift the date.
        # Alternatively, use e.g. parsedatetime, which supports "eod tomorrow".
    if new_date.tzinfo is None:
        if timezone == 'local':
            timezone = tz.tzlocal()
        elif isinstance(timezone, str):
            timezone = tz.gettz(timezone)
        new_date.replace(tzinfo=timezone)
    # Surprisingly, when adding or updating due_date_utc with the v7.0 Sync API,
    # `due_date_utc` should supposedly be in ISO8601 format, not the usual ctime-like format. Sigh.
    new_date_utc = local_time_to_utc(new_date, fmt=ISO_8601_FMT)
    for task in tasks:
        date_string = task['date_string']
        task.update(due_date_utc=new_date_utc, date_string=date_string)
        # Note: other fields are not updated!
        if update_local:
            task['due_date_utc'] = new_date_utc
    if update_local:
        parse_task_dates(tasks)
    return tasks


def update_tasks(tasks):
    """ Generic task updater.

    Todoist task updating caveats:

    * priority: This is VERY weird! From the v7 sync API docs:
        > "Note: Keep in mind that "very urgent" is the priority 1 on clients. So, p1 will return 4 in the API."
        In other words, these are all reversed:
            p4 -> 1, p3 -> 2, p2 -> 3, p1 -> 4.
        That is just insane.

    """
    return tasks


def mark_tasks_completed(tasks, method='close'):
    """ Mark tasks as completed using method='close'.

    Note: The Todoist v7 Sync API has two command types for completing tasks:
        'item_complete' - used by ?
        'item_uncomplete' - Mark task as uncomplete.
        'item_update_date_complete' - used to mark recurring task completion.
        'item_close' - does exactly what official clients do when you close a task:
            regular task is completed and moved to history,
            subtasks are checked (marked as done, but not moved to history),
            recurring task is moved forward (due date is updated).
            Aka: "done".

    See: https://developer.todoist.com/sync/v7/#complete-items

    Args:
        tasks:  List of tasks.
        method: The method used to close the task.
            There are several meanings of marking a task as completed, especially for recurring tasks.

    Returns:
        tasks:  List of tasks (after closing them).

    """
    for task in tasks:
        if method == 'close':
            task.close()
        else:
            raise ValueError(f"Value for method = {method!r} not recognized!")
    return tasks


def fetch_completed_tasks(tasks):
    """ This will replace `tasks` with a list of completed tasks dicts. May not work nicely. Only for playing around.

    You should probably use the old CLI instead:
        $ todoist print-completed-today --print-fmt "* {title}"
    """
    print(f"Discarting the current {len(tasks)} tasks, and fetching completed tasks instead...")
    from actionista.todoist.adhoc_cli import completed_get_all
    # This will use a different `api` object instance to fetch completed tasks:
    tasks, projects = completed_get_all()
    inject_project_info(tasks, projects)
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
    'has': filter_tasks,  # Undocumented alias, for now.
    'is': special_is_filter,  # Special cases, e.g. "-is incomplete" or "-is not overdue".
    'not': is_not_filter,
    'due': due_date_filter,
    # contains, startswith, glob/iglob, eq/ieq are all trivial derivatives of filter:
    # But they are special in that we use the binary operator name as the action name,
    # and assumes we want to filter the tasks, using 'content' as the task key/attribute.
    'contains': content_contains_filter,
    'startswith': content_startswith_filter,
    'endswith': content_endswith_filter,
    'glob': content_glob_filter,
    'iglob': content_iglob_filter,
    'eq': content_eq_filter,
    'ieq': content_ieq_filter,
    # Convenience actions where action name specifies the task attribute to filter on:
    'content': content_filter,  # `-content endswith "sugar".
    'name': content_filter,  # Alias for content_filter.
    'project': project_filter,
    'priority': priority_filter,
    # More derived 'priority' filters:
    'priority-eq': priority_eq_filter,
    'priority-ge': priority_ge_filter,
    'priority-str': priority_str_filter,
    'priority-str-eq': priority_str_eq_filter,
    'p1': p1_filter,
    'p2': p2_filter,
    'p3': p3_filter,
    'p4': p4_filter,
    # Update task actions:
    'reschedule': reschedule_tasks,
    'mark-completed': mark_tasks_completed,
    'mark-as-done': mark_tasks_completed,
    # 'fetch-completed': fetch_completed_tasks,  # WARNING: Not sure how this works, but probably doesn't work well.
    # The following actions are overwritten when the api object is created inside the action_cli() function:
    'verbose': None, 'v': None,
    'delete-cache': None,
    'sync': None,
    'commit': None,
    'show-queue': None,
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

        More examples:

            $ todoist-action-cli -due before tomorrow -not recurring -project not Personal-* \
                -sort "project_name,priority_str,due_date_local_iso" -print

    -Note: -sync is currently implied as the first action.-  (Edit: No, using cache for while testing.)

    Available actions include:
        -filter         filter the task list.
        -sort           sort the task list.
        -print          print the task list.
        -reschedule     reschedule all tasks in the current task list, usually after filter-selecting.
        -mark-completed mark all tasks in the tasks list as completed.
        -sync:          Sync changes with the server. NOTE that sync will reset all previous task filters!
        -commit:        Commit local changes. Will ask for confirmation if `-y` has not been given beforehand.
        -y, -yes:       Skip all confirmation prompts.

    You can chain as many operations as you need, but you cannot fork the pipeline.
    There is also no support for "OR" operators (or JOIN, or similar complexities).

    To get help on each action, use:
        `$ todoist-action-cli -help <action>`

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
            You can print the full task data using "{task}", or the special "repr" or "pprint" keywords.
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
    (base_args, base_kwargs), action_groups = parse_argv(argv=argv)

    config = get_config() or {}
    config.update(base_kwargs)
    token = get_token(raise_if_missing=True, config=config)
    api = todoist.TodoistAPI(token=token)
    if config.get('api_url'):
        # Default: 'https://todoist.com/API/v7/' (including the last '/')
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
    task_itemss = api.state['items']

    # Inject project info, so we can access e.g. task['project_name']:
    if verbose >= 1:
        print("Injecting project info...")
    inject_project_info(tasks=task_itemss, projects=api.projects.all())
    if verbose >= 2:
        print("Parsing dates and creating ISO strings...")
    parse_task_dates(task_itemss, strict=False)

    def increment_verbosity(tasks):
        """ Increase program informational output verbosity. """
        # If you modify (reassign) an immutable type within a closure, it is by default considered a local variable.
        # To prevent this, declare that the variable is non-local:
        nonlocal verbose
        verbose += 1
        return tasks
    ACTIONS['v'] = ACTIONS['verbose'] = increment_verbosity

    ask_before_commit = True

    def disable_confirmation_prompt(tasks):
        """ Disable confirmation prompt before enacting irreversible commands, e.g. -commit. """
        nonlocal ask_before_commit
        ask_before_commit = False
        return tasks
    ACTIONS['y'] = ACTIONS['yes'] = ACTIONS['no-prompt'] = disable_confirmation_prompt

    # Better to define sync here rather than relying on getting api from existing task
    def sync(tasks):
        """ Pull task updates from the server to synchronize the local task data cache.
        Note: api.sync() without arguments will just fetch updates (no commit of local changes).
        """
        # Remove custom fields (in preparation for JSON serialization during `_write_cache()`:
        n_before = len(tasks)
        print("\nSyncing... (fetching updates FROM the server; use `commit` to push changes!\n")
        for task in api.state['items']:
            for k in CUSTOM_FIELDS:
                task.data.pop(k, None)  # pop(k, None) returns None if key doesn't exists, unlike `del task[k]`.
        api.sync()
        tasks = api.state['items']
        n_after = len(tasks)
        print(f" - {n_after} tasks after sync ({n_before} tasks in the task list before sync).")
        parse_task_dates(tasks)
        inject_project_info(tasks=tasks, projects=api.projects.all())
        return tasks
    ACTIONS['sync'] = sync

    def commit(tasks, *, raise_on_error=True):
        """ Commit is a sync that includes local commands from the queue, emptying the queue. Raises SyncError. """
        # Prompt if needed:
        if ask_before_commit:
            answer = input(f"\nPROMPT: About to commit {len(api.queue)} updates. Continue? [Y/n] ") or 'Y'
            if answer[0].lower() == 'n':
                print(" - OK, ABORTING commit.")
                return tasks
        print(f"\nCommitting {len(api.queue)} local changes and fetching updates...\n")
        # Remove custom fields before commit (and re-add them again afterwards)
        for task in api.state['items']:
            for k in CUSTOM_FIELDS:
                task.data.pop(k, None)  # pop(k, None) returns None if key doesn't exists, unlike `del task[k]`.
        # Commit changes (includes an automatic sync), and re-parse task items:
        api.commit(raise_on_error=raise_on_error)
        tasks = api.state['items']
        parse_task_dates(tasks)
        inject_project_info(tasks=tasks, projects=api.projects.all())
        return tasks
    ACTIONS['commit'] = commit

    # Better to define sync here rather than relying on getting api from existing task
    def show_queue(tasks):
        """ Show list of API commands in the POST queue. """
        # Remove custom fields (in preparation for JSON serialization during `_write_cache()`:
        from pprint import pprint
        print("\n\nAPI QUEUE:\n----------\n")
        pprint(api.queue)
        return tasks
    ACTIONS['show-queue'] = show_queue
    ACTIONS['print-queue'] = show_queue

    def delete_cache(tasks):
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

    def print_help(tasks, cmd=None):
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
    ACTIONS['h'] = ACTIONS['help'] = print_help

    unrecognized_actions = [agroup[0] for agroup in action_groups if agroup[0] not in ACTIONS]
    if unrecognized_actions:
        print("ERRROR, the following actions were not recognized:", unrecognized_actions)
        return

    if len(action_groups) == 0:
        # Print default help
        action_groups.append(('help', [], {}))

    # For each action in the action chain, invoke the action providing the (remaining) tasks as first argument.
    for action_key, action_args, action_kwargs in action_groups:
        n_tasks = len(task_itemss)
        if verbose >= 2:
            print(f"\nInvoking '{action_key}' action on {n_tasks} tasks with args: {action_args!r}\n")
        action_func = ACTIONS[action_key]
        task_itemss = action_func(task_itemss, *action_args, **action_kwargs)
        assert task_itemss is not None


if __name__ == '__main__':
    action_cli()
