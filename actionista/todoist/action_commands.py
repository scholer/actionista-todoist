# Copyright 2019, Rasmus Sorensen <rasmusscholer@gmail.com>
"""

Module containing Todoist action commands for the todoist-action-cli.




"""
import operator
import sys
import builtins

import parsedatetime
from dateutil import tz
from todoist.models import Item

from actionista import binary_operators
# 'in' is a reserved keyword, so the equivalent command is `in_`:
setattr(binary_operators, 'in', binary_operators.in_)
from actionista.date_utils import ISO_8601_FMT, start_of_day, DATE_DAY_FMT, end_of_day
from actionista.date_utils import local_time_to_utc, get_rfc3339_datestr
from actionista.todoist.config import DEFAULT_TASK_PRINT_FMT, DEFAULT_TASK_SORT_KEYS, DEFAULT_TASK_SORT_ORDER
from actionista.todoist.config import get_config
from actionista.todoist.tasks_utils import get_task_value, get_recurring_tasks, is_recurring
from actionista.todoist.tasks_utils import inject_tasks_project_fields


CONFIG = get_config()


def print_tasks(
        tasks: list,
        print_fmt: str = DEFAULT_TASK_PRINT_FMT,
        header=None, sep: str = "\n",
        *,
        data_attr: str = "_custom_data",
        verbose: int = 0,
        config=None,
):
    """ Print tasks, using a python format string.

    Examples:
        `-print`
        `-print "{project_name:15} {due_date_safe_dt:%Y-%m-%d %H:%M  } {content}"`
        `-print "{project_name:15} {content}" "Project name:   Task:`

    Args:
        tasks: List of tasks or task_data dicts to print.
        print_fmt: How to print each task.
            Note: You can use print_fmt="pprint" to just print all tasks using pprint.
        header: Print a header before printing the tasks.
        sep: How to separate each printed task. Default is just "\n".
        # Keyword only arguments:
        data_attr: The task attribute to get task data from.
            Original data from the Todoist Sync API is stored in Item.data,
            but I prefer to add derived data fields in a separate Item._custom_data,
            so that they don't get persisted when writing the cache to disk.
        verbose: The verbosity to print informational messages with during the filtering process.
        config: Optional configuration dict.

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

    See `inject_tasks_date_fields()` for available date fields. In brief:
        due_date_utc
        due_date_utc_iso
        due_date_dt
        due_date_local_dt
        due_date_local_iso
        due_date_safe_dt   # These two '_safe_' fields are guaranteed to be present, even if the task
        due_date_safe_iso  # has no due_date, in which case we use the end of the century. (Note: local time!)
        # We also have the same above fields for `date_added` and `completed_date`.

    """
    if config is None:
        config = CONFIG
    if print_fmt is None:
        print_fmt = config.get('default_task_print_fmt', DEFAULT_TASK_PRINT_FMT) if config else DEFAULT_TASK_PRINT_FMT
    if verbose > -1:
        print(f"\n - Printing {len(tasks)} tasks",
              f"separated by {sep!r}, using print_fmt:\n{print_fmt!r}.\n" if verbose else "...\n",
              file=sys.stderr)
    if header:
        print(header)
    # Use `task._custom_data`, which is a copy of task.data with extra stuff added (if available).
    task_dicts = [getattr(task, data_attr, task.data) if isinstance(task, Item) else task for task in tasks]
    if print_fmt == 'repr' or print_fmt == 'pprint':
        import pprint
        pprint.pprint(task_dicts)
    else:
        print(sep.join(print_fmt.format(task=task, **task) for task in task_dicts))
    return tasks


def sort_tasks(tasks, keys=DEFAULT_TASK_SORT_KEYS, order=DEFAULT_TASK_SORT_ORDER,
               *, data_attr="_custom_data", verbose=0, config=None):
    """ Sort the list of tasks, by task attribute in ascending or descending order.

    Args:
        tasks: The tasks to sort (dicts or todoist.moddl.Item objects).
        keys: The keys to sort by. Should be a list or comma-separated string.
        order: The sort order, either ascending or descending.
        # Keyword only arguments:
        data_attr: Ues this attribute for task data. For instance, if the
        verbose: The verbosity to print informational messages with during the filtering process.

    Examples:

        Sort tasks by project_name, then priority, in descending order:
            -sort "project_name,priority" descending
            sort_tasks(tasks, keys="project_name,priority", order="descending")

    Frequently-used sortings:

        project_name,priority_str,item_order
        project_name,item_order
        due_date,priority,item_order

    """
    if config is None:
        config = CONFIG
    if keys is None:
        keys = config.get('default_task_sort_keys', DEFAULT_TASK_SORT_KEYS) if config else DEFAULT_TASK_SORT_KEYS
    if order is None:
        order = config.get('default_task_sort_order', DEFAULT_TASK_SORT_ORDER) if config else DEFAULT_TASK_SORT_ORDER
    if verbose > -1:
        print(f"\n - Sorting {len(tasks)} tasks by {keys!r} ({order}).", file=sys.stderr)
    if isinstance(keys, str):
        keys = keys.split(',')
    itemgetter = operator.itemgetter(*keys)
    if data_attr:
        def keyfunc(task):
            return itemgetter(getattr(task, data_attr, task.data))
    else:
        keyfunc = itemgetter
    tasks = sorted(tasks, key=keyfunc, reverse=(order == "descending"))
    return tasks


