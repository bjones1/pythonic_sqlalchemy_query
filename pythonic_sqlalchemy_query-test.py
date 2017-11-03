# ****************************************************************************************************
# pythonic_sqlalchemy_query-test.py - Unit tests and demonstrations for `pythonic_sqlalchemy_query.py`
# ****************************************************************************************************
from sqlalchemy import create_engine, ForeignKey, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.orm import aliased
from sqlalchemy.ext import baked
from sqlalchemy.sql.expression import bindparam
from sqlalchemy.sql.expression import func

from pythonic_sqlalchemy_query import (
    QueryMaker, QueryMakerDeclarativeMeta, QueryMakerQuery, QueryMakerSession
)
#
# Demo code
# =========
#
# Database setup
# --------------
engine = create_engine('sqlite:///:memory:')#, echo=True)
# See `sessionmaker <http://docs.sqlalchemy.org/en/latest/orm/session_api.html?highlight=sessionmaker#sqlalchemy.orm.session.sessionmaker>`_, `query_cls <http://docs.sqlalchemy.org/en/latest/orm/session_api.html?highlight=sessionmaker#sqlalchemy.orm.session.Session.params.query_cls>`_.
Session = sessionmaker(bind=engine, query_cls=QueryMakerQuery, class_=QueryMakerSession)
session = Session()
#
# Model
# -----
# Use the QueryMakerDeclarativeMeta in our `Declarative class`_ definitions.
Base = declarative_base(metaclass=QueryMakerDeclarativeMeta)
#
# Create a simple User and Adddress based on the `tutorial <http://docs.sqlalchemy.org/en/latest/orm/tutorial.html>`_.
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    fullname = Column(String)
    password = Column(String)

    # Define a default query which assumes the key is a User's name if given a string.
    @classmethod
    def default_query(cls, key):
        if isinstance(key, str):
            return cls.name == key

    def __repr__(self):
       return "<User(name='%s', fullname='%s', password='%s')>" % (
                            self.name, self.fullname, self.password)

class Address(Base):
    __tablename__ = 'addresses'
    id = Column(Integer, primary_key=True)
    email_address = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))

    user = relationship("User", back_populates="addresses")

    # Define a default query which assumes the key is an Address's e-mail address.
    @classmethod
    def default_query(cls, key):
        return cls.email_address == key

    def __repr__(self):
        return "<Address(email_address='%s')>" % self.email_address

User.addresses = relationship(
    "Address", order_by=Address.id, back_populates="user")

# Create all tables.
Base.metadata.create_all(engine)
#
# Test data
# ---------
jack = User(name='jack', fullname='Jack Bean', password='gjffdd')
jack.addresses = [
                  Address(email_address='jack@google.com'),
                  Address(email_address='j25@yahoo.com')]
session.add(jack)
session.commit()
#
# Demonstration and unit tests
# ----------------------------
# Print the results of a query and optionally compare the results with the expected value.
def _print_query(str_query, locals_=None):
    print('-'*78)
    print('Query: ' + str_query)
    query = eval(str_query, globals(), locals_)
    if isinstance(query, QueryMaker):
        query = query.q
    print('Resulting SQL emitted:\n{}\nResults:'.format(str(query)))
    return query

def print_query(str_query, expected_result=None, locals_=None):
    query = _print_query(str_query, locals_)
    for _ in query:
        print(_)
    print()
    if expected_result:
        assert query.all() == expected_result
    return query
#
# Traditional versus Pythonic
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^
def test_traditional_versus_pythonic():
    # Create a query to select the Address for 'jack@google.com' from User 'jack'.
    #
    # The Pythonic version of a query:
    pythonic_query = "session.User['jack'].addresses['jack@google.com']"
    print_query(pythonic_query, [jack.addresses[0]])

    # The traditional approach:
    traditional_query = (
        # Ask for the Address...
        "session.query(Address)."
        # by querying a User named 'jack'...
        "select_from(User).filter(User.name == 'jack')."
        # then joining this to the Address 'jack@google.com`.
        "join(Address).filter(Address.email_address == 'jack@google.com')"
    )
    print_query(traditional_query, [jack.addresses[0]])
