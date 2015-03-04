from ome.models import *
from ome.loading.model_loading import parse

from sqlalchemy import func
from sqlalchemy import desc, func, or_, and_
from collections import defaultdict

class NotFoundError(Exception):
    pass

# Reactions
def get_reaction_and_models(reaction_bigg_id, session):
    result_db = (session
                 .query(Reaction.bigg_id,
                        Reaction.name,
                        Model.bigg_id,
                        Genome.organism)
                 .join(ModelReaction, ModelReaction.reaction_id == Reaction.id)
                 .join(Model, Model.id == ModelReaction.model_id)
                 .join(Genome, Genome.id == Model.genome_id)
                 .filter(Reaction.bigg_id == reaction_bigg_id)
                 .all())
    if len(result_db) == 0:
        raise NotFoundError('Could not find reaction')

    db_link_results = get_db_links_for_reaction(reaction_bigg_id, session)

    return {'bigg_id': result_db[0][0],
            'name': result_db[0][1],
            'database_links': db_link_results,
            'models_containing_reaction': [{'bigg_id': x[2], 'organism': x[3]}
                                           for x in result_db]}
    
def get_reactions_for_model(model_bigg_id, session):
    result_db = (session
                 .query(Reaction.bigg_id)
                 .join(ModelReaction, ModelReaction.reaction_id == Reaction.id)
                 .join(Model, Model.id == ModelReaction.model_id)
                 .filter(Model.bigg_id == model_bigg_id)
                 .all())
    return [x[0] for x in result_db]

def get_model_reaction(model_bigg_id, reaction_bigg_id, session):
    result_db = (session
                 .query(Reaction.bigg_id,
                        Reaction.name,
                        Model.bigg_id,
                        ModelReaction.gene_reaction_rule,
                        ModelReaction.lower_bound,
                        ModelReaction.upper_bound,
                        ModelReaction.objective_coefficient)
                 .join(ModelReaction, ModelReaction.reaction_id == Reaction.id)
                 .join(Model, Model.id == ModelReaction.model_id)
                 .filter(Model.bigg_id == model_bigg_id)
                 .filter(Reaction.bigg_id == reaction_bigg_id)
                 .first())
    if result_db is None:
        raise NotFoundError('ModelReaction not found')

    # metabolites:
    metabolite_db = get_metabolite_list_for_reaction(reaction_bigg_id, session)
    gene_db = get_gene_list_for_model_reaction(model_bigg_id, reaction_bigg_id,
                                               session)
    model_db = get_model_list_for_reaction(reaction_bigg_id, session)
    model_result = [x for x in model_db if x != model_bigg_id]

    # database_links
    db_link_results = get_db_links_for_reaction(reaction_bigg_id, session)
    
    # escher maps
    escher_maps = get_escher_maps_for_reaction(reaction_bigg_id, model_bigg_id, session)
    
    return {'bigg_id': result_db[0],
            'name': result_db[1],
            'model_bigg_id': result_db[2],
            'gene_reaction_rule': result_db[3],
            'lower_bound': result_db[4],
            'upper_bound': result_db[5],
            'objective_coefficient': result_db[6],
            'metabolites': metabolite_db,
            'genes': gene_db,
            'database_links': db_link_results,
            'other_models_with_reaction': model_result,
            'escher_maps': escher_maps}
        
def get_reaction(reaction_bigg_id, session):
    return (session
            .query(Reaction)
            .filter(Reaction.bigg_id == reaction_bigg_id)
            .first())
    
# Models
def get_model_list_and_counts(session):
    model_db = (session
                .query(Model, ModelCount, Genome)
                .join(ModelCount, ModelCount.model_id == Model.id)
                .join(Genome, Genome.id == Model.genome_id)
                .order_by(Model.bigg_id)
                .all())
    return_dict = [{'bigg_id': x[0].bigg_id,
                    'organism': x[2].organism,
                    'metabolite_count': x[1].metabolite_count,
                    'reaction_count': x[1].reaction_count,
                    'gene_count': x[1].gene_count}
                   for x in model_db]
    return return_dict
    
def get_model_list_for_reaction(reaction_bigg_id, session):
    result = (session
              .query(Model.bigg_id)
              .join(ModelReaction, ModelReaction.model_id == Model.id)
              .join(Reaction, Reaction.id == ModelReaction.reaction_id)
              .filter(Reaction.bigg_id == reaction_bigg_id)
              .all())
    return [x[0] for x in result]