def filter_tasks(
        tasks,
        taskkey, op_name, value,
        missing="exclude", default=None,
        value_transform=None, negate=False,
        data_attr="_custom_data",
        *, verbose=0):
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
            value_transform can be the name of any function/class in the current namespace.
        negate: Can be used to negate (invert) the filter.
            Some operators already have an inverse operator, e.g. `eq` vs `ne`, `le` vs `gt`.
            But other operators do not have a simple inverse operator, e.g. `startswith`.
            So, if you want to remove/exclude tasks starting with 'Email', use:
                -filter content startswith Email exclude _ _ True
            Note: Negate applies to the transform, but not to tasks included/excluded due to missing value.
        data_attr: Instead of using task or task.data, use `getatr(task, data_attr)`.
            This is useful if you are setting custom task data on `task._custom_data` to keep them separate.
        verbose: The verbosity to print informational messages with during the filtering process.

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
              "less-than-or-equal-to (`le`) operator, make sure to specify full time in comparison.\n",
              file=sys.stderr)
    if taskkey == 'due_date_utc':
        print("\nNOTICE: You are using 'due_date_utc' as filter taskkey. This has the rather-unhelpful "
              "format: 'Mon 26 Mar 2018 21:59:59 +0000'.\n", file=sys.stderr)
    # We often use "_" as placeholeder on the command line, because we cannot enter e None value:
    if default == '_' or default == '__None__':
        default = None
    if value_transform == '_' or value_transform == '__None__':
        value_transform = None
    if isinstance(negate, str) and negate.lower() in ('false', '_', '__none__', '0'):
        # Enabling easier ways to specify `negate` on the command line.
        negate = False

    negate = bool(negate)
    if isinstance(value, str) and len(value) > 0 and value[0] == "!":
        # Using exclamation mark is an established way to make a negative filter,
        # e.g. `-label !habit` to filter-out tasks with the "habit" label.
        negate = not negate
        value = value[1:]

    op = getattr(binary_operators, op_name)
    # I'm currently negating explicitly in the all four 'missing' cases,
    # but I could also just have re-defined `op` as: `def op(a, b): return _op(a, b) != negate`

    if verbose > -1:
        print(f"\n - Filtering {len(tasks)} tasks with: {taskkey!r} {op_name} {value!r} "
              f"(missing={missing!r}, default={default!r}, value_transform={value_transform!r}, negate={negate!r}).",
              file=sys.stderr)

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
                if verbose > -1:
                    print(f"Creating filter value transform by `eval({value_transform!r})` ...", file=sys.stderr)
                t = eval(value_transform)
                if hasattr(t, '__call__'):
                    value_transform = t
                else:
                    # Was a one-off eval transform intended as: `value = eval('value*2')`.
                    value = t
                    value_transform = None  # Prevent further transformation

    # value_transform can be used to transform the filter/comparison value to e.g. an int or datetime object:
    if value_transform:
        # custom callable:
        value = value_transform(value)
        if default and missing == "default":  # Only try to transform task default value if we actually need it
            default = value_transform(default)

    # TODO: Remove this! Instead, use `get_task_value()` - and `value_transform(value)` to tranform comparison value.
    def get_value(task, default_=None):
        nonlocal value
        task = getattr(task, data_attr, task.data) if isinstance(task, Item) else task
        # return taskkey not in task or op(itemgetter(task), value)
        if 'due' in task and taskkey in ('due_date', 'due_date_utc'):
            # Support for v7.1 Sync API with separate 'due' dict attribute:
            # Although this may depend on how `inject_tasks_date_fields()` deals with v7.1 tasks.
            due_dict = task.get('due') or {}
            task_value = due_dict.get(taskkey.replace('due_', ''))  # items in the 'due' dict don't have 'due_' prefix
        else:
            task_value = task.get(taskkey, default_)
        # Coercing the comparison value may not be optimal for lists, e.g. `-filter label_names contains 'habit'`
        # Maybe only coerce for ints? (e.g. priority?)
        if task_value is not None and type(task_value) != type(value) and isinstance(task_value, int):
            # Note: We are converting the *comparison value*, not the task value:
            print("NOTICE: `type(task_value) != type(value)` - Coercing `value` to %s:" % type(task_value),
                  file=sys.stderr)
            value = type(task_value)(value)
        return task_value

    if missing == "raise":
        def filter_eval(task):
            task_value = get_value(task)
            if verbose > 0:
                print(f"\n - Evaluating: task[{taskkey!r}] = {task_value}  {op_name} ({op}) {value} "
                      f"for task {task['content']} (due: {get_task_value(task, 'due_date')}) ",
                      file=sys.stderr)
            if task_value is None:
                raise ValueError(f"Key {taskkey!r} not present (or None) in task {task['id']}: {task['content']}")
            return op(task_value, value) != negate  # This comparison with negate will negate if negate is True.
    elif missing == "include":
        def filter_eval(task):
            # return taskkey not in task or op(itemgetter(task), value)
            task_value = get_value(task)
            if verbose > 0:
                print(f"\n - Evaluating: task[{taskkey!r}] = {task_value}  {op_name} ({op}) {value} "
                      f"for task {task['content']} (due: {get_task_value(task, 'due_date')}) ",
                      file=sys.stderr)
            return task_value is None or (op(task_value, value) != negate)
    elif missing == "exclude":
        def filter_eval(task):
            # return taskkey in task and op(itemgetter(task), value)
            task_value = get_value(task)
            if verbose > 0:
                print(f"\n - Evaluating: task[{taskkey!r}] = {task_value}  {op_name} ({op}) {value} "
                      f"for task {task['content']} (due: {get_task_value(task, 'due_date')}) ",
                      file=sys.stderr)
            return task_value is not None and (op(task_value, value) != negate)
    elif missing == "default":
        def filter_eval(task):
            task_value = get_value(task, default)
            return op(task_value, value) != negate
        if default is None:
            print('\nWARNING: filter_tasks() called with missing="default" but no default value given (is None).\n',
                  file=sys.stderr)
    else:
        raise ValueError("Argument `missing` value %r not recognized." % (missing,))

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

    # print(f"generic_args_filter_adaptor: args={args}")  # debugging
    return filter_tasks(tasks, taskkey=taskkey, op_name=op_name, value=value, negate=negate, *args, **kwargs)


