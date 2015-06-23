# run for certain tables
java -jar bin/schemaSpy_5.0.0.jar -t pgsql -db bigg -u zaking -s public -o docs/schema -host localhost -port 5432 -dp /usr/local/Cellar/postgresql-jdbc/9.3-1102/libexec/postgresql-9.3-1102.jdbc3.jar -i "(.*model.*)|(genome)|(metabolite)|(.*component.*)|(chromosome)|(compartment)|(escher.*)|(gene)|(publication.*)|(reaction.*)|(synonym.*)"

# make a pdf of the figure
dot -Tpdf docs/schema/diagrams/summary/relationships.real.large.dot -o figure.pdf
