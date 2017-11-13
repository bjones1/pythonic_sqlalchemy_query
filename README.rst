.. License

   Copyright 2017 Bryan A. Jones

   Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

   The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

The `pythonic_sqlalchemy_query module <http://pythonic-sqlalchemy-query.readthedocs.io/en/latest/pythonic_sqlalchemy_query/__init__.py.html>`_ provides concise, Pythonic query syntax for SQLAlchemy. For example, these two queries produce identical results:

.. code-block:: Python3

    pythonic_query = session.User['jack'].addresses['jack@google.com']
    traditional_query = (
        # Ask for the Address...
        session.query(Address).
        # by querying a User named 'jack'...
        select_from(User).filter(User.name == 'jack').
        # then joining this to the Address 'jack@google.com`.
        join(Address).filter(Address.email_address == 'jack@google.com')

Installation
============
``pip install pythonic_sqlalchemy_query``

Use with SQLAlchemy
===================
For most cases:

.. code-block:: Python3

    from pythonic_sqlalchemy_query import QueryMakerSession

    # Construct an engine as usual.
    engine = create_engine(...)
    # Create a session aware of this module.
    Session = sessionmaker(bind=engine, class_=QueryMakerSession)
    session = Session()

    # After defining some declarative classes, query away:
    for result in session.User['jack'].addresses:
        # Do some processing on result...

The `examples <http://pythonic-sqlalchemy-query.readthedocs.io/en/latest/tests/test_pythonic_sqlalchemy_query.py.html>`__ provide full, working code.

Use with Flask-SQLAlchemy
=========================
For most cases:

.. code-block:: Python3

    from pythonic_sqlalchemy_query.flask import SQLAlchemyPythonicQuery

    app = Flask(__name__)
    db = SQLAlchemyPythonicQuery(app)

    # After defining some declarative classes, query away:
    for result in User['jack'].addresses:
        # Do some processing on result...

The `examples <http://pythonic-sqlalchemy-query.readthedocs.io/en/latest/tests/test_flask.py.html>`__ provide full, working code.

Documentation
=============
See the `pythonic_sqlalchemy_query module`_.

License
=======
This software is distributed under the terms of the `MIT license <http://pythonic-sqlalchemy-query.readthedocs.io/en/latest/license.html>`_.