def get_model_list_for_metabolite(metabolite_bigg_id, session):
    result = (session
              .query(Model.bigg_id, Compartment.bigg_id)
              .join(ModelCompartmentalizedComponent)
              .join(CompartmentalizedComponent)
              .join(Compartment)
              .join(Metabolite)
              .filter(Metabolite.bigg_id == metabolite_bigg_id)
              .all())
    return [{'bigg_id': x[0], 'compartment_bigg_id': x[1]} for x in result]

def get_model_list(session):
    model_list = (session
                  .query(Model.bigg_id)
                  .order_by(Model.bigg_id)
                  .all())
    list = [x[0] for x in model_list]
    list.sort()
    return list

def get_model_and_counts(model_bigg_id, session):
    model_db = (session
                .query(Model, ModelCount, Genome)
                .join(ModelCount, ModelCount.model_id == Model.id)
                .join(Genome, Genome.id == Model.genome_id)
                .filter(Model.bigg_id == model_bigg_id)
                .first())
    return_dict = {'bigg_id': model_db[0].bigg_id,
                   'organism': model_db[2].organism,
                   'metabolite_count': model_db[1].metabolite_count,
                   'reaction_count': model_db[1].reaction_count,
                   'gene_count': model_db[1].gene_count}
    return return_dict
        
# Metabolites
def get_metabolites_for_model(model_bigg_id, session):
    result_db = (session
                 .query(Metabolite.bigg_id, Compartment.bigg_id, Model.bigg_id)
                 .join(CompartmentalizedComponent)
                 .join(ModelCompartmentalizedComponent)
                 .join(Model)
                 .filter(CompartmentalizedComponent.compartment_id == Compartment.id)
                 .filter(Model.bigg_id == model_bigg_id)
                 .all())
    return [{'bigg_id': x[0], 'compartment_bigg_id': x[1], 'model_bigg_id': x[2]}
            for x in result_db]

def get_metabolite_list_for_reaction(reaction_id, session):
    result_db = (session
                 .query(Metabolite.bigg_id,
                        ReactionMatrix.stoichiometry,
                        Compartment.bigg_id,
                        Metabolite.name)
                 # Metabolite -> ReactionMatrix
                 .join(CompartmentalizedComponent,
                       CompartmentalizedComponent.component_id == Metabolite.id)
                 .join(ReactionMatrix,
                       ReactionMatrix.compartmentalized_component_id == CompartmentalizedComponent.id)
                 # -> Reaction> Model
                 .join(Reaction,
                       Reaction.id == ReactionMatrix.reaction_id)
                 # -> Compartment
                 .join(Compartment,
                       Compartment.id == CompartmentalizedComponent.compartment_id)
                 # filter
                 .filter(Reaction.bigg_id == reaction_id)
                 .all())
    return [{'bigg_id': x[0], 'stoichiometry': x[1], 'compartment_bigg_id': x[2],
             'name': x[3]} for x in result_db]
    
def get_metabolite(met_bigg_id, session):
    result_db = (session
                 .query(Metabolite.bigg_id,
                        Metabolite.name,
                        Metabolite.formula)
                 .filter(Metabolite.bigg_id == met_bigg_id)
                 .first())
    comp_comp_db = (session
                    .query(Compartment.bigg_id, Model.bigg_id, Genome.organism)
                    .join(CompartmentalizedComponent)
                    .join(ModelCompartmentalizedComponent)
                    .join(Model)
                    .join(Genome, Genome.id == Model.genome_id)
                    .join(Metabolite)
                    .filter(Metabolite.bigg_id == met_bigg_id)
                    .all())
    db_link_results = get_db_links_for_metabolite(met_bigg_id, session)

    return {'bigg_id': result_db[0],
            'name': result_db[1],
            'formula': result_db[2],
            'database_links': db_link_results,
            'compartments_in_models': [{'bigg_id': c[0], 'model_bigg_id': c[1], 'organism': c[2]}
                                       for c in comp_comp_db]}

