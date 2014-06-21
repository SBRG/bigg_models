from sqlalchemy import create_engine, ForeignKey, Column, Integer, String, Numeric, Table, MetaData, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from model import Map, Model, Component, Reaction, Compartment, Metabolite, Compartmentalized_Component, Model_Reaction, Reaction_Matrix, Gene, Model_Compartmentalized_Component, Model_Gene, GPR_Matrix

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
gprTable = Table('gpr', meta, autoload=True, autoload_with=grmitengine)
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
        map = Map(bigg_id = componentObject.id, grmit_id = instance.molecule_id, category = "metabolite")
        bigg2session.add(map)
        bigg2session.commit()
        grmitsession.close()
        bigg2session.close()
        
def loadModel(modelTable, grmitsession, bigg2session):
    for instance in grmitsession.query(modelTable):
        modelObject = Model(name = instance.name, firstcreated = instance.firstcreated)
        bigg2session.add(modelObject)
        bigg2session.commit()
        map = Map(bigg_id = modelObject.id, grmit_id = instance.modelversion_id, category = "model")
        bigg2session.add(map)
        bigg2session.commit()
        grmitsession.close()
        bigg2session.close()
        
def loadReaction(reactionTable, grmitsession, bigg2session):
    for instance in grmitsession.query(reactionTable):
        reactionObject = Reaction(name = instance.abbreviation)
        bigg2session.add(reactionObject)
        bigg2session.commit()
        map = Map(bigg_id = reactionObject.id, grmit_id = instance.reaction_id, category = "reaction")
        grmitsession.close()
        bigg2session.close()

def loadCompartment(metaboliteTable, grmitsession, bigg2session):
    for instance in grmitsession.query(metaboliteTable):
        if not bigg2session.query(Compartment).filter(Compartment.name == instance.compartment).count():
            compartmentObject = Compartment(name = instance.compartment)
            bigg2session.add(compartmentObject)
            bigg2session.commit()
            grmitsession.close()
            bigg2session.close()
        
def loadGenes(geneTable, grmitsession, bigg2session):
    for instance in grmitsession.query(geneTable):
        geneObject = Gene(name = instance.genesymbol)
        bigg2session.add(geneObject)
        bigg2session.commit()
        map = Map(bigg_id = geneObject.id, grmit_id = instance.gene_id, category = "gene")
        bigg2session.add(map)
        bigg2session.commit()
        grmitsession.close()
        bigg2session.close()
        
      
def loadMetabolites(metaboliteTable, grmitsession, bigg2session):
    for instance in session.query(Component):
        metaboliteObject = Metabolite(id=instance.id)
        session.add(metaboliteObject)
        bigg2session.commit()
        grmitsession.close()
        bigg2sesson.close()
        
def loadModelGenes(geneTable, modelTable, grmitsession, bigg2session):
    for model in grmitsession.query(modelTable):
        for gene in grmitsession.query(geneTable).filter(model.modelversion_id == geneTable.c.modelversion_id):
            modelMap = bigg2session.query(Map).filter(Map.category=="model").filter(Map.grmit_id == model.modelversion_id).first()
            geneMap = bigg2session.query(Map).filter(Map.category=="gene").filter(Map.grmit_id == gene.gene_id).first()
            m = bigg2session.query(Model).filter(Model.id == modelMap.bigg_id).first()
            g = bigg2session.query(Gene).filter(Gene.id == geneMap.bigg_id).first()
            modelGeneObject = Model_Gene(model_id = m.id, gene_id = g.id)
            bigg2session.add(modelGeneObject)
            bigg2session.commit()
            map = Map(bigg_id = modelGeneObject.id, grmit_id = g.id, category="model_gene")
            bigg2session.add(map)
            bigg2session.commit()
            grmitsession.close()
            bigg2session.close()