def special_is_filter(tasks, *args, **kwargs):
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
        taskkey = 'due_date_utc_iso'  # Switch to 'due_date_iso' (or 'due_date_dt')
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
        tasks = filter_tasks(tasks, taskkey="checked", op_name="eq", value=0, missing="include", **kwargs)
        # Then return tasks that are due as requested:
        # return filter_tasks(tasks, taskkey=taskkey, op_name=op_name, value=utc_str, negate=negate, **kwargs)
        # Update, 2019-Sep: Use local datetime object for comparison:
        # OBS: can't compare offset-naive and offset-aware datetimes - so make sure `dt` has tzinfo:
        dt = dt.astimezone(tz.tzlocal())
        # Discussion: Maybe use 'due_date_safe_dt', which where tasks with no due date is set to a distant future.
        return filter_tasks(tasks, taskkey='due_date_dt', op_name=op_name, value=dt, negate=negate,
                            missing='exclude', **kwargs)
    elif args[0] in ('checked', 'unchecked', 'complete', 'incomplete', 'completed', 'done'):
        # -is not checked
        if args[0][:2] in ('in', 'un'):
            checked_val = 0
        else:
            checked_val = 1
        taskkey = "checked"
        op_name = "eq"
        return filter_tasks(tasks, taskkey=taskkey, op_name=op_name, value=checked_val, negate=negate, **kwargs)
    elif args[0] == 'in':
        taskkey = "project_name"
        op_name = "eq"
        value = args[1]
        return filter_tasks(tasks, taskkey=taskkey, op_name=op_name, value=value, negate=negate, **kwargs)
    elif args[0] == 'recurring':
        """ `-is [not] recurring` filter.
        NOTE: The 'is_recurring' attribute is not officially exposed and "may be removed soon",
        c.f. https://github.com/Doist/todoist-api/issues/33.
        Until then, perhaps it is better to filter based on whether the due_string starts with the word "every". 
        """
        # taskkey = "is_recurring"
        # op_name = "eq"
        # value = 1
        # return filter_tasks(tasks, taskkey=taskkey, op_name=op_name, value=value, negate=negate)
        # -is not recurring : for recurring task : negate==True, startswith('every')==True => startswith == negate
        print(f"\n - Filtering {len(tasks)} tasks, excluding {'' if negate else 'non-'}recurring tasks...")
        return get_recurring_tasks(tasks, negate=negate)
    else:
        raise ValueError("`-is` parameter %r not recognized. (args = %r)" % (args[0], args))


