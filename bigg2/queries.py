from ome.models import *
from ome.base import Publication, PublicationModel
from ome.loading.model_loading import parse

from sqlalchemy import func
from sqlalchemy import desc, asc, func, or_, and_
from collections import defaultdict
from os.path import abspath, dirname, join

root_directory = abspath(dirname(__file__))


#-------------------------------------------------------------------------------
# Utils
#-------------------------------------------------------------------------------


class NotFoundError(Exception):
    pass


def _shorten_name(name, l=100):
    if name is None:
        return None
    if len(name) > l:
        return name[:l] + '...'
    else:
        return name


def _apply_order_limit_offset(query, sort_column_object=None, sort_direction='ascending',
                              page=None, size=None):
    """Get model metabolites.

    Arguments
    ---------
    
    query: A sqlalchemy query

    sort_column_object: An object or list of objects to order by, or None to not
    order.
    
    sort_direction: Either 'ascending' or 'descending'. Ignored if
    sort_column_object is None.

    page: The page, or None for all pages.
    
    size: The page length, or None for all pages.

    Returns
    -------

    An updated query.

    """
    # sort
    if sort_column_object is not None:
        if sort_direction == 'descending':
            direction_fn = desc
        elif sort_direction == 'ascending':
            direction_fn = asc
        else:
            raise Exception('Bad sort direction %s' % sort_direction)

        if type(sort_column_object) is list:
            query = query.order_by(*[direction_fn(x) for x in sort_column_object])
        else:
            query = query.order_by(direction_fn(sort_column_object))

    # limit and offset
    if page is not None and size is not None:
        page = int(page); size = int(size)
        offset = page * size
        query = query.limit(size).offset(offset)

    return query


#-------------------------------------------------------------------------------
# Reactions
#-------------------------------------------------------------------------------


def get_universal_reactions_count(session):
    """Return the number of universal reactions."""
    return session.query(Reaction).count()


def get_universal_reactions(session, page=None, size=None, sort_column=None,
                            sort_direction='ascending'):
    """Get universal reactions.

    Arguments
    ---------
    
    session: An ome session object.
    
    page: The page, or None for all pages.
    
    size: The page length, or None for all pages.

    sort_column: The name of the column to sort. Must be one of 'bigg_id', 'name'.

    sort_direction: Either 'ascending' or 'descending'.

    Returns
    -------

    A list of objects with keys 'bigg_id', 'name'. 

    """
    # get the sort column
    columns = {'bigg_id': func.lower(Reaction.bigg_id),
               'name': func.lower(Reaction.name)}

    if sort_column is None:
        sort_column_object = None
    else:
        try:
            sort_column_object = columns[sort_column]
        except KeyError:
            print 'Bad sort_column name: %s' % sort_column
            sort_column_object = columns.itervalues().next()

    # set up the query
    query = (session
             .query(Reaction.bigg_id, Reaction.name))

    # order and limit
    query = _apply_order_limit_offset(query, sort_column_object, sort_direction,
                                      page, size)

    return [{'bigg_id': x[0], 'name': x[1]} for x in query.all()]


def get_model_reactions_count(model_bigg_id, session):
    """Count the model reactions."""
    return (session
            .query(Reaction)
            .join(ModelReaction, ModelReaction.reaction_id == Reaction.id)
            .join(Model, Model.id == ModelReaction.model_id)
            .filter(Model.bigg_id == model_bigg_id)
            .count())


def get_model_reactions(model_bigg_id, session, page=None, size=None,
                        sort_column=None, sort_direction='ascending'):
    """Get model reactions.

    Arguments
    ---------
    
    model_bigg_id: The bigg id of the model to retrieve reactions.

    session: An ome session object.
    
    page: The page, or None for all pages.
    
    size: The page length, or None for all pages.

    sort_column: The name of the column to sort. Must be one of 'bigg_id', 'name',
    'model_bigg_id', and 'organism'.

    sort_direction: Either 'ascending' or 'descending'.

    Returns
    -------

    A list of objects with keys 'bigg_id', 'name', 'model_bigg_id', and
    'organism'.

    """
    # get the sort column
    columns = {'bigg_id': func.lower(Reaction.bigg_id),
               'name': func.lower(Reaction.name),
               'model_bigg_id': func.lower(Model.bigg_id),
               'organism': func.lower(Genome.organism)}

    if sort_column is None:
        sort_column_object = None
    else:
        try:
            sort_column_object = columns[sort_column]
        except KeyError:
            print 'Bad sort_column name: %s' % sort_column
            sort_column_object = columns.itervalues().next()

    # set up the query
    query = (session
             .query(Reaction.bigg_id, Reaction.name, Model.bigg_id, Genome.organism)
             .join(ModelReaction, ModelReaction.reaction_id == Reaction.id)
             .join(Model, Model.id == ModelReaction.model_id)
             .outerjoin(Genome, Genome.id == Model.genome_id)
             .filter(Model.bigg_id == model_bigg_id))

    # order and limit
    query = _apply_order_limit_offset(query, sort_column_object, sort_direction,
                                      page, size)

    return [{'bigg_id': x[0], 'name': x[1], 'model_bigg_id': x[2], 'organism': x[3]} 
            for x in query.all()]


