from cobra import Model, Reaction, Metabolite, Object
from cobra.io.sbml import create_cobra_model_from_sbml_file
from cobra.io.sbml import write_cobra_model_to_sbml_file
import psycopg2
import sys
import re
from os.path import isfile
import time
import os


def databasetomodel(modelversion_id, modelname=False):
    #1. takes a modelid and builds a cobra model object.
    #2. requires modelversion_id as an argument and optionally a model name

    config = {}
    execfile("config", config) 
    
    model_name = "m_" +str(modelversion_id)
    cobra_model = Model(model_name)  

    if modelname:
     print modelname, "Name feature not yet implemented"
     sys.exit()
     #to do: get model by name
         
    conn_string = "host='%s' dbname='%s' user='%s' password='%s'"%(config['host'], config['dbname'], config['user'], config['password'])
    
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()
    
    modelversion=modelversion_id
    countreactants=0
    countdeleted=0
    countmetabolite=0
    
    query="set search_path to public" #to do: from config
    cursor.execute(query)
    conn.commit()
    
    try:
        query="select abbreviation, officialname, reaction_id, equation, subsystem, lower_bound, upper_bound, objective_coefficient from reaction where modelversion_id=%s"%modelversion
        
        cursor.execute(query)
        reactions = cursor.fetchall()
        conn.commit()
    except psycopg2.DatabaseError, e:
        print 'Error %s' % e    
        sys.exit(1)
    
    the_metabolites={}
    
    for reaction, name, reaction_id, equation, subsystem, lower_bound, upper_bound, objective_coefficient in reactions: #get all the reactions, for each one: 
        reactionvar= Reaction(reaction)  
       
        reactionvar.name = name
        
        reactionvar.subsystem=subsystem
    
        query="select a.officialname, a.formula, a.abbreviation, a.compartment, a.charge, a.casnumber, a.keggid from metabolite_keggcass a inner join reactionmetabolite on (a.molecule_id=reactionmetabolite.molecule_id) inner join reaction on (reaction.reaction_id=reactionmetabolite.reaction_id) where (reaction.reaction_id=" + str(reaction_id)  +" ) and (a.modelversion_id=%d)"%modelversion
        
        cursor.execute(query)
        conn.commit
        reactants = cursor.fetchall()
    
        name=[]
        the_metabolites.clear()
        for officialname, formula, reactant, compartment, charge, casnumber, keggid in reactants: #get all the metabolites for one reaction:
    
            name=(Metabolite(reactant, '', officialname, compartment))
            
            name.notes={'CHARGE':charge, 'KEGGID': keggid, 'CASNUMBER':casnumber, 'FORMULA1':formula}
            
            countmetabolite +=1
            if 'deleted' in name.id: 
                continue
    
            name.id='M_'+name.id
            newvar=name
                   
            newvar.id=re.sub('-','_',newvar.id)
 
            newvar.id=re.sub('\)','_',newvar.id)
            newvar.name.replace('-','_')
            newvar.name.replace('\(','_')
            newvar.name.replace('\)','_')
                 
            newvalue=(Metabolite(reactant, '', officialname, compartment))
    
            newvalue.notes={'CHARGE':charge, 'KEGGID': keggid, 'CASNUMBER':casnumber, 'FORMULA1' : formula} #pm to add charge
                
            #exec('%s=%r') % (newvar, newvalue) 
            
            #get S from q        
            try: 
                newvalue
            except:
                print "error no newvalue for :  ", reactant
       
            if (newvalue=="M_"):
                print "error no newvalue for :  ", reactant
            try:   
                query= "select molecule_id from metabolite_keggcass where abbreviation='%s' and modelversion_id='%d'"%(reactant,modelversion)
                cursor.execute(query)
                mid = cursor.fetchone()
                conn.commit
            except psycopg2.DatabaseError, e:
                print 'Error %s' % e    
                sys.exit(1)
            
            try:
                query="select reaction_id from reaction where abbreviation='%s' and modelversion_id='%d'"%(reaction,modelversion)
           
                cursor.execute(query)
                rid = cursor.fetchone()
                conn.commit
            except psycopg2.DatabaseError, e:
                print 'Error %s' % e    
                sys.exit(1)
                
            try:
                query="select s from reactionmetabolite where molecule_id='%d'and reaction_id='%d' "%( mid[0],rid[0] )
                cursor.execute(query)
                s = cursor.fetchone()  
                conn.commit
            except psycopg2.DatabaseError, e:
                print 'Error %s' % e    
                sys.exit(1)
            
            the_metabolites.update({newvalue:round(s[0],6)},)
            # = {newvalue:1, newvalue:-1} add from S: td
   
        Reaction.add_metabolites(reactionvar, the_metabolites)
        
        """test inline from Reaction:
        _id_to_metabolites = dict([(x.id, x) for x in reactionvar._metabolites])
        
        new_metabolites = []
        for the_metabolite, the_coefficient in the_metabolites.items():
            
            if the_metabolite.id in _id_to_metabolites:
                reaction_metabolite = _id_to_metabolites[the_metabolite.id]
               # the_metabolite.update({'notes':{'CHARGE':1}} ) pm
                reactionvar._metabolites[reaction_metabolite] += the_coefficient             
            else:
                reactionvar._metabolites[the_metabolite] = the_coefficient    
                
                the_metabolite._reaction.add(reactionvar)
                new_metabolites.append(the_metabolite)
        for the_metabolite, the_coefficient in reactionvar._metabolites.items():
                        
            if the_coefficient == 0:
                
                the_metabolite._reaction.remove(reactionvar)
                reactionvar._metabolites.pop(the_metabolite)
        reactionvar.reconstruct_reaction()
        _id_to_metabolites = dict([(x.id, x)
                                        for x in reactionvar._metabolites])
        if hasattr(reactionvar._model, 'add_metabolites'):
     
            reactionvar._model.add_metabolites(new_metabolites)
         """  
        #cobra_model.add_reactions(reactionvar)
        try:
            query="select a.genesymbol, a.gene_id from gene as a inner join gpr on (gpr.gene_id=a.gene_id) inner join reaction on (gpr.reaction_id=reaction.reaction_id) where reaction.reaction_id=" + str(reaction_id)
            cursor.execute(query)
            genes = cursor.fetchall()
            conn.commit
        except psycopg2.DatabaseError, e:
            print 'Error %s' % e    
            sys.exit(1)
         
        if genes:
          
            try:
                query="select reactionrule from gpr where gene_id='%d' and reaction_id='%d'"%(genes[0][1], rid[0])
                cursor.execute(query)
                gene_reaction_rule = cursor.fetchone()
                conn.commit
            except psycopg2.DatabaseError, e:
                print 'Error %s' % e    
                sys.exit(1)
            
            reactionvar.add_gene_reaction_rule(gene_reaction_rule[0])

        cobra_model.add_reactions(reactionvar)
        
        if upper_bound:
            reactionvar.upper_bound=round(upper_bound,1)#int(upper_bound)
        else:
            reactionvar.upper_bound=0
        
        if lower_bound:
            reactionvar.lower_bound=round(lower_bound,1)#int(lower_bound)
        else:
            reactionvar.lower_bound=0
        
        if objective_coefficient:
            reactionvar.objective_coefficient=round(objective_coefficient,1) #int(objective_coefficient)
        else:
            reactionvar.objective_coefficient=0
      
    print '%i reactions in model' % len(cobra_model.reactions)
    print '%i metabolites in model' % len(cobra_model.metabolites)
    print '%i genes in model' % len(cobra_model.genes)
           
    write_cobra_model_to_sbml_file(cobra_model, str(modelversion_id) +'.xml')
    cursor.close()
    conn.close()   
    return 1