def is_not_filter(tasks, *args, **kwargs):
    """ Convenience `-not` action, just an alias for `-is not`. Can be used as e.g. `-not recurring`."""
    args = ['not'] + list(args)
    return special_is_filter(tasks, *args, **kwargs)


def due_date_filter(tasks, *when, **kwargs):
    """ Special `-due [when]` filter. Is just an alias for `-is due [when]`. """
    args = ['due'] + list(when)  # Apparently *args is a tuple, not a list.
    return special_is_filter(tasks, *args, **kwargs)


def content_filter(tasks, *args, **kwargs):
    """ Convenience adaptor to filter tasks based on the 'content' attribute (default op_name 'iglob'). """
    return generic_args_filter_adaptor(tasks=tasks, taskkey='content', args=args, **kwargs)


def content_contains_filter(tasks, value, *args, **kwargs):
    """ Convenience filter action using taskkey="content", op_name="contains". """
    return filter_tasks(tasks, taskkey="content", op_name="contains", value=value, *args, **kwargs)


def content_startswith_filter(tasks, value, *args, **kwargs):
    """ Convenience filter action using taskkey="content", op_name="startswith". """
    return filter_tasks(tasks, taskkey="content", op_name="startswith", value=value, *args, **kwargs)


def content_endswith_filter(tasks, value, *args, **kwargs):
    """ Convenience filter action using taskkey="content", op_name="endswith"."""
    return filter_tasks(tasks, taskkey="content", op_name="endswith", value=value, *args, **kwargs)


def content_glob_filter(tasks, value, *args, **kwargs):
    """ Convenience filter action using taskkey="content", op_name="glob". """
    return filter_tasks(tasks, taskkey="content", op_name="glob", value=value, *args, **kwargs)


def content_iglob_filter(tasks, value, *args, **kwargs):
    """ Convenience filter action using taskkey="content", op_name="iglob". """
    return filter_tasks(tasks, taskkey="content", op_name="iglob", value=value, *args, **kwargs)


def content_eq_filter(tasks, value, *args, **kwargs):
    """ Convenience filter action using taskkey="content", op_name="eq". """
    return filter_tasks(tasks, taskkey="content", op_name="eq", value=value, *args, **kwargs)


def content_ieq_filter(tasks, value, *args, **kwargs):
    """ Convenience filter action using taskkey="content", op_name="ieq". """
    return filter_tasks(tasks, taskkey="content", op_name="ieq", value=value, *args, **kwargs)


def project_filter(tasks, *args, **kwargs):
    """ Convenience adaptor for filter action using taskkey="project_name" (default op_name "iglob"). """
    return generic_args_filter_adaptor(tasks=tasks, taskkey='project_name', args=args, **kwargs)


def project_iglob_filter(tasks, value, *args, **kwargs):
    """ Convenience filter action using taskkey="content", op_name="iglob". """
    return filter_tasks(tasks, taskkey="project_name", op_name="iglob", value=value, *args, **kwargs)


def label_filter(tasks, value, *args, **kwargs):
    """ Convenience filter action using taskkey="label_names", op_name="iin".
    OBS: The syntax is `-filter <taskkey> <op> <value>`,
    so we should be using `contains` as the op name.
    """
    return filter_tasks(tasks, taskkey="label_names", op_name="icontains", value=value, *args, **kwargs)


def priority_filter(tasks, *args, **kwargs):
    """ Convenience adaptor for filter action using taskkey="priority" (default op_name "eq"). """
    return generic_args_filter_adaptor(
        tasks=tasks, taskkey='priority', args=args, default_op='eq', value_transform=int, **kwargs)


def priority_ge_filter(tasks, value, *args, **kwargs):
    """ Convenience filter action using taskkey="priority", op_name="ge". """
    value = int(value)
    return filter_tasks(tasks, taskkey="priority", op_name="ge", value=value, *args, **kwargs)


