from cobra.io import sbml

def createSBML(input):
    raise Exception('Not implemented: need to replace theseus dependency with a local library')
    model = models.load_model(input)        
    sbml.write_cobra_model_to_sbml_file(model, ""+model.id + ".xml")
    return model
    
