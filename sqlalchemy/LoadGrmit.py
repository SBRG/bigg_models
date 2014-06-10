from sqlalchemy import create_engine, ForeignKey, Column, Integer, String, Numeric, Table, MetaData, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from model import Model, Component, Reaction, Compartment, Metabolite, Compartmentalized_Component, Model_Reaction, Reaction_Matrix, Gene, Model_Compartmentalized_Component, Model_Gene, GPR_Matrix

Session = sessionmaker()

grmitengine = create_engine("postgresql://justin:justin@pestis:5432/grmit")
bigg2engine = create_engine("postgresql://dbuser@localhost:5432/bigg2")


Session.configure(bind=grmitengine)
grmitsession = Session()

Session.configure(bind=bigg2engine)
bigg2session = Session()

meta = MetaData()

metaboliteTable = Table('metabolite', meta, autoload=True, autoload_with=grmitengine)
geneTable = Table('gene', meta, autoload=True, autoload_with=grmitengine)
gprtabeTable = Table('gpr', meta, autoload=True, autoload_with=grmitengine)
ecocycgenesTable = Table('ecocycgenes', meta, autoload=True, autoload_with=grmitengine)
modelTable = Table('model', meta, autoload=True, autoload_with=grmitengine)
notesTable = Table('notes', meta, autoload=True, autoload_with=grmitengine)
reactionTable = Table('reaction', meta, autoload=True, autoload_with=grmitengine)
reactionmetaboliteTable = Table('reactionmetabolite', meta, autoload=True, autoload_with=grmitengine)
simulationTable = Table('simulation', meta, autoload=True, autoload_with=grmitengine)
transactionTable = Table('transaction', meta, autoload=True, autoload_with=grmitengine)
versionTable = Table('version', meta, autoload=True, autoload_with=grmitengine)


def loadComponent(metaboliteTable, grmitsession, bigg2session):
    for instance in grmitsession.query(metaboliteTable):
        componentObject = Component(identifier = instance.abbreviation, name = instance.officialname, formula = instance.formula)
        bigg2session.add(componentObject)
        bigg2session.commit()
        grmitsession.close()
        bigg2session.close()
        
def loadModel(modelTable, grmitsession, bigg2session):
    for instance in grmitsession.query(modelTable):
        modelObject = Model(name = instance.name, firstcreated = instance.firstcreated)
        bigg2session.add(modelObject)
        bigg2session.commit()
        grmitsession.close()
        bigg2session.close()
        
def loadReaction(reactionTable, grmitsession, bigg2session)
    for instance in grmitsession.query(reactionTable):
        reactionObject = Reaction(name = instance.abbreviation)
        bigg2session.add(reactionObject)
        bigg2session.commit()
        grmitsession.close()
        bigg2session.close()
#loadModel(modelTable, grmitsession, bigg2session)
#loadComponent(metaboliteTable, grmitsession, bigg2session)
"""loadGene():
loadGpr():
loadModel():
loadReaction():
loadReactionMetabolite():
load"""