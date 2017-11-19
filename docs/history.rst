.. License

   Copyright 2017 Bryan A. Jones

   Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

   The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

*******
History
*******
-   Development version:

    -   Added additional tests.

-   1.1.1: 15-Nov-2017

    -   Refactor test code.
    -   Refactor Flask's scoped session into the core.

-   1.1.0: 13-Nov-2017

    -   Restructured to place code in a package.
    -   Added Flask-SQLAlchemy extensions.

-   1.0.4: 6-Nov-2017

    -   Changed license to MIT to match SQLAlchemy's license.

-   1.0.3: 3-Nov-2017

    -   Correct broken hyperlinks.

-   1.0.2: 3-Nov-2017

    -   Provide a better ``__iter__`` for `QueryMaker`.
    -   Correct the ``__setattr__`` in `_QueryWrapper`.

-   1.0.1: 3-Nov-2017

    -   Allow access to Query variables and special methods from a _QueryWrapper.

-   1.0.0: 3-Nov-2017

    -   Inital release.

Before PyPI release
===================
This program was originally `posted <https://groups.google.com/d/msg/sqlalchemy/B10yyOPUGhQ/6NFYEvMABAAJ>`_ on the SQLAlchemy mailing list. Thanks to Mike Bayer for helpful feedback.