#
# More examples
# ^^^^^^^^^^^^^
def test_more_examples():
    # Ask for the full User object for jack.
    print_query("session.User['jack']", [jack])
    # Ask only for Jack's full name.
    print_query("session.User['jack'].fullname", [(jack.fullname, )])
    # Get all of Jack's addresses.
    print_query("session.User['jack'].addresses", jack.addresses)
    # Get just the email-address of all of Jack's addresses.
    print_query("session.User['jack'].addresses.email_address", [(x.email_address, ) for x in jack.addresses])
    # Get just the email-address j25@yahoo.com of Jack's addresses.
    print_query("session.User['jack'].addresses['j25@yahoo.com']", [jack.addresses[1]])
    # Ask for the full Address object for j25@yahoo.com.
    print_query("session.Address['j25@yahoo.com']", [jack.addresses[1]])
    # Ask for the User associated with this address.
    print_query("session.Address['j25@yahoo.com'].user", [jack])
    # Use a filter criterion to select a User with a full name of Jack Bean.
    print_query("session.User[User.fullname == 'Jack Bean']", [jack])
    # Use two filter criteria to find the user named jack with a full name of Jack Bean.
    print_query("session.User['jack'][User.fullname == 'Jack Bean']", [jack])
    # Look for the user with id 1.
    print_query("session.User[1]", [jack])
    # Use an SQL expression in the query.
    print_query("session.User[func.lower(User.fullname) == 'jack bean']", [jack])

    # Transform to a query for indexing.
    assert _print_query("session.Address.q[1]") == jack.addresses[1]
    # Call the ``count`` method on the underlying Query object.
    assert _print_query("session.Address.q.count()") == 2
    # Call the ``order_by`` method on the underlying Query object.
    print_query("session.Address.q.order_by(Address.email_address)", list(reversed([jack.addresses][0])))
    # Use the underlying query object for complex joins.
    adalias1 = aliased(Address)
    print_query("session.User.q.join(adalias1, User.addresses)['j25@yahoo.com']", [jack.addresses[1]], locals())

    # Queries are generative_: ``qm`` can be re-used.
    qm = session.User['jack']
    print_query("qm.addresses", jack.addresses, locals())
    print_query("qm", [jack], locals())
#
# Advanced examples
# ^^^^^^^^^^^^^^^^^
def test_advanced_examples():
    # Specify exactly what to return by accessing the underlying query.
    print_query("session.User['jack'].addresses._query.add_columns(User.id, Address.id)", [(1, 1), (1, 2)] )

    # If QueryMakerSession isn't used, the session can be provided at the end of the query. However, this means the ``.q`` property won't be useful (since it has no assigned session).
    print_query("User['jack'].to_query(session)", [jack])

    # If the QueryMakerDeclarativeMeta_ metaclass wasn't used, this performs the equivalent of ``User['jack']`` manually.
    print_query("QueryMaker(User)['jack'].to_query(session)", [jack])

    # Add to an existing query: first, find the User named jack.
    q = session.query().select_from(User).filter(User.name == 'jack')
    # Then ask for the Address for jack@google.com.
    print_query("q.query_maker().addresses['jack@google.com']", [jack.addresses[0]], locals())
    # Do the same manually (without relying on the QueryMakerQuery_ ``query_maker`` method).
    print_query("QueryMaker(query=q).addresses['jack@google.com']", [jack.addresses[0]], locals())

    # `Baked queries <http://docs.sqlalchemy.org/en/latest/orm/extensions/baked.html>`_ are supported.
    bakery = baked.bakery()
    baked_query = bakery(lambda session: session.User)
    baked_query += lambda query: query[User.name == bindparam('username')]
    # The last item in the query must end with a ``.q``.
    baked_query += lambda query: query.q.order_by(User.id).q
    print_query("baked_query(session).params(username='jack', email='jack@google.com')", [jack], locals())
#
# main
# ^^^^
# Run the example code.
if __name__ == '__main__':
    test_traditional_versus_pythonic()
    test_more_examples()
    test_advanced_examples()
