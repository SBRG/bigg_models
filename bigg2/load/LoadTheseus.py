from theseus import models
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from sqlalchemy import create_engine, Table, MetaData, update
from ome import base, components
from model import Model, Escher_Map, Component, Reaction, Compartment, Metabolite, Compartmentalized_Component, Model_Reaction, Reaction_Matrix, Gene, Model_Compartmentalized_Component, Model_Gene, GPR_Matrix, Synonyms, Genome
from ome.loading import component_loading
from LoadGenome import load_genomes
import re
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
                    geneObject = Gene(locus_id = gene.id)
                    session.add(geneObject)
                
    def loadModels(self, modellist, session, dict):
        for model in modellist:
            genome = session.query(Genome).filter(Genome.bioproject_id == dict[model.id][0]).first()
            if genome != None:
                modelObject = Model(biggid = model.id, firstcreated = dict[model.id][1], genome_id = genome.id, notes = '')
                session.add(modelObject)
            else:
                print model.id
                print "corresponding genbank file was not uploaded"   
    
    def loadComponents(self, modellist, session):
        for model in modellist:
            for component in model.metabolites:
                metabolite = session.query(Metabolite).filter(Metabolite.name == component.id.split("_")[0])
                #metabolite = session.query(Metabolite).filter(Metabolite.kegg_id == component.notes.get("KEGGID")[0]) 
                keggid = str(component.notes.get("KEGGID", 'None')).strip('[]')
                casnumber = str(component.notes.get("CASNUMBER", 'None')).strip('[]')
                seed = str(component.notes.get("SEED", 'None')).strip('[]')
                chebi = str(component.notes.get("CHEBI", 'None')).strip('[]')
                metacyc = str(component.notes.get("METACYC", 'None')).strip('[]')
                upa = str(component.notes.get("UPA", 'None')).strip('[]')
                brenda = str(component.notes.get("BRENDA", 'None')).strip('[]')
                if not metabolite.count():
                    if component.notes.get("KEGGID",[''])[0] == '' or component.notes.get("KEGGID",[''])[0]== None:
                        metaboliteObject = Metabolite(name = component.id.split("_")[0], long_name = component.name, kegg_id = keggid, cas_number = casnumber, seed = seed, chebi = chebi, metacyc = metacyc, upa = upa, brenda = brenda, formula = str(component.formula), flag=False)
                    else:
                          metaboliteObject = Metabolite(name = component.id.split("_")[0], long_name = component.name, kegg_id = keggid, cas_number = casnumber, seed = seed, chebi = chebi, metacyc = metacyc, upa = upa, brenda = brenda, formula = str(component.formula), flag=True)
                    session.add(metaboliteObject)
                else:
                    metaboliteObject = metabolite.first()               
                    if metaboliteObject.kegg_id == None or metaboliteObject.kegg_id == '':
                        metaboliteObject.kegg_id = keggid
                    if metaboliteObject.cas_number == None or metaboliteObject.cas_number == '':
                        metaboliteObject.cas_number = casnumber
                    if str(metaboliteObject.formula) == None or str(metaboliteObject.formula) == '':
                        metaboliteObject.formula = str(metaboliteObject.formula)
                        
                                
    def loadReactions(self , modellist, session):
        for model in modellist:
            for reaction in model.reactions:
                if not session.query(Reaction).filter(Reaction.name == reaction.id).count():
                    reactionObject = Reaction(name = reaction.id, long_name = reaction.name, notes = '')
                    session.add(reactionObject)
    
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
                    if session.query(Gene).filter(Gene.locus_id == gene.id).first() != None:
                        genequery = session.query(Gene).filter(Gene.locus_id == gene.id).first()          
                        modelquery = session.query(Model).filter(Model.biggid == model.id).first()
                        #genequery = session.query(Gene).filter(Gene.locus_id == gene.id).filter(Gene.genome_id == modelquery.genome_id).first()
                        object = Model_Gene(model_id = modelquery.id, gene_id = genequery.id)
                        session.add(object)
                    elif session.query(Gene).filter(Gene.name == gene.id).first() != None:
                        genequery = session.query(Gene).filter(Gene.name == gene.id).first()
                        modelquery = session.query(Model).filter(Model.biggid == model.id).first()
                        object = Model_Gene(model_id = modelquery.id, gene_id = genequery.id)
                        session.add(object)
                    else:
                        #geneObject = Gene(locus_id = gene.id, leftpos=None, rightpos=None, strand=None, name=gene.id)
                        #session.add(geneObject)
                        synonymquery = session.query(Synonyms).filter(Synonyms.synonym == gene.id.split(".")[0]).filter(Synonyms.type == 'gene').first()
                        if synonymquery != None:
                            modelquery = session.query(Model).filter(Model.biggid == model.id).first()
                            
                            genecheck = session.query(Gene).filter(Gene.id == synonymquery.ome_id).first()
                            if genecheck:
                                object = Model_Gene(model_id = modelquery.id, gene_id = synonymquery.ome_id)
                                session.add(object)
                                
                                if modelquery.biggid == "RECON1":
                                    geneobject = session.query(Gene).filter(Gene.id == synonymquery.ome_id).first()
                                    geneobject.locus_id = gene.id
                            else:
                                print synonymquery.ome_id  
                        else:
                            print gene.id, model.id
             
    def loadCompartmentalizedComponent(self, modellist, session):
        for model in modellist:
            for metabolite in model.metabolites:
                identifier = session.query(Compartment).filter(Compartment.name == metabolite.id[-1:len(metabolite.id)]).first()
                m = session.query(Metabolite).filter(Metabolite.name == metabolite.id.split("_")[0]).first()
                #m = session.query(Metabolite).filter(Metabolite.kegg_id == metabolite.notes.get("KEGGID")[0]).first()
                object = Compartmentalized_Component(component_id = m.id, compartment_id = identifier.id)
                session.add(object)
                
    def loadModelCompartmentalizedComponent(self, modellist, session):
        for model in modellist:
            for metabolite in model.metabolites:
                componentquery = session.query(Metabolite).filter(Metabolite.name == metabolite.id.split("_")[0]).first()
                #componentquery = session.query(Metabolite).filter(Metabolite.kegg_id == metabolite.notes.get("KEGGID")[0]).first()
                compartmentquery = session.query(Compartment).filter(Compartment.name == metabolite.id[-1:len(metabolite.id)]).first()
                compartmentalized_component_query = session.query(Compartmentalized_Component).filter(Compartmentalized_Component.component_id == componentquery.id).filter(Compartmentalized_Component.compartment_id == compartmentquery.id).first()
                modelquery = session.query(Model).filter(Model.biggid == model.id).first()
                if modelquery is None:
                    print "model query is none", model.id
                if compartmentalized_component_query is None:
                    print "compartmentalized_component_query is none", metabolite.id
                object = Model_Compartmentalized_Component(model_id = modelquery.id, compartmentalized_component_id = compartmentalized_component_query.id, compartment_id = compartmentquery.id)
                session.add(object)


    def loadModelReaction(self, modellist, session):
        for model in modellist:
            for reaction in model.reactions:
                reactionquery = session.query(Reaction).filter(Reaction.name == reaction.id).first()
                modelquery = session.query(Model).filter(Model.biggid == model.id).first()
                object = Model_Reaction(reaction_id = reactionquery.id, model_id = modelquery.id, name = reaction.id, upperbound = reaction.upper_bound, lowerbound = reaction.lower_bound, gpr = reaction.gene_reaction_rule)
                session.add(object)
            
    
    def loadGPRMatrix(self, modellist, session):
        for model in modellist:
            for reaction in model.reactions:
                for gene in reaction._genes:
                    if gene.id != 's0001':
                        
                        model_query = session.query(Model).filter(Model.biggid == model.id).first()
                        model_gene_query = session.query(Model_Gene).join(Gene).filter(Gene.locus_id == gene.id).filter(Model_Gene.model_id == model_query.id).first()
                    
                        if model_gene_query != None:
                            model_reaction_query = session.query(Model_Reaction).filter(Model_Reaction.name == reaction.id).filter(Model_Reaction.model_id == model_query.id).first()
                            object = GPR_Matrix(model_gene_id = model_gene_query.id, model_reaction_id = model_reaction_query.id) 
                            session.add(object)
                        else:
                            model_gene_query = session.query(Model_Gene).join(Gene).filter(Gene.name == gene.id).filter(Model_Gene.model_id == model_query.id).first()
                            if model_gene_query != None:
                                model_reaction_query = session.query(Model_Reaction).filter(Model_Reaction.name == reaction.id).filter(Model_Reaction.model_id == model_query.id).first()
                                object = GPR_Matrix(model_gene_id = model_gene_query.id, model_reaction_id = model_reaction_query.id) 
                                session.add(object)
                            else:
                                synonymquery = session.query(Synonyms).filter(Synonyms.synonym == gene.id.split(".")[0]).first()
                                if synonymquery != None:
                                    if synonymquery.ome_id != None:
                                        model_gene_query = session.query(Model_Gene).join(Gene).filter(Gene.id == synonymquery.ome_id).filter(Model_Gene.model_id == model_query.id).first()
                                        model_reaction_query = session.query(Model_Reaction).filter(Model_Reaction.name == reaction.id).filter(Model_Reaction.model_id == model_query.id).first()
                                        object = GPR_Matrix(model_gene_id = model_gene_query.id, model_reaction_id = model_reaction_query.id) 
                                        session.add(object)
                                    else:
                                        print "ome id is null " + synonymquery.ome_id
                                else:
                                    print "mistake", gene.id, reaction.id
                
    def loadReactionMatrix(self, modellist, session):
        for model in modellist:
            for reaction in model.reactions:                
                reactionquery = session.query(Reaction).filter(Reaction.name == reaction.id).first()
                for metabolite in reaction._metabolites:
                    
                    componentquery = session.query(Metabolite).filter(Metabolite.name == metabolite.id.split("_")[0]).first()
                    #componentquery = session.query(Metabolite).filter(Metabolite.kegg_id == metabolite.notes.get("KEGGID")[0]).first()                    
                    compartmentquery = session.query(Compartment).filter(Compartment.name == metabolite.id[-1:len(metabolite.id)]).first()
                    compartmentalized_component_query = session.query(Compartmentalized_Component).filter(Compartmentalized_Component.component_id == componentquery.id).filter(Compartmentalized_Component.compartment_id == compartmentquery.id).first()     
                    if not session.query(Reaction_Matrix).filter(Reaction_Matrix.reaction_id == reactionquery.id).filter(Reaction_Matrix.compartmentalized_component_id == compartmentalized_component_query.id).count():
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