def get_model_comp_metabolite(met_bigg_id, compartment_bigg_id, model_bigg_id,
                              session):
    result_db = (session
                 .query(Metabolite.bigg_id,
                        Metabolite.name,
                        Compartment.bigg_id,
                        Model.bigg_id,
                        Metabolite.formula)
                 .join(CompartmentalizedComponent)
                 .join(Compartment)
                 .join(ModelCompartmentalizedComponent)
                 .join(Model)
                 .filter(Metabolite.bigg_id == met_bigg_id)
                 .filter(Compartment.bigg_id == compartment_bigg_id)
                 .filter(Model.bigg_id == model_bigg_id)
                 .first())
    reactions_db = (session
                    .query(Reaction.bigg_id, Reaction.name, Model.bigg_id)
                    .join(ReactionMatrix)
                    .join(CompartmentalizedComponent)
                    .join(Metabolite)
                    .join(ModelReaction)
                    .join(Model)
                    .filter(Metabolite.bigg_id == met_bigg_id)
                    .filter(Model.bigg_id == model_bigg_id)
                    .all())
    model_db = get_model_list_for_metabolite(met_bigg_id, session)
    escher_maps = get_escher_maps_for_metabolite(met_bigg_id,
                                                 compartment_bigg_id,
                                                 model_bigg_id, session)
    model_result = [x for x in model_db if x['bigg_id'] != model_bigg_id]

    db_link_results = get_db_links_for_metabolite(met_bigg_id, session)

    return {'bigg_id': result_db[0],
            'name': result_db[1],
            'compartment_bigg_id': result_db[2],
            'model_bigg_id': result_db[3],
            'formula': result_db[4],
            'database_links': db_link_results,
            'reactions': [{'bigg_id': r[0], 'name': r[1], 'model_bigg_id': r[2]}
                          for r in reactions_db],
            'escher_maps': escher_maps,
            'other_models_with_metabolite': model_result}
    
# Genes
def get_gene_list_for_model(model_bigg_id, session):
    result = (session
              .query(Gene.bigg_id)
              .join(ModelGene)
              .join(Model)
              .filter(Model.bigg_id == model_bigg_id)
              .all())
    return [x[0] for x in result]
    
def get_gene_list_for_model_reaction(model_bigg_id, reaction_id, session):
    result_db = (session
                 .query(Gene.bigg_id, Gene.name)
                 .join(ModelGene, ModelGene.gene_id == Gene.id)
                 .join(GeneReactionMatrix, GeneReactionMatrix.model_gene_id == ModelGene.id)
                 .join(ModelReaction, ModelReaction.id == GeneReactionMatrix.model_reaction_id)
                 .join(Reaction, Reaction.id == ModelReaction.reaction_id)
                 .join(Model, Model.id == ModelReaction.model_id)
                 .filter(Model.bigg_id == model_bigg_id)
                 .filter(Reaction.bigg_id == reaction_id)
                 .all())
    return [{'bigg_id': x[0], 'name': x[1]}
            for x in result_db]
    
def get_model_gene(gene_bigg_id, model_bigg_id, session):
    result_db = (session
                 .query(Gene.bigg_id,
                        Gene.name,
                        Gene.info,
                        Gene.leftpos,
                        Gene.rightpos,
                        Model.bigg_id)
                 .join(ModelGene)
                 .join(Model)
                 .filter(Gene.bigg_id == gene_bigg_id)
                 .filter(Model.bigg_id == model_bigg_id)
                 .first())
    reaction_db = (session
                   .query(Reaction.bigg_id,
                          ModelReaction.gene_reaction_rule,
                          Reaction.name)
                   .join(ModelReaction, ModelReaction.reaction_id == Reaction.id)
                   .join(Model, Model.id == ModelReaction.model_id)
                   .join(GeneReactionMatrix, GeneReactionMatrix.model_reaction_id == ModelReaction.id)
                   .join(ModelGene, ModelGene.id == GeneReactionMatrix.model_gene_id)
                   .join(Gene, Gene.id == ModelGene.gene_id)
                   .filter(Model.bigg_id == model_bigg_id)
                   .filter(Gene.bigg_id == gene_bigg_id)
                   .all())
    reaction_results = [{'bigg_id': r[0], 'gene_reaction_rule': r[1],
                         'name': r[2]} for r in reaction_db]

    return {'bigg_id': result_db[0],
            'name': result_db[1],
            'info': result_db[2],
            'leftpos': result_db[3],
            'rightpos': result_db[4],
            'model_bigg_id': result_db[5],
            'reactions': reaction_results}

