# Copyright 2018 Rasmus Scholer Sorensen

"""

The main Todoist v7 "Sync" API has become rather complex.
That is probably required for "full-featured" applications,
but for small command-line scripts, the Sync API is a bit overkill.

Doist is therefore (as of primo 2018) introducing a new, simple, REST API,
which can be used for those simple use-cases.


This module features classes and functions to utilize the Todoist REST API.

Update: The REST API is out.

* It is based on the v8 Sync API specs (e.g. separate `due` property), but is called "REST v1".
* Although creating a new Task Item actually specifies passing `due_string` and `due_lang` values.
    * https://developer.todoist.com/rest/v1/?python#create-a-new-task
* https://developer.todoist.com/rest/v1/?python

"""

import requests

from actionista.todoist.config import get_token


class TodoistRestApi:
    """ A simple class for interacting with the Todoist REST API, currently at https://beta.todoist.com/API/v8/. """

    API_BASE_URL = "https://api.todoist.com/rest/v1/"


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

    def delete(self, endpoint, **kwargs):
        endpoint_url = self.API_BASE_URL + endpoint
        res = self.session.delete(url=endpoint_url, **kwargs)
        res.raise_for_status()
        return res.json()

    def get_tasks(self, project_id=None, label_id=None, filter=None):
        kwargs = dict(project_id=project_id, label_id=label_id, filter=filter)
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        return self.get(endpoint='tasks', **kwargs)

    def close_task(self, task_id: int):
        assert isinstance(task_id, int)
        endpoint = f"tasks/{task_id}/close"
        res = self.post(endpoint=endpoint)
        print(f"Closed task {task_id}; response: {res}  (should be 204).")
        return res

    def delete_task(self, task_id: int):
        assert isinstance(task_id, int)
        endpoint = f"tasks/{task_id}"
        res = self.delete(endpoint=endpoint)
        print(f"Deleted task {task_id}; response: {res}  (should be 204).")
        return res

    def get_task_comments(self, task_id: int):
        assert isinstance(task_id, int)
        endpoint = f"comments/"
        params = {"task_id": task_id}
        return self.get(endpoint=endpoint, params=params)

