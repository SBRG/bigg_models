import psycopg2
import sys
import re
from os.path import isfile

def compare(model1, model2, logic='in', table='reaction'):
#compare: compares the reaction or metabolites of two models using abbreviation for equivalence
#default: returns reactions in common to model1 and model2
#options: logic="not in", returns reactions in model1 not in model2
#options: table="metabolite", returns metabolites in common, or exclusive to model1
#use: x,y=compare(...)

	config = {}
	execfile("config", config) 

	conn_string = "host='%s' dbname='%s' user='%s' password='%s'"%(config['host'], config['dbname'], config['user'], config['password'])
	conn = psycopg2.connect(conn_string)
	cursor = conn.cursor()

	if(table=='reaction'): #td return column names:  select column_name from information_schema.columns where table_name='reaction';
		if (logic=='in'):
			query="select * from reaction where modelversion_id=%s and abbreviation in (select abbreviation from reaction where modelversion_id=%s)"%(model1,model2)

		else:
			query="select * from reaction where modelversion_id=%s and abbreviation not in (select abbreviation from reaction where modelversion_id=%s)"%(model1,model2)	

		cursor.execute(query)
		results = cursor.fetchall()

	if(table=='metabolite'):
		if (logic=='in'):
			query="select * from metabolite where modelversion_id=%s and abbreviation in (select abbreviation from metabolite where modelversion_id=%s)"%(model1,model2)
		else:
			query="select * from metabolite where modelversion_id=%s and abbreviation not in (select abbreviation from metabolite where modelversion_id=%s)"%(model1,model2)	

		cursor.execute(query)
		results = cursor.fetchall()

	if(table=='gene'):
		if (logic=='in'):
			query="select * from gene where modelversion_id=%s and genesymbol in (select genesymbol from gene where modelversion_id=%s)"%(model1,model2)

		else:
			query="select * from gene where modelversion_id=%s and genesymbol not in (select genesymbol from gene where modelversion_id=%s)"%(model1,model2)	

		cursor.execute(query)
		results = cursor.fetchall()

	query="select string_agg(column_name , ', ') from information_schema.columns where table_name = '%s' group by table_name"%table
	cursor.execute(query)
	names = cursor.fetchone()
	cursor.close()
	conn.close()

	return (names, results)


def comparereactionfeature(model1, model2, feature='upper_bound'):
#feature can be upper_bound, lower_bound, objective_coefficient or formula
#returns column name, reactions, number of reactions
#use: x,y,z=comparereactionfeature(218,222)

	config = {}
	execfile("config", config) 
	conn_string = "host='%s' dbname='%s' user='%s' password='%s'"%(config['host'], config['dbname'], config['user'], config['password'])
	conn = psycopg2.connect(conn_string)
	cursor = conn.cursor()

	query="create temp table first as select * from reaction where  modelversion_id=%d"%model1
	cursor.execute(query)

	query="create temp table second as select * from reaction where  modelversion_id=%d"%model2
	cursor.execute(query)

	query="select count(*) from second as a inner join first as b on (a.abbreviation=b.abbreviation) where a.%s=b.%s"%(feature,feature)
	cursor.execute(query)
	reactionnum = cursor.fetchone()

	query="select * from second as a inner join first as b on (a.abbreviation=b.abbreviation) where a.%s=b.%s"%(feature,feature)
	cursor.execute(query)
	reactions = cursor.fetchall()

	query="select string_agg(column_name , ', ') from information_schema.columns where table_name = 'reaction' group by table_name"
	cursor.execute(query)
	reactionnames = cursor.fetchone()

	query="discard temp"
	cursor.execute(query)

	cursor.close()
	conn.close()

	return(reactionnames, reactions, reactionnum[0])

def comparemetabolitefeature(model1, model2, feature='formula'):
#feature can be upper_bound, lower_bound, objective_coefficient,formula, gpr 
#returns column name, reactions, number of reactions
#use: x,y,z=comparereactionfeature(218,222)

	config = {}
	execfile("config", config) 
	conn_string = "host='%s' dbname='%s' user='%s' password='%s'"%(config['host'], config['dbname'], config['user'], config['password'])
	conn = psycopg2.connect(conn_string)
	cursor = conn.cursor()

	query="create temp table first as select * from metabolite where  modelversion_id=%d"%model1
	cursor.execute(query)

	query="create temp table second as select * from metabolite where  modelversion_id=%d"%model2
	cursor.execute(query)

	query="select count(*) from second as a inner join first as b on (a.abbreviation=b.abbreviation) where a.%s=b.%s"%(feature,feature)
	cursor.execute(query)
	reactionnum = cursor.fetchone()

	query="select * from second as a inner join first as b on (a.abbreviation=b.abbreviation) where a.%s=b.%s"%(feature,feature)
	cursor.execute(query)
	reactions = cursor.fetchall()

	query="select string_agg(column_name , ', ') from information_schema.columns where table_name = 'metabolite' group by table_name"
	cursor.execute(query)
	reactionnames = cursor.fetchone()

	query="discard temp"
	cursor.execute(query)

	cursor.close()
	conn.close()

	return(reactionnames, reactions, reactionnum[0])

def comparegenefeature(model1, model2, feature='reactionrule'):
#feature is  gpr 
#returns number of reactions, gpr
#use: x,y=comparegenefeature(218,222)

	config = {}
	execfile("config", config) 
	conn_string = "host='%s' dbname='%s' user='%s' password='%s'"%(config['host'], config['dbname'], config['user'], config['password'])
	conn = psycopg2.connect(conn_string)
	cursor = conn.cursor()

	#query="create temp table first as select * from gene where  modelversion_id=%d"%model1

	query="create temp table first as select b.genesymbol, a.reactionrule from gpr as a inner join gene as b on (a.gene_id=b.gene_id) where b.modelversion_id=%s"%model1	
	cursor.execute(query)

	#query="create temp table second as select * from gene where  modelversion_id=%d"%model2

	query="create temp table second as select b.genesymbol, a.reactionrule from gpr as a inner join gene as b on (a.gene_id=b.gene_id) where b.modelversion_id=%s"%model2		
	cursor.execute(query)

	query="select count(*) from second as a inner join first as b on (a.reactionrule=b.reactionrule)"# where a.%s=b.%s"%(feature,feature)	
	cursor.execute(query)
	genenum = cursor.fetchone()

	query="select  a.genesymbol,  b.reactionrule from second as a inner join first as b on (a.reactionrule=b.reactionrule)"# where a.%s=b.%s"%(feature,feature)	
	cursor.execute(query)
	genes = cursor.fetchall()

	query="discard temp"
	cursor.execute(query)

	cursor.close()
	conn.close()

	return(genenum[0], genes)