# database_links
def compile_db_links(results, link_type=None):
    pretty_names = {'KEGGID': 'KEGG',
                    'CASNUMBER': 'CAS',
                    'METACYC': 'MetaCyc',
                    'CHEBI': 'ChEBI',
                    'REACTOME': 'Reactome',
                    'BIOPATH': 'BioPath'}
                    
    links = {'KEGGID': 'http://www.genome.jp/dbget-bin/www_bget?cpd:',
             'UPA': 'http://www.grenoble.prabi.fr/obiwarehouse/unipathway/upc?upid=',
             'CHEBI': 'http://www.ebi.ac.uk/chebi/searchId.do?chebiId=',
             'REACTOME': 'http://www.reactome.org/cgi-bin/instancebrowser?ID=',
             'BIOPATH': 'http://www.molecular-networks.com/biopath3/biopath/mols/'}
    if link_type == 'metabolite':
        links['METACYC'] = 'http://metacyc.org/META/NEW-IMAGE?type=COMPOUND&object='
        links['SEED'] = 'http://seed-viewer.theseed.org/seedviewer.cgi?page=CompoundViewer&compound='
        links['BIOPATH'] = 'http://www.molecular-networks.com/biopath3/biopath/mols/'
        links['HMDB'] = 'http://www.hmdb.ca/metabolites/'
    elif link_type == 'reaction':
        links['BIOPATH'] = 'http://www.molecular-networks.com/biopath3/biopath/rxn/'
    else:
        links['METACYC'] = 'http://metacyc.org/META/NEW-IMAGE?object='

    sources = defaultdict(list)
    for r in results:
        try:
            name = pretty_names[r[0]]
        except KeyError:
            name = r[0]
        try:
            link = links[r[0]] + r[1]
        except KeyError:
            link = None
        sources[name].append({'link': link, 'id': r[1]})
    return sources

def get_db_links_for_reaction(reaction_bigg_id, session):
    result_db = (session
                 .query(LinkOut.external_source, LinkOut.external_id)
                 .join(Reaction, Reaction.id == LinkOut.ome_id)
                 .filter(LinkOut.type == 'reaction')
                 .filter(Reaction.bigg_id == reaction_bigg_id)
                 .all())
    return compile_db_links(result_db, link_type='reaction')

def get_db_links_for_metabolite(met_bigg_id, session):
    result_db = (session
                 .query(LinkOut.external_source, LinkOut.external_id)
                 .join(Metabolite, Metabolite.id == LinkOut.ome_id)
                 .filter(LinkOut.type == 'metabolite')
                 .filter(Metabolite.bigg_id == met_bigg_id)
                 .all())
    return compile_db_links(result_db, link_type='metabolite')

# utilities
def build_reaction_string(metabolitelist, lower_bound, upper_bound):
    post_reaction_string = ""
    pre_reaction_string = ""
    for met in metabolitelist:
        if float(met['stoichiometry']) < 0:
            if float(met['stoichiometry'])!= -1:
                pre_reaction_string += "{0:.1f}".format(abs(met['stoichiometry'])) + \
                                       " " + met['bigg_id']+"_"+met['compartment_bigg_id'] + " + "
            else:
                pre_reaction_string += " " + met['bigg_id']+"_"+met['compartment_bigg_id'] + " + "
        if float(met['stoichiometry'])>0:
            if float(met['stoichiometry'])!= 1:
                post_reaction_string += "{0:.1f}".format(abs(met['stoichiometry'])) + " " + \
                                        met['bigg_id']+"_"+met['compartment_bigg_id'] + " + "
            else:
                post_reaction_string += " " + met['bigg_id']+"_"+met['compartment_bigg_id'] + " + "

    if len(metabolitelist) == 1:
        reaction_string = pre_reaction_string[:-2] + " &#8652; " + post_reaction_string[:-2]
    elif lower_bound <0 and upper_bound <=0:
        reaction_string = pre_reaction_string[:-2] + " &#10229; " + post_reaction_string[:-2]
    elif lower_bound >= 0:
        reaction_string = pre_reaction_string[:-2] + " &#10230; " + post_reaction_string[:-2]
    else:
        reaction_string = pre_reaction_string[:-2] + " &#8652; " + post_reaction_string[:-2]

    return reaction_string
    
# Escher maps
def get_escher_maps_for_reaction(reaction_bigg_id, model_bigg_id, session):
    result_db = (session
                 .query(EscherMap.map_name, EscherMapMatrix.escher_map_element_id)
                 .join(EscherMapMatrix,
                       EscherMapMatrix.escher_map_id == EscherMap.id)
                 .join(ModelReaction,
                       ModelReaction.id == EscherMapMatrix.ome_id)
                 .join(Model,
                       Model.id == ModelReaction.model_id)
                 .join(Reaction,
                       Reaction.id == ModelReaction.reaction_id)
                 .filter(Reaction.bigg_id == reaction_bigg_id)
                 .filter(Model.bigg_id == model_bigg_id)
                 .order_by(EscherMap.priority.desc())
                 .all())
    return [{'map_name': x[0], 'element_id': x[1]} for x in result_db]

