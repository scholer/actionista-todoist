# Copyright 2019, Rasmus Sorensen <rasmusscholer@gmail.com>
"""


"""
import shlex
import sys


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

        >>> cmd = 'set1=val1 verbose auto-print verbose -add-task "Task 123" project=MyProject due=tomorrow priority=p1'
        >>> parse_argv(shlex.split(cmd))
        (
            ['verbose', 'auto-print', 'verbose'], {'set1': 'val1'},
            [
                ('filter', ('due_date_utc', 'contains', '2017-12-31'), {}),
                ('add-task', ('Task123',), {'project': 'MyProject', 'due': 'tomorrow', 'priority': 'p1'}),
            ]
        )


        # Print tasks due on New Year's Eve 2017 for the project named "Project1":
        >>> cmd = '-filter due_date_utc contains 2017-12-31 -filter project_name eq Project1 -print "{content}"'
        >>> parse_argv(shlex.split(cmd))
        (
            [], {},
            [
                ('filter', ('due_date_utc', 'contains', '2017-12-31')),
                ('filter', ('project_name', 'eq', 'Experiments')),
                ('print', ('{content}')),
            ]
        )

        # Print tasks starting with "RS123", mark them as complete, and sync the change to the server:
        >>> parse_argv(shlex.split('-filter content startswith RS123 -print "{content}" -mark-completed -sync'))
        (
            [], {},
            [
                ('filter', ('content', 'startswith', 'RS123')),
                ('print', ('{content}')),
                ('mark_tasks_completed', (,)),
                ('sync', (,)),
            ]
        )

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
