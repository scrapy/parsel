Release procedures
------------------

* Update NEWS file with the release notes.
  Review changes using: ``restview --pypi-strict <(cat README.rst NEWS | grep -v ':changelog')``
* Run bumpversion with the proper release type
* Push code and tags to GitHub to trigger build
* Copy release notes to https://github.com/scrapy/parsel/releases
* Verify in a temporary virtualenv that ``pip install parsel`` installs the
  latest version
* Update version builds at: https://readthedocs.org/projects/parsel/versions/
  You should ensure that previous stable version is active and point stable to the new tag
