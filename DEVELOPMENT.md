



Publishing:
-----------

Publishing takes the following steps:

1. Create distribution package and upload to PyPI.
2. Make a tagged release on GitHub.


### Create PyPI distribution release:


Create distribution package:

	$ python setup.py sdist bdist_wheel

Perform basic local package checks (e.g. that the `long_description` will
render properly):

    $ twine check dist/*

Test the package by uploading to test server, using either setuptools or twine:

	$ twine upload --repository-url https://test.pypi.org/legacy/ dist/*

Upload the distribution package to PyPI, using either setuptools or twine:

	$ twine upload dist/*

OBS: You can also use good old setuptools to upload, but it may or may not be secure:

	$ python setup.py upload dist/*

You can use a `.pypirc` file to store your PyPI credentials.
You can also set `TWINE_` environment variables, or use `keyring` package.


Refs:

* https://packaging.python.org/tutorials/packaging-projects/



#### Alternative options (not currently used):


Using `poetry`:

	$ poetry publish


Using `flit`:

	$ flit publish


Using `hatch`:

	$ hatch release



### Create GitHub release:

Two options:

* Either go to https://github.com/scholer/actionista-todoist/releases and create a release.
* Or create an annotated git tag: `git tag -a <version>`, then push the tags to GitHub
  using `git push --tags`.



Documentations:
---------------

Documentation options:

* Sphinx + ReadTheDocs - now with "reasonable" Markdown support.
* MkDocs + GitHub Pages.
    * MkDocs builds Markdown documentation to static HTML, which can be served however you'd like,
      e.g. with GitHub Pages. 
    * With GitHub pages, the docs lives in a separate branch of your
      repository, `gh-pages` by default. You can publish docs with MkDocs directly to 
      gh-pages using `mkdocs gh-deploy`.
* You can also use MkDocs with ReadTheDocs: 
  https://read-the-docs.readthedocs.io/en/latest/intro/getting-started-with-mkdocs.html.
  



### MkDocs:

1. Init new project using: `mkdocs new .`
2. Edit `index.md` and add other doc files.
3. Serve locally, `mkdocs serve`.
4. Edit `mkdocs.yml`, updating `site_name:` and `nav:` (and optionally `theme:`).
5. Build: `mkdocs build`.
    * Add `site/` to `.gitignore` if you haven't done so already.
      `echo "site/" >> .gitignore`.
6. Deploy as GitHub Pages: `mkdocs gh-deploy`.
7. Alternatively, configure your ReadTheDocs to import your 




