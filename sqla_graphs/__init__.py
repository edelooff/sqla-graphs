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
from sqlalchemy.orm.properties import RelationshipProperty


NODE_TABLE_START = (
    '<TABLE BORDER="0" CELLBORDER="1" CELLPADDING="1" CELLSPACING="0">'
    '<TR><TD BGCOLOR="{bgcolor}" VALIGN="BOTTOM">'
    '<FONT POINT-SIZE="{top_margin}"><BR ALIGN="LEFT" /></FONT>'
    '<FONT COLOR="{color}" POINT-SIZE="{fontsize}"><B>{title}</B></FONT>'
    '</TD></TR>')
NODE_BLOCK_START = '<TR><TD><TABLE BORDER="0" CELLSPACING="0" CELLPADDING="1">'
NODE_BLOCK_END = '</TABLE></TD></TR>'
DEFAULT_STYLE = {
    'edge': {
        'arrowsize': 0.6,
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

    style = style if style is not None else {}
    return {
        'edge': collapse('edge'),
        'inheritance': collapse('edge', 'inheritance'),
        'relationship': collapse('edge', 'relationship'),
        'node': collapse('node'),
        'node_table_header': collapse('node_table_header')}


def node_row(content, port=''):
    """Renders a content row for a node table."""
    if isinstance(content, (list, tuple)):
        content = ''.join(content)
    return '<TR><TD ALIGN="LEFT" PORT="{port}">{content}</TD></TR>'.format(
        port=port, content=content)


class ModelGrapher(object):
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
        self.show_attributes = show_attributes
        self.show_datatypes = show_datatypes
        self.show_inherited = show_inherited
        self.show_operations = show_operations
        self.show_multiplicity_one = show_multiplicity_one
        self.graph_options = self.GRAPH_OPTIONS.copy()
        if graph_options is not None:
            self.graph_options.update(graph_options)
        self.renamer = name_mangler or (lambda obj: obj)
        self.style = calculate_style(style)

    def _column_label(self, column):
        """Returns the column name with type if so configured."""
        if self.show_datatypes:
            return '{}: {}'.format(
                *map(self.renamer, (column.name, type(column.type).__name__)))
        return self.renamer(column.name)

    def _formatted_argspec(self, function):
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

    @staticmethod
    def is_local_class_method(class_):
        """Test whether attr name is a method defined on the provided class."""
        def _checker(attribute):
            obj = getattr(class_, attribute)
            return (isinstance(obj, (FunctionType, MethodType)) and
                    obj.__module__ is class_.__module__)
        return _checker

    def _model_label(self, mapper):
        model = mapper.class_
        html = [NODE_TABLE_START.format(
            title=self.renamer(model.__name__),
            **self.style['node_table_header'])]

        # Column attributes
        if self.show_attributes:
            html.append(NODE_BLOCK_START)
            for column in mapper.columns:
                if self.show_inherited or column.table is mapper.tables[0]:
                    html.append(node_row(self._column_label(column)))
            html.append(NODE_BLOCK_END)

        # Model methods
        if self.show_operations:
            operations = filter(self.is_local_class_method(model), vars(model))
            if operations:
                html.append(NODE_BLOCK_START)
                for name in sorted(operations):
                    func = getattr(model, name)
                    oper = [self.renamer(name), self._formatted_argspec(func)]
                    if not isinstance(func, MethodType):
                        oper.insert(0, '*')  # Non-instancemethod indicator
                    html.append(node_row(oper))
                html.append(NODE_BLOCK_END)
        return '<{}</TABLE>>'.format(''.join(html))

    def _multiplicity_indicator(self, prop):
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

    def _relationship_label(self, rel):
        """Returns the relationship name with multiplicity indicator."""
        return '  {}{}  '.format(
            self._multiplicity_indicator(rel), self.renamer(rel.key))

    def graph(self, mappers):
        graph = Dot(**self.graph_options)
        relations = set()

        def class_name(obj):
            """Returns a quoted string of the name of the mapped class."""
            return '"{}"'.format(obj.class_.__name__)

        # Create nodes from mappers
        for mapper in mappers:
            graph.add_node(Node(
                class_name(mapper),
                label=self._model_label(mapper),
                **self.style['node']))
            if mapper.inherits:
                between = class_name(mapper.inherits), class_name(mapper)
                graph.add_edge(Edge(*between, **self.style['inheritance']))
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
                between = class_name(src.parent), class_name(dest.parent)
                options['headlabel'] = self._relationship_label(src)
                options['taillabel'] = self._relationship_label(dest)
                options['dir'] = 'both'
            else:
                prop, = relation
                between = class_name(prop.parent), class_name(prop.mapper)
                options['headlabel'] = self._relationship_label(prop)
            graph.add_edge(Edge(*between, **options))
        return graph


class TableGrapher(object):
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
        self.show_datatypes = show_datatypes
        self.show_indexes = show_indexes
        self.graph_options = self.GRAPH_OPTIONS.copy()
        if graph_options is not None:
            self.graph_options.update(graph_options)
        self.renamer = name_mangler or (lambda obj: obj)
        self.style = calculate_style(style)

    def graph(self, tables, skip_tables=()):
        graph = Dot(**self.graph_options)
        for table in tables:
            if table.name in skip_tables:
                continue

            graph.add_node(Node(
                table.name,
                label=self._table_label(table),
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
                graph.add_edge(Edge(*edge, **options))
        return graph

    def _table_label(self, table):
        html = [NODE_TABLE_START.format(
            title=self.renamer(table.name),
            **self.style['node_table_header'])]

        # Columns
        html.append(NODE_BLOCK_START)
        for col in table.columns:
            html.append(node_row(self._format_column(col), port=col.name))
        html.append(NODE_BLOCK_END)

        # Indexes
        if self.show_indexes and (table.indexes or table.primary_key):
            html.append(NODE_BLOCK_START)
            if table.primary_key:
                html.append(node_row(self._format_index(
                    'PRIMARY', table.primary_key.columns)))
            for index in table.indexes:
                html.append(node_row(self._format_index(
                    'UNIQUE' if index.unique else 'INDEX', index.columns)))
            html.append(NODE_BLOCK_END)
        return '<{}</TABLE>>'.format(''.join(html))

    def _format_column(self, col):
        if self.show_datatypes:
            return '{}: {}'.format(
                *map(self.renamer, (col.name, str(col.type))))
        return self.renamer(col.name)

    def _format_index(self, idx_type, cols):
        return '{} ({})'.format(
            idx_type, ', '.join(self.renamer(col.name) for col in cols))
