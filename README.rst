

INSTALLATION:
-------------

To install git repository in editable mode (development mode)::

    $ pip install -U -e .


Otherwise::

    $ pip install -U rstodo



USAGE:
------

Installing this project (``rstodo``) with ``pip`` will give you some readily
available command line interface entry points::

    $ todoist <command> <args>
    $ todoist print-query <query> [<print-fmt>]
    $ todoist print-completed-today [<print-fmt>]
    $ todoist print-today-or-overdue-items [<print-fmt>]

    # And a couple of endpoints with convenient defaults:
    $ todoist_today_or_overdue

