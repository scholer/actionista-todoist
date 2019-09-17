# Copyright 2019, Rasmus Sorensen <rasmusscholer@gmail.com>
"""


"""
import sys
from pprint import pformat

from actionista.todoist.tasks_utils import get_proper_priority_int
from actionista.todoist.utils import get_todoist_api


def add_task(
        content, due=None, project=None, labels=None, priority=None, note=None,
        auto_reminder=None, auto_parse_labels=None, *,
        sync=True, commit=True, show_queue=False, verbose=0,
        api=None,
):
    """ Add a single task to Todoist.

    Args:
        content: The task content (task name).
        due: Due date (str)
        project: Project name (str)
        labels: List of task labels (names)
        priority: Task priority, either number [1-4] or str ["p4", "p3", 'p2", "p1"].
        note: Add a single note to the task.
        auto_reminder: Automatically add a default reminder to the task, if task is due at a specific time of day.
        auto_parse_labels: Automatically extract "@label" strings from the task content.
        sync: Start by synching the Sync API cache (recommended, unless testing).
        commit: End by committing the added task to the Todoist server (recommended, unless testing).
        show_queue: Show API queue before submitting the changes to the server.
        verbose: Be extra verbose when printing information during function run.
        api: Use this TodoistAPI object for the operation.

    Returns:
        The newly added task (todoist.models.Item object).

    """
    if api is None:
        api = get_todoist_api()
    if sync:
        api.sync()
    if verbose >= 0:
        print(f"\nAdding new task:", file=sys.stderr)
        print(f" - content:", content, file=sys.stderr)
        print(f" - project:", project, file=sys.stderr)
        print(f" - labels:", list(labels) if labels else None, file=sys.stderr)
        print(f" - priority:", priority, file=sys.stderr)
        print(f" - due:", due, file=sys.stderr)
        print(f" - note:", note, file=sys.stderr)

    params = {}

    if due:
        params['due'] = {"string": due}

    if project:
        if isinstance(project, str):
            # We need to find project_id from project_name:
            project_name = project
            try:
                project_id = next(iter(p['id'] for p in api.projects.all() if p['name'].lower() == project_name.lower()))
            except StopIteration:
                msg = f'Project name "{project_name}" was not recognized. Please create project first. '
                print(f"\n\nERROR: {msg}\n")
                print("(You can use `todoist-cli print-projects` to see a list of available projects.)\n")
                raise ValueError(msg) from None  # raise from None to not show the StopIteration exception.
        else:
            # Project should be a project_id:
            assert isinstance(project, int)
            project_id = project
        params['project_id'] = project_id

    if labels:
        if isinstance(labels, str):
            labels = [label.strip() for label in labels.split(",")]
        if any(isinstance(label, str) for label in labels):
            # Assume label-name: We need to find label_id from label_name (lower-cased):
            labels_by_name = {label['name'].lower(): label for label in api.labels.all()}
            labels = [label if isinstance(label, int) else labels_by_name[label.lower()]['id'] for label in labels]
        params['labels'] = labels

    if priority is not None:
        params['priority'] = get_proper_priority_int(priority)

    if auto_reminder is not None:
        assert isinstance(auto_reminder, bool)
        params['auto_reminder'] = auto_reminder
    if auto_parse_labels is not None:
        assert isinstance(auto_parse_labels, bool)
        params['auto_parse_labels'] = auto_parse_labels

    # Add/create new task:
    new_task = api.items.add(content, **params)

    if verbose >= 1:
        print(f"\nNew task added:", file=sys.stderr)
        print(pformat(new_task.data), file=sys.stderr)

    if note:
        # Using a temporary ID is OK.
        new_note = api.notes.add(new_task["id"], note)
        if verbose >= 1:
            print(f"\nNew note added:", file=sys.stderr)
            print(pformat(new_note.data), file=sys.stderr)

    if show_queue:
        def get_obj_data(obj):
            return obj.data
        print("\n\nAPI QUEUE:\n----------\n")
        import json
        # This is actually the best, since it can use `default=get_obj_data` to represent model objects.
        print(json.dumps(api.queue, indent=2, default=get_obj_data))

    if commit:
        if verbose >= 0:
            print(f"\nSubmitting new task to server...", file=sys.stderr)
        api.commit()
        if verbose >= 0:
            print(f" - OK!", file=sys.stderr)
    else:
        if verbose >= 0:
            print(f"\nNew task created - but not committed to server! (because `commit=False`)", file=sys.stderr)

    return new_task
