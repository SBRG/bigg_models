from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import Session
from sqlalchemy.ext.declarative import declarative_base

import pytest
from sqlalchemy.orm import sessionmaker, aliased
from sqlalchemy import create_engine, desc, func, or_
import sys
from curation import * 
from ome.models import (Model, Component, Reaction, Compartment, Metabolite, 
                        CompartmentalizedComponent, ModelReaction, ReactionMatrix, 
                        GPRMatrix, ModelCompartmentalizedComponent, ModelGene, Gene, Chromosome)
from ome.base import GenomeRegion

engine = create_engine("postgresql://dbuser@localhost:5432/ome_stage_2")
Session = sessionmaker(bind = engine)
session = Session()


def test_addGene():
    longName = "testLongName"
    locusId = "testID"
    name = "test"
    leftpos = 12
    rightpos = 123
    strand = "+"
    ncbiID = "AE000512.1"
    try: chromosome = session.query(Chromosome).filter(Chromosome.ncbi_id == ncbiID).one()
    except: 
        print "genbank file does not exist in database"
    gene = addGene(longName, locusId, name, leftpos, rightpos, ncbiID, strand) 
    assert session.query(Gene).filter(Gene.long_name == longName).filter(Gene.locus_id ==locusId)\
                                .filter(Gene.name == name).filter(Gene.leftpos == leftpos)\
                                .filter(Gene.rightpos == rightpos).filter(Gene.strand == strand)\
                                .filter(Gene.chromosome_id == chromosome.id).count() == 1
def test_updateGene():
    geneId = 616610
    geneDict = {'info':'test_long_name'}
    genomeRegionDict = {'name' : 'test_name'}
    updateGene(geneId, geneDict, genomeRegionDict)
    for key in geneDict.keys():
        assert session.query(Gene).filter(Gene.id == geneId).first().__dict__[key] == geneDict[key]
    for key in genomeRegionDict.keys():
        assert session.query(Gene).filter(Gene.id == geneId).first().__dict__[key] == genomeRegionDict[key]
      
def test_deleteGene():
    geneId = 616610
    deleteGene(geneId)
    assert session.query(Gene).filter(Gene.id == geneId).count() == 0

def test_addMetabolite():
    name = "test_name"
    long_name = "test_long_name"
    kegg_id = "test_kegg_id"
    cas_number = "test_cas_number"
    seed = "test_seed"
    chebi = "test_chebi"
    metacyc = "test_metacyc"
    upa = "test_upa"
    brenda = "test_brenda"
    formula = "test_formula"
    addMetabolite(name, long_name, kegg_id, cas_number, seed, chebi, metacyc, upa, brenda, formula)
    assert session.query(Metabolite).filter(Metabolite.name == name).filter(Metabolite.long_name == long_name)\
                .filter(Metabolite.kegg_id == kegg_id).filter(Metabolite.cas_number == cas_number).filter(Metabolite.seed == seed).filter(Metabolite.chebi == chebi)\
                .filter(Metabolite.metacyc == metacyc).filter(Metabolite.upa == upa).filter(Metabolite.brenda == brenda).filter(Metabolite.formula == formula).filter(Metabolite.flag == bool(kegg_id)).count() == 1

def test_updateMetabolite():
    metaboliteId = 616610
    metaboliteDict = {'name':'test_update_name', 'long_name':'test_update_long_name'}
    updateMetabolite(metaboliteId, metaboliteDict)
    for key in metaboliteDict.keys():
        assert session.query(Metabolite).filter(Metabolite.id == metaboliteId).first().__dict__[key] == metaboliteDict[key]

def test_deletMetabolite():
    metaboliteId = 1
    deleteMetabolite(metaboliteId)
    assert session.query(Metabolite).filter(Metabolite.id == metaboliteId).count() == 0

def test_addCompartmentalizedComponent():
    compartmentId = 1
    componentId = 1
    addCompartmentalizedComponent(compartmentId, componentId)
    assert session.query(CompartmentalizedComponent).filter(CompartmentalizedComponent.compartmentId ==compartmentId)\
                                                    .filter(CompartmentalizedComponent.componentId == componentId).count() == 1

def test_addReaction():
    name = ""
    long_name = ""
    type = ""
    notes = ""
    addReaction(name, long_name, type, notes)
    assert session.query(Reaction).filter(Reaction.name == name).filter(Reaction.long_name == long_name).filter(Reaction.type == type).filter(Reaction.notes ==notes).count() == 1