def loadCompartmentalizedComponent(metaboliteTable, grmitsession, bigg2session):
    for metabolite in grmitsession.query(metaboliteTable):
        for compartment in grmitsession.query(compartmentTable).filter(compartmentTable.c.name == metabolite.compartment):
            metaboliteMap = bigg2session.query(Map).filter(Map.category=="metabolite").filter(Map.grmit_id == metabolite.molecule_id).first()
            #m = bigg2session.query(Component).filter(Component.id == metaboliteMap.bigg_id).first()
            compartmentalizedComponent = Compartmentalized_Component(component_id = metaboliteMap.bigg_id, compartment_id = compartment.id)
            bigg2session.add(compartmentalizedComponent)
            bigg2session.commit()
            map = Map(bigg_id =compartmentalizedComponent.id, grmit_id = metabolite.molecule_id, category = "compartmentalized_component")
            bigg2session.add(map)
            bigg3session.commit()
            bigg2session.close()
            grmitsession.close()

def loadModelCompartmentalizedComponent(metaboliteTable, grmitsession, bigg2session):
    for metabolite in grmitsession.query(metaboliteTable):
        compartmentalizedcomponentMap = bigg2session.query(Map).filter(Map.category == "compartmentalized_component").filter(Map.grmit_id == metabolite.molecule_id).first()
        modelMap = bigg2session.query(Map).filter(Map.category=="model").filter(Map.grmit_id == metabolite.modelversion_id).first()
        object = Model_Compartmentalized_Component(compartmentalized_component_id = compartmentalizedcomponentMap.bigg_id, model_id = modelMap.bigg_id)
        bigg2session.add(object)
        bigg2session.commit()
        bigg2session.close()
        grmitsession.close()

def loadModelReaction(reactionTable, grmitsession, bigg2session):
    for reaction in grmitsession.query(reactionTable):
        modelMap = bigg2session.query(Map).filter(Map.category=="reaction").filter(Map.grmit_id == reaction.modelversion_id).first()
        reactionMap = bigg2session.query(Map).filter(Map.category=="reaction").filter(Map.grmit_id == reaction.reaction_id).first()
        object = Model_Reaction(reaction_id = reactionMap.bigg_id, model_id = modelMap.bigg_id, name = reaction.abbreviation, gpr = reaction.gpr, lowerbound = reaction.lower_bound, upperbound = reaction.upper_bound)
        bigg2session.add(object)
        bigg2session.commit()
        map = Map(bigg_id = object.id, grmit_id = reaction.reaction_id, category = "model_reaction")
        bigg2session.add(map)
        bigg2session.commit()
        bigg2session.close()
        grmitsession.close()

def loadGPRMatrix(gprTable, grmitsession, bigg2session):
    for gpr in grmitsession.query(gprTable):
        geneMap = bigg2session.query(Map).filter('model_gene').filter(Map.grmit_id == gpr.gene_id).first()
        reactionMap = bigg2session.query(Map).filter('model_reaction').filter(Map.grmit_id == gpr.reaction_id).first()
        object = GPR_Matrix(model_gene_id = geneMap.bigg_id, model_reaction_id = reactionMap.bigg_id)
        bigg2session.add(object)
        bigg2session.commit()
        bigg2session.close()
        gmitsession.close()

def loadReactionMatrix(reactionmetaboliteTable, grmitsession, bigg2session):
    for reactionmetabolite in grmitsession.query(reactionmetaboliteTable):
        reactionMap = bigg2session.query(Map).filter('reaction').filter(Map.grmit_id == reactionmetabolite.reaction_id).first()
        compartmentalizedcomponentMap = bigg2session.(Map).filter('compartmentalized_component').filter(Map.grmit_id = reactionmetabolite.molecule_id).first()
        object = Reaction_Matrix(reaction_id = reactionMap.bigg_id, compartmentalized_component_id = compartmentalizedcomponentMap.bigg_id, stoichiometry = reactionmetabolite.s)
        bigg2session.add(object)
        bigg2session.commit()
        bigg2session.close()
        grmitsession.close()        
