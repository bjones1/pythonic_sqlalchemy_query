# .. License
#
#   Copyright 2017 Bryan A. Jones
#
#   Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# ****************************************************************************************
# |docname| - Unit tests and demonstrations for `../pythonic_sqlalchemy_query/__init__.py`
# ****************************************************************************************
# .. _pytest syntax:
#
# To run: execute ``pytest tests`` from the project's root directory.
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8
# <http://www.python.org/dev/peps/pep-0008/#imports>`_.
#
# Standard library
# ----------------
from pprint import pprint

# Third-party imports
# -------------------
from sqlalchemy import create_engine, ForeignKey, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.orm import aliased
from sqlalchemy.ext import baked
from sqlalchemy.sql.expression import bindparam
from sqlalchemy.sql.expression import func

# Local imports
# -------------
from pythonic_sqlalchemy_query import (
    QueryMaker, QueryMakerDeclarativeMeta, QueryMakerQuery, QueryMakerSession
)
from util import print_query, _print_query

# Setup
# =====
# .. _Database setup:
#
# Database setup
# --------------
engine = create_engine('sqlite:///:memory:')#, echo=True)
# The `QueryMakerSession` allows syntax such as ``session(User)...``. For typical use, you may omit the ``query_cls=QueryMakerQuery``. See `sessionmaker <http://docs.sqlalchemy.org/en/latest/orm/session_api.html?highlight=sessionmaker#sqlalchemy.orm.session.sessionmaker>`_, `query_cls <http://docs.sqlalchemy.org/en/latest/orm/session_api.html?highlight=sessionmaker#sqlalchemy.orm.session.Session.params.query_cls>`_, and `class_ <http://docs.sqlalchemy.org/en/latest/orm/session_api.html?highlight=sessionmaker#sqlalchemy.orm.session.Session.params.class_>`_.
Session = sessionmaker(bind=engine, query_cls=QueryMakerQuery, class_=QueryMakerSession)
session = Session()

# Model
# -----
# Use the `QueryMakerDeclarativeMeta` in our `declarative class <http://docs.sqlalchemy.org/en/latest/orm/tutorial.html#declare-a-mapping>`_ definitions.
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

# Test data
# ---------
jack = User(name='jack', fullname='Jack Bean', password='gjffdd')
jack.addresses = [
                  Address(email_address='jack@google.com'),
                  Address(email_address='j25@yahoo.com')]
session.add(jack)
session.commit()

# .. _Demonstration and unit tests:
#
# Demonstration and unit tests
# ============================
#
# Traditional versus Pythonic
# ---------------------------
def test_traditional_versus_pythonic():
    # Create a query to select the Address for 'jack@google.com' from User 'jack'.
    #
    # The Pythonic version of a query:
    pythonic_query = "session(User)['jack'].addresses['jack@google.com']"
    print_query(pythonic_query, [jack.addresses[0]], globals())

    # The traditional approach:
    traditional_query = (
        # Ask for the Address...
        "session.query(Address)."
        # by querying a User named 'jack'...
        "select_from(User).filter(User.name == 'jack')."
        # then joining this to the Address 'jack@google.com`.
        "join(Address).filter(Address.email_address == 'jack@google.com')"
    )
    print_query(traditional_query, [jack.addresses[0]], globals())

