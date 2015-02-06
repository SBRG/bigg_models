from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import Session
from sqlalchemy.ext.declarative import declarative_base

import pytest
from sqlalchemy.orm import sessionmaker, aliased
from sqlalchemy import create_engine, desc, func, or_
import sys

from ome.models import *
from ome.base import GenomeRegion, Session


#delete rows in models
#TRUNCATE model CASCADE;

"""
GENE
"""

def addGene(long_name, locus_id, gene_name, leftpos, rightpos, ncbi, strand, info=None, synonyms = None):
    session = Session()
    ome_gene = {}
    try: chromosome = session.query(Chromosome).filter(Chromosome.ncbi_id == ncbi).one()
    except: 
        raise Exception("genbank file does not exist in database or there is more than one")
    ome_gene['long_name'] = long_name
    ome_gene['locus_id'] = locus_id
    ome_gene['name'] = gene_name
    ome_gene['strand'] = strand
    ome_gene['leftpos'] = leftpos
    ome_gene['rightpos'] = rightpos
    ome_gene['chromosome_id'] = chromosome.id
    if info is not None:
        ome_gene['info'] = info
    if not session.query(Gene).filter(Gene.long_name == long_name, Gene.locus_id == locus_id, Gene.name == gene_name, Gene.strand == strand, Gene.leftpos == leftpos, Gene.rightpos == rightpos).count():
        gene = Gene(**ome_gene)
        session.add(gene)
        session.commit()
        return gene
    else:
        return session.query(Gene).filter(Gene.long_name == long_name, Gene.locus_id == locus_id, Gene.name == gene_name, Gene.strand == strand, Gene.leftpos == leftpos, Gene.rightpos == rightpos).one()
    
#addGene("X", "x11", "testing", 12, 123, "AE000512.1", "+") 

def updateGene(geneId, geneDict = None, genomeRegionDict = None):
    session = Session()
    try: gene = session.query(Gene).filter(Gene.id == geneId).one()
    except:
        print "gene does not exist in database"
        raise Exception 
    if geneDict is not None and geneDict:
        session.query(Gene).filter(Gene.id == geneId).update(geneDict)
        session.commit()
        session.close()
    if genomeRegionDict is not None and genomeRegionDict:
        session.query(GenomeRegion).filter(GenomeRegion.id == geneId).update(genomeRegionDict)
        session.commit()
        session.close()

#updateGene(2707975, {'long_name':'nothing'}, {'name': 'testing2'})

def deleteGene(geneId):
    session = Session()
    try: gene = session.query(Gene).filter(Gene.id == geneId).one()
    except:
        print "gene does not exist in database"
        raise
    session.delete(gene)
    session.commit()
    session.close()
    
#def deleteGPRMatrix(geneId, reactionId):
#def deleteModelGene(modelId, geneId):

"""
METABOLITE
"""

def addMetabolite(name, long_name, kegg_id, cas_number, seed, chebi, metacyc, upa, brenda, formula):
    session = Session()
    if not session.query(Metabolite).filter(Metabolite.name == name).filter(Metabolite.formula == formula).filter(Metabolite.kegg_id == kegg_id).count():
        metabolite = Metabolite(name = name,
                                long_name = component.name,
                                kegg_id = kegg_id,
                                cas_number = cas_number,
                                seed = seed, 
                                chebi = chebi, 
                                metacyc = metacyc,
                                upa = upa, 
                                brenda = brenda,
                                formula = str(component.formula),
                                flag = bool(kegg_id))
        session.add(metabolite)
        session.commit()
        session.close()
        return metabolite
    else:
        print "metabolite already in database"
    
def updateMetabolite(metaboliteId, metaboliteDict = None):
    session = Session()
    try: metabolite = session.query(Metabolite).filter(Metabolite.id == metaboliteId).one()
    except:
        print "metabolite does not exist in database"
        raise
    if metaboliteDict is not None and metaboliteDict:
        session.query(Metabolite).filter(Metabolite.id == metaboliteId).update(metaboliteDict)
        session.commit()
        session.close()
        
def deleteMetabolite(metaboliteId):
    session = Session()
    try: metabolite = session.query(Metabolite).filter(Metabolite.id == metaboliteId).one()
    except:
        print "metabolite does not exist in database"
        raise
    session.delete(metabolite)
    session.commit()
    session.close()
    
#deleteMetabolite(1984204)

"""
MODEL
"""

def addModel(biggId, firstCreated, genomeId, notes = None):
    session = Session()
    if not session.query(Model).filter(Model.bigg_id == biggId).count():
        model = Model(bigg_id = biggId, first_created = firstCreated, genome_id = genomeId, notes =notes)
        session.add(model)
        session.commit()
        session.close()
        return model
    else:
        print "model already in database"
        