"""
def loadModelGenes(geneTable, modelTable, grmitsession, bigg2sesssion):
    for model in grmitsession.query(modelTable):
        for gene in grmitsession.query(geneTable).filter(geneTable.modelversion_id == model.modelversion_id):
            m = bigg2session.query(Model).filter(Model.name == model.modelname).first()
            g = bigg2session.query(Gene).filter(Gene.name == gene.genesymbol).first()
            modelGeneObject = Model_Gene(model_id = m.id, gene_id = g.id)
            bigg2session.add(modelGeneObject)
            bigg2session.commit()
            grmitsession.close()
            bigg2sesson.close()

def loadCompartmentalizedComponent(metaboliteTable, grmitsession, bigg2session):
    for metabolite in grmitsession.query(metaboliteTable):
        compartment = bigg2session.query(Compartment).filter(Compartment.name == metabolite.compartment).first()
        component = bigg2session.query(Component).filter(Component.name == metabolite.officialname).first()
        compartmentalizedComponentObject = Compartmentalized_Component(compartment_id = compartment.id, component_id = component.id)                     
        bigg2session.add(compartmentalizedComponentObject)
        bigg2session.commit()
        
        m1 = grmitsession.query(modelTable).filter(modelTable.modelversion_id == metabolite.modelversion_id).first()
        m = bigg2session.query(Model).filter(Model.name == m1.name)
        modelCompartmentalizedComponentObject = Model_Compartmentalized_Component(model_id = m.id, compartmentalized_component_id = compartmentalizedComponentObject.id)
        bigg2session.add(modelCompartmentalizedComponentObject)
        bigg2session.commit()
        grmitsession.close()
        bigg2session.close()
        
def loadModelCompartmentalizedComponent(metaboliteTable, grmitsession, bigg2session):
    for instance in bigg2session.query(Compartmentalized_Component):
        compartment = bigg2session.query(Compartment).filter(Compartment.id == instance.compartment_id)
        component = bigg2session.query(Component).filter(Component.id == instance.component_id)
        comp = grmitsession.query(componentTable).filter(component.name == metaboliteTable.officialname).filter(compartment.name == metaboliteTable.compartment).first()
        model = grmitsession.query(modelTable).filter(modelTable.modelversion_id == comp.modelversion_id)
        modelCompartmentalizedComponentObject = Model_Compartmentalized_Component(model_id = model.id, compartmentalized_component_id = instance.id)
        bigg2session.add(modelCompartmentalizedComponentObject)
        bigg2session.commit()
        bigg2session.close()
        grmitsession.close()
        
def loadModelReaction(reactionTable, grmitsession, bigg2session):
    for reaction in grmitsession.query(reactionTable):
        model = grmitsession.query(modelTable).filter(modelTable.modelversion_id == reaction.modelversion_id).first()
        m = bigg2session.query(Model).filter(Model.name == model.modelname).first()
        r = bigg2session.query(Reaction).filter(Reaction.name == reaction.abbreviation).first()
        modelReactionObject = Model_Reaction(model_id = m.id, reaction_id = r.id, name = r.abbreviation, upperbound = r.upper_bound, lowerbound = r.lower_bound, gpr = r.gpr)
        bigg2session.add(modelReactionObject)
        bigg2session.commit()
        grmitsession.close()
        bigg2session.close()

def loadGPRMatrix(gprTable, grmitsession, bigg2session):
    for instance in grmitsession.query(gprTable):
        
def loadReactionMatrix(reactionmetaboliteTable, grmitsession, bigg2session):
  
#def loadCompartmentalizedComponent(metaboliteTable, grmitsession, bigg2session):
   
loadCompartment(metaboliteTable, grmitsession, bigg2session)
loadComponent(metaboliteTable, grmitsession, bigg2session)
loadCompartmentalizedComponent(metaboliteTable, grmitsession, bigg2session)
loadModelCompartmentalizedComponent(metaboliteTable, grmitsession, bigg2session)
"""
loadModel(modelTable, grmitsession, bigg2session)
loadGenes(geneTable, grmitsession, bigg2session)
loadModelGenes(geneTable, modelTable, grmitsession, bigg2session)