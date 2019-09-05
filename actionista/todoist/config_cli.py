# Copyright 2019, Rasmus Sorensen <rasmusscholer@gmail.com>
"""

`todoist-action-config`: Actionista for Todoist configuration CLI.


TODO: Add support for OAuth-based authorization and token retrieval.

"""

import sys
import click
import todoist

from .config import store_token, store_default_user_config, get_token
from .utils import sync_and_check

@click.command("Actionista for Todoist configuration CLI")
@click.option("--interactive/--no-interactive", default=None)
@click.option("--store-default-config/--no-store-default-config", default=None)
@click.option("--token")
@click.option("--check-token/--no-check-token", default=None)
def todoist_config_cli(interactive=None, token=None, store_default_config=None, check_token=None):
    """ Create or update Actionista for Todoist configuration files. """
    if interactive is None:
        interactive = (not token) and (not store_default_config)
    if token or interactive:
        if interactive:
            print("""\n
Setup is configuring your API login token. The API token is a small string of numbers and 
letters, and is used in place of a password for authenticating with the Todoist servers.

You can find your personal API token by selecting 'Settings' -> 'Integrations' from 
the Todoist web app, or going to: https://todoist.com/prefs/integrations
""")
        token = store_token(new_token=token)
        if check_token is None:
            check_token = (input("\nWould you like to verify that the token works? [Y/n]  ").lower() or 'y') == 'y'
        if check_token:
            print("\nVerifying API token...")
            if token != get_token():
                print("\nWARNING: The new token does not actually match the API token stored on disk!")
            api = todoist.TodoistAPI(token=token)
            print(" - Synching API...")
            try:
                res = sync_and_check(api, raise_on_error=True)
            except todoist.api.SyncError as exc:
                print(" - ERROR!")
                print(f"\n --> {exc}")
                print("\nPlease re-check the API token and re-run this configuration command.")
                sys.exit(1)
            else:
                print(" - Success - token OK!")
    if store_default_config or interactive:
        if interactive:
            print("""\n
Setup is now checking your default configuration file. The configuration file can be used 
to customize e.g. how tasks are sorted and printed by default.""")
        store_default_user_config()


if __name__ == '__main__':
    todoist_config_cli()
