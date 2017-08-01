# -*- coding: utf-8 -*-

from sqlalchemy.orm import sessionmaker, aliased
from sqlalchemy import desc, func, or_
import pytest
import sys
from cobra.io import read_sbml_model, load_matlab_model, load_json_model
import pytest
import numpy
from os.path import abspath, dirname, join, exists
from os import listdir
from numpy.testing import assert_almost_equal
try:
    import cPickle as pickle
except ImportError:
    import pickle
import re
from time import time
import itertools
import six

from cobradb.models import *
from cobradb import settings
from cobradb.model_dumping import dump_model
from cobradb.parse import convert_ids, remove_boundary_metabolites, invalid_formula
from cobradb.util import load_tsv

from bigg_models.server import (directory as bigg_root_directory,
                                static_model_dir)


# Make a list of models to test

DEBUG = False
STRICT_MASS_BALANCE = False

if DEBUG:
    model_files = ['iJO1366.xml']
else:
    model_files = [x[0] for x in load_tsv(settings.model_genome)]


# make the fixtures

@pytest.fixture(scope='session')
def session(request):
    """Make a session"""
    def teardown():
        Session.close_all()
    request.addfinalizer(teardown)

    return Session()


@pytest.fixture(scope='session', params=model_files)
def pub_model(request):
    # get a specific model. This fixture and all the tests that use it will run
    # for every model in the model_files list.
    model_file = request.param
    model_path = join(settings.model_directory, model_file)

    # load the file
    start = time()
    try:
        if model_path.endswith('.xml'):
            # LibSBML does not like unicode filepaths in Python 2.7
            pub_model = read_sbml_model(str(model_path))
        elif model_path.endswith('.mat'):
            pub_model = load_matlab_model(model_path)
        elif model_path.endswith('.json'):
            pub_model = load_json_model(model_path)
        else:
            raise Exception('Unrecongnized extension for model %s' % model_file)
    except IOError:
        raise Exception('Could not find model %s' % model_path)
    print("Loaded %s in %.2f sec" % (model_file, time() - start))

    return pub_model


@pytest.fixture(scope='session')
def db_model(pub_model):
    # dump the model
    start = time()
    # take out special characters from model bigg_id
    db_model = dump_model(pub_model.id.replace('.', '_'))
    print("Dumped %s in %.2f sec" % (pub_model.id, time() - start))
    return db_model


# model tests will run for every model in the model_files list

# counts

def _check_merged(cobra_dictlist, model_bigg_id, cobra_type):
    """Use original_bigg_ids in the notes to identify merged reactions,
    metabolites, and genes.

    """

    # find number of copies for each gene
    db_merged = {}
    for o in cobra_dictlist:
        if cobra_type == 'reaction':
            bigg_id = re.sub(r'_copy\d+', '', o.id)
        else:
            bigg_id = o.id
        if bigg_id in db_merged:
            db_merged[bigg_id]['bigg_ids_w_copy'] += (o.id,)
        else:
            original_bigg_ids = o.notes['original_bigg_ids']
            if len(original_bigg_ids) == 0:
                raise Exception('{} missing original ID for {} in {}'
                                .format(bigg_id, cobra_type, model_bigg_id))
            db_merged[bigg_id] = {'bigg_ids_w_copy': (o.id,),
                                  'original_bigg_ids': original_bigg_ids}

    # count merged
    db_merged_extra = sum([len(v['original_bigg_ids']) - len(v['bigg_ids_w_copy'])
                           for v in six.itervalues(db_merged)])

    # report merged
    if db_merged_extra > 0:
        merged_dict = {v['bigg_ids_w_copy']: v['original_bigg_ids'] for v in six.itervalues(db_merged)
                       if len(v['original_bigg_ids']) > len(v['bigg_ids_w_copy'])}
        print('{} {} merged in model {}: {}'
              .format(db_merged_extra, cobra_type + 's', model_bigg_id, merged_dict))
    return db_merged_extra


def _find_missing(db_dictlist, pub_dictlist):
    return [x for x in pub_dictlist
            if x.id not in itertools.chain(*[y.notes['original_bigg_ids'] for y in db_dictlist])]


def _find_boundary_mets(mets):
    return len([m for m in mets if m.id.endswith('_b')])


def test_reaction_count(db_model, pub_model):
    # check for merged reactions
    pub_reactions_len = len(pub_model.reactions)
    db_reactions_len = len(db_model.reactions)
    db_merged_extra = _check_merged(db_model.reactions, db_model.id, 'reaction')
    try:
        assert db_reactions_len + db_merged_extra == pub_reactions_len
    except AssertionError as e:
        missing = _find_missing(db_model.reactions, pub_model.reactions)
        print('Missing reactions:')
        print(missing)
        raise e


def test_metabolite_count(db_model, pub_model):
    # check for merged metabolites
    pub_metabolites_len = len(pub_model.metabolites)
    pub_boundary_len = _find_boundary_mets(pub_model.metabolites)
    db_metabolites_len = len(db_model.metabolites)
    db_merged_extra = _check_merged(db_model.metabolites, db_model.id, 'metabolite')
    try:
        assert db_metabolites_len + db_merged_extra == pub_metabolites_len - pub_boundary_len
    except AssertionError as e:
        missing = _find_missing(db_model.metabolites, pub_model.metabolites)
        print(missing)
        raise e


