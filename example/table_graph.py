import datetime

from sqla_graphs import TableGrapher

from example_model import Base


def main():
    print 'Generating SQLAlchemy table graph'
    grapher = TableGrapher(
        graph_options={'rankdir': 'TB'},
        style={'node_table_header': {'bgcolor': '#000080'}})
    graph = grapher.graph(tables=Base.metadata.tables.values())
    graph.write_png('table_graph_{}.png'.format(
        datetime.datetime.utcnow().isoformat()))


if __name__ == '__main__':
    main()