def get_reaction_and_models(reaction_bigg_id, session):
    result_db = (session
                 .query(Reaction.bigg_id,
                        Reaction.name,
                        Reaction.pseudoreaction,
                        Model.bigg_id,
                        Genome.organism)
                 .join(ModelReaction, ModelReaction.reaction_id == Reaction.id)
                 .join(Model, Model.id == ModelReaction.model_id)
                 .outerjoin(Genome, Genome.id == Model.genome_id)
                 .filter(Reaction.bigg_id == reaction_bigg_id)
                 .distinct()
                 .all())
    if len(result_db) == 0:
        raise NotFoundError('Could not find reaction')

    db_link_results = get_db_links_for_reaction(reaction_bigg_id, session)

    # metabolites
    metabolite_db = get_metabolite_list_for_reaction(reaction_bigg_id, session)

    return {'bigg_id': result_db[0][0],
            'name': result_db[0][1],
            'pseudoreaction': result_db[0][2],
            'database_links': db_link_results,
            'metabolites': metabolite_db,
            'models_containing_reaction': [{'bigg_id': x[3], 'organism': x[4]}
                                           for x in result_db]}
    
def get_reactions_for_model(model_bigg_id, session):
    result_db = (session
                 .query(Reaction.bigg_id, Reaction.name, Genome.organism)
                 .join(ModelReaction, ModelReaction.reaction_id == Reaction.id)
                 .join(Model, Model.id == ModelReaction.model_id)
                 .outerjoin(Genome, Genome.id == Model.genome_id)
                 .filter(Model.bigg_id == model_bigg_id)
                 .all())
    return [{'bigg_id': x[0], 'name': x[1], 'organism': x[2]}
             for x in result_db]


def get_model_reaction(model_bigg_id, reaction_bigg_id, session):
    model_reaction_db = (session
                         .query(Reaction.bigg_id,
                                Reaction.name,
                                ModelReaction.id,
                                ModelReaction.gene_reaction_rule,
                                ModelReaction.lower_bound,
                                ModelReaction.upper_bound,
                                ModelReaction.objective_coefficient,
                                Reaction.pseudoreaction)
                         .join(ModelReaction, ModelReaction.reaction_id == Reaction.id)
                         .join(Model, Model.id == ModelReaction.model_id)
                         .filter(Model.bigg_id == model_bigg_id)
                         .filter(Reaction.bigg_id == reaction_bigg_id)
                         .all())
    if model_reaction_db is None:
        raise NotFoundError('ModelReaction not found')

    # metabolites
    metabolite_db = get_metabolite_list_for_reaction(reaction_bigg_id, session)

    # models
    model_db = get_model_list_for_reaction(reaction_bigg_id, session)
    model_result = [x for x in model_db if x != model_bigg_id]

    # database_links
    db_link_results = get_db_links_for_reaction(reaction_bigg_id, session)

    # escher maps
    escher_maps = get_escher_maps_for_reaction(reaction_bigg_id, model_bigg_id, session)

    result_list = []
    for result_db in model_reaction_db:
        gene_db = get_gene_list_for_model_reaction(result_db[2], session)

        result_list.append({'gene_reaction_rule': result_db[3],
                            'lower_bound': result_db[4],
                            'upper_bound': result_db[5],
                            'objective_coefficient': result_db[6],
                            'genes': gene_db})
    
    return {'count': len(result_list),
            'bigg_id': reaction_bigg_id,
            'name': model_reaction_db[0][1],
            'pseudoreaction': model_reaction_db[0][7],
            'model_bigg_id': model_bigg_id,
            'metabolites': metabolite_db,
            'database_links': db_link_results,
            'other_models_with_reaction': model_result,
            'escher_maps': escher_maps,
            'results': result_list}

        
def get_reaction(reaction_bigg_id, session):
    return (session
            .query(Reaction)
            .filter(Reaction.bigg_id == reaction_bigg_id)
            .first())


#-------------------------------------------------------------------------------
# Metabolites
#-------------------------------------------------------------------------------


def get_universal_metabolites_count(session):
    return session.query(Metabolite).count()


def get_universal_metabolites(session, page=None, size=None, sort_column=None,
                              sort_direction='ascending'):
    """Get universal metabolites.

    Arguments
    ---------
    
    session: An ome session object.
    
    page: The page, or None for all pages.
    
    size: The page length, or None for all pages.

    sort_column: The name of the column to sort. Must be one of 'bigg_id', 'name'.

    sort_direction: Either 'ascending' or 'descending'.

    Returns
    -------

    A list of objects with keys 'bigg_id', 'name'. 

    """
    # get the sort column
    columns = {'bigg_id': func.lower(Metabolite.bigg_id),
               'name': func.lower(Metabolite.name)}

    if sort_column is None:
        sort_column_object = None
    else:
        try:
            sort_column_object = columns[sort_column]
        except KeyError:
            print 'Bad sort_column name: %s' % sort_column
            sort_column_object = columns.itervalues().next()

    # set up the query
    query = (session
             .query(Metabolite.bigg_id, Metabolite.name))

    # order and limit
    query = _apply_order_limit_offset(query, sort_column_object, sort_direction,
                                      page, size)

    return [{'bigg_id': x[0], 'name': x[1]} for x in query.all()]