def todatabase(file, modelversion_id=False, description=False): 
    #1. takes an smbl model and inserts it into the grmit database
    #2. tracks a modelversion_id automatically for each model added 
    #3. optionally adds description to the model record
    #4. optionally revises the model with the option modelversion_id
    #   Returns: modelversion_id
    if not isfile(file):
        raise IOError('SBML file not found: %s'%file)

    if modelversion_id:
        print "modelversion_id not yet implemented"
        sys.exit()
    
    config = {}
    execfile("config", config) 
    #config['dbname']='grmit1'
 
    conn_string = "host='%s' dbname='%s' user='%s' password='%s'"%(config['host'], config['dbname'], config['user'], config['password'])
   
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()
    query="set search_path to public"
    cursor.execute(query)
    conn.commit()

    if not description:    
        description='test'
        
    try:
        query="insert into model(name, description) values ('%s','%s')"%(file,description)      
        cursor.execute(query)
        conn.commit()
    except psycopg2.DatabaseError, e:
            print 'Error %s' % e    
            sys.exit(1)
    
    try:
        query="select max(modelversion_id) from model"
        cursor.execute(query)
        conn.commit()
        num=cursor.fetchone()
    except psycopg2.DatabaseError, e:
            print 'Error %s' % e    
            sys.exit(1)
    
    modelversion=num[0]

    cobra_model=create_cobra_model_from_sbml_file(file)
      
    for x in cobra_model.genes:
        
        try:
            query="select gene_id, genesymbol from gene where genesymbol='%s' and modelversion_id='%d'"%(x, modelversion)
    
            cursor.execute(query)
            conn.commit()
            genes = cursor.fetchall()
        except psycopg2.DatabaseError, e:
            print 'Error %s' % e    
            sys.exit(1)
       
        if not genes: 
            try:
                query="insert into gene (genesymbol, modelversion_id) values ('%s', '%d') returning gene_id"%(x, modelversion)
                cursor.execute(query)
                conn.commit()
                row=cursor.fetchone()
                gid=row[0]
                             
            except psycopg2.DatabaseError, e:
                print 'Error %s' % e    
                sys.exit(1)
           
    for x in cobra_model.reactions:
         
        try:
            query="select abbreviation, reaction_id from reaction where abbreviation='%s' and modelversion_id='%d'"%(x, modelversion)
       
            cursor.execute(query)
            conn.commit()
            reactions = cursor.fetchall()
  
        except psycopg2.DatabaseError, e:
            print 'Error %s' % e    
            sys.exit(1)
        
        if not reactions: 
            query="insert into reaction (abbreviation, equation, gpr, subsystem, modelversion_id, lower_bound, upper_bound, objective_coefficient) values ('%s', '%s','%s', '%s', '%d', '%f', '%f', '%f') returning reaction_id"%(x, x.reaction, x.gene_reaction_rule, x.subsystem, modelversion, x.lower_bound, x.upper_bound, x.objective_coefficient) 

            cursor.execute(query) 
            conn.commit()       
            row = cursor.fetchone(); 
            rid = row[0];
                      
            if x._genes:
                #for key,value in x._genes.iteritems():
                for item in x._genes:
                    
                        #genename=key
                        genename=item
                    
                        try:
                            query="select reaction_id from reaction where abbreviation='%s'and modelversion_id='%d'"%(x, modelversion)
                            #query="select reaction_id from reaction where abbreviation='%s'and modelversion_id='%d'"%(x, modelversion) #pm mod oct 25
                            cursor.execute(query)
                            conn.commit()
                            rid = cursor.fetchone()
                       
                        except psycopg2.DatabaseError, e:
                            print 'Error %s' % e    
                            sys.exit(1)
                        
                        try:
                            query="select gene_id from gene where genesymbol='%s' and modelversion_id='%d'"%(genename,modelversion) #pm mod oct 25
                            #query="select gene_id from gene where genesymbol='%s' "%(genename)
                            cursor.execute(query)
                            conn.commit()
                            gid = cursor.fetchone()
                        except psycopg2.DatabaseError, e:
                            print 'Error %s' % e    
                            sys.exit(1)
                            
                        try:
                            query="insert into gpr (reaction_id,gene_id,reactionrule,modelversion_id) values ('%d','%d','%s', '%d')"%(rid[0],gid[0],x.gene_reaction_rule, modelversion)                    
                            cursor.execute(query)
                            conn.commit()
                        except psycopg2.DatabaseError, e:
                            print 'Error %s' % e    
                            sys.exit(1)
    
    for x in cobra_model.metabolites:
       
        query="select abbreviation from metabolite where abbreviation='%s' and modelversion_id='%d'"%(x, modelversion)
        
        cursor.execute(query)
        conn.commit()
        metabolites = cursor.fetchall()
       
        if not metabolites: 
            """
               if not metabolites: 
            rname=x.name.replace("\'", "\'\'")
            for key, value in x.notes.iteritems() :
                charge=int(value[0])if x.charge:
                charge=x.charge
                
            elif (x.notes['charge']):
                rname=x.name.replace("\'", "\'\'")
                for key, value in x.notes.iteritems() :
                    #charge=int(value[0])
                    #charge=x.notes['charge']
            
            else:
                charge=0
        """
            rname=x.name.replace("\'", "\'\'")
            if( x.notes.has_key('CHARGE')):
                charge= int(x.notes['CHARGE'][0])
               
            else:
                charge= x.charge
                               
            query="insert into metabolite (officialname, abbreviation, compartment, modelversion_id, formula, charge) values ('%s','%s','%s','%d', '%s', '%d') returning molecule_id"%(rname, x, x.compartment, modelversion, x.formula, charge)
            
            cursor.execute(query)
            conn.commit()
            row=cursor.fetchone()
            mid = row[0];
           
    for x in cobra_model.reactions: #insert links and s in mr join table: td, store reaction equation for validation
 
        query="select reaction_id from reaction where abbreviation='%s' and modelversion_id='%d'"%(x, modelversion)
        cursor.execute(query)
        conn.commit()
        rindex = cursor.fetchone()
        
        for key, value in x._metabolites.iteritems() :
            
            query="select molecule_id from metabolite where abbreviation='%s' and modelversion_id='%d'"%(key, modelversion)
            
            cursor.execute(query)
            conn.commit()
            mindex = cursor.fetchone()
            
            query="insert into reactionmetabolite(reaction_id, molecule_id, s, modelversion_id) values ('%d', '%d', '%f', '%d')"%(rindex[0], mindex[0], value, modelversion)
  
            cursor.execute(query)
            conn.commit()
    
    cursor.close()
    conn.close()    
    print '%i reaction in model' % len(cobra_model.reactions)
    print '%i metabolites in model' % len(cobra_model.metabolites)
    print '%i genes in model' % len(cobra_model.genes)
    return modelversion_id