def priority_eq_filter(tasks, value, *args, **kwargs):
    """ Convenience filter action using taskkey="priority", op_name="eq". """
    value = int(value)
    return filter_tasks(tasks, taskkey="priority", op_name="eq", value=value, *args, **kwargs)


def priority_str_filter(tasks, *args, **kwargs):
    """ Convenience adaptor for filter action using taskkey="priority_str" (default op_name "eq"). """
    # return filter_tasks(tasks, taskkey="priority_str", op_name="eq", value=value, *args)
    return generic_args_filter_adaptor(
        tasks=tasks, taskkey='priority_str', args=args, default_op='eq', **kwargs
    )


def priority_str_eq_filter(tasks, value, *args, **kwargs):
    """ Convenience filter action using taskkey="priority_str", op_name="eq". """
    return filter_tasks(tasks, taskkey="priority_str", op_name="eq", value=value, *args, **kwargs)


def p1_filter(tasks, *args, **kwargs):
    """ Filter tasks including only tasks with priority 'p1'. """
    return priority_str_eq_filter(tasks, value="p1", *args, **kwargs)


def p2_filter(tasks, *args, **kwargs):
    """ Filter tasks including only tasks with priority 'p2'. """
    return priority_str_eq_filter(tasks, value="p2", *args, **kwargs)


def p3_filter(tasks, *args, **kwargs):
    """ Filter tasks including only tasks with priority 'p3'. """
    return priority_str_eq_filter(tasks, value="p3", *args, **kwargs)


def p4_filter(tasks, *args, **kwargs):
    """ Filter tasks including only tasks with priority 'p3'. """
    return priority_str_eq_filter(tasks, value="p4", *args, **kwargs)


def reschedule_tasks(tasks, new_date, *, verbose=0):
    """ Reschedule tasks to a new date/time.

    Args:
        tasks: List of tasks.
        new_date: The new due_date string to send.
        verbose: Adjust the verbosity to increase or decrease the amount of information
            printed during function run.

    Returns:
        List of tasks.

    This command treats recurring and non-recurring tasks differently:

        * Regular, non-recurring tasks are rescheduled by updating due.string = new_date.
        * Recurring tasks are rescheduled by updating due.date = rfc3339(new_date),
            but keeping due.string as-is, so that the recurrence schedule won't change.

    If you would like to force one specific behavior, regardless of whether the task
    is recurring or not, please use one of the following functions:

        reschedule_tasks_due_date()  - this will always update due.date.
        reschedule_tasks_by_due_string() - this will always update due.string.

    If you would like to reschedule to a due date with a *fixed timezone*, please use:

        reschedule_tasks_fixed_timezone() - this will update due.date and due.timezone.

    Example: Reschedule tasks for tomorrow:

        >>> reschedule_tasks(tasks, 'tomorrow')

    CLI Example: Reschedule overdue tasks for tomorrow

        $ todoist-action-cli -sync -due before today -reschedule tomorrow

    API refs:
    * https://developer.todoist.com/sync/v8/#create-or-update-due-dates

    """
    if verbose > -1:
        print("\n - Rescheduling %s tasks for %r..." % (len(tasks), new_date), file=sys.stderr)

    date_rfc3339 = get_rfc3339_datestr(new_date)
    for task in tasks:
        if is_recurring(task):
            # Adjust "due.date", but keep "due.string" as-is:
            # OBS: It is probably still better to just use `-close` for repeating tasks:
            params = dict(due={
                "date": date_rfc3339,
                "string": get_task_value(task, 'due_string_safe'),
                "is_recurring": True,
            })
            task.update(**params)
            if verbose > 0:
                print(f" - Rescheduling task {task['content']} ({get_task_value(task, 'due_string_safe')}) "
                      f"with params: {params} ",
                      file=sys.stderr)
        else:
            # Adjust due.string, let server parse it:
            task.update(due={"string": new_date})
            if verbose > 0:
                print(f" - Rescheduling task {task['content']} for due.string={new_date}", file=sys.stderr)

    if verbose > -1:
        print("\n --> OBS: Remember to use `-commit` to push the changes (not `-sync`)! <--\n\n", file=sys.stderr)

    return tasks


def reschedule_tasks_due_date(tasks: list, due_date: str, *, verbose=0):
    """ Reschedule a recurring task by updating due.date but leaving due.string as-is. """
    date_rfc3339 = get_rfc3339_datestr(due_date)
    if verbose > -1:
        print(f"\n - Rescheduling {len(tasks)} tasks for '{due_date}' ({date_rfc3339}) ...",
              file=sys.stderr)
        print(" - Remember to use `-commit` to push the changes (not `-sync`)!\n\n", file=sys.stderr)
    for task in tasks:
        task.update(due={"date": date_rfc3339})
        # OBS: Other task date fields aren't updated until you've committed the changes!
    return tasks


