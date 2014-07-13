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

#257 - iAF692
#253 - iJO1366

modelversionID = [253]


def loadComponent(metaboliteTable, grmitsession, bigg2session):
    for id in modelversionID:
        for instance in grmitsession.query(metaboliteTable).filter(metaboliteTable.c.modelversion_id == id):
            componentObject = Component(identifier = instance.abbreviation, name = instance.officialname, formula = instance.formula)
            componentquery = bigg2session.query(Component).filter(Component.identifier == instance.abbreviation)
            if componentquery.count()>0:
                #don't add new component object and only add map 
                component = componentquery.first() 
                map = Map(bigg_id = component.id, grmit_id = instance.molecule_id, category="metabolite") 
                bigg2session.add(map)
                bigg2session.commit()
                grmitsession.close()
                bigg2session.close()
            else:
                bigg2session.add(componentObject)
                bigg2session.commit()
                map = Map(bigg_id = componentObject.id, grmit_id = instance.molecule_id, category = "metabolite")
                bigg2session.add(map)
                bigg2session.commit()
                grmitsession.close()
                bigg2session.close()
        
def loadModel(modelTable, grmitsession, bigg2session):
    for id in modelversionID:
        instance = grmitsession.query(modelTable).filter(modelTable.c.modelversion_id == id).first()
        modelObject = Model(name = 'iJO1366', firstcreated = instance.firstcreated)
        bigg2session.add(modelObject)
        bigg2session.commit()
        map = Map(bigg_id = modelObject.id, grmit_id = instance.modelversion_id, category = "model")
        bigg2session.add(map)
        bigg2session.commit()
        grmitsession.close()
        bigg2session.close()
        
def loadReaction(reactionTable, grmitsession, bigg2session):
    for id in modelversionID:
        for instance in grmitsession.query(reactionTable).filter(reactionTable.c.modelversion_id == id):
            reactionObject = Reaction(name = instance.abbreviation)
            reactionquery = bigg2session.query(Reaction).filter(Reaction.name == instance.abbreviation)
            if reactionquery.count() > 0:
                reaction = reactionquery.first()
                map = Map(bigg_id = reaction.id, grmit_id = instance.reaction_id, category = "reaction")
                bigg2session.add(map)
                bigg2session.commit()
                grmitsession.close()
                bigg2session.close()
            else:
                bigg2session.add(reactionObject)
                bigg2session.commit()
                map = Map(bigg_id = reactionObject.id, grmit_id = instance.reaction_id, category = "reaction")
                bigg2session.add(map)
                bigg2session.commit()
                grmitsession.close()
                bigg2session.close()

def loadCompartment(metaboliteTable, grmitsession, bigg2session):
    for id in modelversionID:
        for instance in grmitsession.query(metaboliteTable).filter(metaboliteTable.c.modelversion_id == id):
            if not bigg2session.query(Compartment).filter(Compartment.name == instance.compartment).count():
                compartmentObject = Compartment(name = instance.compartment)
                bigg2session.add(compartmentObject)
                bigg2session.commit()
                grmitsession.close()
                bigg2session.close()

        
def loadGenes(geneTable, grmitsession, bigg2session):
    for id in modelversionID:
        for instance in grmitsession.query(geneTable).filter(geneTable.c.modelversion_id == id):
            geneObject = Gene(name = instance.genesymbol)
            bigg2session.add(geneObject)
            bigg2session.commit()
            map = Map(bigg_id = geneObject.id, grmit_id = instance.gene_id, category = "gene")
            bigg2session.add(map)
            bigg2session.commit()
            grmitsession.close()
            bigg2session.close()
             
def loadModelGenes(geneTable, modelTable, grmitsession, bigg2session):
    for id in modelversionID:
        for model in grmitsession.query(modelTable).filter(modelTable.c.modelversion_id == id):
            for gene in grmitsession.query(geneTable).filter(model.modelversion_id == geneTable.c.modelversion_id):
                modelMap = bigg2session.query(Map).filter(Map.category=="model").filter(Map.grmit_id == model.modelversion_id).first()
                geneMap = bigg2session.query(Map).filter(Map.category=="gene").filter(Map.grmit_id == gene.gene_id).first()
                #m = bigg2session.query(Model).filter(Model.id == modelMap.bigg_id).first()
                #g = bigg2session.query(Gene).filter(Gene.id == geneMap.bigg_id).first()
                modelGeneObject = Model_Gene(model_id = modelMap.bigg_id, gene_id = geneMap.bigg_id)
                bigg2session.add(modelGeneObject)
                bigg2session.commit()
                map = Map(bigg_id = modelGeneObject.id, grmit_id = gene.gene_id, category="model_gene")
                bigg2session.add(map)
                bigg2session.commit()
                grmitsession.close()
                bigg2session.close()

