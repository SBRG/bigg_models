from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import Session
from sqlalchemy.ext.declarative import declarative_base

import pytest
from sqlalchemy.orm import sessionmaker, aliased
from sqlalchemy import create_engine, desc, func, or_
import sys

from ome.models import *
from ome.base import Session

def sharedReactions(model1, model2):
    session = Session()
    modelquery1 = session.query(Model).filter(Model.bigg_id == model1).first()
    modelquery2 = session.query(Model).filter(Model.bigg_id == model2).first()
    query =  session.query(ModelReaction.reaction_id).distinct().filter(or_(ModelReaction.model_id == modelquery1.id, ModelReaction.model_id == modelquery2.id))
    for r in query.all():
        session.query(Reaction).filter(Reaction.id == r).one().name
    print '' + str(query.count()) + ' shared reactions'
    #print ' this query was used: ' + str(query)
    session.close()

    
#sharedReactions('iS_1188','iWFL_1372')    
def shardMetabolites(model1, model2):
    session = Session()
    modelquery1 = session.query(Model).filter(Model.bigg_id == model1).first()
    modelquery2 = session.query(Model).filter(Model.bigg_id == model2).first()
    query = session.query(CompartmentalizedComponent.component_id).distinct().join(ModelCompartmentalizedComponent).filter(or_(ModelCompartmentalizedComponent.model_id == modelquery1.id, ModelCompartmentalizedComponent.model_id == modelquery2.id))
    for m in query.all():
        session.query(Metabolite).filter(Metabolite.id == m).one().name
    print '' + str(query.count()) + ' shared metabolites' 
    #print ' this query was used: ' + str(query)
    session.close()


def getModelsForReaction(reaction):
    session = Session()
    query = session.query(ModelReaction).distinct(ModelReaction.model_id).filter(ModelReaction.reaction_id == reaction.id)
    print query.count
    for rm in query.all():
        model = session.query(Model).filter(Model.id == rm.model_id).one()
        print model.bigg_id
    session.close()
    
def getModelsForMetabolite(metaboliteName):
    session = Session()
    metabolite = session.query(Metabolite).filter(Metabolite.name == metaboliteName)
    for cc in session.query(CompartmentalizedComponent).filter(CompartmentalizedComponent.component_id == metabolite.id).all():
        for mcc in session.query(ModelCompartmentalizedComponent).filter(ModelCompartmentalizedComponent.compartmentalized_component_id == cc.id).all():
            model = session.query(Model).filter(Model.id == mcc.model_id).first()
            print model.bigg_id
    session.close()
    
    #TODO
def getMetabolitesOfReaction(reactionName):
    session = Session()
    reaction = session.query(Reaction).filter(Reaction.name == reactionName)
    for met in session.query(ReactionMatrix).filter(ReactionMatrix.reaction_id == reaction.id).all():
        cc = session.query(CompartmentalizedComponent).filter(CompartmentalizedComponent.id == met.compartmentalized_component_id).first()
        print session.query(Metabolite).filter(Metabolite.id == cc.component_id).name
    session.close()
        
if __name__ == "__main__":
    if len(sys.argv) == 4:
        if str(sys.argv[1]) == 'models':
            model1 = str(sys.argv[2])
            model2 = str(sys.argv[3])
            #print "the reations that are shared between these two models are:"
            sharedReactions(model1, model2)
            #print "the metabolites that are shared between these two models are:"
            shardMetabolites(model1, model2)
    