def reschedule_tasks_by_due_string(tasks: list, due_string: str, *, check_recurring=True, verbose: int = 0):
    """ Reschedule tasks using due.string, letting the server parse the string. """
    if verbose > -1:
        print(f"\n - Rescheduling {len(tasks)} tasks for '{due_string}' ...", file=sys.stderr)
        print(" - Remember to use `-commit` to push the changes (not `-sync`)!\n\n", file=sys.stderr)
    if check_recurring is True:
        recurring_tasks = get_recurring_tasks(tasks)
        if len(recurring_tasks) > 0:
            print("\nWARNING: One or more of the tasks being rescheduled is currently a recurring task:")
            print_tasks(recurring_tasks)
            print("\n")
    for task in tasks:
        task.update(due={"string": due_string})
        # OBS: Other task date fields aren't updated until you've committed the changes!
    return tasks


def reschedule_tasks_fixed_timezone(tasks: list, due_string: str, timezone: str, *, verbose: int = 0):
    """ Reschedule tasks using due.date with fixed timezone.
    Again, the easiest solution is to just let the Todoist server parse the user input string.
    """
    if verbose > -1:
        print(f"\n - Rescheduling {len(tasks)} tasks for '{due_string}' "
              f"with fixed timezone '{timezone}' ...", file=sys.stderr)
        print(" - Remember to use `-commit` to push the changes (not `-sync`)!\n\n", file=sys.stderr)
    for task in tasks:
        task.update(due={"string": due_string, "timezone": timezone})
        # OBS: Other task date fields aren't updated until you've committed the changes!
    return tasks


def update_tasks(tasks, *, verbose=0, **kwargs):
    """ Generic task updater. (NOT FUNCTIONAL)

    """
    if verbose > -1:
        print("Updating tasks using kwargs:", kwargs, file=sys.stderr)
    for task in tasks:
        task.update(**kwargs)
    return tasks


def rename_tasks(tasks, new_content, *, verbose=0):
    """ Rename selected tasks, using API method 'item_update'. """
    if verbose > -1:
        print(f'\n - Renaming {len(tasks)} selected task(s) to "{new_content}" ...')
    for task in tasks:
        if verbose > -1:
            print(f' - Renaming task: "{task.data["content"]}" --> "{new_content}"')
        task.update(content=new_content)
    return tasks


def mark_tasks_completed(tasks, method='close', *, verbose=0):
    """ Mark tasks as completed using method='close'.

    Note: The Todoist v7 Sync API has two command types for completing tasks:
        'item_complete' - used by ?
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
        verbose: Increase or decrease the verbosity of the information printed during function run.

    Returns:
        tasks:  List of tasks (after closing them).

    See also:
        'item_uncomplete' - Mark task as uncomplete (re-open it).

    """
    if verbose > 0:
        print(f"\nMarking tasks as complete using method {method!r}...", file=sys.stderr)
        if method in ('close', 'item_close'):
            print(f"\nOBS: Consider using `-close` command directly instead ...", file=sys.stderr)
        print(" --> Remember to `-commit` the changes to the server! <--", file=sys.stderr)

    for task in tasks:
        if method in ('close', 'item_close'):
            task.close()
        elif method in ('complete', 'item_complete'):
            task.complete()
        elif method in ('item_update_date_complete', 'complete_recurring'):
            raise NotImplementedError(
                f"Using method {method!r} is not implemented. "
                f"If using the CLI, please use the `-close` action instead. "
                f"If calling from Python, please use either close_tasks() function, or "
                f"`task.update_date_complete()`. ")
        else:
            raise ValueError(f"Value for method = {method!r} not recognized!")
    return tasks


def close_tasks(tasks, *, verbose=0):
    """ Mark tasks as completed using method='close'.

    See mark_tasks_completed for more info on the different API methods to "complete" a task.

    See: https://developer.todoist.com/sync/v8/#close-item

    Args:
        tasks:  List of tasks.
        verbose: Increase or decrease the verbosity of the information printed during function run.

    Returns:
        tasks:  List of tasks (after closing them).

    See also:
        'item_uncomplete' - Mark task as uncomplete (re-open it).

    """
    if verbose > -1:
        print(f"\nClosing tasks (using API method 'item_close') ...", file=sys.stderr)
        print("\n --> Remember to `-commit` the changes to the server! <--", file=sys.stderr)
    for task in tasks:
        task.close()
    return tasks