def loadCompartmentalizedComponent(metaboliteTable, grmitsession, bigg2session):
    for id in modelversionID:
        for metabolite in grmitsession.query(metaboliteTable).filter(metaboliteTable.c.modelversion_id == id):
            compartment = bigg2session.query(Compartment).filter(Compartment.name == metabolite.compartment).first()
            metaboliteMap = bigg2session.query(Map).filter(Map.category=="metabolite").filter(Map.grmit_id == metabolite.molecule_id).first()
            compartmentalizedComponent = Compartmentalized_Component(component_id = metaboliteMap.bigg_id, compartment_id = compartment.id)
            bigg2session.add(compartmentalizedComponent)
            bigg2session.commit()
            map = Map(bigg_id =compartmentalizedComponent.id, grmit_id = metabolite.molecule_id, category = "compartmentalized_component")
            bigg2session.add(map)
            bigg2session.commit()
            bigg2session.close()
            grmitsession.close()

def loadModelCompartmentalizedComponent(metaboliteTable, grmitsession, bigg2session):
    for id in modelversionID:
        for metabolite in grmitsession.query(metaboliteTable).filter(metaboliteTable.c.modelversion_id == id):
            compartmentalizedcomponentMap = bigg2session.query(Map).filter(Map.category == "compartmentalized_component").filter(Map.grmit_id == metabolite.molecule_id).first()
            modelMap = bigg2session.query(Map).filter(Map.category=="model").filter(Map.grmit_id == metabolite.modelversion_id).first()
            object = Model_Compartmentalized_Component(compartmentalized_component_id = compartmentalizedcomponentMap.bigg_id, model_id = modelMap.bigg_id)
            bigg2session.add(object)
            bigg2session.commit()
            bigg2session.close()
            grmitsession.close()

def loadModelReaction(reactionTable, grmitsession, bigg2session):
    for id in modelversionID:
        for reaction in grmitsession.query(reactionTable).filter(reactionTable.c.modelversion_id == id):
            modelMap = bigg2session.query(Map).filter(Map.category=="model").filter(Map.grmit_id == reaction.modelversion_id).first()
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
    for id in modelversionID:
        for gpr in grmitsession.query(gprTable).filter(gprTable.c.modelversion_id == id):
            geneMap = bigg2session.query(Map).filter(Map.category =='model_gene').filter(Map.grmit_id == gpr.gene_id).first()
            reactionMap = bigg2session.query(Map).filter(Map.category == 'model_reaction').filter(Map.grmit_id == gpr.reaction_id).first()
            object = GPR_Matrix(model_gene_id = geneMap.bigg_id, model_reaction_id = reactionMap.bigg_id)
            bigg2session.add(object)
            bigg2session.commit()
            bigg2session.close()
            grmitsession.close()

def loadReactionMatrix(reactionmetaboliteTable, grmitsession, bigg2session):
    for id in modelversionID:
        for reactionmetabolite in grmitsession.query(reactionmetaboliteTable).filter(reactionmetaboliteTable.c.modelversion_id == id):
            reactionMap = bigg2session.query(Map).filter(Map.category == 'reaction').filter(Map.grmit_id == reactionmetabolite.reaction_id).first()
            compartmentalizedcomponentMap = bigg2session.query(Map).filter(Map.category == 'compartmentalized_component').filter(Map.grmit_id == reactionmetabolite.molecule_id).first()
            object = Reaction_Matrix(reaction_id = reactionMap.bigg_id, compartmentalized_component_id = compartmentalizedcomponentMap.bigg_id, stoichiometry = reactionmetabolite.s)
            bigg2session.add(object)
            bigg2session.commit()
            bigg2session.close()
            grmitsession.close()  

if __name__ == "__main__":
    print "loading.."
    loadModel(modelTable, grmitsession, bigg2session)
    loadComponent(metaboliteTable, grmitsession, bigg2session)
    loadReaction(reactionTable, grmitsession, bigg2session)
    loadCompartment(metaboliteTable, grmitsession, bigg2session)
    loadCompartmentalizedComponent(metaboliteTable, grmitsession, bigg2session)
    loadModelCompartmentalizedComponent(metaboliteTable, grmitsession, bigg2session)
    loadModelReaction(reactionTable, grmitsession, bigg2session)
    loadGenes(geneTable, grmitsession, bigg2session)
    loadModelGenes(geneTable, modelTable, grmitsession, bigg2session)
    loadGPRMatrix(gprTable, grmitsession, bigg2session)
    loadReactionMatrix(reactionmetaboliteTable, grmitsession, bigg2session)

