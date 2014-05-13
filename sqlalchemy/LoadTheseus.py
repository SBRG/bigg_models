from theseus import models
from sqlalchemy import create_engine, ForeignKey, Column, Integer, String, Numeric, Table, MetaData, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import 

Session = sessionmaker()

engine = create_engine("postgresql://jslu@localhost:5432/bigg2")

Session.configure(bind=engine)

"""
create all the tables with no foreign keys then use select where
"""
class Model:
	selectedModel = None
	def __init__(self, name):
		self.name = name
		selectedModel = models.load_model(name)
	"""
	def insertReactions(self, session):
		for x in selectedModel.reactions:
			reaction = Reaction(name=x.id,long_name=x.name)
			session.add(reaction)
	"""
	def insertModel(self, session):
		model = Model(id = selectedModel.id, name = selectedModel.name, firstcreated = '2008-11-11 13:23:44')
		session.add(model)
		
models = [models.get_model_list()]
class Component:
	def loadComponents(session):
		for model in models:
			for metabolite in model.metabolites():
				component = Component(name = metabolite.name, formula = metabolite.formula)
				metabolite = Metabolite()
				session.add(metabolite)
				session.add(component)
	
class Compartmentalized_Component: 
class Reaction:
class Compartment:
	def loadCompartments



	
@contextmanager
def create_Session():
	session = Session()
	try:
		yield session
		session.commit()
	except:
		session.rollback()
		raise
	finally:
		session.close()
		
def run_program():
	with create_Session() as session:
		Model('ijo1366').insertReactions(session)
		
if __name__ == '__main__':
	run_program()