def deletemodel(modelversion_id, modelname=False):
    #1. takes a model and deletes a cobra model object.
    #2. requires modelversion_id as an argument and optionally a model name
    
    config = {}
    execfile("config", config) 
 
    cobra_model = Model('example_cobra_model')  

    if modelname:
     print modelname, "Name feature not yet implemented"
     sys.exit()
     #to do: get model by name
         
    conn_string = "host='%s' dbname='%s' user='%s' password='%s'"%(config['host'], config['dbname'], config['user'], config['password'])   
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()
    
    query="delete from gene where modelversion_id='%s'"%modelversion_id
    cursor.execute(query)
    query="delete from reaction where modelversion_id='%s'"%modelversion_id
    cursor.execute(query)
    query="delete from gpr where modelversion_id='%s'"%modelversion_id
    cursor.execute(query)
    query="delete from metabolite where modelversion_id='%s'"%modelversion_id
    cursor.execute(query)
    query="delete from reactionmetabolite where modelversion_id='%s'"%modelversion_id
    cursor.execute(query)
    query="delete from model where modelversion_id='%s'"%modelversion_id
    cursor.execute(query) 
    query=query.replace("'", r"''")
    query="insert into transaction(username, action, modelversion_id) values ('%s', '%s', '%d')"%( config['user'], query, modelversion_id )
    
    cursor.execute(query) 
    conn.commit()
    cursor.close()
    conn.close() 
    return 1
    
