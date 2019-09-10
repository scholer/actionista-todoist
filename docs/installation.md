
INSTALLATION
-------------


### Installation with ``pipx``

For regular end-users, I recommend using ``pipx`` to install the Actionista-Todoist command line apps:

	$ pipx install actionista-todoist

If you don't have pipx installed, you can refer to the
[pipx installation guide](https://pipxproject.github.io/pipx/installation/).
Briefly:

	$ pip install pipx
	$ pipx ensurepath

The last step will add `~/.local/bin` to the PATH environment variable.
Please make sure to close and restart your terminal/command prompt after
installing pipx for the first time.


Known installation errors:

* If you are using ``conda``, there is a known issue where you receive an error,
  "Error: [Errno 2] No such file or directory:", when trying to install packages with ``pipx``.
  If you get this error, please update your ``conda`` python and make sure you are only using
  the "defaults" channel, *not* "conda-forge".


### Installation with ``pip``

To install distribution release package from the Python Packaging Index (PyPI):

    $ pip install -U actionista-todoist


Alternatively, install the latest git master source by fetching the git repository from github
and install the package in editable mode (development mode):

    $ git clone git@github.com:scholer/actionista-todoist && cd actionista-todoist
    $ pip install -U -e .



CONFIGURATION
--------------

Once ``actionista-todoist`` package is installed, you need to obtain a login token from the todoist website:
Log into your todoist.com account, go to ``Settings -> Integrations``, and copy the API token.
(You can also go directly to the page: https://todoist.com/prefs/integrations).

Now run:

	$ actionista-todoist-config --interactive

to set up the login token with your Actionista-Todoist installation.
The API token is stored in ``~/.todoist_token.txt``.
The ``actionista-todoist-config`` command will also create a default config file,
``~/.todoist_config.yaml``, which you can edit to change default sorting and printing format.

You can update your Todoist API token either by running:

	$ actionista-todoist-config --token <your-token-here> --check-token

or by manually editing the file ``~/.todoist_token.txt`` and place your token in here.

