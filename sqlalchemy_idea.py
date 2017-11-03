# ******************************************************************
# QueryMaker - Proivde concise, Pythonic query syntax for SQLAlchemy
# ******************************************************************
from sqlalchemy import create_engine, ForeignKey, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy.orm import sessionmaker, Query, relationship
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty
from sqlalchemy.orm.base import _generative
from sqlalchemy.sql.elements import ClauseElement
from sqlalchemy.orm.session import Session
from sqlalchemy.orm.util import class_mapper
from sqlalchemy.orm.exc import UnmappedClassError
from sqlalchemy.inspection import inspect
from sqlalchemy.sql.expression import func
#
# QueryMaker
# ==========
# This class provides a concise, Pythonic syntax for simple queries; for example, ``User['jack'].addresses`` produces a Query_ for the Address of a User named jack. See the `demonstration and unit tests`_ for examples.
#
# This works by translating class instances in a query/select, indexes into filters, and columns/relationships into joins. The following code shows the Pythonic syntax on the first line, followed by the resulting translation into SQLAlchemy performed by this class on the next line.
#
# .. code:: Python
#   :number-lines:
#
#   User                        ['jack']                   .addresses
#   Query([]).select_from(User).filter(User.name == 'jack').join(Address).add_entity(Address)
#
#
class QueryMaker:
    def __init__(self,
      # A `Declarative class <http://docs.sqlalchemy.org/en/latest/orm/tutorial.html#declare-a-mapping>`_ to query.
      declarative_class,
      # Optionally, begin with an existing query_.
      query=None):

        # Keep track of which `Declarative class`_ we're querying.
        assert _is_sa_mapped(declarative_class)
        self.declarative_class = declarative_class
        # Keep track of the last selectable construct, to generate the select in ``to_query``.
        self.select = declarative_class
        # If it's not provied, create an empty `query <http://docs.sqlalchemy.org/en/latest/orm/query.html>`_; ``to_query`` will fill in the missing information. TODO: If a query was provided, could I infer the declarative_class based on what the left side of a join would be? There's a reset_joinpoint, but I want to find the current joinpoint. There's a _joinpoint _joinpoint_zero(), but I don't understand these very well.
        self.query = query or Query([]).select_from(declarative_class)
        assert isinstance(self.query, Query)

    # Copied verbatim from ``sqlalchemy.orm.query.Query._clone``. This adds the support needed for the _`generative` interface. (Mostly) quoting from query_, "QueryMaker_ features a generative interface whereby successive calls return a new QueryMaker_ object, a copy of the former with additional criteria and options associated with it."
    def _clone(self):
        cls = self.__class__
        q = cls.__new__(cls)
        q.__dict__ = self.__dict__.copy()
        return q

    # Looking up a class's `Column <http://docs.sqlalchemy.org/en/latest/core/metadata.html#sqlalchemy.schema.Column>`_ or `relationship <http://docs.sqlalchemy.org/en/latest/orm/relationship_api.html#sqlalchemy.orm.relationship>`_ generates the matching query.
    @_generative()
    def __getattr__(self, name):
        # Find the Column_ or relationship_ in the `Declarative class`_ we're querying.
        attr = getattr(self.declarative_class, name)
        # If the attribute refers to a column, save this as a possible select statement. Note that a Column_ gets replaced with an `InstrumentedAttribute <http://docs.sqlalchemy.org/en/latest/orm/internals.html?highlight=instrumentedattribute#sqlalchemy.orm.attributes.InstrumentedAttribute>`_; see `QueryableAttribute <http://docs.sqlalchemy.org/en/latest/orm/internals.html?highlight=instrumentedattribute#sqlalchemy.orm.attributes.QueryableAttribute.property>`_.
        if isinstance(attr.property, ColumnProperty):
            self.select = attr
        elif isinstance(attr.property, RelationshipProperty):
            # Figure out what class this relationship refers to. See `mapper.params.class_ <http://docs.sqlalchemy.org/en/latest/orm/mapping_api.html?highlight=mapper#sqlalchemy.orm.mapper.params.class_>`_.
            self.declarative_class = attr.property.mapper.class_
            # Update the query by performing the implied join.
            self.query = self.query.join(self.declarative_class)
            # Save this relationship as a possible select statement.
            self.select = self.declarative_class
        else:
            # This isn't a Column_ or a relationship_.
            assert False

    # Indexing the object performs the implied filter. For example, ``User['jack']`` implies ``query.filter(User.name == 'jack')``.
    @_generative()
    def __getitem__(self,
      # Mostly often, this is a key which will be filtered by the ``default_query`` method of the currently-active `Declarative class`_. In the example above, the ``User`` class must define a ``default_query`` to operate on strings.
      #
      # However, it may also be a filter criterion, such as ``User[User.name == 'jack']``.
      key):

        # See if this is a filter criterion; if not, rely in the ``default_query`` defined by the `Declarative class`_ or fall back to the first primary key.
        criteria = None
        if isinstance(key, ClauseElement):
            criteria = key
        elif hasattr(self.declarative_class, 'default_query'):
            criteria = self.declarative_class.default_query(key)
        if criteria is None:
            pks = inspect(self.declarative_class).primary_key
            criteria = pks[0] == key
        self.query = self.query.filter(criteria)

    # Transform this object into a Query_.
    def to_query(self,
      # Optionally, the `Session <http://docs.sqlalchemy.org/en/latest/orm/session_api.html?highlight=session#sqlalchemy.orm.session.Session>`_ to run this query in.
      session=None):

        # If a session was specified, use it to produce the query_; otherwise, use the existing query_.
        query = self.query.with_session(session) if session else self.query
        # Choose the correct method to select either a column or a class (e.g. an entity). As noted earlier, a Column_ becomes and InstrumentedAttribute_.
        if isinstance(self.select, InstrumentedAttribute):
            return query.add_columns(self.select)
        else:
            return query.add_entity(self.select)
