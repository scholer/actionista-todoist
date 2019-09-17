# from distutils.core import setup
from setuptools import setup, find_packages
import os

# Note: Make sure to use `pip -v` when pip-installing, so you can check what is being installed.

# Note: I like the "action-cli" approach so much that I am planning to use it for other "query-oriented" CLI projects.
# Thus, there will be a shared 'actionista-base' package that provides the basic "action-chain" functionalities,
# with specialized, domain-specific packages on top.

# Regarding shared namespace between multiple distribution packages (project distributions?):
# * Put `__import__('pkg_resources').declare_namespace(__name__)` in all `actionista.__init__.py` files.
# * Add `namespace_packages =["rewind"]` argument to `setuptools.setup(...)` invocation in `setup.py`.
# * c.f. https://stackoverflow.com/a/12508037/3241277
# * c.f. http://setuptools.readthedocs.io/en/latest/setuptools.html
# * c.f. https://packaging.python.org/guides/packaging-namespace-packages/
PROJECT_ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the README file

try:
    with open(os.path.join(PROJECT_ROOT_DIR, 'README.md'), encoding='utf-8') as f:
        long_description = f.read()
except IOError:
    long_description = """
Actionista Action CLI for Todoist (actionista-todoist). 

A `find`-inspired CLI for Todoist.

Add, select, print, reschedule, modify, and complete tasks in a batch-wise fashion
from the command line.

See `README.md` for usage.

"""


# Distribution build and release:
#   python setup.py sdist
#   python setup.py bdist_wheel
#   twine upload dist/*
setup(
    name='actionista-todoist',
    version='2019.9.16',  # remember to also update __init__.py
    packages=find_packages(),  # List all packages (directories) to include in the source dist.
    url='https://github.com/scholer/actionista-todoist',
    license='GNU General Public License v3 (GPLv3)',
    author='Rasmus Scholer Sorensen',
    author_email='rasmusscholer@gmail.com',
    description='Actionista Action CLI for Todoist. '
                'Add, select, print, reschedule, modify, and complete tasks in a batch-wise fashion '
                'from the command line.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords=['Todoist', 'Tasks', 'Productivity', 'TODO', 'GTD', 'CLI'],
    entry_points={
        'console_scripts': [
            # Action CLI entry points:
            'todoist-action-cli=actionista.todoist.action_cli:action_cli',
            'actionista-todoist=actionista.todoist.action_cli:action_cli',  # New alias

            # todoist config CLI entry points:
            'todoist-action-config=actionista.todoist.config_cli:todoist_config_cli',
            'actionista-todoist-config=actionista.todoist.config_cli:todoist_config_cli',  # Alias

            # todoist_cli entry points (click-based):
            'todoist-cli=actionista.todoist.todoist_cli:todoist_cli',
            'todoist-add-task=actionista.todoist.todoist_cli:add_task_cli',

            # Entry points for adhoc_cli commands (argparse-based):
            # 'todoist-adhoc=actionista.todoist.adhoc_cli:main',
            'todoist-adhoc-cli=actionista.todoist.adhoc_cli:main',
        ],
        # 'gui_scripts': [
        # ]
    },
    # pip will install these modules as requirements.
    install_requires=[
        'todoist-python>=8.0',  # Official Todoist python API from Doist
        'pyyaml',           # Config loading.
        'pytz',             # Timezone support.
        'python-dateutil',  # Parsing ISO timestamps.
        'dateparser',       # Required for human_date_to_iso()
        'parsedatetime',    # Has better concept of accuracy of parsed date/time than dateparser.
        'click',            # CLI package. (Only used for auxiliary CLI programs)
    ],
    python_requires='>=3.6',  # Type-hints, f-strings,
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: End Users/Desktop',
        # 'Intended Audience :: Science/Research',
        # 'Intended Audience :: Developers',
        # 'Intended Audience :: Education',
        # 'Intended Audience :: Healthcare Industry',

        # 'Topic :: Software Development :: Build Tools',
        # 'Topic :: Education',
        # 'Topic :: Scientific/Engineering',

        # Pick your license as you wish (should match 'license' above)
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',

        'Operating System :: MacOS',
        'Operating System :: Microsoft',
        'Operating System :: POSIX :: Linux',
    ],
)
