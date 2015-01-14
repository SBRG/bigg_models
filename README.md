BiGG 2.0
--------

Install PostgreSQL.

For autcompletion, install the pg_trgm module with this command:

```shell
psql -d bigg -c "CREATE EXTENSION IF NOT EXISTS pg_trgm"
```

Generate a schema browser
-------------------------

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
