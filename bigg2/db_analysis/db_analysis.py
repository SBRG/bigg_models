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
    print regex
    results = (session.query(ModelReaction, Reaction, Model)
               .join(Reaction)
               .join(Model)
               .filter(Reaction.name.ilike(regex))
               .all())
    print results
    
def model_fraction_sharing_reaction(reaction_bigg_id):
    """ Find the fraction of models that have the reaction id. Returns a tuple
    of (fraction, model_list).

    Arguments
    ---------

    reaction_bigg_id: the bigg id the of the reaction.

    """

    session = Session()

    raise NotImplementedError()
    # results = (session.query(ModelReaction, Reaction.id, Model)
    #            .join(Reaction)
    #            .join(Model)
    #            .filter(Reaction.biggid == reaction_bigg_id)
    #            .any())
    # print results

if __name__=="__main__":
    from sys import argv, exit
    if len(argv) < 2:
        print 'Usage: python db_analysis.py "GAPD"'
        exit()
    model_fraction_sharing_reaction(argv[1])
