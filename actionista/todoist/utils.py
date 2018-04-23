# Copyright 2017–2018 Rasmus Scholer Sorensen


import os
import yaml
import todoist
# date/time packages:
# import pytz
# import pendulum
# import arrow
# import maya  # Kenneth's "Date and time for Humans" package.
# import moment
# import zulu

CONFIG_PATHS = [
    "~/.todoist_config.yaml"
]

TOKEN_PATHS = [
    "~/.todoist_token.txt"
]


def get_config():
    fn_cands = map(os.path.expanduser, CONFIG_PATHS)
    try:
        config_fn = next(cand for cand in fn_cands if os.path.isfile(cand))
    except StopIteration:
        return None
    with open(config_fn) as fp:
        config = yaml.load(fp)
    return config


def get_token(raise_if_missing=True, config=None):
    """ Get Todoist login token.

    Will search standard token file locations (`TOKEN_PATHS`), and if no token files are found,
    will load config and return `config['token']`.

    Returns:
        str token, or None if no token was found.

    How to obtain and install your Todoist API token:
        1. Log into your todoist.com account, go to Settings → Integrations → Copy the API token.
        2. Place the token string either in a single file in one of the paths listed in `TOKEN_PATHS`,
            or put the token in the configuration file keyed under 'token'.

    """
    token = None
    config = get_config()
    if config is not None:
        token = config.get('token')
    if token:
        return token
    fn_cands = map(os.path.expanduser, TOKEN_PATHS)
    try:
        fn = next(cand for cand in fn_cands if os.path.isfile(cand))
    except StopIteration:
        pass
    else:
        with open(fn) as fp:
            token = fp.read().strip()
    if not token and raise_if_missing:
        raise ValueError(
            "Unable to find token. Please place Todoist API token either in config file (`~/.todoist_config.yaml`)"
            "or separate `~/.todoist_token.txt` file."
        )
    return token


def get_todoist_api(token=None):
    """ Returns Todoist API object with token read from file or config. """
    if token is None:
        token = get_token()
    api = todoist.TodoistAPI(token=token)
    return api

