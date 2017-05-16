SQLAlchemy graphs
#################

A graphing library for SQLAlchemy based on pydot (current 1.2.2) and Graphviz.

This code is based on a `usage recipe by Ants Aasma`__ on SQLAlchemy's wiki
and subsequent work by Florian Schulze (and others) in the form of
`sqlalchemy_schemadisplay`_ which is available on both GitHub and PyPI.

__ schemadisplay_recipe_

Quick example
=============

Because I know you're in a hurry, here's an example to generate a graph of
your declarative SQLAlchemy model:

.. code-block:: python

    from sqla_graphs import ModelGrapher
    from your.project.model import Base

    grapher = ModelGrapher(
        show_operations=True,
        style={'node_table_header': {'bgcolor': '#000088'}})
    graph = grapher.graph(Base.__subclasses__())
    graph.write_png('model_graph.png')


You can also feed it the tables from the declarative base's metadata or tables
reflected from a connection. That looks like this:

.. code-block:: python

    from sqla_graphs import TableGrapher
    from your.project.model import Base

    grapher = TableGrapher(
        style={'node_table_header': {'bgcolor': '#000080'}})
    graph = grapher.graph(tables=Base.metadata.tables.values())
    graph.write_png('table_graph.png')


Included in the examples directory are two scripts that create model and table
graphs based on an included example model, in case you don't have your own to
bring to the table.

Installation
============

Lacking a PyPI distribution, the installation steps are below. They clone
the repository, set up and activate a `virtualenv`_ and install the package
into this fresh environment:

.. code-block:: bash

    git clone https://github.com/edelooff/sqla-graphs.git
    virtualenv env
    source env/bin/activate
    cd sqla-graphs
    pip install -e .

Goals
=====

The goal of this project is to continue and extend the usefulness of the
original recipe. In more practical terms the design goals are these:

+ Maintain compatibility with current versions of SQLAlchemy_ and pydot_
+ Follow PEP8_ style in implementation and spirit
+ Be easily extensible and configurable by others

"It doesn't do X"
===================================

Feature requests are welcome, though this mainly exists to scrath my own itch,
so development may be slow. Pull requests are **even better**, of course.

Future development
==================

Scripts that allow for creation of graphs based on a module:class argument
or database connection string.

..  _PEP8: https://www.python.org/dev/peps/pep-0008/
..  _pydot: https://pypi.python.org/pypi/pydot
..  _schemadisplay_recipe: https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/SchemaDisplay
..  _SQLAlchemy: http://www.sqlalchemy.org/
..  _sqlalchemy_schemadisplay: https://github.com/fschulze/sqlalchemy_schemadisplay
..  _virtualenv: http://docs.python-guide.org/en/latest/dev/virtualenvs/
