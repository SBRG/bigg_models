from theseus import models
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from sqlalchemy import create_engine, Table, MetaData
from ome import base, components
from model import Model, Escher_Map, Component, Reaction, Compartment, Metabolite, Compartmentalized_Component, Model_Reaction, Reaction_Matrix, Gene, Model_Compartmentalized_Component, Model_Gene, GPR_Matrix
from ome.loading import component_loading

Session = sessionmaker()


grmitengine = create_engine("postgresql://justin:justin@pestis:5432/grmit")
Session.configure(bind=grmitengine)
grmitsession = Session()
meta = MetaData()
keggcasTable = Table('metabolite_keggcass', meta, autoload=True, autoload_with=grmitengine)


engine = create_engine("postgresql://dbuser@localhost:5432/ome")
Session.configure(bind=engine)

class IndependentObjects:

    def loadGenes(self, modellist, session):
        for model in modellist:
            for gene in model.genes:
                if not session.query(Gene).filter(Gene.name == gene.id).count():
                    geneObject = Gene(name = gene.id)
                    session.add(geneObject)
                
    def loadModels(self, modellist, session):
        for model in modellist:
            modelObject = Model(biggid = model.id, firstcreated = '2013-10-21 14:26:22')
            session.add(modelObject)
            
    
    def loadComponents(self, modellist, session):
        for model in modellist:
            for component in model.metabolites:
                if not session.query(Component).filter(Component.name == component.name).count() and not session.query(Metabolite).filter(Metabolite.biggid == component.id[0:-2]).count():
                    #componentObject = Component()
                    #session.add(componentObject)
                    metaboliteObject = Metabolite(biggid = component.id[0:-2], name = component.name, kegg_id = component.notes.get("KEGGID"), cas_number = component.notes.get("CASNUMBER"), formula = str(component.formula))
                    session.add(metaboliteObject)
                                
    def loadReactions(self , modellist, session):
        for model in modellist:
            for reaction in model.reactions:
                if not session.query(Reaction).filter(Reaction.name == reaction.name).count():
                    reactionObject = Reaction(biggid = reaction.id, name = reaction.name)
                    session.add(reactionObject)
                    for metabolite in reaction._metabolites:
                        
                        componentquery = session.query(Metabolite).filter(Metabolite.biggid == metabolite.id).first()
                        if componentquery is not None:
                            compartmentalized_component_query = session.query(Compartmentalized_Component).filter(Compartmentalized_Component.component_id == componentquery.id).first()
                            #reactionquery = session.query(Reaction).filter(Reaction.biggid == reaction.id).first()
                    
                            for stoichKey in reaction._metabolites.keys():
                                if str(stoichKey) == metabolite.id:
                                    stoichiometryobject = reaction._metabolites[stoichKey]
                            RMobject = Reaction_Matrix(reaction_id = reactionObject.id, compartmentalized_component_id = compartmentalized_component_query.id, stoichiometry = stoichiometryobject)
                            session.add(RMobject)
    
    def loadCompartments(self, modellist, session):
        for model in modellist:
            for component in model.metabolites:
                if component.id is not None:
                    if not session.query(Compartment).filter(Compartment.name == component.id[-1:len(component.id)]).count():
                        compartmentObject = Compartment(name = component.id[-1:len(component.id)])
                        session.add(compartmentObject)
                        
                   

