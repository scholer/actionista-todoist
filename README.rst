

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


TODOIST web APIs:
-----------------

See `todoist.py` module docstring.


TODOIST SYNC API v7 notes:
--------------------------


## Activity log ('activity/get') vs Completed ('completed/get_all')

Example activity log event::

    {
      "id" : 955333384,
      "object_type" : "item",
      "object_id" : 101157918,
      "event_type" : "added",
      "event_date" : "Fri 01 Jul 2016 14:24:59 +0000",
      "parent_project_id" : 174361513,
      "parent_item_id" : null,
      "initiator_id" : null,
      "extra_data" : {
        "content" : "Task1",
        "client" : "Mozilla/5.0; Todoist/830"
      }
    }


Example completed/get_all response::

    {
      "items": [
        { "content": "Item11",
          "meta_data": null,
          "user_id": 1855589,
          "task_id": 33511505,
          "note_count": 0,
          "project_id": 128501470,
          "completed_date": "Tue 17 Feb 2015 15:40:41 +0000",
          "id": 33511505
        }
      ],
      "projects": {
        # All projects with items listed above.
      }
    }



