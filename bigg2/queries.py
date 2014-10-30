from ome.models import (Model, Component, Reaction, Compartment, Metabolite, 
                        CompartmentalizedComponent, ModelReaction, ReactionMatrix, 
                        GPRMatrix, ModelCompartmentalizedComponent, ModelGene, Gene, Chromosome)
class ReactionQuery():
    def get_ModelReaction(self, reactionId, modelId, session):
        return (session
            .query(ModelReaction)
            .filter(ModelReaction.reaction_id == reactionId)
            .filter(ModelReaction.model_id == modelId))

    def get_model(self, modelName, session):
        return (session.query(Model)
                .filter(Model.bigg_id == modelName)
                .first())
            
    def get_reaction(self, reactionName, session):
        return (session
                .query(ModelReaction, Reaction)
                .join(Reaction)
                .filter(reactionName == Reaction.name)
                .first()[1])
    """
    def get_metabolite_list(self, modelquery, reaction, session):
        return [(x[0].biggid, x[1].stoichiometry, x[2].name) 
                for x in (session
                        .query(Metabolite,ReactionMatrix,Compartment)
                        .join(Component)
                        .join(CompartmentalizedComponent)
                        
                        .join(ModelCompartmentalizedComponent)
                        .join(Model)
                        .join(ReactionMatrix)
                        .filter(ReactionMatrix.reaction_id == reaction.id)
                        .filter(Model.id == modelquery.id)
                        )]
    """
    def get_metabolite_list(self, modelquery, reaction, session):
        return [(x[0].name, x[1].stoichiometry, x[2].name) 
                for x in (session
                        .query(Metabolite,ReactionMatrix,Compartment)
                        #.join(Component)
                        .join(CompartmentalizedComponent)
                        .join(Compartment)
                        .join(ModelCompartmentalizedComponent)
                        .join(Model)
                        .join(ReactionMatrix)
                        .filter(ReactionMatrix.reaction_id == reaction.id)
                        .filter(Model.id == modelquery.id)
                        )]
    def get_gene_list(self , reaction, modelquery, session):
        chroms = session.query(Chromosome).filter(Chromosome.genome_id == modelquery.genome_id).all()
        result = []
        for chrom in chroms:
            result.extend([(x.name,x.locus_id) for x in (session
                                .query(Gene)
                                .join(ModelGene)
                                .join(GPRMatrix)
                                .join(ModelReaction)
                                .join(Model)
                                .join(Reaction)
                                .filter(chrom.id == Gene.chromosome_id)
                                .filter(reaction.id == Reaction.id)
                                .all())])
        return result
    def get_reaction_list(self, modelName, session):
        return [(x.name) 
                for x in (session
                .query(Reaction)
                .join(ModelReaction)
                .join(Model)
                .filter(Model.bigg_id == modelName)
                .all())]
    

class ModelQuery():
    def get_model(self, modelName, session):
        return (session.query(Model)
                .filter(Model.bigg_id == modelName)
                .first())
    def get_ModelReaction_count(self, modelquery, session):
        return (session.query(ModelReaction)
        .filter(ModelReaction.model_id == modelquery.id)
        .count())
        
    def get_model_metabolite_count(self, modelquery, session):
        return (session
                .query(ModelCompartmentalizedComponent)
                .filter(ModelCompartmentalizedComponent.model_id == modelquery.id)
                .count())
    
    def get_gene_count(self, modelquery, session):
        return (session.query(ModelGene)
                #.join(Model)
                #.join(Gene)
                #.filter(Model.genome_id  == Gene.genome_id)
                .filter(ModelGene.model_id == modelquery.id)
                
                .count())
                
    def get_model_list(self, session):
        return [x.bigg_id for x in (session
                                .query(Model).all())]
                
class MetaboliteQuery():
    def get_ModelReactions(self, metaboliteId, compartmentName, modelquery, session):
        return (session
                .query(Reaction)
                .join(ModelReaction)
                .join(ReactionMatrix)
                .join(CompartmentalizedComponent)
                .join(Compartment)
                .join(Component)
                .join(Metabolite)
                .filter(Compartment.name == compartmentName)
                .filter(Metabolite.name == metaboliteId.split("_")[0])
                .filter(ModelReaction.model_id == modelquery.id)
                .all())
    """         
    def get_ModelReaction(self, x, m, session):
        return (session
                .query(ModelReaction)
                .filter(ModelReaction.reaction_id == x)
                .filter(ModelReaction.model_id == m)
                .all())
    """
    def get_model(self, modelReaction, session):
        return (session
            .query(Model)
            .filter( Model.id == modelReaction.model_id)
            .first())
    def get_metabolite_list(self, modelName, session):
        return [(x[0].name, x[1].name) for x in (session
                .query(Metabolite, Compartment)
                .join(CompartmentalizedComponent)
                #.join(Compartment)
                .join(ModelCompartmentalizedComponent)
                .join(Model)
                .filter(CompartmentalizedComponent.compartment_id == Compartment.id)
                .filter(Model.bigg_id == modelName)
                .all())]

class GeneQuery():
    def get_ModelReaction(self, geneId, session):
        return (session
                .query(ModelReaction)
                .join(GPRMatrix)
                .join(ModelGene)
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
                                .join(ModelGene)
                                .join(Model)
                                #.filter(Model.genome_id == Gene.genome_id)
                                .filter(Model.bigg_id == modelName)
                                .all())]
                                
class StringBuilder():
    def build_reaction_string(self, metabolitelist, modelreaction):
        post_reaction_string =""
        pre_reaction_string =""
        for metabolite in metabolitelist:
            if float(metabolite[1])<0:
                if float(metabolite[1])!= -1:
                    pre_reaction_string += "{0:.1f}".format(abs(metabolite[1])) + " " + metabolite[0]+"_"+metabolite[2] + " + "
                else:
                    pre_reaction_string += " " + metabolite[0]+"_"+metabolite[2] + " + "
            if float(metabolite[1])>0:
                if float(metabolite[1])!= 1:
                    post_reaction_string += "{0:.1f}".format(abs(metabolite[1])) + " " + metabolite[0]+"_"+metabolite[2] + " + "
                else:
                    post_reaction_string += " " + metabolite[0]+"_"+metabolite[2] + " + "
        if len(metabolitelist) == 1:
            reaction_string = pre_reaction_string[:-2] + " &#8652; " + post_reaction_string[:-2]
        elif modelreaction.lowerbound <0 and modelreaction.upperbound <=0:
            reaction_string = pre_reaction_string[:-2] + " &#10229; " + post_reaction_string[:-2]
        elif modelreaction.lowerbound >= 0:
            reaction_string = pre_reaction_string[:-2] + " &#10230; " + post_reaction_string[:-2]
        else:
            reaction_string = pre_reaction_string[:-2] + " &#8652; " + post_reaction_string[:-2]
        return reaction_string
           
    
    
