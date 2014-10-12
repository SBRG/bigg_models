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
        """
            if(model.id == 'iSF1195'):
                modelObject = Model(biggid = model.id, firstcreated = '2014-9-16 14:26:22', genome_id = 7)
            if(model.id == 'iSB619'):
                modelObject = Model(biggid = model.id, firstcreated = '2013-10-21 14:26:22', genome_id = 3)
            if(model.id == 'iJN746'):
                modelObject = Model(biggid = model.id, firstcreated = '2013-10-21 14:26:22', genome_id = 6)
            if(model.id == 'iIT341'):
                modelObject = Model(biggid = model.id, firstcreated = '2013-10-21 14:26:22', genome_id = 4)
            if(model.id == 'iNJ661'):
                modelObject = Model(biggid = model.id, firstcreated = '2013-10-21 14:26:22', genome_id = 3)
            if(model.id == 'iJO1366'):
                modelObject = Model(biggid = model.id, firstcreated = '2013-10-21 14:26:22', genome_id = 15)  
            if(model.id == 'iAF692'):
                modelObject = Model(biggid = model.id, firstcreated = '2013-10-21 14:26:22', genome_id = 5) 
            if(model.id == 'model'):
                modelObject = Model(biggid = model.id, firstcreated = '2013-10-21 14:26:22', genome_id = 1)
            if(model.id == 'iAPECO1_1312 '):
                
            session.add(modelObject)
        """    
    
    def loadComponents(self, modellist, session):
        for model in modellist:
            for component in model.metabolites:
                metabolite = session.query(Metabolite).filter(Metabolite.name == component.id.split("_")[0])
                #metabolite = session.query(Metabolite).filter(Metabolite.kegg_id == component.notes.get("KEGGID")[0]) 
                if not metabolite.count():
                    if component.notes.get("KEGGID")[0] == '' or component.notes.get("KEGGID")[0]== None:
                        metaboliteObject = Metabolite(name = component.id.split("_")[0], long_name = component.name, kegg_id = component.notes.get("KEGGID")[0], cas_number = component.notes.get("CASNUMBER")[0], formula = component.notes.get("FORMULA1")[0], flag=False)
                    else:
                        metaboliteObject = Metabolite(name = component.id.split("_")[0], long_name = component.name, kegg_id = component.notes.get("KEGGID")[0], cas_number = component.notes.get("CASNUMBER")[0], formula = component.notes.get("FORMULA1")[0], flag=True)
                    session.add(metaboliteObject)
                else:
                    metaboliteObject = metabolite.first()               
                    if metaboliteObject.kegg_id == None or metaboliteObject.kegg_id == '':
                        metaboliteObject.kegg_id = component.notes.get("KEGGID")[0]
                        #metabolite.update({Metabolite.kegg_id: str(component.notes.get("KEGGID"))})
                    if metaboliteObject.cas_number == None or metaboliteObject.cas_number == '':
                        metaboliteObject.cas_number = component.notes.get("CASNUMBER")[0]
                        #metabolite.update({Metabolite.cas_number: str(component.notes.get("CASNUMBER"))})
                    if metaboliteObject.formula == None or metaboliteObject.formula == '':
                        metaboliteObject.formula = component.notes.get("FORMULA1")[0]
                        #metabolite.update({Metabolite.formula: str(component.notes.get("FORMULA1"))})
                                
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
                                    genequery = session.query(Gene).filter(Gene.id == synonymquery.ome_id).first()
                                    genequery.locus_id = gene.id
                            else:
                                print synonymquery.ome_id  
                        else:
                            print gene.id, model.id
                        """
                        print gene.id +' not found!'
pWW0_128 not found!
pWW0_131 not found!
pWW0_097 not found!
pWW0_091 not found!
pWW0_090 not found!
pWW0_093 not found!
pWW0_100 not found!
pWW0_101 not found!
pWW0_102 not found!
pWW0_099 not found!
pWW0_096 not found!
pWW0_095 not found!
pWW0_092 not found!
pWW0_129 not found!
pWW0_130 not found!
pWW0_094 not found!
pWW0_127 not found!
PP_3739 not found!
HP0903 not found!
HP0094 not found!
HP0093 not found!
HP0905 not found!
Rv1755c not found!
Rv2233 not found!
Rv0619 not found!
Rv0618 not found!
Rv2322c not found!
Rv2321c not found!
Mbar_A3662 not found!
MBd0198 not found!
Mbar_A0379 not found!
MBd0274 not found!
MBd0275 not found!
MBd3023 not found!
MBd3024 not found!
MBd4270 not found!
Mbar_A0628 not found!
Mbar_A1948 not found!
MBd3608 not found!
Mbar_A1506 not found!
MBd1413 not found!
Mbar_A3605 not found!
MBd3435 not found!
Mbar_A0991 not found!
MBd1561 not found!
MBd4025 not found!
MBd1438 not found!
Mbar_A3633 not found!
MBd4022 not found!
MBd0933 not found!
MBd3602 not found!
Mbar_A1502 not found!
                        """
                
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
    
    for m in dict.keys():
        if m == 'Recon':
            modelObjectList.append(models.load_model('model'))
        elif(m=='Ecoli_core_model'):
            modelObjectList.append(models.load_model('E_coli_core'))
        else:   
            modelObjectList.append(models.load_model(m))
    
    #for m in models.get_model_list():
    #    modelObjectList.append(models.load_model(m))
    #modelObjectList.append(models.load_model('Recon1'))
    #modelObjectList.append(models.load_model('iSF1195'))
    #modelObjectList.append(models.load_model('iAF1260')) #Escherichia coli str. K-12 substr. MG1655
    #modelObjectList.append(models.load_model('iJO1366'))
    #modelObjectList.append(models.load_model('iJN746'))
    #modelObjectList.append(models.load_model('iIT341'))
    #modelObjectList.append(models.load_model('iNJ661'))
    #modelObjectList.append(models.load_model('iAF692')) There are no gene names. It is all locus ids
    #modelObjectList.append(models.load_model('iSB619'))
    
    with create_Session() as session:
        with open("genbanklist.txt") as file:
            for line in file:
                load_genomes(line.strip('\n'))       
        #component_loading.load_genomes(base, components)
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
