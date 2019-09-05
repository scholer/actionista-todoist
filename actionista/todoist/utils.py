# Copyright 2017–2018 Rasmus Scholer Sorensen

import sys
import todoist
# date/time packages:
# import pytz
# import pendulum
# import arrow
# import maya  # Kenneth's "Date and time for Humans" package.
# import moment
# import zulu
from actionista.todoist.config import get_token


def get_todoist_api(token=None):
    """ Returns Todoist API object with token read from file or config. """
    if token is None:
        token = get_token()
    api = todoist.TodoistAPI(token=token)
    return api


def sync_and_check(api, raise_on_error=True):
    """ Sync api with servers and check that the response is good. """
    res = api.sync()  # returns a dict of parsed json data
    if 'error' in res:
        msg = f"API sync error: {res['error']} (code: {res['error_code']}, tag: {res['error_tag']}, http: {res['http_code']})"
        if raise_on_error:
            raise todoist.api.SyncError(msg)
        else:
            print(f"\n{msg}\n", file=sys.stderr)
            return False
    return res

