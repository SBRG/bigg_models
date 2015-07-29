BiGG 2.0
--------

Installation
============

BiGG 2 is a web front end for genome-scale models stored using the
[OME Framework](https://github.com/sbrg/ome). Be sure to use the <a
href="https://github.com/sbrg/ome/tree/bigg">bigg branch</a>.

To install BiGG, first, follow the OME installation instructions:
https://github.com/SBRG/ome/blob/bigg/INSTALL.md

Then, do the following to get BiGG2 up and running:

1. Download the code with ```git clone git@github.com:SBRG/BIGG2.git```
2. ```cd BIGG2```
3. Install with ```python setup.py develop``` (may need to sudo or add --user)
4. Generate the static models by running the ```make_all_static_models``` command.
5. Start the server with ```python -m bigg2.server --port=8910```

Generate a schema browser
=========================

Install and run schemaSpy. For example, here are the Mac OS X instructions:

```shell
brew install graphviz

brew tap gbeine/homebrew-java
brew install postgresql-jdbc

java -jar bin/schemaSpy_5.0.0.jar -t pgsql -db bigg -u username -s public \
  -o docs/schema -host localhost -port 5432 \
  -dp /usr/local/Cellar/postgresql-jdbc/9.3-1102/libexec/postgresql-9.3-1102.jdbc3.jar
```

Then open `docs/schema/index.html` in a web browser.
