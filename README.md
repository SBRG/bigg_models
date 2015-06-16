BiGG 2.0
--------

Installation
============

BiGG 2 is a web front end for genome-scale models stored using the
[OME Framework](https://github.com/sbrg/ome). Be sure to use the <a
href="https://github.com/sbrg/ome/tree/bigg">bigg branch</a>.

To install BiGG, first, follow the OME installation instructions:
https://github.com/SBRG/ome/blob/bigg/INSTALL.md

Then, BiGG 2 can be installed and run with these commands:

```
python setup.py install # or develop
python -m bigg2.server --port=8910
```

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