def complete_and_update_date_for_recurring_tasks(tasks, new_date=None, due_string=None, *, verbose=0):
    """ Mark tasks as completed using method='item_update_date_complete'.

    See mark_tasks_completed for more info on the different API methods to "complete" a task.

    See: https://developer.todoist.com/sync/v8/#close-item

    Args:
        tasks:  List of tasks.
        new_date: The new/next due/occurrence date for the recurring task,
            e.g. `new_date="2019-09-
        due_string: Change the "due string" that specifies when the task occurs,
            e.g. `due_string="every monday 5 pm"`.
        verbose: Increase or decrease the verbosity of the information printed during function run.

    Returns:
        tasks:  List of tasks (after completing/updating them).

    See also:
        'item_update_date_complete' - Mark task as uncomplete (re-open it).

    """
    if verbose > 0:
        print(f"\nCompleting recurring tasks and moving the due date to {new_date if new_date else 'next occurrence'} "
              f"(using API method 'item_update_date_complete') ...", file=sys.stderr)
        print("\n --> Remember to `-commit` the changes to the server! <--", file=sys.stderr)
    print("NOTICE: todoist.models.Item.update_date_complete() is currently broken in "
          "todoist-python package version 8.0.0.")
    for task in tasks:
        task.update_date_complete(new_date, due_string)
    return tasks


def uncomplete_tasks(tasks, *, verbose=0):
    """ Re-open tasks (uncomplete tasks) using API method 'item_uncomplete'.

    See: https://developer.todoist.com/sync/v8/#uncomplete-item

    Args:
        tasks:  List of tasks.
        verbose: Increase or decrease the verbosity of the information printed during function run.

    Returns:
        tasks:  List of tasks (after reopening them).

    """
    if verbose > 0:
        print(f"\nRe-opening tasks (using API method 'item_uncomplete') ...", file=sys.stderr)
        print("\n --> Remember to `-commit` the changes to the server! <--", file=sys.stderr)
    for task in tasks:
        task.uncomplete()
    return tasks


def archive_tasks(tasks, *, verbose=0):
    """ Archive tasks using API method 'item_archive'.

    See: https://developer.todoist.com/sync/v8/?shell#archive-item

    Args:
        tasks:  List of tasks.
        verbose: Increase or decrease the verbosity of the information printed during function run.

    Returns:
        tasks:  List of tasks (after archiving them).

    """
    if verbose > 0:
        print(f"\nArchiving tasks (using API method 'item_archive') ...", file=sys.stderr)
        print("\n --> Remember to `-commit` the changes to the server! <--", file=sys.stderr)
    for task in tasks:
        task.archive()
    return tasks


def delete_tasks(tasks, *, verbose=0):
    """ Delete tasks using API method 'item_delete'.

    See: https://developer.todoist.com/sync/v8/?shell#delete-item

    Args:
        tasks:  List of tasks.
        verbose: Increase or decrease the verbosity of the information printed during function run.

    Returns:
        tasks:  List of tasks (after deleting them).

    """
    if verbose > 0:
        print(f"\nArchiving tasks (using API method 'item_delete') ...", file=sys.stderr)
        print("\n --> Remember to `-commit` the changes to the server! <--", file=sys.stderr)
    for task in tasks:
        task.delete()
    return tasks


