import datetime

from sqlalchemy.orm import class_mapper
from sqla_graphs import ModelGrapher

from example_model import Base


def main():
    print 'Generating SQLAlchemy model graph'
    grapher = ModelGrapher(
        show_operations=True,
        style={'node_table_header': {'bgcolor': '#000088'}})
    graph = grapher.graph(map(class_mapper, Base.__subclasses__()))
    graph.write_png('model_graph_{}.png'.format(
        datetime.datetime.utcnow().isoformat()))


if __name__ == '__main__':
    main()
