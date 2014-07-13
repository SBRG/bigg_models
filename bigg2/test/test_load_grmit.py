from bigg2.load.LoadGrmit import *

from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import Session
from sqlalchemy.ext.declarative import declarative_base

from pytest import raises

#unit testing sqlalchemy apps
#http://alextechrants.blogspot.com/2013/08/unit-testing-sqlalchemy-apps.html



def setup_module():
    global transaction, connection, engine, geneTable, modelTable, reactionTable, reactionmetaboliteTable, metaboliteTable, bigg2session, grmitsession
    # Connect to the database and create the schema within a transaction
    engine = create_engine('postgresql://dbuser@localhost:5432/test')
    Session2 = sessionmaker()
    grmitengine = create_engine("postgresql://justin:justin@pestis:5432/grmit")
    connection2 = grmitengine.connect()
    grmitsession = Session(connection2)
    transaction2 = connection2.begin()
    
    connection = engine.connect()
    bigg2session = Session(connection)
    transaction = connection.begin()
    
    #metaboliteTable = Table('metabolite', meta, autoload=True, autoload_with=grmitengine)
    #geneTable = Table('gene', meta, autoload=True, autoload_with=grmitengine)
    #gprTable = Table('gpr', meta, autoload=True, autoload_with=grmitengine)
    #modelTable = Table('model', meta, autoload=True, autoload_with=grmitengine)
    #reactionTable = Table('reaction', meta, autoload=True, autoload_with=grmitengine)
    #reactionmetaboliteTable = Table('reactionmetabolite', meta, autoload=True, autoload_with=grmitengine)
    # If you want to insert fixtures to the DB, do it here


def teardown_module():
    # Roll back the top level transaction and disconnect from the database
    transaction.rollback()
    connection.close()
    engine.dispose()
 

class DatabaseTest(object):
    def setup(self):
        self.transaction = connection.begin_nested()
        self.session = Session(connection)

        
    def teardown(self):
        self.transaction.rollback()

class TestLoadGrmit(DatabaseTest):
    setup_module()
    def testLoadModel(self):
        #DatabaseTest.setup(self)
        transaction = connection.begin_nested()
        transaction2 = connection.begin_nested()
        loadModel(modelTable, grmitsession, bigg2session)
        #transaction.rollback()
        
x = TestLoadGrmit()
x.testLoadModel()
    
