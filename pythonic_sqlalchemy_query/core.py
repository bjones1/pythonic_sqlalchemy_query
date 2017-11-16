# *************************
# |docname| - Core routines
# *************************
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8
# <http://www.python.org/dev/peps/pep-0008/#imports>`_.
#
# Standard library
# ----------------
import inspect as py_inspect

# Third-party imports
# -------------------
from sqlalchemy.orm import Query, scoped_session
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm.base import _generative
from sqlalchemy.sql.elements import ClauseElement
from sqlalchemy.orm.session import Session
from sqlalchemy.orm.util import class_mapper
from sqlalchemy.orm.mapper import Mapper
from sqlalchemy.inspection import inspect

# .. _QueryMaker:
#
# QueryMaker
# ==========
# This class provides a concise, Pythonic syntax for simple queries; for example, ``session.User['jack'].addresses`` produces a Query_ for the Address of a User named jack.
#
# This class provides the following methods:
#
# - Constructor: ``session.User`` (with help from QueryMakerSession_) creates a query on a User table.
# - Indexing: ``session.User['jack']`` performs filtering.
# - Attributes: ``session.User['jack'].addresses`` joins to the Addresses table.
# - Iteration: ``for x in session.User['jack'].addresses`` iterates over the results of the query.
# - Query access: ``User['jack'].addresses.q`` returns a Query-like object. Any Query_ method can be invoked on it.
#
# See the `demonstration and unit tests` for examples and some less-used methods.
#
# This works by translating class instances in a query/select, indexes into filters, and columns/relationships into joins. The following code shows the Pythonic syntax on the first line, followed by the resulting translation into SQLAlchemy performed by this class on the next line.
#
# .. code-block:: Python
#   :linenos:
#
#   User                        ['jack']                   .addresses
#   Query([]).select_from(User).filter(User.name == 'jack').join(Address).add_entity(Address)
#
# Limitations
# -----------
# Note that the `delete <http://docs.sqlalchemy.org/en/latest/orm/query.html#sqlalchemy.orm.query.Query.delete>`_ and `update <http://docs.sqlalchemy.org/en/latest/orm/query.html#sqlalchemy.orm.query.Query.update>`_ methods cannot be involed on the query produced by this class. Safer (but lower-performance) is:
#
# .. code-block:: python3
#   :linenos:
#
#   for _ in session.User['jack']:
#       session.delete(_)
#
# Rationale:
#
# - Per the docs on delete_ and update_, these come with a long list of caveats. Making dangerous functions easy to invoke is poor design.
# - For implementation, QueryMaker_ cannot invoke `select_from <http://docs.sqlalchemy.org/en/latest/orm/query.html#sqlalchemy.orm.query.Query.select_from>`_. Doing so raises ``sqlalchemy.exc.InvalidRequestError: Can't call Query.update() or Query.delete() when join(), outerjoin(), select_from(), or from_self() has been called``. So, select_from_ must be deferred -- but to when? ``User['jack'].addresses`` requires a select_from_, while ``User['jack']`` needs just ``add_entity``. We can't know which to invoke until the entire expression is complete.
class QueryMaker(object):
    def __init__(self,
      # An optional `Declarative class <http://docs.sqlalchemy.org/en/latest/orm/tutorial.html#declare-a-mapping>`_ to query.
      declarative_class=None,
      # Optionally, begin with an existing query_.
      query=None):

        if declarative_class:
            assert _is_mapped_class(declarative_class)

        # If a query is provided, try to infer the declarative_class.
        if query is not None:
            assert isinstance(query, Query)
            self._query = query
            try:
                self._select = self._get_joinpoint_zero_class()
            except:
                # We can't infer it. Use what's provided instead, and add this to the query.
                assert declarative_class
                self._select = declarative_class
                self._query = self._query.select_from(declarative_class)
            else:
                # If a declarative_class was provided, make sure it's consistent with the inferred class.
                if declarative_class:
                    assert declarative_class is self._select
        else:
            # The declarative class must be provided if the query wasn't.
            assert declarative_class
            # No a query was not provied, create an empty `query <http://docs.sqlalchemy.org/en/latest/orm/query.html>`_; ``to_query`` will fill in the missing information.
            self._query = Query([]).select_from(declarative_class)
            # Keep track of the last selectable construct, to generate the select in ``to_query``.
            self._select = declarative_class

    # Copied verbatim from ``sqlalchemy.orm.query.Query._clone``. This adds the support needed for the _`generative` interface. (Mostly) quoting from query_, "QueryMaker_ features a generative interface whereby successive calls return a new QueryMaker_ object, a copy of the former with additional criteria and options associated with it."
    def _clone(self):
        cls = self.__class__
        q = cls.__new__(cls)
        q.__dict__ = self.__dict__.copy()
        return q

    # Looking up a class's `Column <http://docs.sqlalchemy.org/en/latest/core/metadata.html#sqlalchemy.schema.Column>`_ or `relationship <http://docs.sqlalchemy.org/en/latest/orm/relationship_api.html#sqlalchemy.orm.relationship>`_ generates the matching query.
    @_generative()
    def __getattr__(self, name):
        # Find the Column_ or relationship_ in the join point class we're querying.
        attr = getattr(self._get_joinpoint_zero_class(), name)
        # If the attribute refers to a column, save this as a possible select statement. Note that a Column_ gets replaced with an `InstrumentedAttribute <http://docs.sqlalchemy.org/en/latest/orm/internals.html?highlight=instrumentedattribute#sqlalchemy.orm.attributes.InstrumentedAttribute>`_; see `QueryableAttribute <http://docs.sqlalchemy.org/en/latest/orm/internals.html?highlight=instrumentedattribute#sqlalchemy.orm.attributes.QueryableAttribute.property>`_.
        if isinstance(attr.property, ColumnProperty):
            self._select = attr
        elif isinstance(attr.property, RelationshipProperty):
            # Figure out what class this relationship refers to. See `mapper.params.class_ <http://docs.sqlalchemy.org/en/latest/orm/mapping_api.html?highlight=mapper#sqlalchemy.orm.mapper.params.class_>`_.
            declarative_class = attr.property.mapper.class_
            # Update the query by performing the implied join.
            self._query = self._query.join(declarative_class)
            # Save this relationship as a possible select statement.
            self._select = declarative_class
        else:
            # This isn't a Column_ or a relationship_.
            assert False

    # Indexing the object performs the implied filter. For example, ``User['jack']`` implies ``query.filter(User.name == 'jack')``.
    @_generative()
    def __getitem__(self,
      # Most often, this is a key which will be filtered by the ``default_query`` method of the currently-active `Declarative class`_. In the example above, the ``User`` class must define a ``default_query`` to operate on strings. However, it may also be a filter criterion, such as ``User[User.name == 'jack']``.
      key):

        # See if this is a filter criterion; if not, rely in the ``default_query`` defined by the `Declarative class`_ or fall back to the first primary key.
        criteria = None
        jp0_class = self._get_joinpoint_zero_class()
        if isinstance(key, ClauseElement):
            criteria = key
        elif hasattr(jp0_class, 'default_query'):
            criteria = jp0_class.default_query(key)
        if criteria is None:
            pks = inspect(jp0_class).primary_key
            criteria = pks[0] == key
        self._query = self._query.filter(criteria)

    # Support common syntax: ``for x in query_maker:`` converts this to a query and returns results. The session must already have been set.
    def __iter__(self):
        return self.to_query().__iter__()

    # This property return a `_QueryWrapper`_, a query-like object which transforms returned Query_ values back into this class while leaving other return values unchanged.
    @property
    def q(self):
        return _QueryWrapper(self)

    # Transform this object into a Query_.
    def to_query(self,
      # Optionally, the `Session <http://docs.sqlalchemy.org/en/latest/orm/session_api.html?highlight=session#sqlalchemy.orm.session.Session>`_ to run this query in.
      session=None):

        # If a session was specified, use it to produce the query_; otherwise, use the existing query_.
        query = self._query.with_session(session) if session else self._query
        # Choose the correct method to select either a column or a class (e.g. an entity). As noted earlier, a Column_ becomes and InstrumentedAttribute_.
        if isinstance(self._select, InstrumentedAttribute):
            return query.add_columns(self._select)
        else:
            return query.add_entity(self._select)

    # Get the right-most join point in the current query.
    def _get_joinpoint_zero_class(self):
        jp0 = self._query._joinpoint_zero()
        # If the join point was returned as a Mapper, get the underlying class.
        if isinstance(jp0, Mapper):
            jp0 = jp0.class_
        return jp0