def get_or_create(session, class_type, **kwargs):
    """gets an object using filter_by on the unique kwargs. If no such object
    is found in the database, a new one will be created which satisfies
    these constraints. This is why every class that wants to use this
    method to be instantiated needs to have a UniqueConstraint defined.
    """

    for constraint in list(class_type.__table_args__):
        if constraint.__class__.__name__ == 'UniqueConstraint':
            unique_cols = constraint.columns.keys()

	inherited_result = True
	if '__mapper_args__' in class_type.__dict__ and 'inherits' in class_type.__mapper_args__:
		inherited_class_type = class_type.__mapper_args__['inherits']
		for constraint in list(inherited_class_type.__table_args__):
			if constraint.__class__.__name__ == 'UniqueConstraint':
				inherited_unique_cols = constraint.columns.keys()

		try: inherited_result = session.query(inherited_class_type).filter_by(**{k: kwargs[k] for k in inherited_unique_cols}).first()
		except: None

    try: result = session.query(class_type).filter_by(**kwargs).first()
    except: result = session.query(class_type).filter_by(**{k: kwargs[k] for k in unique_cols}).first()

    if not result or not inherited_result:
        result = class_type(**kwargs)
        session.add(result)
        session.commit()

    return result

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
    
    dict = {}
    with open("model-genome.txt") as file:
        for line in file:
            modelinfo = line.split(',')
            templist = []
            templist.append(modelinfo[1])
            templist.append(modelinfo[2].strip('\n'))
            dict[modelinfo[0]] = templist
    modelObjectList = []
    session = Session()
    for m in dict.keys():
        if(m == 'Recon'):
            m = 'model'
        if session.query(Model).filter(Model.biggid == m).count()>0:
            print "model name is already taken and or is already loaded"
        elif(m=='Ecoli_core_model'):
            modelObjectList.append(models.load_model('E_coli_core'))  
        else:   
            modelObjectList.append(models.load_model(m))
    
    with create_Session() as session:
        with open("genbanklist.txt") as file:
            for line in file:
                load_genomes(line.strip('\n'))
        IndependentObjects().loadModels(modelObjectList, session, dict)
        IndependentObjects().loadComponents(modelObjectList,session)
        IndependentObjects().loadCompartments(modelObjectList, session)
        DependentObjects().loadCompartmentalizedComponent(modelObjectList, session)
        IndependentObjects().loadReactions(modelObjectList, session)
        DependentObjects().loadModelGenes(modelObjectList, session)
        DependentObjects().loadModelCompartmentalizedComponent(modelObjectList, session)
        DependentObjects().loadModelReaction(modelObjectList, session)
        DependentObjects().loadGPRMatrix(modelObjectList, session)
        DependentObjects().loadReactionMatrix(modelObjectList, session)
        #DependentObjects().loadEscher(session)
        
if __name__ == '__main__':
    run_program()
