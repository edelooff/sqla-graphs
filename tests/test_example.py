from itertools import chain

import pytest
from sqlalchemy import Table, Column, ForeignKey, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from .utils import get_edge_labels, normalize

from sqla_graphs import ModelGrapher

Base = declarative_base()

T_PARENT_CHILD = Table(
    "parent_child",
    Base.metadata,
    Column("parent_id", Integer, ForeignKey("parent.id"), primary_key=True),
    Column("child_id", Integer, ForeignKey("child.id"), primary_key=True),
)


class Parent(Base):
    __tablename__ = "parent"
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    children = relationship(
        "Child",
        back_populates="parents",
        secondary=T_PARENT_CHILD,
    )

    def add_child(self, name):
        return Child(name=name, parents=[self])


class Child(Base):
    __tablename__ = "child"

    # Column definition
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    favourite_toy_id = Column(ForeignKey("toy.id"))

    # Relationships
    parents = relationship(
        "Parent",
        back_populates="children",
        secondary=T_PARENT_CHILD,
    )
    toys = relationship(
        "Toy",
        back_populates="owner",
        foreign_keys="Toy.child_id",
    )
    favourite_toy = relationship("Toy", foreign_keys=favourite_toy_id)

    # Operations
    def add_parent(self, name):
        return Parent(name=name, children=[self])

    def add_toy(self, name="Doodle"):
        return Toy(name=name, owner=self)


class Toy(Base):
    __tablename__ = "toy"

    # Column definition
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    child_id = Column(Integer, ForeignKey("child.id"), nullable=False)

    # Relationships
    owner = relationship(
        "Child",
        back_populates="toys",
        foreign_keys=child_id,
    )


@pytest.fixture
def model_graph():
    grapher = ModelGrapher(
        show_operations=True,
        style={"node_table_header": {"bgcolor": "#000088"}},
    )
    return grapher.graph([Parent, Child, Toy])


def test_model_names(model_graph):
    """Model names are the node names, as expected."""
    node_dict = model_graph.obj_dict["nodes"]
    assert set(map(normalize, node_dict)) == {"Parent", "Child", "Toy"}


def test_edges_and_labels(model_graph):
    """Edges are drawn and labeled as expected."""
    edges = model_graph.obj_dict["edges"]
    edge_sets = {tuple(sorted(map(normalize, pair))) for pair in edges}
    assert edge_sets == {("Child", "Parent"), ("Child", "Toy")}

    # Includes markers for 'exact one', 'one or more' and 'optional
    expected_edges_and_labels = [
        {"Child": "+children", "Parent": "+parents"},
        {"Child": "owner", "Toy": "+toys"},
        {"Child": "", "Toy": "0..1 favourite_toy"},
    ]
    for edge in chain.from_iterable(edges.values()):
        edge_labels = get_edge_labels(edge)
        assert edge_labels in expected_edges_and_labels
        expected_edges_and_labels.remove(edge_labels)
    assert expected_edges_and_labels == []


@pytest.mark.parametrize(
    "model, method_signature",
    [
        pytest.param("Child", "*add_parent(name)", id="Child.add_parent"),
        pytest.param("Child", "*add_toy(name='Doodle')", id="Child.add_toy"),
        pytest.param("Parent", "*add_child(name)", id="Parent.add_child"),
    ],
)
def test_model_methods_in_nodes(model_graph, model, method_signature):
    """The model methods show up in the nodes as expected."""
    for name, details in model_graph.obj_dict['nodes'].items():
        if normalize(name) == model:
            assert method_signature in details[0]['attributes']['label']