def changegene(model, change, genesymbol, reaction_id, gpr=None):
#description: change model=modelversion_id, change=add, delete, update)

    if type(model) is not int:
        print "Model must be an integer" 
        return 0 
    if type(change) is not string:
        print "Change must be a string"
        return 0

    if(change.lower()=='add'):
            query=" insert into gene(genesymbol, modelversion_id) values ('%s', '%d') returning gene_id"%(genesymbol, model)           
            cursor.execute(query)
            row=cursor.fetchone()
            gid=row[0]
            if gpr is not None:
                query="insert into gpr(gene_id, reaction_id, gpr) values ('%d', '%d', '%s')"%(gid, reaction_id, gpr)
            else:
                query="insert into gpr(gene_id, reaction_id) values ('%d', '%d')"%(gid, reaction_id) 
            query=query.replace("'", r"''")
            query="insert into transaction(username, action, modelversion_id) values ('%s', '%s', '%d')"%( config['user'], query, modelversion_id )
            
    if(change.lower()=='update'):
            query="update gene15"
            query=query.replace("'", r"''")
            query="insert into transaction(username, action, modelversion_id) values ('%s', '%s', '%d')"%( config['user'], query, modelversion_id )
            
    if(change.lower()=='delete'):
            query="delete gene15"         
            query="delete gpr"
            query=query.replace("'", r"''")
            query="insert into transaction(username, action, modelversion_id) values ('%s', '%s', '%d')"%( config['user'], query, modelversion_id )


