from sqlalchemy import create_engine, ForeignKey, Column, Integer, String, Numeric, Table, MetaData, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine("postgresql://jslu@localhost:5432/bigg2")

Base = declarative_base(bind=engine)
metadata = MetaData(bind=engine)

Session = sessionmaker(bind=engine)
session = Session()

class Component(Base):
	__tablename__='component'
	id = Column(Integer, primary_key=True)
	name = Column(String)
	formula = Column(String)
	
class Metabolite(Base):
	__tablename__='metabolite'
	id = Column(Integer, ForeignKey('component.id'), primary_key=True)

class Compartmentalized_Component(Base):
	__tablename__='compartmentalized_component'
	componenent_id = Column(Integer, ForeignKey('component.id'), primary_key=True)
	compartment_id = Column(Integer, ForeignKey('compartment.id'), primary_key=True)
	
class Compartment(Base):
	__tablename__='compartment'
	id = Column(Integer, primary_key=True)
	name = Column(String)
	
class Model(Base):
	__tablename__='model'
	id = Column(Integer, primary_key=True)
	name = Column(String)
	firstcreated = Column(DateTime)
	
class Model_Reaction(Base):
	__tablename__='model_reaction'
	id = Column(Integer, primary_key=True)
	reaction_id = Column(Integer, ForeignKey('reaction.id'), primary_key=True)
	model_id = Column(Integer, ForeignKey('model.id'), primary_key=True)
	name = Column(String)
	upperbound = Column(Numeric)
	lowerbound = Column(Numeric)
	gpr = Column(String)
	
class Reaction_Matrix(Base):
	__tablename__='reaction_matrix'
	reaction_id = Column(Integer, ForeignKey('reaction.id'), primary_key=True)
	compartmentalized_component_id = Column(Integer, ForeignKey('compartmentalized_component.id'), primary_key=True)
	model_id = Column(Integer, ForeignKey('model.id'), primary_key=True)
	stoichiometry = Column(Numeric)
	
class Reaction(Base):
	__tablename__='reaction'
	id = Column(Integer, primary_key=True)
	name = Column(String)
	long_name = Column(String)
	
	
Base.metadata.create_all(engine)