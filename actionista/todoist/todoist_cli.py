# Copyright 2019, Rasmus Sorensen <rasmusscholer@gmail.com>
"""

Dedicated add-item CLI.

This is a newer version of the "Ad-hoc CLIs" found in `adhoc_cli.py`.

The CLIs found here are based on `click`, while `adhoc_cli` uses `argparse`.

"""

import sys
import click
from pprint import pprint

from actionista.todoist.api_commands import add_task
from .utils import get_todoist_api
from .config import get_config
from .config import DEFAULT_PROJECT_PRINT_FMT, DEFAULT_PROJECT_SORT_KEYS, DEFAULT_PROJECT_SORT_ORDER


@click.group("todoist-cli")
def todoist_cli():
    """ Actionista for Todoist CLI.

    Note: This is NOT the "Action Chain CLI", but a more traditional CLI, grouping
    the following CLI commands:

    See also: `todoist-adhoc` CLI command.
    """
    pass

# todoist_cli.add_command(add_task)  # Add manually (without decorator).

# Q: Can this be invoked directly when decorated with Group.command(), instead of click.command()?
# A: Yes, `add_task_cli` can still be invoked directly.
@todoist_cli.command("add-task")  # NOT click.command().
@click.argument("content")
@click.option("--due", metavar="DUE-DATE")
@click.option("--project", metavar="PROJECT-NAME")
@click.option("--label", "labels", multiple=True, metavar="LABEL")
@click.option("--priority", type=click.Choice(["p1", "p2", "p3", "p4"]))
@click.option("--note", metavar="NOTE")
@click.option("--auto-reminder/--no-auto-reminder", default=True)
@click.option("--auto-parse-labels/--no-auto-parse-labels", default=True)
@click.option("--sync/--no-sync", default=True)
@click.option("--commit/--no-commit", default=True)
@click.option("--show-queue/--no-show-queue", default=False)
@click.option("--verbose", "-v", count=True)
def add_task_cli(
        content, due=None, project=None, labels=None, priority=None, note=None,
        auto_reminder=None, auto_parse_labels=None,
        sync=True, commit=True, show_queue=False, verbose=0,
):
    """ Actionista for Todoist: Add-task CLI """
    return add_task(
        content, due=due, project=project, labels=labels, priority=priority, note=note,
        auto_reminder=auto_reminder, auto_parse_labels=auto_parse_labels,
        sync=sync, commit=commit, show_queue=show_queue,
        verbose=verbose,
    )


def add_tasks_cli(
        tasks_file, input_format=None, due=None, project=None, labels=None, priority=None
):
    """ Add multiple tasks from text or CSV/TSV file. """
    raise NotImplementedError("Add-tasks-CLI (for adding multiple tasks from csv/text file is not yet implemented.")


@todoist_cli.command("print-projects")  # NOT click.command().
@click.option("--print-fmt", metavar="PRINT-FORMAT")
@click.option("--sort-keys", metavar="KEYS-TO-SORT-ON")
@click.option("--sort-order", type=click.Choice(["ascending", "descending", "reversed"]))
@click.option("--sync/--no-sync", default=True)
@click.option("--verbose", "-v", count=True)
def print_projects_cli(print_fmt=None, sort_keys=None, sort_order=None, sep="\n", sync=True, verbose=0):
    """ Print projects. """
    config = get_config()
    if print_fmt is None:
        print_fmt = config.get("default_project_print_fmt", DEFAULT_PROJECT_PRINT_FMT)
    if sort_keys is None:
        sort_keys = config.get("default_project_sort_keys", DEFAULT_PROJECT_SORT_KEYS)
    if sort_order is None:
        sort_order = config.get("default_project_sort_order", DEFAULT_PROJECT_SORT_ORDER)
    if isinstance(sort_keys, str):
        sort_keys = [k.strip() for k in sort_keys.split(",")]

    api = get_todoist_api()
    if sync:
        if verbose:
            print("\nSyncing data with server...", file=sys.stderr)
        api.sync()

    projects = api.projects.all()  # Returns a list copy of api.state['projects']

    if sort_keys:
        from operator import itemgetter
        keyfunc = itemgetter(*sort_keys)
        projects = sorted(projects, key=keyfunc, reverse=(sort_order!="ascending"))

    if print_fmt == "pprint":
        pprint(projects)
    elif print_fmt == "pprint-data":
        pprint([project.data for project in projects])  # Convert to list of dicts which prints better.
    else:
        for project in projects:
            fmt_kwargs = getattr(project, 'data', project)
            fmt_kwargs.setdefault('project_name', fmt_kwargs.get('name'))
            print(print_fmt.format(**fmt_kwargs), end=sep)


if __name__ == '__main__':
    # todoist_cli()  # `todoist-cli` entry point
    # add_task_cli()  # `todoist-add-task` entry point.
    print_projects_cli()  # `todoist-cli print-projects`