def get_model_metabolites_count(model_bigg_id, session):
    """Count the model metabolites."""
    return (session
            .query(Metabolite)
            .join(CompartmentalizedComponent)
            .join(ModelCompartmentalizedComponent)
            .join(Model)
            .filter(Model.bigg_id == model_bigg_id)
            .count())


def get_model_metabolites(model_bigg_id, session, page=None, size=None, sort_column=None,
                          sort_direction='ascending'):
    """Get model metabolites.

    Arguments
    ---------
    
    model_bigg_id: The bigg id of the model to retrieve metabolites.

    session: An ome session object.
    
    page: The page, or None for all pages.
    
    size: The page length, or None for all pages.

    sort_column: The name of the column to sort. Must be one of 'bigg_id',
    'name', 'model_bigg_id', and 'organism'.

    sort_direction: Either 'ascending' or 'descending'.

    Returns
    -------

    A list of objects with keys 'bigg_id', 'name', 'compartment_bigg_id',
    'model_bigg_id', and 'organism'.

    """
    # get the sort column
    columns = {'bigg_id': [func.lower(Metabolite.bigg_id), func.lower(Compartment.bigg_id)],
               'name': func.lower(Metabolite.name),
               'model_bigg_id': func.lower(Model.bigg_id),
               'organism': func.lower(Genome.organism)}

    if sort_column is None:
        sort_column_object = None
    else:
        try:
            sort_column_object = columns[sort_column]
        except KeyError:
            print 'Bad sort_column name: %s' % sort_column
            sort_column_object = columns.itervalues().next()

    # set up the query
    query = (session
             .query(Metabolite.bigg_id, Metabolite.name, Model.bigg_id, Genome.organism, Compartment.bigg_id)
             .join(CompartmentalizedComponent)
             .join(ModelCompartmentalizedComponent)
             .join(Model)
             .join(Compartment, Compartment.id == CompartmentalizedComponent.compartment_id)
             .outerjoin(Genome, Genome.id == Model.genome_id)
             .filter(Model.bigg_id == model_bigg_id))

    # order and limit
    query = _apply_order_limit_offset(query, sort_column_object, sort_direction,
                                      page, size)

    return [{'bigg_id': x[0], 'name': x[1], 'model_bigg_id': x[2], 'organism': x[3], 'compartment_bigg_id': x[4]} 
            for x in query.all()]


#-------------------------------------------------------------------------------
# Models
#-------------------------------------------------------------------------------


def get_models_count(session):
    """Return the number of models in the database."""
    return session.query(Model).count()


def get_models(session, page=None, size=None, sort_column=None, sort_direction='ascending'):
    """Get models and number of components.

    Arguments
    ---------
    
    session: An ome session object.
    
    page: The page, or None for all pages.
    
    size: The page length, or None for all pages.

    sort_column: The name of the column to sort. Must be one of 'bigg_id',
    'organism', 'metabolite_count', 'reaction_count', and 'gene_count'.

    sort_direction: Either 'ascending' or 'descending'.

    Returns
    -------

    A list of objects with keys 'bigg_id', 'organism', 'metabolite_count',
    'reaction_count', and 'gene_count'.

    """
    # get the sort column
    columns = {'bigg_id': func.lower(Model.bigg_id),
               'organism': func.lower(Genome.organism),
               'metabolite_count': ModelCount.metabolite_count,
               'reaction_count': ModelCount.reaction_count,
               'gene_count': ModelCount.gene_count}

    if sort_column is None:
        sort_column_object = None
    else:
        try:
            sort_column_object = columns[sort_column]
        except KeyError:
            print 'Bad sort_column name: %s' % sort_column
            sort_column_object = columns.itervalues().next()

    # set up the query
    query = (session
             .query(Model.bigg_id, Genome.organism, ModelCount.metabolite_count, 
                    ModelCount.reaction_count, ModelCount.gene_count)
             .join(ModelCount, ModelCount.model_id == Model.id)
             .outerjoin(Genome, Genome.id == Model.genome_id))

    # order and limit
    query = _apply_order_limit_offset(query, sort_column_object, sort_direction,
                                      page, size)

    return [{'bigg_id': x[0], 'organism': x[1], 'metabolite_count': x[2], 'reaction_count': x[3], 'gene_count': x[4]} 
            for x in query.all()]