#
# QueryMakerDeclarativeMeta
# -------------------------
# Turn indexing of a `Declarative class`_ into a query. For example, ``User['jack']`` is a query. See the model_ for an example of its use.
class QueryMakerDeclarativeMeta(DeclarativeMeta):
    def __getitem__(cls, key):
        return QueryMaker(cls)[key]
#
# QueryMakerQuery
# ---------------
# Provide support for changing a Query instance into a QueryMaker instance. See the `database setup`_ for an example of its use.
class QueryMakerQuery(Query):
    def query_maker(self, declarative_class):
        return QueryMaker(declarative_class, self)
#
# QueryMakerSession
# -----------------
# Create a Session which recognizes declarative classes as an attribute. This enables ``session.User['jack']``. See the `database setup`_ for an example of its use.
class QueryMakerSession(Session):
    def __getattr__(self, name):
        g = globals()
        if (name in g) and _is_sa_mapped(g[name]):
            return QueryMaker(g[name], self.query().select_from(g[name]))
        else:
            return super().__getattr__(name)

# Copied from https://stackoverflow.com/a/7662943.
def _is_sa_mapped(cls):
    try:
        class_mapper(cls)
        return True
    except UnmappedClassError:
        return False
#
# Demo code
# =========
#
# Database setup
# --------------
engine = create_engine('sqlite:///:memory:')#, echo=True)
# See `sessionmaker <http://docs.sqlalchemy.org/en/latest/orm/session_api.html?highlight=sessionmaker#sqlalchemy.orm.session.sessionmaker>`_, `query_cls <http://docs.sqlalchemy.org/en/latest/orm/session_api.html?highlight=sessionmaker#sqlalchemy.orm.session.Session.params.query_cls>`_.
Session_ = sessionmaker(bind=engine, query_cls=QueryMakerQuery, class_=QueryMakerSession)
session = Session_()
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
def print_query(str_query, expected_result=None, locals_=None):
    print('-'*78)
    print('Query: ' + str_query)
    query = eval(str_query, globals(), locals_)
    print('Resulting SQL emitted:\n{}\nResults:'.format(str(query)))
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
    pythonic_query = "User['jack'].addresses['jack@google.com'].to_query(session)"
    print_query(pythonic_query, [jack.addresses[0]])

    # The traditional approach:
    traditional_query = """(
        # Ask for the Address...
        session.query(Address).
        # by querying a User named 'jack'...
        select_from(User).filter(User.name == 'jack').
        # then joining this to the Address 'jack@google.com`.
        join(Address).filter(Address.email_address == 'jack@google.com')
    )"""
    print_query(traditional_query, [jack.addresses[0]])
