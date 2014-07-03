from model import (Model, Component, Reaction, Compartment, Metabolite, 
                        Compartmentalized_Component, Model_Reaction, Reaction_Matrix, 
                        GPR_Matrix, Model_Compartmentalized_Component, Model_Gene, Gene)
class ReactionQuery():
    def get_model_reaction(self, reactionName, session):
	    return (session
			    .query(Model_Reaction, Reaction)
			    .join(Reaction).filter(reactionName == Reaction.name)
			    .first()[0])
    def get_model(self, modelName, session):
	    return (session.query(Model)
			    .filter(Model.name == modelName)
			    .first())
			
    def get_reaction(self, reactionName, session):
	    return (session
			    .query(Model_Reaction, Reaction)
			    .join(Reaction)
			    .filter(reactionName == Reaction.name)
			    .first()[1])

    def get_metabolite_list(self, reaction, session):
	    return [(x[0].identifier, int(x[1].stoichiometry)) 
			    for x in (session
			            .query(Component,Reaction_Matrix)
			            .join(Compartmentalized_Component)
			            .join(Reaction_Matrix)
			            .filter(Reaction_Matrix.reaction_id == reaction.id)
			            .all())]
    def get_gene_list(self , reactionName, session):
        return [x.name for x in (session
                                .query(Gene)
                                .join(Model_Gene)
                                .join(GPR_Matrix).
                                join(Model_Reaction)
                                .join(Reaction)
                                .filter(reactionName == Reaction.name)
                                .all())]
    def get_reaction_list(self, modelName, session):
	    return [(x.name) 
	            for x in (session
	            .query(Reaction)
	            .join(Model_Reaction)
	            .join(Model)
	            .filter(Model.name == modelName)
	            .all())]
	

class ModelQuery():
    def get_model(self, modelName, session):
        return (session.query(Model)
                .filter(Model.name == modelName)
                .first())
    def get_model_reaction_count(self, modelquery, session):
        return (session.query(Model_Reaction)
        .filter(Model_Reaction.model_id == modelquery.id)
        .count())
        
    def get_model_metabolite_count(self, modelquery, session):
        return (session
                .query(Model_Compartmentalized_Component)
                .filter(Model_Compartmentalized_Component.model_id == modelquery.id)
                .count())
    
    def get_gene_count(self, modelquery, session):
        return (session.query(Model_Gene)
                .filter(Model_Gene.model_id == modelquery.id)
                .count())
                
    def get_model_list(self, session):
        return [x.name for x in (session
                                .query(Model).all())]
                
class MetaboliteQuery():
    def get_reactions(self, metaboliteId, session):
        return (session
                .query(Reaction)
                .join(Reaction_Matrix)
                .join(Compartmentalized_Component)
                .join(Component)
                .filter(Component.identifier == metaboliteId)
                .all())
                
    def get_model_reaction(self, x, session):
        return (session
                .query(Model_Reaction)
                .join(Reaction)
                .filter(Reaction.id == x.id)
                .first())
    def get_model(self, modelReaction, session):
        return (session
            .query(Model)
            .filter( Model.id == modelReaction.model_id)
            .first())
    def get_metabolite_list(self, modelName, session):
        return [x.identifier for x in (session
                .query(Component)
                .join(Compartmentalized_Component)
                .join(Model_Compartmentalized_Component)
                .join(Model)
                .filter(Model.name == modelName)
                .all())]

class GeneQuery():
    def get_model_reaction(self, geneId, session):
        return (session
                .query(Model_Reaction)
                .join(GPR_Matrix)
                .join(Model_Gene)
                .join(Gene)
                .filter(Gene.name == geneId))
    def get_model(self, instance, session):
        return (session
                .query(Model)
                .filter( Model.id == instance.model_id)
                .first())
    def get_gene_list(self, modelName, session):
        return [x.name for x in (session
                                .query(Gene)
                                .join(Model_Gene)
                                .join(Model)
                                .filter(Model.name == modelName)
                                .all())]
                                
class StringBuilder():
    def build_reaction_string(self, metabolitelist, modelreaction):
        post_reaction_string =""
        pre_reaction_string =""
        for metabolite in metabolitelist:
            if float(metabolite[1])<0:
                if float(metabolite[1])!= -1:
                    pre_reaction_string += str(abs(metabolite[1])) + " " + metabolite[0] + " + "
                else:
                    pre_reaction_string += " " + metabolite[0] + " + "
            if float(metabolite[1])>0:
                if float(metabolite[1])!= 1:
                    post_reaction_string += str(abs(metabolite[1])) + " " + metabolite[0] + " + "
                else:
                    post_reaction_string += " " + metabolite[0] + " + "
        if modelreaction.lowerbound <0 and modelreaction.upperbound <=0:
            reaction_string = pre_reaction_string[:-2] + " <-- " + post_reaction_string[:-2]
        elif modelreaction.lowerbound >= 0:
            reaction_string = pre_reaction_string[:-2] + " --> " + post_reaction_string[:-2]
        else:
            reaction_string = pre_reaction_string[:-2] + " <==> " + post_reaction_string[:-2]
        return reaction_string
"""
def build_reaction_string(self, use_metabolite_names=False):
        def format(number):
            if number == 1:
                return ""
            if number == int(number):
                return str(int(number)) + " "
            return str(number) + " "
        reactant_dict = {}
        product_dict = {}
        id_type = 'id'
        if use_metabolite_names:
            id_type = 'name'
        reactant_bits = []
        product_bits = []
        for the_metabolite, coefficient in self._metabolites.items():
            name = str(getattr(the_metabolite, id_type))
            if coefficient > 0:
                product_bits.append(format(coefficient) + name)
            else:
                reactant_bits.append(format(abs(coefficient)) + name)

        reaction_string = ' + '.join(reactant_bits)
        if not self.reversibility:
            if self.lower_bound < 0 and self.upper_bound <=0:
                reaction_string += ' <-- '
            else:
                reaction_string += ' --> '
        else:
            reaction_string += ' <=> '
        reaction_string += ' + '.join(product_bits)
        return reaction_string   
"""                 
    
    