def test_updateReaction():
    reactionId = 1
    reactionDict = {'name': 'test_name', 'long_name':'test_long_name', 'type':'test_type', 'notes':'test_notes'}
    updateReaction(reactionId, reactionDict)
    for key in reactionDict.keys():
        assert session.query(Reaction).filter(Reaction.id == reactionId).first().__dict__[key] == reactionDict[key]
        
def test_deleteReaction():
    reactionId = 1
    deleteReaction(reactionId)
    assert session.query(Reaction).filter(Reaction.id == reactionId).count() == 0

def test_addModel():
    biggId = 1
    firstCreated = ""
    genomeId = 1
    notes = "test_notes"
    addModel(biggId, firstCreated, genomeId, notes)
    assert session.query(Model).filter(Model.biggId == biggId).filter(Model.firstCreated == firstCreated).filter(Model.genomeId == genomeId).filter(Model.notes == notes).count() == 1

def test_updateModel():
    modelId = 1
    genomeId = 1
    modelDict = {'notes': 'test_notes', 'genome_id': genomeId, 'firstcreated': ''}
    updateModel(modelId, modelDict)
    for key in modelDict.keys():
        assert session.query(Model).filter(Model.id == modelId).first().__dict__[key] == modelDict[key]
               
def test_deleteModel():
    modelId = 1
    deleteModel(modelId)
    assert session.query(Model).filter(Model.id == modelId).count() == 0


def test_addGPR():
    geneId = 1
    reactionId = 1
    addGPR(geneId, reactionId)
    assert session.query(GPR).filter(GPR.gene_id == geneId).filter(GPR.reaction_id == reactionId).count() == 1

def test_deleteGPR():
    geneId = 1
    reactionId = 1
    deleteGPR(geneId, reactionId)
    assert session.query(GPR).filter(GPR.gene_id == geneId).filter(GPR.reaction_id == reactionId).count() == 0

def test_addReactionMatrix():
    compartmentalizedComponentId = 1
    reactionId = 1
    addReactionMatrix(reactionId, CompartmentalizedComponentId)
    assert session.query(ReactionMatrix).filter(ReactionMatrix.reaction_id == reactionId).filter(ReactionMatrix.compartmentalized_component_id == compartmentalizedComponentId).count() == 1

def test_deleteReactionMatrix():
    compartmentalizedComponentId = 1
    reactionId = 1
    deleteReactionMatrix(reactionId, CompartmentalizedComponentId)
    assert session.query(ReactionMatrix).filter(ReactionMatrix.reaction_id == reactionId).filter(ReactionMatrix.compartmentalized_component_id == compartmentalizedComponentId).count() == 0

def test_addModelReaction():
    modelId = 1
    reactionId = 1
    addModelReaction(modelId, reactionId)
    assert session.query(ModelReaction).filter(ModelReaction.model_id == modelId).filter(ModelReaction.reaction_id == reactionId).count() == 1

def test_deleteModelReaction():
    modelId = 1
    reactionId = 1
    deleteModelReaction(modelId, reactionId)
    assert session.query(ModelReaction).filter(ModelReaction.model_id == modelId).filter(ModelReaction.reaction_id == reactionId).count() == 0

def test_addModelGene():
    modelId = 1
    geneId = 1
    addModelGene(modelId, geneId)
    assert session.query(ModelGene).filter(ModelGene.model_id == modelId).filter(ModelGene.gene_id == geneId).count() == 1
    
def test_deleteModelGene():
    modelId = 1
    geneId = 1
    deleteModelGene(modelId, geneId)
    assert session.query(ModelGene).filter(ModelGene.model_id == modelId).filter(ModelGene.gene_id == geneId).count() == 0

def test_addModelCompartmentalizedComponent():
    modelId = 1
    compartmentalizedComponentId = 1
    addModelCompartmentalizedComponent(modelId, compartmentalizedComponentId)
    assert session.query(ModelCompartmentalizedComponent).filter(ModelCompartmentalizedComponent.model_id == modelId)\
                                                        .filter(ModelCompartmentalizedComponent.compartmentalized_component_id == compartmentalizedComponentId).count() == 1

def test_deleteModelCompartmentalizedComponent():
    modelId = 1
    compartmentalizedComponentId = 1
    deleteModelCompartmentalizedComponent(modelId, compartmentalizedComponentId)
    assert session.query(ModelCompartmentalizedComponent).filter(ModelCompartmentalizedComponent.model_id == modelId)\
                                                        .filter(ModelCompartmentalizedComponent.compartmentalized_component_id == compartmentalizedComponentId).count() == 0