# More examples
# -------------
def test_more_examples():
    # Ask for the full User object for jack.
    print_query("session(User)['jack']", [jack], globals())
    # Ask only for Jack's full name.
    print_query("session(User)['jack'].fullname", [(jack.fullname, )], globals())
    # Get all of Jack's addresses.
    print_query("session(User)['jack'].addresses", jack.addresses, globals())
    # Get just the email-address of all of Jack's addresses.
    print_query("session(User)['jack'].addresses.email_address", [(x.email_address, ) for x in jack.addresses], globals())
    # Get just the email-address j25@yahoo.com of Jack's addresses.
    print_query("session(User)['jack'].addresses['j25@yahoo.com']", [jack.addresses[1]], globals())
    # Ask for the full Address object for j25@yahoo.com.
    print_query("session(Address)['j25@yahoo.com']", [jack.addresses[1]], globals())
    # Ask for the User associated with this address.
    print_query("session(Address)['j25@yahoo.com'].user", [jack], globals())
    # Use a filter criterion to select a User with a full name of Jack Bean.
    print_query("session(User)[User.fullname == 'Jack Bean']", [jack], globals())
    # Use two filter criteria to find the user named jack with a full name of Jack Bean.
    print_query("session(User)['jack'][User.fullname == 'Jack Bean']", [jack], globals())
    # Look for the user with id 1.
    print_query("session(User)[1]", [jack], globals())
    # Use an SQL expression in the query.
    print_query("session(User)[func.lower(User.fullname) == 'jack bean']", [jack], globals())
    # Ask for all Users.
    print_query("session(User)", [jack], globals())
    # Ask for the name of all Users.
    print_query("session(User).name", [(jack.name, )], globals())

    # Transform to a query for indexing.
    assert _print_query("session(Address).q[1]", globals()) == jack.addresses[1]
    # Call the ``count`` method on the underlying Query object.
    assert _print_query("session(Address).q.count()", globals()) == 2
    # Call the ``order_by`` method on the underlying Query object.
    print_query("session(Address).q.order_by(Address.email_address)", list(reversed([jack.addresses][0])), globals())
    # Use the underlying query object for complex joins.
    adalias1 = aliased(Address)
    print_query("session(User).q.join(adalias1, User.addresses)['j25@yahoo.com']", [jack.addresses[1]], globals(), locals())

    # Queries are generative: ``qm`` can be re-used.
    qm = session(User)['jack']
    print_query("qm.addresses", jack.addresses, globals(), locals())
    print_query("qm", [jack], globals(), locals())

    # Properties and variables can be accessed as usual.
    cds_str = "session(User)['jack'].fullname.q.column_descriptions"
    print('-'*78)
    print('Code: {}\nResult:'.format(cds_str))
    cds = eval(cds_str)
    assert cds[0]['name'] == 'fullname'
    pprint(cds)
    print('')

# .. _Advanced examples:
#
# Advanced examples
# -----------------
def test_advanced_examples():
    # Specify exactly what to return by accessing the underlying query.
    print_query("session(User)['jack'].addresses._query.add_columns(User.id, Address.id)", [(1, 1), (1, 2)], globals() )

    # If `QueryMakerSession` isn't used, the session can be provided at the end of the query. However, this means the ``.q`` property won't be useful (since it has no assigned session).
    print_query("User['jack'].to_query(session)", [jack], globals())

    # If the `QueryMakerDeclarativeMeta` metaclass wasn't used, this performs the equivalent of ``User['jack']`` manually.
    print_query("QueryMaker(User)['jack'].to_query(session)", [jack], globals())

    # Add to an existing query: first, find the User named jack.
    q = session.query().select_from(User).filter(User.name == 'jack')
    # Then ask for the Address for jack@google.com.
    print_query("q.query_maker().addresses['jack@google.com']", [jack.addresses[0]], globals(), locals())
    # Do the same manually (without relying on the `QueryMakerQuery` ``query_maker`` method).
    print_query("QueryMaker(query=q).addresses['jack@google.com']", [jack.addresses[0]], globals(), locals())

    # `Baked queries <http://docs.sqlalchemy.org/en/latest/orm/extensions/baked.html>`_ are supported.
    bakery = baked.bakery()
    baked_query = bakery(lambda session: session(User))
    baked_query += lambda query: query[User.name == bindparam('username')]
    # The last item in the query must end with a ``.q``. Note that this doesn't print nicely. Using ``.to_query()`` instead fixes this.
    baked_query += lambda query: query.q.order_by(User.id).q
    print_query("baked_query(session).params(username='jack', email='jack@google.com')", [jack], globals(), locals())

# main
# ====
# Run the example code. This can also be `tested using pytest <pytest syntax>`.
if __name__ == '__main__':
    test_traditional_versus_pythonic()
    test_more_examples()
    test_advanced_examples()