def changemetabolite(model, change):
#description: change model=modelversion_id, change=add, delete, update)

    if type(model) is not int:
        print "Model must be an integer" 
        return 0 
    if type(change) is not string:
        print "Change must be a string"
        return 0

    if(change.lower()=='add'):
            query=" insert into gene  "
            query=query.replace("'", r"''")
            query="insert into transaction(username, action, modelversion_id) values ('%s', '%s', '%d')"%( config['user'], query, modelversion_id )
            
    if(change.lower()=='update'):
            query="update gene"
            query=query.replace("'", r"''")
            query="insert into transaction(username, action, modelversion_id) values ('%s', '%s', '%d')"%( config['user'], query, modelversion_id )
            
    if(change.lower()=='delete'):
            query="delete gene"
            
            query="delete gpr"
            query=query.replace("'", r"''")
            query="insert into transaction(username, action, modelversion_id) values ('%s', '%s', '%d')"%( config['user'], query, modelversion_id )
 
            
def changereaction(model, change):
#description: change model=modelversion_id, change=add, delete, update)

    if type(model) is not int:
        print "Model must be an integer" 
        return 0 
    if type(change) is not string:
        print "Change must be a string"
        return 0

    if(change.lower()=='add'):
            query=" insert into gene  "
            query=query.replace("'", r"''")
            query="insert into transaction(username, action, modelversion_id) values ('%s', '%s', '%d')"%( config['user'], query, modelversion_id )
            
    if(change.lower()=='update'):
            query="update gene"
            query=query.replace("'", r"''")
            query="insert into transaction(username, action, modelversion_id) values ('%s', '%s', '%d')"%( config['user'], query, modelversion_id )
            
    if(change.lower()=='delete'):
            query="delete gene"
            
            query="delete gpr"
            query=query.replace("'", r"''")
            query="insert into transaction(username, action, modelversion_id) values ('%s', '%s', '%d')"%( config['user'], query, modelversion_id )
      
def addreaction():
    td
def addmetabolite():
    td
def addgene():
    td
def deletereaction():
    td
def deletemetabolite():
    td
def deletegene():
    td

def checkreactionduplicate():
    todo
    #check that there are no duplicates of a reaction insert or change
       
def createmodel():
    todo
    #create a model from array of gene, reaction, metabolites
    #return modelversion_id

def duplicatemodel(modelversion_id):
    todo
    #return modelversion_id
    
def createmodelversion(modelversion_id, version_number=None, version_information=None):
    todo
    #add a model version, for example create a new model through:

    #newmodelid=duplicatemodel(id)
    #changereaction(modelid, reactionid)
    #changemetabolite(modelid, moleculeid)
    #changegene(modelid, geneid)
    
    #insert into version, version information
    #createmodelversion(newid)

def createuserprofile(name, email):
    todo
    #return userid
    
def updateuserprofile(user):
    #returns recent transaction log
    todo
    
def validateuser(name, email):
    todo
    #return T/F on login
    
#modellist = [408, 260, 257, 258, 162]

databasetomodel(171)
#databasetomodel(409)