def get_escher_maps_for_metabolite(metabolite_bigg_id, compartment_bigg_id,
                                   model_bigg_id, session):
    result_db = (session
                 .query(EscherMap.map_name, EscherMapMatrix.escher_map_element_id)
                 .join(EscherMapMatrix,
                       EscherMapMatrix.escher_map_id == EscherMap.id)
                 .join(ModelCompartmentalizedComponent,
                       ModelCompartmentalizedComponent.id == EscherMapMatrix.ome_id)
                 .join(Model,
                       Model.id == ModelCompartmentalizedComponent.model_id)
                 .join(CompartmentalizedComponent,
                       CompartmentalizedComponent.id == ModelCompartmentalizedComponent.compartmentalized_component_id)
                 .join(Metabolite,
                       Metabolite.id == CompartmentalizedComponent.component_id)
                 .join(Compartment,
                       Compartment.id == CompartmentalizedComponent.compartment_id)
                 .filter(Metabolite.bigg_id == metabolite_bigg_id)
                 .filter(Compartment.bigg_id == compartment_bigg_id)
                 .filter(Model.bigg_id == model_bigg_id)
                 .order_by(EscherMap.priority.desc())
                 .all())
    return [{'map_name': x[0], 'element_id': x[1]} for x in result_db]
    
def json_for_map(map_name, session):
    result_db = (session
                 .query(EscherMap.map_data)
                 .filter(EscherMap.map_name == map_name)
                 .first())
    if result_db is None:
        raise NotFoundError('Could not find Escher map %s' % map_name)

    return result_db[0].decode('utf8')
    
# search
name_sim_cutoff = 0.3
bigg_id_sim_cutoff = 0.5
gene_bigg_id_sim_cutoff = 1.0
organism_sim_cutoff = 0.3

def search_for_genes(query_string, session, limit_models=None):
    # genes by bigg_id
    sim_bigg_id = func.similarity(Gene.bigg_id, query_string)
    sim_name = func.similarity(Gene.name, query_string)
    qu = (session
          .query(Gene.bigg_id, Model.bigg_id, Gene.name, sim_bigg_id)
          .join(ModelGene)
          .join(Model)
          .filter(or_(sim_bigg_id >= gene_bigg_id_sim_cutoff,
                      and_(sim_name >= name_sim_cutoff,
                           Gene.name != '')))
          .order_by(sim_bigg_id.desc(), sim_name.desc()))
    if limit_models:
        qu = qu.filter(Model.bigg_id.in_(limit_models))
    result_db = qu.all()
    return [{'bigg_id': x[0], 'model_bigg_id': x[1]}
            for x in result_db]

def search_for_universal_reactions(query_string, session):
    # reactions by bigg_id
    sim_bigg_id = func.similarity(Reaction.bigg_id, query_string)
    sim_name = func.similarity(Reaction.name, query_string)
    result_db = (session
                 .query(Reaction.bigg_id)
                 .filter(or_(sim_bigg_id >= bigg_id_sim_cutoff,
                            and_(sim_name >= name_sim_cutoff,
                                 Reaction.name != '')))
                 .order_by(sim_bigg_id.desc(), sim_name.desc())
                 .all())
    return [{'bigg_id': x[0], 'model_bigg_id': 'universal'} for x in result_db]

def search_for_reactions(query_string, session, limit_models=None):
    # reactions by bigg_id
    sim_bigg_id = func.similarity(Reaction.bigg_id, query_string)
    sim_name = func.similarity(Reaction.name, query_string)
    qu = (session
          .query(Reaction.bigg_id, Model.bigg_id)
          .join(ModelReaction)
          .join(Model)
          .filter(or_(sim_bigg_id >= bigg_id_sim_cutoff,
                      and_(sim_name >= name_sim_cutoff,
                           Reaction.name != '')))
          .order_by(sim_bigg_id.desc(), sim_name.desc()))
    if limit_models:
        qu = qu.filter(Model.bigg_id.in_(limit_models))
    result_db = qu.all()
    return [{'bigg_id': x[0], 'model_bigg_id': x[1]} for x in result_db]

