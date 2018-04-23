# Copyright 2018 Rasmus Scholer Sorensen

"""

The main Todoist v7 "Sync" API has become rather complex.
That is probably required for "full-featured" applications,
but for small command-line scripts, the API is a bit overkill.

Doist is therefore (as of primo 2018) introducing a new, simple, v8 REST API,
which can be used for those simple use-cases.


This module features classes and functions to utilize the Todoist v8 REST API.

"""

import requests

from actionista.todoist.utils import get_token


class TodoistRestApi:
    """ A simple class for interacting with the Todoist REST API, currently at https://beta.todoist.com/API/v8/. """

    API_BASE_URL = "https://beta.todoist.com/API/v8/"  # Update URL when the API comes out of beta.

    def __init__(self, token=None):
        self._token = None
        if token is None:
            token = get_token()
        self.update_token(token)
        self.session = requests.Session()

    def update_token(self, token):
        self._token = token
        self.session.headers.update({
            "Authorization": "Bearer %s" % token})

    def get(self, endpoint, **kwargs):
        endpoint_url = self.API_BASE_URL + endpoint
        res = self.session.get(url=endpoint_url, **kwargs)
        res.raise_for_status()
        return res.json()

    def post(self, endpoint, **kwargs):
        endpoint_url = self.API_BASE_URL + endpoint
        res = self.session.post(url=endpoint_url, **kwargs)
        res.raise_for_status()
        return res.json()

    def get_tasks(self, project_id=None, label_id=None, filter=None):
        kwargs = dict(project_id=project_id, label_id=label_id, filter=filter)
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        return self.get(endpoint='tasks', **kwargs)
