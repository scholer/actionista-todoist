from distutils.core import setup


setup(
    name='rstodo',
    version='0.0.3',
    packages=['rstodo'],  # List all packages (directories) to include in the source dist.
    url='github.com/scholer/rstodo',
    license='GPLv3',
    author='Rasmus Scholer Sorensen',
    author_email='rasmusscholer@gmail.com',
    description='Tools to interact with my todo list (Todoist, mostly).',
    keywords=['Productivity', 'TODO', 'Todoist', 'GTD', 'Rewards'],
    entry_points={
        'console_scripts': [
            'todoist=rstodo.todoist:main',
            'todoist_today_or_overdue=rstodo.todoist:print_today_or_overdue_tasks',
        ],
        # 'gui_scripts': [
        #     'AnnotateGel=gelutils.gelannotator_gui:main',
        # ]
    },
    # pip will install these modules as requirements.
    install_requires=[
        # 'todoist',
        'todoist-python',  # official Todoist python API from Doist
        'pyyaml',
        'pytz',
        # 'jupyter',
        # 'notebook'
    ],
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        # 'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Education',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Healthcare Industry',

        # 'Topic :: Software Development :: Build Tools',
        # 'Topic :: Education',
        # 'Topic :: Scientific/Engineering',
        # 'Topic :: Scientific/Engineering :: Bio-Informatics',
        # 'Topic :: Scientific/Engineering :: Medical Science Apps.',

        # Pick your license as you wish (should match 'license' above)
        'License :: GNU Public License v3',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',

        'Operating System :: MacOS',
        'Operating System :: Microsoft',
        'Operating System :: POSIX :: Linux',
    ],
)
