from sqlalchemy import create_engine, ForeignKey, Column, Integer, String, Numeric, Table, MetaData, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

#engine = create_engine('postgresql://localhost:5432/bigg2')
engine = create_engine("postgresql://jslu@localhost:5432/bigg2")

Base = declarative_base(bind=engine)
metadata = MetaData(bind=engine)

Session = sessionmaker(bind=engine)
session = Session()

class Reaction(Base):
	__tablename__ = 'reaction'
	modelversion_id = Column(Integer)
	name = Column(String)
	abbreviation = Column(String)
	equation = Column(String)
	subsystem = Column(String)
	reflection = Column(String)
	id = Column(Integer, primary_key = True)
	gene_reaction_rule = Column(String)
	lower_bound = Column(Numeric)
	upper_bound = Column(Numeric)
	objective_coefficient = Column(Numeric)
	reversibility = Column(Integer)
	def __repr__(self):
		return 'Reaction (%d): %s' % (modelversion_id, abbreviation)
	
class Metabolite(Base):
	__tablename__ = 'metabolite'
	modelversion_id = Column(Integer)
	abbreviation = Column(String)
	officialname = Column(String)
	formula = Column(String)
	charge = Column(Integer)
	compartment = Column(String)
	id = Column(Integer, primary_key=True)
	
class Model(Base):
	__tablename__ = 'model'
	id = Column(Integer, primary_key = True)
	description = Column(String)
	currentime = Column(DateTime)
	modelversion_id = Column(Integer)
	name = Column(String)
	firstcreated = Column(DateTime)

class ReactionMetabolite(Base):	
	__tablename__= 'reactionmetabolite'
	modelversion_id = Column(Integer)
	reaction_id = Column(Integer, primary_key=True)
	molecule_id = Column(Integer, primary_key=True)
	s = Column(Numeric)	

class gpr(Base):
	__tablename__='gpr'
	modelversion_id = Column(Integer)
	reaction_id = Column(Integer, ForeignKey('reaction.reaction_id'), nullable=False)
	gene_id = Column(Integer, ForeignKey('gene.gene_id'), nullable=False)
	reactionrule = Column(String, primary_key=True)

class Formula(Base):
	__tablename__='formula'
	formula = Column(String)
	id = Column(Integer, primary_key=True)
	weight = Column(String)

class Gene(Base):
	__tablename__='gene'
	modelversion_id = Column(Integer)
	genesymbol = Column(String)
	name = Column(String)
	locus_start = Column(String)
	locus_end = Column(String)
	id = Column(Integer, primary_key=True)

"""	
class ModelReaction(Base):
	__tablename__='modelreaction'
	index = Column(Integer, primary_key=True)
	model_index = Column(Integer, ForeignKey('model.index'), nullable=False)
	reaction_id = Column(Integer, ForeignKey('reaction.reaction_id'), nullable=False)
"""

	
