from ome.base import Session
from ome.models import (ModelReaction, Reaction, Model)

def matches_for_reaction_name(reaction_name):
    """ Find reactions with fuzzy matches to reaction name, and return
    statistics about the matching reactions.

    Arguments
    ---------

    reaction_name: the string to match against reaction names.

    """

    session = Session()

    regex = reaction_name.replace('-', '%').replace(' ', '%')
    print(regex)
    results = (session.query(ModelReaction, Reaction, Model)
               .join(Reaction)
               .join(Model)
               .filter(Reaction.name.ilike(regex))
               .all())
    print(results)

def model_fraction_sharing_reaction(reaction_bigg_id):
    """ Find the fraction of models that have the reaction id. Returns a tuple
    of (fraction, model_list).

    Arguments
    ---------

    reaction_bigg_id: the bigg id the of the reaction.

    """

    session = Session()

    all_models = session.query(Model.bigg_id).all();
    has_count = (session
                 .query(Model.bigg_id)
                 .join(ModelReaction)
                 .join(Reaction)
                 .filter(Reaction.bigg_id == reaction_bigg_id)
                 .all())
    print('%d of %d models (%.1f%%) have reaction %s' % (len(has_count),
                                                          len(all_models),
                                                          100.0 * len(has_count) / len(all_models),
                                                          reaction_bigg_id))

    print('\n'.join([str(x[0]) for x in all_models if x not in has_count]))

if __name__=="__main__":
    from sys import argv, exit
    if len(argv) < 2:
        print('Usage: python db_analysis.py "GAPD"')
        exit()
    model_fraction_sharing_reaction(argv[1])
