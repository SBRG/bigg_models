BiGG 2
------

Installation
============

BiGG 2 is a web front end for genome-scale models stored using the
[OME Framework](https://github.com/sbrg/ome).

To install BiGG, first, follow the OME installation instructions:
https://github.com/SBRG/ome/blob/bigg/INSTALL.md

Then, do the following to get BiGG2 up and running:

1. Download the code with ```git clone git@github.com:SBRG/BIGG2.git```
2. ```cd BIGG2```
3. Install with ```python setup.py develop``` (may need to sudo or add --user)
4. Generate the PostgreSQL indices by running ```bin/make_database_indices```.
4. Generate the static models by running ```bin/make_all_static_models```.
5. Start the server with ```python -m bigg2.server --port=8910```

Testing BiGG 2
==============

Tests are run in both the [ome](https://github.com/sbrg/ome) and BiGG codebases
using [pytest](http://pytest.org/). Running `py.test` with ome will create a
temporary database and load it with a few simple test models. These tests can be
run at any time. Running `py.test` with BiGG 2 will run a series of test that
are specific to the models currently available at http://bigg.ucsd.edu. These
tests can only be run after the whole database is loaded.

Dumping and restoring the database
==================================

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