def add_task(tasks, api, task_content, *, project=None, due=None, priority=None, labels=None,
             auto_reminder=True, auto_parse_labels=True, verbose=0):
    """ Add a new task API method 'item_add'.

    See: https://developer.todoist.com/sync/v8/?shell#add-an-item

    Args:
        tasks:  List of tasks.
        api: tooist.api.TodoistAPI object (so we can get projects, labels, etc.)
        due: Due date (str)
        project: Project name (str)
        labels: List of task labels (names)
        priority: Task priority, either number [1-4] or str ["p4", "p3", 'p2", "p1"].
        auto_reminder: Automatically add a default reminder to the task, if task is due at a specific time of day.
        auto_parse_labels: Automatically extract "@label" strings from the task content.
        verbose: Increase or decrease the verbosity of the information printed during function run.

    Returns:
        tasks:  List of tasks (after deleting them).

    """
    if verbose > -1:
        print(f"\nAdding new task (using API method 'item_add') ...", file=sys.stderr)
        print("\n --> Remember to `-commit` the changes to the server! <--", file=sys.stderr)

    params = {'auto_reminder': auto_reminder, 'auto_parse_labels': auto_parse_labels}

    if due:
        params['due'] = {"string": due}

    if project:
        if isinstance(project, str):
            # Assume project-name:
            # We need to find project_id from project_name:
            # If projects is e.g. a list of projects, create a dict mapping project_id to project:
            project_name = project
            # projects_by_name = {p['name']: p for p in api.projects.all()}
            # project_id = projects_by_name[project]['id']
            project_id = next(iter(p['id'] for p in api.projects.all() if p['name'] == project_name))
        else:
            # Project should be a project_id:
            assert isinstance(project, int)
            project_id = project
        params['project_id'] = project_id

    if labels:
        if isinstance(labels, str):
            labels = [label.strip() for label in labels.split(",")]
        if any(isinstance(label, str) for label in labels):
            # Assume label-name: We need to find label_id from label_name:
            labels_by_name = {label['name']: label for label in api.labels.all()}
            labels = [label if isinstance(label, int) else labels_by_name[label]['id'] for label in labels]
        params['labels'] = labels

    if priority:
        if isinstance(priority, str):
            # Priority in the form of "p1" to "p4".
            priority_str = priority
            priority_str_map = dict(p1=4, p2=3, p3=2, p4=1)
            try:
                priority = priority_str_map[priority]
            except KeyError:
                raise ValueError("Argument `priority` must be one of 'p1', 'p2', 'p3', or 'p4' (if str).")
        else:
            # Integer between 1 and 4:
            if not isinstance(priority, int):
                raise TypeError("Argument `priority` must be str or int.")
            if priority < 1 or 4 < priority:
                raise ValueError("Argument `priority` must be between 1 and 4 (if int).")
        params['priority'] = priority

    new_task = api.items.add(task_content, **params)
    # tasks.append(new_task)  # This should not be needed, because api.items.add() updates the `tasks` list.

    return tasks


def fetch_completed_tasks(tasks, *, verbose=0):
    """ This will replace `tasks` with a list of completed tasks dicts. May not work nicely. Only for playing around.

    You should probably use the old CLI instead:
        $ todoist print-completed-today --print-fmt "* {title}"
    """
    if verbose > -1:
        print(f"Discarting the current {len(tasks)} tasks, and fetching completed tasks instead...")
    from actionista.todoist.adhoc_cli import completed_get_all
    # This will use a different `api` object instance to fetch completed tasks:
    tasks, projects = completed_get_all()
    inject_tasks_project_fields(tasks, projects)
    return tasks


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
    # Label filter:
    'label': label_filter,  # Alias for `-filter label_names icontains <value>`
    # Priority filter (where priority=4 is higher than priority=1)
    'priority': priority_filter,
    'priority-eq': priority_eq_filter,
    'priority-ge': priority_ge_filter,
    'priority-str': priority_str_filter,
    'priority-str-eq': priority_str_eq_filter,
    # priority_str filters (where "p1" has higher priority than "p4")
    'p1': p1_filter,
    'p2': p2_filter,
    'p3': p3_filter,
    'p4': p4_filter,
    # Reschedule task actions:
    'reschedule': reschedule_tasks,
    'reschedule-due-date': reschedule_tasks_due_date,
    'reschedule-by-string': reschedule_tasks_by_due_string,
    'reschedule-fixed-timezone': reschedule_tasks_fixed_timezone,
    # Rename task:
    'rename': rename_tasks,
    # Complete task actions:
    'mark-completed': mark_tasks_completed,
    # 'mark-as-done': mark_tasks_completed,  # Deprecated.
    'close': close_tasks,
    'reopen': uncomplete_tasks,  # alias for uncomplete
    'uncomplete': uncomplete_tasks,
    'archive': archive_tasks,
    'complete_and_update': complete_and_update_date_for_recurring_tasks,
    # 'fetch-completed': fetch_completed_tasks,  # WARNING: Not sure how this works, but probably doesn't work well.
    # The following actions are overwritten when the api object is created inside the action_cli() function:
    'verbose': None, 'v': None,  # Increase verbosity.
    'delete-cache': None,  # Delete local cache files.
    'sync': None,  # Pulls updates from the server, but does not push changes to the server.
    'commit': None,  # Push changes to the server.
    'show-queue': None,  # Show the command queue, that will be pushed to the server on `commit`.
}

# These are actions that requires the full `api` object to work,
# e.g. because they need to convert a project-name to project-id.
API_ACTIONS = {
    "add-task": add_task,
}
