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
# ******************************************************************
# |docname| - Unit tests for `../pythonic_sqlalchemy_query/flask.py`
# ******************************************************************
# This file provide working examples and tests for `../pythonic_sqlalchemy_query/flask.py`.
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8
# <http://www.python.org/dev/peps/pep-0008/#imports>`_.
#
# Standard library
# ----------------
# None
#
# Third-party imports
# -------------------
from flask import Flask
from sqlalchemy.sql.expression import func

# Local imports
# -------------
from pythonic_sqlalchemy_query.flask import SQLAlchemyPythonicQuery
from util import print_query

# Setup
# =====
# Create a basic Flask-SQLAlchemy application.
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemyPythonicQuery(app)

# Model
# -----
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    fullname = db.Column(db.String)
    password = db.Column(db.String)

    # Define a default query which assumes the key is a User's name if given a string.
    @classmethod
    def default_query(cls, key):
        if isinstance(key, str):
            return cls.name == key

    def __repr__(self):
       return "<User(name='%s', fullname='%s', password='%s')>" % (
                            self.name, self.fullname, self.password)

class Address(db.Model):
    __tablename__ = 'addresses'
    id = db.Column(db.Integer, primary_key=True)
    email_address = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    user = db.relationship("User", back_populates="addresses")

    # Define a default query which assumes the key is an Address's e-mail address.
    @classmethod
    def default_query(cls, key):
        return cls.email_address == key

    def __repr__(self):
        return "<Address(email_address='%s')>" % self.email_address

User.addresses = db.relationship(
    "Address", order_by=Address.id, back_populates="user")

# Create all tables.
db.create_all()
#
# Test data
# ---------
jack = User(name='jack', fullname='Jack Bean', password='gjffdd')
jack.addresses = [
                  Address(email_address='jack@google.com'),
                  Address(email_address='j25@yahoo.com')]
db.session.add(jack)
db.session.commit()

# .. _Flask Demonstration and unit tests:
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
    pythonic_query = "User['jack'].addresses['jack@google.com']"
    print_query(pythonic_query, [jack.addresses[0]], globals())

    # The traditional approach:
    traditional_query = (
        # Ask for the Address...
        "Address.query."
        # by querying a User named 'jack'...
        "select_from(User).filter(User.name == 'jack')."
        # then joining this to the Address 'jack@google.com`.
        "join(Address).filter(Address.email_address == 'jack@google.com')"
    )
    print_query(traditional_query, [jack.addresses[0]], globals())

# Examples
# --------
def test_more_examples():
    # Ask for the full User object for jack.
    print_query("User['jack']", [jack], globals())
    # Ask only for Jack's full name.
    print_query("User['jack'].fullname", [(jack.fullname, )], globals())
    # Get all of Jack's addresses.
    print_query("User['jack'].addresses", jack.addresses, globals())
    # Get just the email-address of all of Jack's addresses.
    print_query("User['jack'].addresses.email_address", [(x.email_address, ) for x in jack.addresses], globals())
    # Get just the email-address j25@yahoo.com of Jack's addresses.
    print_query("User['jack'].addresses['j25@yahoo.com']", [jack.addresses[1]], globals())
    # Ask for the full Address object for j25@yahoo.com.
    print_query("Address['j25@yahoo.com']", [jack.addresses[1]], globals())
    # Ask for the User associated with this address.
    print_query("Address['j25@yahoo.com'].user", [jack], globals())
    # Use a filter criterion to select a User with a full name of Jack Bean.
    print_query("User[User.fullname == 'Jack Bean']", [jack], globals())
    # Use two filter criteria to find the user named jack with a full name of Jack Bean.
    print_query("User['jack'][User.fullname == 'Jack Bean']", [jack], globals())
    # Look for the user with id 1.
    print_query("User[1]", [jack], globals())
    # Use an SQL expression in the query.
    print_query("User[func.lower(User.fullname) == 'jack bean']", [jack], globals())

    # Query using the session. A bit longer, but it produces the same results. For comparison:
    print_query(           "User['jack'].addresses['jack@google.com']", [jack.addresses[0]], globals())
    print_query("db.session.User['jack'].addresses['jack@google.com']", [jack.addresses[0]], globals())

# main
# ====
# Run the example code. This can also be tested using `pytest <https://docs.pytest.org>`_: ``pytest pythonic_sqlalchemy_query-test.py``.
if __name__ == '__main__':
    test_traditional_versus_pythonic()
    test_more_examples()