def search_for_universal_metabolites(query_string, session):
    # metabolites by bigg_id
    sim_bigg_id = func.similarity(Metabolite.bigg_id, query_string)
    sim_name = func.similarity(Metabolite.name, query_string)
    result_db = (session
                 .query(Metabolite.bigg_id)
                 .filter(or_(sim_bigg_id >= bigg_id_sim_cutoff,
                             and_(sim_name >= name_sim_cutoff,
                                  Metabolite.name != '')))
                 .order_by(sim_bigg_id.desc(), sim_name.desc())
                 .all())
    return [{'bigg_id': x[0], 'model_bigg_id': 'universal'} for x in result_db]

def search_for_metabolites(query_string, session, limit_models=None,
                           strict=False):
    """Search for metabolites.

    Arguments
    ---------

    query_string: search string

    session: the session

    limit_models: search for results in only this array of model BiGG IDs

    strict: if True, then only look for exact matches to the BiGG ID, with the
    compartment.

    """
    # metabolites by bigg_id
    sim_bigg_id = func.similarity(Metabolite.bigg_id, query_string)
    sim_name = func.similarity(Metabolite.name, query_string)
    qu = (session
          .query(Metabolite.bigg_id, Compartment.bigg_id, Model.bigg_id)
          .join(CompartmentalizedComponent,
                CompartmentalizedComponent.component_id == Metabolite.id)
          .join(Compartment,
                Compartment.id == CompartmentalizedComponent.compartment_id)
          .join(ModelCompartmentalizedComponent,
                ModelCompartmentalizedComponent.compartmentalized_component_id == CompartmentalizedComponent.id)
          .join(Model, Model.id == ModelCompartmentalizedComponent.model_id))
    if strict:
        try:
            metabolite_bigg_id, compartment_bigg_id = parse.split_compartment(query_string)
        except Exception:
            return [] 
        qu = (qu
              .filter(Metabolite.bigg_id == metabolite_bigg_id)
              .filter(Compartment.bigg_id == compartment_bigg_id))
    else:
        qu = (qu
              .filter(or_(sim_bigg_id >= bigg_id_sim_cutoff,
                          and_(sim_name >= name_sim_cutoff,
                               Metabolite.name != '')))
              .order_by(sim_bigg_id.desc(), sim_name.desc()))
    if limit_models:
        qu = qu.filter(Model.bigg_id.in_(limit_models))
    result_db = qu.all()
    return [{'bigg_id': x[0], 'compartment_bigg_id': x[1], 'model_bigg_id': x[2]}
            for x in result_db]

def search_for_models(query_string, session):
    # models by bigg_id
    sim_bigg_id = func.similarity(Model.bigg_id, query_string)
    sim_organism = func.similarity(Genome.organism, query_string)
    result_db = (session
                 .query(Model.bigg_id, ModelCount, Genome.organism)
                 .join(ModelCount)
                 .join(Genome)
                 .filter(or_(sim_bigg_id >= bigg_id_sim_cutoff, sim_organism >= organism_sim_cutoff))
                 .order_by(sim_bigg_id.desc(), sim_organism.desc())
                 .all())
    return [{'bigg_id': x[0], 'organism': x[2], 'metabolite_count': x[1].metabolite_count,
             'reaction_count': x[1].reaction_count, 'gene_count': x[1].gene_count}
            for x in result_db]

def search_ids_fast(query_string, session):
    gene_q = (session
              .query(Gene.bigg_id)
              .filter(Gene.bigg_id.ilike(query_string + '%')))
    gene_name_q = (session
                   .query(Gene.name)
                   .filter(Gene.name.ilike(query_string + '%')))
    reaction_q = (session
                  .query(Reaction.bigg_id)
                  .filter(Reaction.bigg_id.ilike(query_string + '%')))
    reaction_name_q = (session
                       .query(Reaction.name)
                       .filter(Reaction.name.ilike(query_string + '%')))
    metabolite_q = (session
                    .query(Metabolite.bigg_id)
                    .filter(Metabolite.bigg_id.ilike(query_string + '%')))
    metabolite_name_q = (session
                         .query(Metabolite.name)
                         .filter(Metabolite.name.ilike(query_string + '%')))
    model_q = (session
               .query(Model.bigg_id)
               .filter(Model.bigg_id.ilike(query_string + '%')))
    organism_q = (session
                  .query(Genome.organism)
                  .filter(Genome.organism.ilike(query_string + '%')))
    result_db = (gene_q
                 .union(gene_name_q,
                        reaction_q,
                        reaction_name_q,
                        metabolite_q,
                        metabolite_name_q,
                        model_q,
                        organism_q)
                 .all())

    return [x[0] for x in result_db]
