import itertools
from inspect import (
    formatargspec,
    getargspec)
from types import (
    FunctionType,
    MethodType)

from pydot import (
    Dot,
    Edge,
    Node)
from sqlalchemy.orm import class_mapper
from sqlalchemy.orm.properties import RelationshipProperty


NODE_TABLE = (
    '<<TABLE BORDER="0" CELLBORDER="1" CELLPADDING="1" CELLSPACING="0">'
    '<TR><TD BGCOLOR="{bgcolor}" VALIGN="BOTTOM">'
    '<FONT POINT-SIZE="{top_margin}"><BR ALIGN="LEFT" /></FONT>'
    '<FONT COLOR="{color}" POINT-SIZE="{fontsize}"><B>{title}</B></FONT>'
    '</TD></TR>{table_content}</TABLE>>')
NODE_BLOCK_START = '<TR><TD><TABLE BORDER="0" CELLSPACING="0" CELLPADDING="1">'
NODE_BLOCK_END = '</TABLE></TD></TR>'
DEFAULT_STYLE = {
    'edge': {
        'arrowsize': 0.8,
        'fontname': 'Bitstream Vera Sans',
        'fontsize': 8,
        'labelfloat': 'true',
        'penwidth': 1},
    'inheritance': {
        'arrowhead': 'none',
        'arrowtail': 'empty'},
    'relationship': {
        'arrowhead': 'vee',
        'arrowtail': 'vee'},
    'relationship-viewonly': {
        'style': 'dashed'},
    'node': {
        'fontname': 'Bitstream Vera Sans',
        'fontsize': 8,
        'shape': 'plaintext'},
    'node_table_header': {
        'bgcolor': '#707070',
        'color': '#FFFFFF',
        'fontsize': 10,
        'top_margin': 2}}


def calculate_style(style):
    def collapse(*keys):
        result = {}
        for key in keys:
            result.update(DEFAULT_STYLE[key])
            result.update(style.get(key, {}))
        return result

    return {
        'edge': collapse('edge'),
        'inheritance': collapse('edge', 'inheritance'),
        'relationship': collapse('edge', 'relationship'),
        'relationship-viewonly': collapse('relationship-viewonly'),
        'node': collapse('node'),
        'node_table_header': collapse('node_table_header')}


class Grapher(object):
    GRAPH_OPTIONS = {}

    def __init__(self, graph_options, name_mangler, style):
        self.graph_options = self.GRAPH_OPTIONS.copy()
        if graph_options is not None:
            self.graph_options.update(graph_options)
        self.renamer = name_mangler or (lambda obj: obj)
        self.style = calculate_style(style or {})

    @staticmethod
    def node_row(content, port=''):
        """Renders a content row for a node table."""
        if isinstance(content, (list, tuple)):
            content = ''.join(content)
        return '<TR><TD ALIGN="LEFT" PORT="{port}">{content}</TD></TR>'.format(
            port=port, content=content)

    def node_table(self, title, *content_iterators):
        """Returns an HTML table label for a Node."""
        return NODE_TABLE.format(
            table_content=''.join(itertools.chain(*content_iterators)),
            title=self.renamer(title),
            **self.style['node_table_header'])

    @staticmethod
    def quote(name):
        """Returns the name in quotes, preventing reserved keyword issues."""
        return '"{}"'.format(name)


