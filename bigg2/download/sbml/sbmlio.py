from cobra.io import sbml
from theseus import models


def createSBML(input):
    model = models.load_model(input)        
    sbml.write_cobra_model_to_sbml_file(model, ""+model.id + ".xml")
    return model