from sqlalchemy import create_engine, ForeignKey, Column, Integer, String, Numeric, Table, MetaData, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import UniqueConstraint
engine = create_engine("postgresql://dbuser@localhost:5432/bigg2")

Base = declarative_base(bind=engine)
metadata = MetaData(bind=engine)

Session = sessionmaker(bind=engine)
session = Session()

class Gene(Base):
	__tablename__='gene'
	id = Column(Integer,primary_key=True)
	name = Column(String)

class Model_Gene(Base):
	__tablename__='model_gene'
	id = Column(Integer, primary_key=True)
	model_id = Column(Integer, ForeignKey('model.id'), nullable=False)
	gene_id = Column(Integer, ForeignKey('gene.id'), nullable=False)

class GPR_Matrix(Base):
    __tablename__='gpr_matrix'
    id = Column(Integer, primary_key=True)
    model_gene_id = Column(Integer, ForeignKey('model_gene.id'), nullable=False)
    model_reaction_id = Column(Integer, ForeignKey('model_reaction.id'), nullable=False)
    
        
class Component(Base):
	__tablename__='component'
	id = Column(Integer, primary_key=True)
	identifier = Column(String)
	name = Column(String)
	formula = Column(String)
	
class Metabolite(Base):
	__tablename__='metabolite'
	id = Column(Integer, ForeignKey('component.id'), primary_key=True)

class Compartmentalized_Component(Base):
	__tablename__='compartmentalized_component'
	id = Column(Integer, primary_key=True)
	component_id = Column(Integer, ForeignKey('component.id'), nullable=False)
	compartment_id = Column(Integer, ForeignKey('compartment.id'), nullable=False)
	UniqueConstraint('compartment_id', 'component_id')
	
class Model_Compartmentalized_Component(Base):
	__tablename__='model_compartmentalized_component'
	id = Column(Integer, primary_key=True)
	model_id = Column(Integer, ForeignKey('model.id'), nullable=False)
	compartmentalized_component_id = Column(Integer, ForeignKey('compartmentalized_component.id'), nullable=False)
	
class Compartment(Base):
	__tablename__='compartment'
	id = Column(Integer, primary_key=True)
	name = Column(String, unique = True)
	
class Model(Base):
	__tablename__='model'
	id = Column(Integer, primary_key=True)
	name = Column(String)
	firstcreated = Column(DateTime)
	UniqueConstraint('name', 'firstcreated')
	
class Model_Reaction(Base):
	__tablename__='model_reaction'
	id = Column(Integer, primary_key=True)
	reaction_id = Column(Integer, ForeignKey('reaction.id'), nullable=False)
	model_id = Column(Integer, ForeignKey('model.id'), nullable=False)
	name = Column(String)
	upperbound = Column(Numeric)
	lowerbound = Column(Numeric)
	gpr = Column(String)
	UniqueConstraint('reaction_id', 'model_id')
	
class Reaction_Matrix(Base):
	__tablename__='reaction_matrix'
	id = Column(Integer, primary_key=True)
	reaction_id = Column(Integer, ForeignKey('reaction.id'), nullable=False)
	compartmentalized_component_id = Column(Integer, ForeignKey('compartmentalized_component.id'), nullable=False)
	stoichiometry = Column(Numeric)
	UniqueConstraint('reaction_id', 'compartmentalized_component')
	
class Reaction(Base):
	__tablename__='reaction'
	id = Column(Integer, primary_key=True)
	name = Column(String)
	long_name = Column(String)
	
	
Base.metadata.create_all(engine)