def updateModel(modelId, modelDict=None):
    session = Session()
    try: model = session.query(Model).filter(Model.id == modelId).one()
    except:
        print "model does not exist in database"
        raise
    if modelDict is not None and modelDict:
        session.query(Model).filter(Model.id == modelId).update(modelDict)
        session.commit()
        session.close()

def deleteModel(modelId):
    session = Session()
    try: model = session.query(Model).filter(Model.id == modelId).one()
    except:
        print "model does not exist in database"
        raise
    session.delete(model)
    session.commit()
    session.close()
    
"""
REACTION
"""
    
def addReaction(name, long_name, type, notes):
    session = Session()
    if not session.query(Reaction).filter(Reaction.id == reactionId).count():
        reaction = Reaction(name = name, long_name = long_name, type = type, notes = notes)
        session.add(reaction)
        session.commit()
        session.close()
        return reaction

def updateReaction(reactionId, reactionDict=None):
    session = Session()
    try: reaction = session.query(Reaction).filter(Reaction.id == reactionId).one()
    except:
        print "reaction does not exist in database"
        raise
    if reactionDict is not None and reactionDict:
        session.query(Reaction).filter(Reaction.id == reactionId).update(reactionDict)
        session.commit()
        session.close()
        
def deleteReaction(reactionId):
    session = Session()
    try: reaction = session.query(Reaction).filter(Reaction.id == reactionId).one()
    except:
        print "reaction does not exist in database"
        raise
    session.delete(reaction)
    session.commit()
    session.close()
    
"""
Model Gene
"""
       
def addModelGene(modelId, geneId):
    session = Session()
    try: model = session.query(Model).filter(Model.id == modelId).one()
    except:
        print "model does not exist in database"
        raise
    try: gene = session.query(Gene).filter(Gene.id == geneId).one()
    except:
        print "gene does not exist in database"
        raise
    modelgene = ModelGene(model_id = model.id, gene_id = gene.id)
    session.add(modelgene)
    session.commit()
    session.close()
    return modelgene
    
def deleteModelGene(modelId, geneId):
    session = Session()
    try: mg = session.query(ModelGene).filter(ModelGene.model_id == modelId).filter(ModelGene.gene_id == geneId).one()
    except: 
        print "model gene does not exist in database"
        raise
    session.delete(mg)
    session.commit()
    session.close()
    
"""
GPRMatrix
"""
    
def addGPRMatrix(geneId, reactionId):
    session = Session()
    try: gene = session.query(Gene).filter(Gene.id == geneId).one()
    except:
        print "gene does not exist in database"
        raise
    try: reaction = session.query(Reaction).filter(Reaction.id == reactionId).one()
    except: 
        print "reaction does not exist in database"
        raise
    GPRMatrix = GPRMatrix(gene_id = gene.id, reaction_id = reaction.id)
    session.add(GPRMatrix)
    session.commit()
    session.close()
    return GPRMatrix
    
def deleteGPRMatrix(geneId, reactionId):
    session = Session()
    try: GPRMatrix = session.query(GPRMatrix).filter(GPRMatrix.gene_id == geneId).filter(GPRMatrix.reaction_id == reactionId).one()
    except:
        print "gene product rule does not exist in database"
        raise
    session.delete(GPRMatrix)
    session.commit()
    session.close()
    
"""
Model Reaction
"""

def addModelReaction(modelId, reactionId):
    session = Session()
    if not session.query(ModelReaction).filter(ModelReaction.model_id == modelId).filter(ModelReaction.reaction_id == reactionId).count():
        try: model = session.query(Model).filter(Model.id == modelId).one()
        except:
            print "model does not exist in database"
            raise
        try: reaction = session.query(Reaction).filter(Reaction.id == reactionId).one()
        except: 
            print "reaction does not exist in database"
            raise
        
        mr = ModelReaction(model_id = model.id, reaction_id = reaction.id)
        session.add(mr)
        session.commit()
        session.close()
        return mr
        
def deleteModelReacton(modelId, reactionId):
    session = Session()
    try: mr = session.query(ModelReaction).filter(ModelReaction.reaction_id == reactionId).filter(ModelReaction.model_id == modelId).one()
    except:
        print "model reaction does not exist in database"
        raise
    session.delete(mr)
    session.commit()
    session.close()
    
"""
Reaction Matrix
"""
    
def addReactionMatrix(reactionId, compartmentalizedComponentId):
    session = Session()
    if not session.query(ReactionMatrix).filter(ReactionMatrix.reaction_id == reactionId).filter(ReactionMatrix.compartmentalized_component_id == compartmentalizedComponentId).count():
        try: cc = session.query(CompartmentalizedComponent).filter(cc.id == compartmentalizedComponentId).one()
        except:
            print "compartmentalized component does not exist in database"
            raise
        try: reaction = session.query(Reaction).filter(Reaction.id == reactionId).one()
        except: 
            print "reaction does not exist in database"
            raise
        rm = ReactionMatrix(reaction_id = reaction.id, compartmentalized_component_id = cc.id)
        session.add(rm)
        session.commit()
        session.close()
        return rm
          