# .. _`_QueryWrapper`:
#
# _QueryWrapper
# -------------
# This class behaves mostly like a Query_. However, if the return value of a method is a Query_, it returns a QueryMaker_ object instead. It's intended for internal use by ``QueryMaker.q``.
class _QueryWrapper(object):
    def __init__(self, query_maker):
        self._query_maker = query_maker

    # Delegate directly to the wrapped Query_. Per `special method lookup <https://docs.python.org/3/reference/datamodel.html#special-lookup>`_, the `special method names <https://docs.python.org/3/reference/datamodel.html#special-method-names>`_ bypass ``__getattr__`` (and even ``__getattribute__``) lookup. Only override what Query_ overrides.
    #
    # The ``_tq`` (to_query) property shortens the following functions.
    @property
    def _tq(self):
        return self._query_maker.to_query()
    def __getitem__(self, key):
        return self._tq.__getitem__(key)
    def __str__(self):
        return self._tq.__str__()
    def __repr__(self):
        return self._tq.__repr__()
    def __iter__(self):
        return self._tq.__iter__()

    # Allow ``__init__`` to create the ``_query_maker`` variable. Everything else goes to the wrapped Query_. Allow direct assignments, as this mimics what an actual Query_ instance would do.
    def __setattr__(self, name, value):
        if name != '_query_maker':
            return self._query_maker.__setattr(name, value)
        else:
            self.__dict__[name] = value

    # Run the method on the underlying Query_. If a Query_ is returned, wrap it in a QueryMaker_.
    def __getattr__(self, name):
        attr = getattr(self._tq, name)
        if not callable(attr):
            # If this isn't a function, then don't do any wrapping.
            return attr
        else:
            def _wrap_query(*args, **kwargs):
                # Invoke the requested Query_ method on the "completed" query returned by ``to_query``.
                ret = attr(*args, **kwargs)
                if isinstance(ret, Query):
                    # If the return value was a Query_, make it generative by returning a new QueryMaker_ instance wrapping the query.
                    query_maker = self._query_maker._clone()
                    jp0_old = query_maker._get_joinpoint_zero_class()
                    # Re-run getattr on the raw query, since we don't want to add columns or entities to the query yet. Otherwise, they'd be added twice (here and again when ``to_query`` is called).
                    query_maker._query = getattr(query_maker._query, name)(*args, **kwargs)
                    # If the query involved a join, then the join point has changed. Update what to select.
                    query_maker._select = query_maker._get_joinpoint_zero_class()
                    return query_maker
                else:
                    # Otherwise, just return the result.
                    return ret

            return _wrap_query

