bigg_models
-----------


[BiGG Models](http://bigg.ucsd.edu) is a website for browsing gold-standard genome-scale models, described in our publication here:

King ZA, Lu JS, Dräger A, Miller PC, Federowicz S, Lerman JA, Ebrahim A, Palsson BO, and Lewis NE. (2015). BiGG Models: A platform for integrating, standardizing, and sharing genome-scale models. Nucl Acids Res. doi:[10.1093/nar/gkv1049](https://doi.org/10.1093/nar/gkv1049).

This repository includes the web server and front-end for BiGG Models. The database is managed by [COBRAdb](https://github.com/sbrg/cobradb). You can see our plans for new BiGG Models features in the [Development Roadmap](https://github.com/SBRG/bigg_models/wiki/Development-roadmap).

Installation
============

To install BiGG Models, first, follow the OME installation instructions:
https://github.com/SBRG/ome/blob/bigg/INSTALL.md

Then, do the following to get BiGG Models up and running:

1. Download the code with ```git clone git@github.com:SBRG/bigg_models.git```
2. ```cd bigg_models```
3. Install with ```python setup.py develop``` (may need to sudo or add --user)
4. Generate the PostgreSQL indices by running ```bin/make_database_indices```.
4. Generate the static models by running ```bin/make_all_static_models```.
5. Start the server with ```python -m bigg_models.server --port=8910```

Alternative installation: Docker
================================

BiGG Models can also be installed with Docker. Everything you need is here, thanks to @psalvy:

https://github.com/psalvy/bigg-docker

Testing BiGG Models
===================

Tests are run in both the [ome](https://github.com/sbrg/ome) and BiGG Models
codebases using [pytest](http://pytest.org/). Running `py.test` with ome will
create a temporary database and load it with a few simple test models. These
tests can be run at any time. Running `py.test` with BiGG Models will run a
series of test that are specific to the models currently available at
http://bigg.ucsd.edu. These tests can only be run after the whole database is
loaded.

Dumping and restoring the database
==================================

The latest database dumps are available in this Dropbox folder:

https://www.dropbox.com/sh/ye05djxrpxy37da/AAD6GrSRTt4MRfuIpprlnLYba?dl=0

We generally dump the database with this command:

```
pg_dump -Fc bigg > bigg_database.dump
```

And then restore like this:

```
pg_restore -c -d bigg bigg_database.dump
```

Generate a schema browser
=========================

Install and run [schemaSpy](http://schemaspy.sourceforge.net/). For example,
here are the Mac OS X instructions:

```shell
brew install graphviz

brew tap gbeine/homebrew-java
brew install postgresql-jdbc

java -jar bin/schemaSpy_5.0.0.jar -t pgsql -db bigg -u username -s public \
  -o docs/schema -host localhost -port 5432 \
  -dp /usr/local/Cellar/postgresql-jdbc/9.3-1102/libexec/postgresql-9.3-1102.jdbc3.jar
```

Then open `docs/schema/index.html` in a web browser.

License
=======

This codebase is released under the
[MIT license](https://github.com/SBRG/bigg_models/blob/master/LICENSE). The
license information for the BiGG Models website hosted at SBRG and the
associated models can be found here: http://bigg.ucsd.edu/license.