def get_model_list_for_reaction(reaction_bigg_id, session):
    result = (session
              .query(Model.bigg_id)
              .join(ModelReaction, ModelReaction.model_id == Model.id)
              .join(Reaction, Reaction.id == ModelReaction.reaction_id)
              .filter(Reaction.bigg_id == reaction_bigg_id)
              .distinct()
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


def get_model_and_counts(model_bigg_id, session):
    model_db = (session
                .query(Model, ModelCount, Genome, Publication.reference_type,
                       Publication.reference_id)
                .join(ModelCount, ModelCount.model_id == Model.id)
                .outerjoin(Genome, Genome.id == Model.genome_id)
                .outerjoin(PublicationModel, PublicationModel.model_id == Model.id)
                .outerjoin(Publication, Publication.id == PublicationModel.publication_id)
                .filter(Model.bigg_id == model_bigg_id)
                .first())
    escher_maps = get_escher_maps_for_model(model_db[0].id, session)
    return_dict = {'bigg_id': model_db[0].bigg_id,
                   'published_filename': model_db[0].published_filename,
                   'organism': getattr(model_db[2], 'organism', None),
                   'genome': getattr(model_db[2], 'bioproject_id', None),
                   'metabolite_count': model_db[1].metabolite_count,
                   'reaction_count': model_db[1].reaction_count,
                   'gene_count': model_db[1].gene_count,
                   'reference_type': model_db[3],
                   'reference_id': model_db[4],
                   'escher_maps': escher_maps}
    return return_dict
        


def get_model_list(session):
    """Return a list of all models, for advanced search."""
    model_list = (session
                  .query(Model.bigg_id)
                  .order_by(Model.bigg_id)
                  .all())
    list = [x[0] for x in model_list]
    list.sort()
    return list


def get_model_json_string(model_bigg_id):
    """Get the model JSON for download."""
    path = join(root_directory, 'static', 'model_dumps',
                model_bigg_id + '.json')
    try:
        with open(path, 'r') as f:
            data = f.read()
    except IOError as e:
        raise NotFoundError(e.message)
    return data


#-------------------------------------------------------------------------------
# Genes
#-------------------------------------------------------------------------------


def get_model_genes_count(model_bigg_id, session):
    """Get the number of gene for the given model."""
    return (session.query(Gene)
            .join(ModelGene)
            .join(Model)
            .filter(Model.bigg_id == model_bigg_id)
            .count())
    

def get_model_genes(model_bigg_id, session, page=None, size=None,
                    sort_column=None, sort_direction='ascending'):
    """Get model genes.

    Arguments
    ---------
    
    model_bigg_id: The bigg id of the model to retrieve genes.

    session: An ome session object.
    
    page: The page, or None for all pages.
    
    size: The page length, or None for all pages.

    sort_column: The name of the column to sort. Must be one of 'bigg_id', 'name',
    'model_bigg_id', and 'organism'.

    sort_direction: Either 'ascending' or 'descending'.

    Returns
    -------

    A list of objects with keys 'bigg_id', 'name', 'model_bigg_id', and
    'organism'.

    """
    # get the sort column
    columns = {'bigg_id': func.lower(Gene.bigg_id),
                'name': func.lower(Gene.name),
                'model_bigg_id': func.lower(Model.bigg_id),
                'organism': func.lower(Genome.organism)}

    if sort_column is None:
        sort_column_object = None
    else:
        try:
            sort_column_object = columns[sort_column]
        except KeyError:
            print 'Bad sort_column name: %s' % sort_column
            sort_column_object = columns.itervalues().next()

    # set up the query
    query = (session
             .query(Gene.bigg_id, Gene.name, Model.bigg_id, Genome.organism)
             .join(ModelGene)
             .join(Model)
             .outerjoin(Genome, Genome.id == Model.genome_id)
             .filter(Model.bigg_id == model_bigg_id))

    # order and limit
    query = _apply_order_limit_offset(query, sort_column_object, sort_direction,
                                      page, size)

    return [{'bigg_id': x[0], 'name': x[1], 'model_bigg_id': x[2], 'organism': x[3]} 
            for x in query.all()]


def get_model_gene(gene_bigg_id, model_bigg_id, session):
    result_db = (session
                 .query(Gene.bigg_id,
                        Gene.name,
                        Gene.info,
                        Gene.leftpos,
                        Gene.rightpos,
                        Model.bigg_id,
                        Gene.id,
                        Gene.strand,
                        Chromosome.ncbi_id,
                        Genome.bioproject_id,
                        Gene.mapped_to_genbank)
                 .join(ModelGene)
                 .join(Model)
                 .outerjoin(Genome, Genome.id == Model.genome_id)
                 .outerjoin(Chromosome, Chromosome.id == Gene.chromosome_id)
                 .filter(Gene.bigg_id == gene_bigg_id)
                 .filter(Model.bigg_id == model_bigg_id)
                 .first())
    if result_db is None:
        raise NotFoundError('Gene not found for bigg_id %s' % gene_bigg_id)
    
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
    synonym_db = (session
                    .query(Synonym.synonym, DataSource.name)
                    .join(DataSource, DataSource.id == Synonym.synonym_data_source_id)
                    .filter(Synonym.ome_id == result_db[6])
                    .all())
    return {'bigg_id': result_db[0],
            'name': result_db[1],
            'info': result_db[2],
            'leftpos': result_db[3],
            'rightpos': result_db[4],
            'model_bigg_id': result_db[5],
            'strand': result_db[7],
            'chromosome_ncbi_id': result_db[8],
            'genome_bioproject_id': result_db[9],
            'mapped_to_genbank': result_db[10],
            'reactions': reaction_results,
            'synonyms': synonym_db}
    

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
                    .outerjoin(Genome, Genome.id == Model.genome_id)
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
    
def get_gene_list_for_model(model_bigg_id, session):
    result = (session
              .query(Gene.bigg_id, Gene.name, Genome.organism, Model.bigg_id)
              .join(ModelGene)
              .join(Model)
              .outerjoin(Genome, Genome.id == Model.genome_id)
              .filter(Model.bigg_id == model_bigg_id)
              .all())
    return [{'bigg_id': x[0], 'name': x[1], 'organism': x[2], 'model_bigg_id': x[3]}
             for x in result]
    

def get_gene_list_for_model_reaction(model_reaction_id, session):
    result_db = (session
                 .query(Gene.bigg_id, Gene.name)
                 .join(ModelGene, ModelGene.gene_id == Gene.id)
                 .join(GeneReactionMatrix, GeneReactionMatrix.model_gene_id == ModelGene.id)
                 .filter(GeneReactionMatrix.model_reaction_id == model_reaction_id)
                 .all())
    return [{'bigg_id': x[0], 'name': x[1]}
            for x in result_db]


# Genomes
def get_genome_and_models(session, bioproject_id):
        genome_db = (session
                     .query(Genome)
                     .filter(Genome.bioproject_id == bioproject_id)
                     .first())
        models_db = (session
                     .query(Model)
                     .filter(Model.genome_id == genome_db.id)
                     .all())
        chromosomes_db = (session
                          .query(Chromosome)
                          .filter(Chromosome.genome_id == genome_db.id)
                          .all())
        return {'bioproject_id': genome_db.bioproject_id,
                'organism': genome_db.organism,
                'models': [x.bigg_id for x in models_db],
                'chromosomes': [x.ncbi_id for x in chromosomes_db]}


# database sources
def get_database_sources(session):
    result_db = (session
                 .query(LinkOut.external_source)
                 .distinct()
                 .all())
    return [x[0] for x in result_db]


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


def get_metabolites_for_database_id(session, query, database_source):
    result_db = (session
                 .query(Metabolite.bigg_id, Metabolite.name)
                 .join(LinkOut, LinkOut.ome_id == Metabolite.id)
                 .filter(LinkOut.external_source == database_source)
                 .filter(LinkOut.external_id == query.strip())
                 .all())
    return [{'bigg_id': x[0], 'model_bigg_id': 'universal', 'name': x[1]}
            for x in result_db]


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
        reaction_string = pre_reaction_string[:-2] + " &#x2192; " + post_reaction_string[:-2]
    elif lower_bound >= 0:
        reaction_string = pre_reaction_string[:-2] + " &#x2192; " + post_reaction_string[:-2]
    else:
        reaction_string = pre_reaction_string[:-2] + " &#8652; " + post_reaction_string[:-2]

    return reaction_string
    
# Escher maps
def get_escher_maps_for_model(model_id, session):
    result_db = (session
                 .query(EscherMap)
                 .filter(EscherMap.model_id == model_id)
                 .all())
    return [{'map_name': x.map_name, 'element_id': None} for x in result_db]

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
    
#-------------------------------------------------------------------------------
# Search
#-------------------------------------------------------------------------------


name_sim_cutoff = 0.3
bigg_id_sim_cutoff = 0.2
gene_bigg_id_sim_cutoff = 1.0
organism_sim_cutoff = 0.1


def search_for_universal_reactions_count(query_string, session):
    """Count the search results."""
    # similarity functions
    sim_bigg_id = func.similarity(Reaction.bigg_id, query_string)
    sim_name = func.similarity(Reaction.name, query_string)

    return (session
            .query(Reaction.bigg_id, Reaction.name)
            .filter(or_(sim_bigg_id >= bigg_id_sim_cutoff,
                        and_(sim_name >= name_sim_cutoff,
                             Reaction.name != '')))
            .count())


def search_for_universal_reactions(query_string, session, page=None, size=None,
                                   sort_column=None, sort_direction='ascending'):
    """Search for universal reactions.

    Arguments
    ---------
    
    query_string: The string to search for.
    
    session: An ome session object.
    
    page: The page, or None for all pages.
    
    size: The page length, or None for all pages.

    sort_column: The name of the column to sort. Must be one of 'bigg_id', 'name'.

    sort_direction: Either 'ascending' or 'descending'.

    Returns
    -------

    A list of objects with keys 'bigg_id', 'name'. 

    """
    # similarity functions
    sim_bigg_id = func.similarity(Reaction.bigg_id, query_string)
    sim_name = func.similarity(Reaction.name, query_string)

    # get the sort column
    columns = {'bigg_id': func.lower(Reaction.bigg_id),
               'name': func.lower(Reaction.name)}

    if sort_column is None:
        # sort by the greater similarity
        sort_column_object = func.greatest(sim_bigg_id, sim_name)
        sort_direction = 'descending'
    else:
        try:
            sort_column_object = columns[sort_column]
        except KeyError:
            print 'Bad sort_column name: %s' % sort_column
            sort_column_object = columns.itervalues().next()

    # set up the query
    query = (session
             .query(Reaction.bigg_id, Reaction.name)
             .filter(or_(sim_bigg_id >= bigg_id_sim_cutoff,
                         and_(sim_name >= name_sim_cutoff,
                              Reaction.name != ''))))

    # order and limit
    query = _apply_order_limit_offset(query, sort_column_object, sort_direction,
                                      page, size)

    return [{'bigg_id': x[0], 'name': x[1]} for x in query.all()]


def search_for_reactions(query_string, session, page=None, size=None, sort_column=None,
                         sort_direction='ascending', limit_models=None):
    """Search for model reactions.

    Arguments
    ---------
    
    query_string: The string to search for.
    
    session: An ome session object.
    
    page: The page, or None for all pages.
    
    size: The page length, or None for all pages.

    sort_column: The name of the column to sort. Must be one of 'bigg_id', 'name',
    'model_bigg_id', and 'organism'.

    sort_direction: Either 'ascending' or 'descending'.

    Returns
    -------

    A list of objects with keys 'bigg_id', 'name', 'model_bigg_id', and
    'organism'.

    """
    # similarity functions
    sim_bigg_id = func.similarity(Reaction.bigg_id, query_string)
    sim_name = func.similarity(Reaction.name, query_string)

    # get the sort column
    columns = {'bigg_id': func.lower(Reaction.bigg_id),
               'name': func.lower(Reaction.name)}

    if sort_column is None:
        # sort by the greater similarity
        sort_column_object = func.greatest(sim_bigg_id, sim_name)
        sort_direction = 'descending'
    else:
        try:
            sort_column_object = columns[sort_column]
        except KeyError:
            print 'Bad sort_column name: %s' % sort_column
            sort_column_object = columns.itervalues().next()

    # set up the query
    query = (session
             .query(Reaction.bigg_id, Model.bigg_id, Genome.organism, Reaction.name)
             .join(ModelReaction)
             .join(Model)
             .outerjoin(Genome)
             .filter(or_(sim_bigg_id >= bigg_id_sim_cutoff,
                         and_(sim_name >= name_sim_cutoff,
                              Reaction.name != ''))))

    # order and limit
    query = _apply_order_limit_offset(query, sort_column_object, sort_direction,
                                      page, size)

    # limit the models
    if limit_models:
        query = query.filter(Model.bigg_id.in_(limit_models))

    return [{'bigg_id': x[0], 'model_bigg_id': x[1], 'organism': x[2], 'name': x[3]}
            for x in query.all()]


def search_for_universal_metabolites_count(query_string, session):
    """Count the search results."""
    # similarity functions
    sim_bigg_id = func.similarity(Metabolite.bigg_id, query_string)
    sim_name = func.similarity(Metabolite.name, query_string)

    return (session
            .query(Metabolite.bigg_id, Metabolite.name)
            .filter(or_(sim_bigg_id >= bigg_id_sim_cutoff,
                        and_(sim_name >= name_sim_cutoff,
                             Metabolite.name != '')))
            .count())


def search_for_universal_metabolites(query_string, session, page=None,
                                     size=None, sort_column=None,
                                     sort_direction='ascending'):
    """Search for universal Metabolites.

    Arguments
    ---------
    
    query_string: The string to search for.
    
    session: An ome session object.
    
    page: The page, or None for all pages.
    
    size: The page length, or None for all pages.

    sort_column: The name of the column to sort. Must be one of 'bigg_id', 'name'.

    sort_direction: Either 'ascending' or 'descending'.

    Returns
    -------

    A list of objects with keys 'bigg_id', 'name'. 

    """
    # similarity functions
    sim_bigg_id = func.similarity(Metabolite.bigg_id, query_string)
    sim_name = func.similarity(Metabolite.name, query_string)

    # get the sort column
    columns = {'bigg_id': func.lower(Metabolite.bigg_id),
               'name': func.lower(Metabolite.name)}

    if sort_column is None:
        # sort by the greater similarity
        sort_column_object = func.greatest(sim_bigg_id, sim_name)
        sort_direction = 'descending'
    else:
        try:
            sort_column_object = columns[sort_column]
        except KeyError:
            print 'Bad sort_column name: %s' % sort_column
            sort_column_object = columns.itervalues().next()

    # set up the query
    query = (session
             .query(Metabolite.bigg_id, Metabolite.name)
             .filter(or_(sim_bigg_id >= bigg_id_sim_cutoff,
                         and_(sim_name >= name_sim_cutoff,
                              Metabolite.name != ''))))

    # order and limit
    query = _apply_order_limit_offset(query, sort_column_object, sort_direction,
                                      page, size)

    return [{'bigg_id': x[0], 'name': x[1]} for x in query.all()]


def search_for_metabolites_by_external_id(query_string, source, session):
    """Search based on the linkout ID."""
    sim_external_id = func.similarity(LinkOut.external_id, query_string)

    query = (session
          .query(Metabolite.bigg_id, Compartment.bigg_id, Model.bigg_id, Genome.organism, LinkOut.external_id)
          .join(CompartmentalizedComponent,
                CompartmentalizedComponent.component_id == Metabolite.id)
          .join(LinkOut,
                LinkOut.ome_id == Metabolite.id)
          .join(Compartment,
                Compartment.id == CompartmentalizedComponent.compartment_id)
          .join(ModelCompartmentalizedComponent,
                ModelCompartmentalizedComponent.compartmentalized_component_id == CompartmentalizedComponent.id)
          .join(Model, Model.id == ModelCompartmentalizedComponent.model_id)
          .outerjoin(Genome)
          .filter(LinkOut.type == 'metabolite')
          .filter(LinkOut.external_source == source)
          .filter(LinkOut.external_id == query_string))

    return [{'bigg_id': x[0], 'compartment_bigg_id': x[1], 'model_bigg_id': x[2], 'organism': x[3]}
            for x in query.all()]


def search_for_metabolites(query_string, session, page=None, size=None,
                           sort_column=None, sort_direction='ascending',
                           limit_models=None, strict=False):
    """Search for model metabolites.

    Arguments
    ---------
    
    query_string: The string to search for.
    
    session: An ome session object.
    
    page: The page, or None for all pages.
    
    size: The page length, or None for all pages.

    sort_column: The name of the column to sort. Must be one of 'bigg_id', 'name',
    'model_bigg_id', and 'organism'.

    sort_direction: Either 'ascending' or 'descending'.

    limit_models: search for results in only this array of model BiGG IDs.

    strict: if True, then only look for exact matches to the BiGG ID, with the
    compartment.

    Returns
    -------

    A list of objects with keys 'bigg_id', 'name', 'model_bigg_id', and
    'organism'.

    """
    # similarity functions
    sim_bigg_id = func.similarity(Metabolite.bigg_id, query_string)
    sim_name = func.similarity(Metabolite.name, query_string)

    # get the sort column
    columns = {'bigg_id': [func.lower(Metabolite.bigg_id), func.lower(Compartment.bigg_id)],
               'name': func.lower(Metabolite.name),
               'model_bigg_id': func.lower(Model.bigg_id),
               'organism': func.lower(Genome.organism)}

    if sort_column is None:
        sort_column_object = None
    else:
        try:
            sort_column_object = columns[sort_column]
        except KeyError:
            print 'Bad sort_column name: %s' % sort_column
            sort_column_object = columns.itervalues().next()


    if sort_column is None:
        if strict:
            # just sort by bigg ID
            sort_column_object = columns['bigg_id']
            sort_direction = 'ascending'
        else:
            # sort by most similar
            sort_column_object = func.greatest(sim_name, sim_bigg_id)
            sort_direction = 'descending'
    else:
        try:
            sort_column_object = columns[sort_column]
        except KeyError:
            print 'Bad sort_column name: %s' % sort_column
            sort_column_object = columns.itervalues().next()

    # set up the query
    query = (session
             .query(Metabolite.bigg_id, Compartment.bigg_id, Model.bigg_id,
                    Genome.organism, Metabolite.name)
             .join(CompartmentalizedComponent,
                   CompartmentalizedComponent.component_id == Metabolite.id)
             .join(Compartment,
                   Compartment.id == CompartmentalizedComponent.compartment_id)
             .join(ModelCompartmentalizedComponent,
                   ModelCompartmentalizedComponent.compartmentalized_component_id == CompartmentalizedComponent.id)
             .join(Model, Model.id == ModelCompartmentalizedComponent.model_id)
             .outerjoin(Genome))

    # whether to allow fuzzy search
    if strict:
        try:
            metabolite_bigg_id, compartment_bigg_id = parse.split_compartment(query_string)
        except Exception:
            return [] 
        query = (query
                 .filter(Metabolite.bigg_id == metabolite_bigg_id)
                 .filter(Compartment.bigg_id == compartment_bigg_id))
    else:
        query = (query
                 .filter(or_(sim_bigg_id >= bigg_id_sim_cutoff,
                             and_(sim_name >= name_sim_cutoff,
                                  Metabolite.name != ''))))

    # order and limit
    query = _apply_order_limit_offset(query, sort_column_object, sort_direction,
                                      page, size)

    # just search certain models
    if limit_models:
        query = query.filter(Model.bigg_id.in_(limit_models))

    return [{'bigg_id': x[0], 'compartment_bigg_id': x[1], 'model_bigg_id': x[2],
             'organism': x[3], 'name': x[4]}
            for x in query.all()]


def search_for_genes_count(query_string, session, limit_models=None):
    """Count the search results."""
    # similarity functions
    sim_bigg_id = func.similarity(Gene.bigg_id, query_string)
    sim_name = func.similarity(Gene.name, query_string)

    # set up the query
    query = (session
             .query(Gene.bigg_id, Model.bigg_id, Gene.name, sim_bigg_id, Genome.organism)
             .join(ModelGene)
             .join(Model)
             .outerjoin(Genome)
             .filter(or_(sim_bigg_id >= gene_bigg_id_sim_cutoff,
                         and_(sim_name >= name_sim_cutoff,
                              Gene.name != ''))))

    # limit the models
    if limit_models:
        query = query.filter(Model.bigg_id.in_(limit_models))

    return query.count()


def search_for_genes(query_string, session, page=None, size=None, sort_column=None,
                     sort_direction='ascending', limit_models=None):
    """Search for genes.

    Arguments
    ---------
    
    query_string: The string to search for.
    
    session: An ome session object.
    
    page: The page, or None for all pages.
    
    size: The page length, or None for all pages.

    sort_column: The name of the column to sort. Must be one of 'bigg_id', 'name',
    'model_bigg_id', and 'organism'.

    sort_direction: Either 'ascending' or 'descending'.

    limit_models: search for results in only this array of model BiGG IDs.

    Returns
    -------

    A list of objects with keys 'bigg_id', 'name', 'model_bigg_id', and
    'organism'.

    """
    # similarity functions
    sim_bigg_id = func.similarity(Gene.bigg_id, query_string)
    sim_name = func.similarity(Gene.name, query_string)

    # get the sort column
    columns = {'bigg_id': func.lower(Gene.bigg_id),
               'name': func.lower(Gene.name),
               'model_bigg_id': func.lower(Model.bigg_id),
               'organism': func.lower(Genome.organism)}

    if sort_column is None:
        # sort by the greater similarity
        sort_column_object = func.greatest(sim_bigg_id, sim_name)
        sort_direction = 'descending'
    else:
        try:
            sort_column_object = columns[sort_column]
        except KeyError:
            print 'Bad sort_column name: %s' % sort_column
            sort_column_object = columns.itervalues().next()

    # set up the query
    query = (session
             .query(Gene.bigg_id, Gene.name, Model.bigg_id, Genome.organism)
             .join(ModelGene)
             .join(Model)
             .outerjoin(Genome)
             .filter(or_(sim_bigg_id >= gene_bigg_id_sim_cutoff,
                         and_(sim_name >= name_sim_cutoff,
                              Gene.name != ''))))

    # order and limit
    query = _apply_order_limit_offset(query, sort_column_object, sort_direction,
                                      page, size)

    # limit the models
    if limit_models:
        query = query.filter(Model.bigg_id.in_(limit_models))

    return [{'bigg_id': x[0], 'name': x[1], 'model_bigg_id': x[2], 'organism': x[3]} 
            for x in query.all()]


def search_for_models_count(query_string, session):
    """Count the search results."""
    # similarity functions
    sim_bigg_id = func.similarity(Model.bigg_id, query_string)
    sim_organism = func.similarity(Genome.organism, query_string)

    # set up the query
    return (session
            .query(Model.bigg_id, ModelCount, Genome.organism)
            .join(ModelCount)
            .outerjoin(Genome)
            .filter(or_(sim_bigg_id >= bigg_id_sim_cutoff, 
                        sim_organism >= organism_sim_cutoff))
            .count())


def search_for_models(query_string, session, page=None, size=None,
                      sort_column=None, sort_direction='ascending'):
    """Search for models.

    Arguments
    ---------
    
    query_string: The string to search for.
    
    session: An ome session object.
    
    page: The page, or None for all pages.
    
    size: The page length, or None for all pages.

    sort_column: The name of the column to sort. Must be one of 'bigg_id',
    'organism', 'metabolite_count', 'reaction_count', and 'gene_count'.

    sort_direction: Either 'ascending' or 'descending'.

    limit_models: search for results in only this array of model BiGG IDs.

    Returns
    -------

    A list of objects with keys 'bigg_id', 'organism', 'metabolite_count',
    'reaction_count', and 'gene_count'.

    """

    # models by bigg_id
    sim_bigg_id = func.similarity(Model.bigg_id, query_string)
    sim_organism = func.similarity(Genome.organism, query_string)

    # get the sort column
    columns = {'bigg_id': func.lower(Model.bigg_id),
               'organism': func.lower(Genome.organism),
               'metabolite_count': ModelCount.metabolite_count,
               'reaction_count': ModelCount.reaction_count,
               'gene_count': ModelCount.gene_count}

    if sort_column is None:
        # sort by the greater similarity
        sort_column_object = func.greatest(sim_bigg_id, sim_organism)
        sort_direction = 'descending'
    else:
        try:
            sort_column_object = columns[sort_column]
        except KeyError:
            print 'Bad sort_column name: %s' % sort_column
            sort_column_object = columns.itervalues().next()

    # set up the query
    query = (session
             .query(Model.bigg_id, Genome.organism, ModelCount.metabolite_count,
                    ModelCount.reaction_count, ModelCount.gene_count)
             .join(ModelCount)
             .outerjoin(Genome)
             .filter(or_(sim_bigg_id >= bigg_id_sim_cutoff, 
                         sim_organism >= organism_sim_cutoff)))

    # order and limit
    query = _apply_order_limit_offset(query, sort_column_object, sort_direction,
                                      page, size)

    return [{'bigg_id': x[0], 'organism': x[1], 'metabolite_count': x[2],
             'reaction_count': x[3], 'gene_count': x[4]}
            for x in query.all()]


def search_ids_fast(query_string, session, limit=None):
    """Search used for autocomplete."""
    gene_q = (session
              .query(Gene.bigg_id)
              .join(ModelGene)
              .filter(Gene.bigg_id.ilike(query_string + '%')))
    gene_name_q = (session
                   .query(Gene.name)
                   .join(ModelGene)
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
    query = (gene_q
             .union(gene_name_q,
                    reaction_q,
                    reaction_name_q,
                    metabolite_q,
                    metabolite_name_q,
                    model_q,
                    organism_q))

    if limit is not None:
        query = query.limit(limit)
        
    return [x[0] for x in query.all()]
