from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import Session

from your.package import Base  # This is your declarative base class
//unit testing sqlalchemy apps
//http://alextechrants.blogspot.com/2013/08/unit-testing-sqlalchemy-apps.html
def setup_module():
    global transaction, connection, engine

    # Connect to the database and create the schema within a transaction
    engine = create_engine('postgresql://jslu@localhost:5432/bigg2')
    connection = engine.connect()
    transaction = connection.begin()
    Base.metadata.create_all(connection)

    # If you want to insert fixtures to the DB, do it here


def teardown_module():
    # Roll back the top level transaction and disconnect from the database
    transaction.rollback()
    connection.close()
    engine.dispose()
 

class DatabaseTest(object):
    def setup(self):
        self.__transaction = connection.begin_nested()
        self.session = Session(connection)

    def teardown(self):
        self.session.close()
        self.__transaction.rollback()