#
# More examples
# ^^^^^^^^^^^^^
def test_more_examples():
    # Ask for the full User object for jack.
    print_query("User['jack'].to_query(session)", [jack])
    # Ask only for Jack's full name.
    print_query("User['jack'].fullname.to_query(session)", [(jack.fullname, )])
    # Get all of Jack's addresses.
    print_query("User['jack'].addresses.to_query(session)", jack.addresses)
    # Get just the email-address of all of Jack's addresses.
    print_query("User['jack'].addresses.email_address.to_query(session)", [(x.email_address, ) for x in jack.addresses])
    # Get just the email-address j25@yahoo.com of Jack's addresses.
    print_query("User['jack'].addresses['j25@yahoo.com'].to_query(session)", [jack.addresses[1]])
    # Ask for the full Address object for j25@yahoo.com.
    print_query("Address['j25@yahoo.com'].to_query(session)", [jack.addresses[1]])
    # Ask for the User associated with this address.
    print_query("Address['j25@yahoo.com'].user.to_query(session)", [jack])
    # Use a filter criterion to select a User with a full name of Jack Bean.
    print_query("User[User.fullname == 'Jack Bean'].to_query(session)", [jack])
    # Use two filter criteria to find the user named jack with a full name of Jack Bean.
    print_query("User['jack'][User.fullname == 'Jack Bean'].to_query(session)", [jack])
    # Look for the user with id 1.
    print_query("User[1].to_query(session)", [jack])
    # Use an SQL expression in the query.
    print_query("User[func.lower(User.fullname) == 'jack bean'].to_query(session)", [jack])
    # Place the session at the beginning of the query, like traditional SQLAlchemy queries.
    print_query("session.User['jack'].to_query()", [jack])
#
# Advanced examples
# ^^^^^^^^^^^^^^^^^
def test_advanced_examples():
    # Queries are generative_: ``q`` can be re-used.
    q = User['jack']
    print_query("q.addresses.to_query(session)", jack.addresses, locals())
    print_query("q.to_query(session)", [jack], locals())

    # Add additional filters to the query.
    print_query("User['jack'].addresses.to_query(session).filter(Address.email_address == 'jack@google.com')", [jack.addresses[0]])

    # If the QueryMakerDeclarativeMeta_ metaclass wasn't used, this performs the equivalent of ``User['jack']`` manually.
    print_query("QueryMaker(User)['jack'].to_query(session)", [jack])

    # Add to an existing query: first, find the User named jack.
    q = session.query().select_from(User).filter(User.name == 'jack')
    # Then ask for the Address for jack@google.com. Note that no ``session`` needs to be provided to ``to_query``.
    print_query("q.query_maker(User).addresses['jack@google.com'].to_query()", [jack.addresses[0]], locals())
    # Do the same manually (without relying on the QueryMakerQuery_ ``query_maker`` method).
    print_query("QueryMaker(User, q).addresses['jack@google.com'].to_query()", [jack.addresses[0]], locals())
#
# main
# ^^^^
# Run the example code.
if __name__ == '__main__':
    test_traditional_versus_pythonic()
    test_more_examples()
    test_advanced_examples()
