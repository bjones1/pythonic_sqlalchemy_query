The `pythonic_sqlalchemy_query module <pythonic_sqlalchemy_query.py.html>`_ provides concise, Pythonic query syntax for SQLAlchemy. For example, the two queries produce identical results:

.. code-block:: Python

    pythonic_query = session.User['jack'].addresses['jack@google.com']
    traditional_query = (
        # Ask for the Address...
        session.query(Address).
        # by querying a User named 'jack'...
        select_from(User).filter(User.name == 'jack').
        # then joining this to the Address 'jack@google.com`.
        join(Address).filter(Address.email_address == 'jack@google.com')

See the `module documentation <pythonic_sqlalchemy_query.py.html>`_ for more information.

Installation
============
``pip install pythonic_sqlalchemy_query``

Use with SQLAlchemy
===================
For most cases:

.. code-block:: Python

    from pythonic_sqlalchemy_query import QueryMakerSession

    # Construct an engine as usual.
    engine = create_engine(...)
    # Create a session aware of this module.
    Session = sessionmaker(bind=engine, class_=QueryMakerSession)
    session = Session()

    # After defining some declarative classes, query away:
    for result in User['jack'].addresses:
        # Do some processing on result...

The `example <pythonic_sqlalchemy_query-test.py.html>`_ provides full, working code.

Documentation
=============
See the `pythonic_sqlalchemy_query module`_.

License
=======
This software is distributed under the terms of the `GNU public license, version 3 <gnu-gpl-v3.0.rst>`_.
