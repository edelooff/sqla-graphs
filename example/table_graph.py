from datetime import datetime

from sqla_graphs import TableGrapher

from example_model import Base


def main():
    print("Generating SQLAlchemy table graph")
    grapher = TableGrapher(
        graph_options={"rankdir": "LR"},
        style={"node_table_header": {"bgcolor": "#000080"}},
    )
    graph = grapher.graph(tables=Base.metadata.tables.values())
    graph.write_png(f"table_graph_{datetime.now():%Y-%m-%d %H:%M}.png")


if __name__ == "__main__":
    main()