# .. _QueryMakerDeclarativeMeta:
#
# QueryMakerDeclarativeMeta
# -------------------------
# Turn indexing of a `Declarative class`_ into a query. For example, ``User['jack']`` is a query. See the `advanced examples` for an example of its use.
class QueryMakerDeclarativeMeta(DeclarativeMeta):
    def __getitem__(cls, key):
        return QueryMaker(cls)[key]

# .. _QueryMakerQuery:
#
# QueryMakerQuery
# ---------------
# Provide support for changing a Query_ instance into a QueryMaker_ instance. See the `advanced examples` for an example of its use.
class QueryMakerQuery(Query):
    def query_maker(self, declarative_class=None):
        return QueryMaker(declarative_class, self)

# .. _QueryMakerSession:
#
# QueryMakerSession
# -----------------
# Create a Session_ which recognizes declarative classes as an attribute. This enables ``session.User['jack']``. See the `database setup` for an example of its use.
class QueryMakerSession(Session):
    def __getattr__(self, name):
        cls = _parent_declarative_class(name)
        if cls:
            return QueryMaker(cls, self.query())
        else:
            return super().__getattr__(name)

# .. _QueryMakerScopedSession:
#
# QueryMakerScopedSession
# ------------------------
# By default, SQLAlchemy doesn't proxy ``__getattr__`` in a `scoped session <http://docs.sqlalchemy.org/en/latest/orm/contextual.html>`_. Provide this.
class QueryMakerScopedSession(scoped_session):
    def __getattr__(self, name):
        cls = _parent_declarative_class(name)
        if cls:
            return QueryMaker(cls, self.registry().query())
        else:
            return super().__getattr__(name)

# Support routines
# ----------------
# Given the name of a declarative class in the caller's parent's stack frame, return it. If it can't be found, return ``None``.
def _parent_declarative_class(name):
    # TODO: Shady. I don't see any other way to accomplish this, though.
    #
    # Get the parent's caller's `frame record <https://docs.python.org/3/library/inspect.html#the-interpreter-stack>`_.
    callers_frame_record = py_inspect.stack()[2]
    # From this, get the `frame object <https://docs.python.org/3/library/inspect.html#types-and-members>`_ (index 0), then the global namespace seen by that frame.
    g = callers_frame_record[0].f_globals
    if (name in g) and _is_mapped_class(g[name]):
        return g[name]
    else:
        return None

# Copied from https://stackoverflow.com/a/7662943.
def _is_mapped_class(cls):
    try:
        class_mapper(cls)
        return True
    except:
        return False