class ModelGrapher(Grapher):
    GRAPH_OPTIONS = {'mclimit': 1000}

    def __init__(
            self,
            show_attributes=True,
            show_datatypes=True,
            show_inherited=True,
            show_operations=False,
            show_multiplicity_one=False,
            graph_options=None,
            name_mangler=None,
            style=None):
        super(ModelGrapher, self).__init__(graph_options, name_mangler, style)
        self.show_attributes = show_attributes
        self.show_datatypes = show_datatypes
        self.show_inherited = show_inherited
        self.show_operations = show_operations
        self.show_multiplicity_one = show_multiplicity_one

    def graph(self, model_classes):
        graph = Dot(**self.graph_options)
        relations = set()

        # Create nodes from mappers
        mappers = map(class_mapper, model_classes)
        for mapper in mappers:
            graph.add_node(Node(
                self.quote(mapper),
                label=self.node_table(
                    mapper.class_.__name__,
                    self._model_columns(mapper),
                    self._model_operations(mapper)),
                **self.style['node']))
            if mapper.inherits:
                graph.add_edge(Edge(
                    map(self.quote, (mapper.inherits, mapper)),
                    **self.style['inheritance']))
            for loader in mapper.iterate_properties:
                if (isinstance(loader, RelationshipProperty) and
                        loader.mapper in mappers):
                    reverse = getattr(loader, '_reverse_property')
                    if len(reverse) == 1:
                        relations.add(frozenset((loader, next(iter(reverse)))))
                    else:
                        relations.add((loader,))

        # Create edges from relationships between mappers
        for relation in relations:
            options = self.style['relationship'].copy()
            if len(relation) == 2:
                src, dest = relation
                if src.viewonly and dest.viewonly:
                    options.update(self.style['relationship-viewonly'])
                between = src.parent, dest.parent
                options['headlabel'] = self._format_relationship(src)
                options['taillabel'] = self._format_relationship(dest)
                options['dir'] = 'both'
            else:
                prop, = relation
                between = prop.parent, prop.mapper
                options['headlabel'] = self._format_relationship(prop)
                if prop.viewonly:
                    options.update(self.style['relationship-viewonly'])
            graph.add_edge(Edge(map(self.quote, between), **options))
        return graph

    def quote(self, mapper):
        """Returns the quoted model name."""
        return super(ModelGrapher, self).quote(mapper.class_.__name__)

    def _model_columns(self, mapper):
        if self.show_attributes:
            yield NODE_BLOCK_START
            for column in mapper.columns:
                if self.show_inherited or column.table is mapper.tables[0]:
                    yield self.node_row(self._column_label(column))
            yield NODE_BLOCK_END

    def _model_operations(self, mapper):
        model = mapper.class_
        operations = filter(self._is_local_class_method(model), vars(model))
        if operations and self.show_operations:
            yield NODE_BLOCK_START
            for name in sorted(operations):
                func = getattr(model, name)
                oper = [self.renamer(name), self._format_argspec(func)]
                if not isinstance(func, MethodType):
                    oper.insert(0, '*')  # Non-instancemethod indicator
                yield self.node_row(oper)
            yield NODE_BLOCK_END

    def _column_label(self, column):
        """Returns the column name with type if so configured."""
        if self.show_datatypes:
            return '{}: {}'.format(
                *map(self.renamer, (column.name, type(column.type).__name__)))
        return self.renamer(column.name)

    def _format_argspec(self, function):
        """Returns a formatted argument spec exluding a method's 'self'."""
        argspec = list(getargspec(function))
        if argspec[0][0] == 'self':
            argspec[0].pop(0)
        for index, content in enumerate(argspec):
            if isinstance(content, (list, tuple)):
                argspec[index] = map(self.renamer, content)
            elif isinstance(content, str):
                argspec[index] = self.renamer(content)
        return formatargspec(*argspec)

    def _format_multiplicity(self, prop):
        """Returns a string with a multiplicity indicator."""
        if prop.uselist:
            return '+'
        if hasattr(prop, 'local_side'):
            cols = prop.local_side
        else:
            cols = prop.local_columns
        if any(col.nullable for col in cols):
            return '0..1 '
        if self.show_multiplicity_one:
            return '1 '
        return ''

    def _format_relationship(self, rel):
        """Returns the relationship name with multiplicity prefix."""
        return '  {}{}  '.format(
            self._format_multiplicity(rel), self.renamer(rel.key))

    @staticmethod
    def _is_local_class_method(class_):
        """Test whether attr name is a method defined on the provided class."""
        def _checker(attribute):
            obj = getattr(class_, attribute)
            return (isinstance(obj, (FunctionType, MethodType)) and
                    obj.__module__ is class_.__module__)
        return _checker


class TableGrapher(Grapher):
    GRAPH_OPTIONS = {
        'concentrate': 'true',
        'mclimit': 1000,
        'rankdir': 'TB'}

    def __init__(
            self,
            show_datatypes=True,
            show_indexes=True,
            graph_options=None,
            name_mangler=None,
            style=None):
        super(TableGrapher, self).__init__(graph_options, name_mangler, style)
        self.show_datatypes = show_datatypes
        self.show_indexes = show_indexes

    def graph(self, tables, skip_tables=()):
        graph = Dot(**self.graph_options)
        for table in tables:
            if table.name in skip_tables:
                continue

            graph.add_node(Node(
                self.quote(table.name),
                label=self.node_table(
                    table.name,
                    self._table_columns(table),
                    self._table_indices(table)),
                **self.style['node']))
            for fk in table.foreign_keys:
                fk_table = fk.column.table
                if fk_table not in tables or fk_table.name in skip_tables:
                    continue
                is_single_parent = fk.parent.primary_key or fk.parent.unique
                options = self.style['edge'].copy()
                options['arrowtail'] = 'empty' if is_single_parent else 'crow'
                options['dir'] = 'both'
                if fk.parent.primary_key and fk.column.primary_key:
                    # Inheritance relationship
                    edge = fk_table.name, table.name
                    options['arrowhead'] = 'none'
                    options['tailport'] = fk.column.name
                    options['headport'] = fk.parent.name
                else:
                    edge = table.name, fk_table.name
                    options['arrowhead'] = 'odot'
                    options['tailport'] = fk.parent.name
                    options['headport'] = fk.column.name
                graph.add_edge(Edge(map(self.quote, edge), **options))
        return graph

    def _table_columns(self, table):
        yield (NODE_BLOCK_START)
        for col in table.columns:
            yield self.node_row(self._format_column(col), port=col.name)
        yield (NODE_BLOCK_END)

    def _table_indices(self, table):
        if self.show_indexes and (table.indexes or table.primary_key):
            yield NODE_BLOCK_START
            if table.primary_key:
                yield self.node_row(self._format_index(
                    'PRIMARY', table.primary_key.columns))
            for index in table.indexes:
                yield self.node_row(self._format_index(
                    'UNIQUE' if index.unique else 'INDEX', index.columns))
            yield NODE_BLOCK_END

    def _format_column(self, col):
        if self.show_datatypes:
            return '{}: {}'.format(
                *map(self.renamer, (col.name, str(col.type))))
        return self.renamer(col.name)

    def _format_index(self, idx_type, cols):
        return '{} ({})'.format(
            idx_type, ', '.join(self.renamer(col.name) for col in cols))