def test_gene_count(db_model, pub_model):
    # check for merged genes
    pub_genes_len = len(pub_model.genes)
    db_genes_len = len(db_model.genes)
    db_merged_extra = _check_merged(db_model.genes, db_model.id, 'gene')
    try:
        assert db_genes_len + db_merged_extra == pub_genes_len
    except AssertionError as e:
        missing = _find_missing(db_model.genes, pub_model.genes)
        print(missing)
        raise e


# ID format

id_reg = re.compile(r'[^a-zA-Z0-9_]')
def _check_ids(l):
    return [r_id for r_id in (r.id for r in l)
            if id_reg.search(r_id) is not None]


def test_reaction_ids(db_model):
    assert _check_ids(db_model.reactions) == []


def test_metabolite_ids(db_model):
    assert _check_ids(db_model.metabolites) == []


def test_gene_ids(db_model):
    assert _check_ids(db_model.genes) == []


# formulas

def test_formula(db_model):
    formula_reg = re.compile(r'[^A-Za-z0-9]')
    def ok(met):
        return formula_reg.search(str(met.formula)) is None
    assert [(x.id, x.formula) for x in db_model.metabolites if not ok(x)] == []


# dumped files

def test_load_sbml(db_model):
    model = read_sbml_model(join(static_model_dir, db_model.id + '.xml'))
    assert model.id == db_model.id


def test_load_compressed_sbml(db_model):
    model = read_sbml_model(join(static_model_dir, db_model.id + '.xml.gz'))
    assert model.id == db_model.id


def test_load_mat(db_model):
    model = load_matlab_model(join(static_model_dir, db_model.id + '.mat'))
    assert model.id == db_model.id


def test_load_json(db_model):
    model = load_json_model(join(static_model_dir, db_model.id + '.json'))
    assert model.id == db_model.id


# optimize

def test_optimize(db_model, pub_model):
    if db_model.id == 'iYO844':
        print(('iYO844 is known to have a different growth rate than the '
               'published model because oxygen metabolites were merged.'))
        return
    solution1 = db_model.optimize()

    # have to remove boundary metabolites to solve with cobrapy
    remove_boundary_metabolites(pub_model)
    solution2 = pub_model.optimize()

    f1 = 0.0 if solution1.f is None else solution1.f
    f2 = 0.0 if solution2.f is None else solution2.f
    assert abs(f1 - f2) < 1e-5


# mass balance

def _filtered_mass_balance(mb):
    return {k: v for k, v in six.iteritems(mb) if abs(v) > 1e-6}


def _all_integer_formula_charge(reaction):
    return all((met.charge is None or int(met.charge) == met.charge)
               and not invalid_formula(met.formula)
               for met in reaction.metabolites.keys())


def test_mass_balance(db_model, pub_model):
    errors = []

    for r in db_model.reactions:
        if (re.match(r'EX_.*', r.id)
            or re.match(r'DM_.*', r.id)
            or re.match(r'sink_.*', r.id, re.IGNORECASE)
            or re.match(r'.*biomass.*', r.id, re.IGNORECASE)):
            continue
        # filter out very low numbers
        mass_balance = _filtered_mass_balance(r.check_mass_balance())

        # check database reaction mass balance
        if len(mass_balance) != 0:
            # look for original reaction
            try:
                pub_reaction = pub_model.reactions.get_by_id(r.notes['original_bigg_ids'][0])
            except KeyError:
                errors.append('{}: Bad mass balance in {} ({}). Not found in pub model.'
                                .format(db_model.id, r.id, mass_balance))
            else:
                # check for models where formula do not load
                if all(x.formula == '' for x in pub_reaction.metabolites):
                    if STRICT_MASS_BALANCE:
                        # if strict, then warn even if the reaction may have
                        # been unbalanced in the original model
                        errors.append('{}: Bad mass balance in {} ({}). No formulas in published model.'
                                      .format(db_model.id, r.id, mass_balance))
                elif _all_integer_formula_charge(pub_reaction) or STRICT_MASS_BALANCE:
                    # Check mass balance in pub model. No error if original
                    # reaction had invalid non-integer charges or formula.
                    pub_mass_balance = _filtered_mass_balance(pub_reaction.check_mass_balance())
                    if len(pub_mass_balance) == 0:
                        errors.append('{}: Bad mass balance in {} ({}). Reaction is balanced in published model.'
                                        .format(db_model.id, r.id, mass_balance))
                    elif STRICT_MASS_BALANCE:
                        # if strict, then warn even if the reaction may have
                        # been unbalanced in the original model
                        errors.append('{}: Bad mass balance in {} ({}) and in published model ({}).'
                                        .format(db_model.id, r.id, mass_balance, pub_mass_balance))

    assert len(errors) == 0

# -----------------
# Common metabolite
# -----------------

def test_pyr(db_model):
    assert 'pyr_c' in db_model.metabolites

# ------------
# Mapped genes
# ------------