class DependentObjects:
    def loadModelGenes(self, modellist, session):
        for model in modellist:
            for gene in model.genes:
                if gene.id != 's0001':
                    genequery = session.query(Gene).filter(Gene.locus_id == gene.id).first()
                    modelquery = session.query(Model).filter(Model.biggid == model.id).first()
                    object = Model_Gene(model_id = modelquery.id, gene_id = genequery.id)
                    session.add(object)
                
    def loadCompartmentalizedComponent(self, modellist, session):
        for model in modellist:
            for metabolite in model.metabolites:
                identifier = session.query(Compartment).filter(Compartment.name == metabolite.id[-1:len(metabolite.id)]).first()
                m = session.query(Metabolite).filter(Metabolite.biggid == metabolite.id[0:-2]).first()
                object = Compartmentalized_Component(component_id = m.id, compartment_id = identifier.id)
                session.add(object)
        """       
        for component in session.query(Metabolite):
            if component.biggid is not None:
                identifier = session.query(Compartment).filter(Compartment.name == component.biggid[-1:len(component.biggid)]).first()
                #instance = session.query(Component).filter(Component.biggid == component.biggid[:-2]).first()
                object = Compartmentalized_Component(component_id = component.id, compartment_id = identifier.id)
                session.add(object)
        """
                
    def loadModelCompartmentalizedComponent(self, modellist, session):
        for model in modellist:
            for metabolite in model.metabolites:
                componentquery = session.query(Metabolite).filter(Metabolite.biggid == metabolite.id[0:-2]).first()
                compartmentquery = session.query(Compartment).filter(Compartment.name == metabolite.id[-1:len(metabolite.id)]).first()
                compartmentalized_component_query = session.query(Compartmentalized_Component).filter(Compartmentalized_Component.component_id == componentquery.id).filter(Compartmentalized_Component.compartment_id == compartmentquery.id).first()
                modelquery = session.query(Model).filter(Model.biggid == model.id).first()
                object = Model_Compartmentalized_Component(model_id = modelquery.id, compartmentalized_component_id = compartmentalized_component_query.id)
                session.add(object)


    def loadModelReaction(self, modellist, session):
        for model in modellist:
            for reaction in model.reactions:
                reactionquery = session.query(Reaction).filter(Reaction.name == reaction.name).first()
                modelquery = session.query(Model).filter(Model.biggid == model.id).first()
                object = Model_Reaction(reaction_id = reactionquery.id, model_id = modelquery.id, biggid = reaction.id, upperbound = reaction.upper_bound, lowerbound = reaction.lower_bound, gpr = reaction.gene_reaction_rule)
                session.add(object)
            
    
    def loadGPRMatrix(self, modellist, session):
        for model in modellist:
            for reaction in model.reactions:
                for gene in reaction._genes:
                    model_query = session.query(Model).filter(Model.biggid == model.id).first()
                    model_gene_query = session.query(Model_Gene).join(Gene).filter(Gene.locus_id == gene.id).filter(Model_Gene.model_id == model_query.id).first()
                    
                    if model_gene_query != None:
                        model_reaction_query = session.query(Model_Reaction).filter(Model_Reaction.biggid == reaction.id).filter(Model_Reaction.model_id == model_query.id).first()
                        object = GPR_Matrix(model_gene_id = model_gene_query.id, model_reaction_id = model_reaction_query.id) 
                        session.add(object)
                
    def loadReactionMatrix(self, modellist, session):
        for model in modellist:
            for reaction in model.reactions:
                for metabolite in reaction._metabolites:
                    componentquery = session.query(Metabolite).filter(Metabolite.biggid == metabolite.id[0:-2]).first()
                    compartmentquery = session.query(Compartment).filter(Compartment.name == metabolite.id[-1:len(metabolite.id)]).first()
                    compartmentalized_component_query = session.query(Compartmentalized_Component).filter(Compartmentalized_Component.component_id == componentquery.id).filter(Compartmentalized_Component.compartment_id == compartmentquery.id).first()
                    #modelquery = session.query(Model).filter(Model.name == model.id).first()
                    reactionquery = session.query(Reaction).filter(Reaction.name == reaction.name).first()
                    
                    for stoichKey in reaction._metabolites.keys():
                        if str(stoichKey) == metabolite.id:
                            stoichiometryobject = reaction._metabolites[stoichKey]
                    object = Reaction_Matrix(reaction_id = reactionquery.id, compartmentalized_component_id = compartmentalized_component_query.id, stoichiometry = stoichiometryobject)
                    session.add(object)
                    
    def loadEscher(self, session):
        m = models.load_model('iJO1366')
        for reaction in m.reactions:
            escher = Escher_Map(biggid = reaction.id, category = "reaction", model_name = m.id)
            session.add(escher)                        

@contextmanager
def create_Session():
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        print "close"
        session.close()
        
def run_program():
    modelObjectList = []
    """for m in models.get_model_list():
        modelObjectList.append(models.load_model(m))
    """
    modelObjectList.append(models.load_model('iJO1366'))
    with create_Session() as session:
        
        component_loading.load_genomes(base, components)
        IndependentObjects().loadModels(modelObjectList, session)
        #IndependentObjects().loadGenes(modelObjectList, session)
        IndependentObjects().loadComponents(modelObjectList,session)
        IndependentObjects().loadCompartments(modelObjectList, session)
        DependentObjects().loadCompartmentalizedComponent(modelObjectList, session)
        IndependentObjects().loadReactions(modelObjectList, session)
        
        #DependentObjects().loadMetabolites(modelObjectList, session)
        DependentObjects().loadModelGenes(modelObjectList, session)
        
        DependentObjects().loadModelCompartmentalizedComponent(modelObjectList, session)
        DependentObjects().loadModelReaction(modelObjectList, session)
        DependentObjects().loadGPRMatrix(modelObjectList, session)
        DependentObjects().loadReactionMatrix(modelObjectList, session)
        
        
        DependentObjects().loadEscher(session)
        
if __name__ == '__main__':
    run_program()
