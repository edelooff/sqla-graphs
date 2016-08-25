SQLAlchemy graphs
#################

A graphing library for SQLAlchemy based on pydot (current 1.2.2) and Graphviz.

This code is based on a `usage recipe by Ants Aasma`__ on SQLAlchemy's wiki
and subsequent work by Florian Schulze (and others) in the form of
`sqlalchemy_schemadisplay`__ which is available on both GitHub and PyPI.

__ https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/SchemaDisplay
__ https://github.com/fschulze/sqlalchemy_schemadisplay

Goals
=====

The goal of this project is to continue and extend the usefulness of the
original recipe. In more practical terms the design goals are these:

+ Maintain compatibility with current versions of SQLAlchemy_ and pydot_
+ Follow PEP8_ style in implementation and spirit
+ Be easily extensible and configurable by others

Work in progress
================

Currently only the model graphing has been taken care of, and examples are
lacking the documentation they require.

Other things to do are small scripts that allow for creation of graphs based
on a module/class argument or database connection string.

..  _PEP8: https://www.python.org/dev/peps/pep-0008/
..  _pydot: https://pypi.python.org/pypi/pydot
..  _SQLAlchemy: http://www.sqlalchemy.org/