def test_mapped_genes(session, db_model):
    # iRC1080 genes are not mapped to the genome
    if db_model.id == 'iRC1080':
        return

    # Count mapped genes
    num_genes = len(db_model.genes)
    count = (session
             .query(Gene)
             .join(ModelGene)
             .join(Model)
             .filter(Model.bigg_id == db_model.id)
             .filter(Gene.mapped_to_genbank == True)
             .count())
    fraction = float(count) / num_genes

    # Most models map greater than 95% of genes, with these exceptions
    if db_model.id == 'iECDH1ME8569_1439':
        assert fraction > 0.92
    elif db_model.id == 'iAB_RBC_283':
        assert fraction > 0.89
    elif db_model.id == 'iLB1027_lipid':
        assert fraction > 0.68
    else:
        assert fraction > 0.95

# ---------------
# Specific issues
# ---------------

def test_mass_balance_iAPECO1_1312_PSUDS(session):
    res_db = (session
              .query(ModelCompartmentalizedComponent)
              .join(Model)
              .join(CompartmentalizedComponent)
              .join(Component)
              .join(Compartment)
              .filter(Model.bigg_id == 'iAPECO1_1312')
              .filter(Component.bigg_id == 'psd5p')
              .filter(Compartment.bigg_id == 'c'))
    assert res_db.one().formula == 'C9H13N2O9P'


def test_akg_iECIAI1_1343(session):
    res_db = (session
              .query(ModelCompartmentalizedComponent)
              .join(Model)
              .join(CompartmentalizedComponent)
              .join(Component)
              .join(Compartment)
              .filter(Model.bigg_id == 'iECIAI1_1343')
              .filter(Component.bigg_id == 'akg')
              .filter(Compartment.bigg_id == 'p'))
    assert res_db.one().formula is None

# def test_recon1_gene_names(session):
#     res_db = (session
#               .query(Gene)
#               .join(ModelGene)
#               .filter(Gene.bigg_id == '4967_AT1')
#               .filter(Model.bigg_id == 'RECON1'))
#     assert ('4967_AT1', 'OGDH') in ((g.bigg_id, g.name) for g in res_db)


def test_dad_2(session):
    """Tests for a bug that occurs with dad__2_c vs. dad_2_c. Fails if you load
    iAF1260 then iMM904.

    In [44]: session.query(Component.bigg_id, Compartment.bigg_id, Model.bigg_id, Reaction.bigg_id).join(CompartmentalizedComponent, CompartmentalizedComponent.component_id==Component.id).join(Compartment, Compartment.id==CompartmentalizedComponent.compartment_id).join(ReactionMatrix, ReactionMatrix.compartmentalized_component_id==CompartmentalizedComponent.id).join(Reaction).join(ModelReaction).join(Model).filter(Model.bigg_id=='iAF1260').filter(Reaction.bigg_id.like('DADA')).all()

    Out[44]:
    [(u'dad__2', u'c', u'iAF1260', u'DADA'),
    (u'din', u'c', u'iAF1260', u'DADA'),
    (u'h2o', u'c', u'iAF1260', u'DADA'),
    (u'h', u'c', u'iAF1260', u'DADA'),
    (u'nh4', u'c', u'iAF1260', u'DADA'),
    (u'dad_2', u'c', u'iAF1260', u'DADA')]

    """
    res_db = (session
              .query(Component.bigg_id, Compartment.bigg_id, Model.bigg_id, Reaction.bigg_id)
              .join(CompartmentalizedComponent, CompartmentalizedComponent.component_id==Component.id)
              .join(Compartment, Compartment.id==CompartmentalizedComponent.compartment_id)
              .join(ReactionMatrix, ReactionMatrix.compartmentalized_component_id==CompartmentalizedComponent.id)
              .join(Reaction)
              .join(ModelReaction)
              .join(Model)
              .filter(Model.bigg_id=='iAF1260')
              .filter(Reaction.bigg_id == 'DADA')
              .filter(Component.bigg_id.like('dad_%2'))
              .all())
    assert len(res_db) == 1
    session.close()

#----------------------------
# Check charge disagreements
#----------------------------

def test_check_charge_disagreements(session):
    # Find metabolites with conflicting charges
    sub = (session.query(Component.bigg_id,
                         # To count nulls, change to: count(distinct coalesce(charge, -1))
                         func.count(func.distinct(ModelCompartmentalizedComponent.charge)).label('cc'),
                         func.array_agg(ModelCompartmentalizedComponent.charge))
           .join(CompartmentalizedComponent)
           .join(ModelCompartmentalizedComponent)
           .join(Model)
           .group_by(Component)
           .subquery())
    res = session.query(sub).filter('cc > 1')
    print('Metabolites with conflicting charges: %s' % ', '.join([x[0] for x in res.all()]))
    assert res.count() == 167

def test_model_without_all_charges(session):
    res = (session.query(Model.bigg_id)
           .join(ModelCompartmentalizedComponent)
           .filter(ModelCompartmentalizedComponent.charge == None)
           .distinct())
    print('Models without complete set of charges: %s' % ', '.join([x[0] for x in res.all()]))
    assert res.count() == 18
