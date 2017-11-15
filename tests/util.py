# *********************************
# |docname| - Utilities for testing
# *********************************
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8
# <http://www.python.org/dev/peps/pep-0008/#imports>`_.
#
# Standard library
# ----------------
# None.

# Third-party imports
# -------------------
# None.

# Local imports
# -------------
from pythonic_sqlalchemy_query import QueryMaker

# Code
# ====
# Print a query its underlying SQL.
def _print_query(str_query, globals_, locals_=None):
    print('-'*78)
    print('Query: ' + str_query)
    query = eval(str_query, globals_, locals_)
    if isinstance(query, QueryMaker):
        query = query.q
    print('Resulting SQL emitted:\n{}\nResults:'.format(str(query)))
    return query

# Print the results of a query and optionally compare the results with the expected value.
def print_query(str_query, expected_result=None, globals_=None, locals_=None):
    query = _print_query(str_query, globals_, locals_)
    for _ in query:
        print(_)
    print('')
    if expected_result:
        assert query.all() == expected_result
    return query