def deleteReactionMatrix(reactionId, compartmentalizedComponentId):
    session = Session()
    try: rm = session.query(ReactionMatrix).filter(ReactionMatrix.reaction_id == reactionId).filter(ReactionMatrix.compartmentalizedComponentId == compartmentalizedComponentId).one()
    except:
        print "reaction matrix does not exist in database"
        raise
    session.delete(rm)
    session.commit()
    session.close()

"""
Compartmentalized Component
"""

def addCompartmentalizedComponent(componentId, compartmentId):
    session = Session()
    if not session.query(CompartmentalizedComponent).filter(CompartmentalizedComponent.component_id == componentId).filter(CompartmentalizedComponent.compartment_id == compartmentId).count():
        try: component = session.query(Component).filter(Component.id == componentId).one()
        except:
            print "model does not exist in database"
            raise
        try: compartment = session.query(Compartment).filter(Compartment.id == compartmentId).one()
        except: 
            print "compartment does not exist in database"
            raise
        cc = CompartmentalizedComponent(component_id = component.id, compartment_id = compartment.id)
        session.add(cc)
        session.commit()
        session.close()
        return cc
        
def deleteCompartmentalizedComponent(componentId, compartmentId):
    session = Session()
    try: cc = session.query(CompartmentalizedComponent).filter(CompartmentalizedComponent.component_id == componentId).filter(CompartmentalizedComponent.compartment_id == compartmentId).one()
    except:
        print "compartmentalized component does not exist in database"
        raise
    session.delete(cc)
    session.commit()
    session.close()
        
"""
Model Compartmentalized Component
"""

def addModelCompartmentalizedComponent(modelId, compartmentalizedComponentId, compartmentId):
    session = Session()
    if not session.query(ModelCompartmentalizedComponent).filter(ModelCompartmentalizedComponent.model_id == modelId).filter(ModelCompartmentalizedComponent.compartmentalized_component_id == compartmentalizedComponentId).filter(ModelCompartmentalizedComponent.compartment_id == compartmentId).count():
        try: model = session.query(Model).filter(Model.id == modelId).one()
        except:
            print "model does not exist in database"
            raise
        try: cc = session.query(CompartmentalizedComponent).filter(CompartmentalizedComponent.id == compartmentalizedComponentId).one()
        except: 
            print "compartmentalized component does not exist in database"
            raise
        try: compartment = session.query(Compartment).filter(Compartment.id == compartmentId).one()
        except: 
            print "compartment does not exist in database"
            raise
        mcc = ModelCompartmentalizedComponent(model_id = model.id, compartmentalized_component_id = cc.id, compartment_id = compartment.id)
        session.add(mcc)
        session.commit()
        session.close()
        return mcc

def deleteModelCompartmentalizedComponent(modelId, compartmentId, compartmentalizedComponentId):
    session = Session()
    try: mcc = session.query(ModelCompartmentalizedComponent).filter(ModelCompartmentalizedComponent.compartmentalized_component_id == compartmentalizedComponentId).filter(ModelCompartmentalizedComponent.model_id == modelId).filter(ModelCompartmentalizedComponent.compartment_id == compartmentId).one()
    except:
        print "model compartmentalized component does not exist in database"
        raise
    session.delete(mcc)
    session.commit()
    session.close()
    
"""
Compartment    
"""

def addCompartment(name):
    session = Session()
    if session.query(Compartment).filter(Compartment.name == name).count() == 1:
        print "already exists in database"
    else:
        compartment = Compartment(name = name)
        session.add(compartment)
        session.commit()
        session.close()
               
def deleteCompartment(compartmentId):
    session = Session()
    try: c = session.query(Comparmtnet).filter(Compartment.id == compartmentId).one()
    except:
        print "compartment does not exist in database"
        raise
    session.delete(c)
    session.commit()
    session.close()
    
def refreshModelCount(modelId):
    session = Session()
    metabolite_count = (session
            .query(func.count(ModelCompartmentalizedComponent.id))
            .filter(ModelCompartmentalizedComponent.model_id == modelId)
            .scalar())
    
    reaction_count = (session.query(func.count(ModelReaction.id))
        .filter(ModelReaction.model_id == modelId)
        .scalar())
    
    gene_count = (session.query(func.count(ModelGene.id))
                .filter(ModelGene.model_id == modelId)       
                .scalar())
    session.query(ModelCount).filter(ModelCount.model_id == modelId).update({ModelCount.gene_count : gene_count, ModelCount.metabolite_count : metabolite_count, ModelCount.reaction_count : reaction_count})
    session.commit()
    session.close()

if __name__ == '__main__':
    for model_id in session.query(Model.id).all():
        refreshModelCount(model_id)
