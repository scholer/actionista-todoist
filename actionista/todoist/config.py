# Copyright 2019, Rasmus Sorensen <rasmusscholer@gmail.com>
"""

Configuration module for Actionista for Todoist package and CLIs/apps.




"""
import os
import yaml


# You can use the "precision" notation to truncate long strings during
# string formatting, e.g. "{field:minwidth.maxwidth}"
DEFAULT_TASK_PRINT_FMT = (
    "{project_name:15.15} "
    # "{due_date_safe_dt:%Y-%m-%d %H:%M}  "
    # "{due_date_safe:^14}  "
    "{due_date_pretty_safe:16} "  # Omits time for all-day due dates.
    "{priority_str} "
    "{checked_str} "
    "{content:.79} "
    "(due {due_string_safe}) " 
    " {labels_str}"
)
# Alternative print_fmt examples:
# print_fmt="{project_name:15} {due_date_safe_dt:%Y-%m-%d %H:%M  } {content}",
# print_fmt="{project_name:15} {due_date_safe_dt:%Y-%m-%d %H:%M}  {checked_str} {content}",
# print_fmt="{project_name:15} {due_date_safe_dt:%Y-%m-%d %H:%M}  {priority_str} {checked_str} {content}",
DEFAULT_TASK_SORT_KEYS = "project_name,priority_str,content".split(",")
DEFAULT_TASK_SORT_ORDER = "ascending"
DEFAULT_PROJECT_PRINT_FMT = "{name}"
DEFAULT_PROJECT_SORT_KEYS = "name".split(",")
DEFAULT_PROJECT_SORT_ORDER = "ascending"
DEFAULT_CONFIG = {
    'default_task_print_fmt': DEFAULT_TASK_PRINT_FMT,
    'default_task_sort_keys': DEFAULT_TASK_SORT_KEYS,
    'default_task_sort_order': DEFAULT_TASK_SORT_ORDER,
    'default_project_print_fmt': DEFAULT_PROJECT_PRINT_FMT,
    'default_project_sort_keys': DEFAULT_PROJECT_SORT_KEYS,
    'default_project_sort_order': DEFAULT_PROJECT_SORT_ORDER,
}
CONFIG_PATHS = [
    "~/.todoist_config.yaml"
]
TOKEN_PATHS = [
    "~/.todoist_token.txt"
]
FILEPATHS = {
    'config': CONFIG_PATHS,
    'token': TOKEN_PATHS
}


def get_config_file(name='config'):
    fn_cands = FILEPATHS[name]
    fn_cands = map(os.path.expanduser, fn_cands)
    try:
        return next(cand for cand in fn_cands if os.path.isfile(cand))
    except StopIteration:
        return None


def get_config(config_fn=None):
    if config_fn is None:
        config_fn = get_config_file()
    if config_fn is None:
        return
    with open(config_fn) as fp:
        config = yaml.safe_load(fp)
    return config


def get_config_and_filepath():
    config_fn = get_config_file()
    if config_fn is None:
        return None, None
    with open(config_fn) as fp:
        config = yaml.safe_load(fp)
    return config, config_fn


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


def store_token(new_token=None):
    """ Store a new token in the config or separate token file. """
    config, config_fn = get_config_and_filepath()
    if config and config.get('token'):
        if 'token' in config:
            print("\n - Using login token from config file:", config_fn)
        current_token = config['token']
        print(f"\n- Current token is: {current_token}")
        if new_token is None:
            new_token = input("Please enter new token (or blank to abort):")
            if not new_token:
                return current_token
        print("\n - Updating config with new token:", new_token)
        config['token'] = new_token
        with open(config_fn, 'w') as fp:
            yaml.safe_dump(config, fp)
        print(" - OK, config saved with new login token.")
        return new_token
    token_file = get_config_file(name='token') or TOKEN_PATHS[0]
    print("\n - Using login token file:", token_file)
    try:
        with open(token_file) as fp:
            current_token = fp.read().strip()
    except IOError:
        current_token = None
    print(f"\n - Current token is: {current_token}")
    if new_token is None:
        new_token = input("\nPlease enter new token (enter blank or 'Ctrl+C' to abort):  ")
        if not new_token:
            return current_token
    print(f"\n - Updating token file {token_file} with new token:", new_token)
    config['token'] = new_token
    with open(token_file, 'w') as fp:
        fp.write(new_token)
    print(" - OK, token file saved with new login token.")
    return new_token


def store_default_user_config(overwrite_existing=False):
    config_fn = get_config_file() or os.path.expanduser(CONFIG_PATHS[0])
    if os.path.exists(config_fn):
        print(f"\nConfig file already exists! ({config_fn})")
        if overwrite_existing is True:
            overwrite = True
        elif overwrite_existing is False:
            overwrite = False
        elif overwrite_existing is None:
            overwrite = (input("Do you want to overwrite the current config? [Y/n]").lower() or 'y')[0] == 'y'
        else:
            raise ValueError(f"Value '{overwrite_existing}' of argument 'overwrite_existing' not recognized. "
                             "Must be one of True/False/None.")
        if not overwrite:
            print(" - Skipping.")
            return
    print("\nWriting default config to file:", config_fn)
    with open(config_fn, 'w') as fp:
        yaml.safe_dump(DEFAULT_CONFIG, fp)
    print(" - OK, default config saved.")
    return DEFAULT_CONFIG
