from datetime import datetime

from sqla_graphs import ModelGrapher

from example_model import Base


def main():
    print("Generating SQLAlchemy model graph")
    grapher = ModelGrapher(
        show_operations=True,
        style={"node_table_header": {"bgcolor": "#000088"}},
    )
    graph = grapher.graph(Base.__subclasses__())
    graph.write_png(f"model_graph_{datetime.now():%Y-%m-%d %H:%M}.png")


if __name__ == "__main__":
    main()
