from sqlalchemy import Table, Column, ForeignKey, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()
T_PARENT_CHILD = Table(
    "parent_child",
    Base.metadata,
    Column("parent_id", Integer, ForeignKey("parent.id"), primary_key=True),
    Column("child_id", Integer, ForeignKey("child.id"), primary_key=True),
)


class Parent(Base):
    __tablename__ = "parent"

    # Column definition
    id = Column(Integer, primary_key=True)
    name = Column(Text)

    # Relationships
    children = relationship(
        "Child",
        back_populates="parents",
        secondary=T_PARENT_CHILD,
    )

    # Operations
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
