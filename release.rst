Release procedures
------------------

* Update NEWS file with the release notes
* Run bumpversion with the proper release type
* Push code and tags to GitHub to trigger build
* Copy release notes to https://github.com/scrapy/parsel/releases
* Verify in a temporary virtualenv that ``pip install parsel`` installs the
  latest version
