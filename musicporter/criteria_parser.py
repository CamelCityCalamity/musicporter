from lark import Lark, Transformer, v_args

GRAMMAR = r"""
    ?start: expr

    ?expr: or_expr

    ?or_expr: and_expr
        | or_expr "or" and_expr   -> or_

    ?and_expr: not_expr
        | and_expr "and" not_expr     -> and_

    ?not_expr: "not" atom           -> not_
        | atom

    ?atom: "(" expr ")"          -> group
        | in_expr
        | contains_expr
        | comparison

    in_expr: field "in" "(" value_list ")"   -> in_expr
    contains_expr: field "contains" value                -> contains_expr
                 | field "contains" "(" value_list ")" -> contains_expr
    has_expr: field "has" value                -> contains_expr
           | field "has" "(" value_list ")" -> contains_expr

    value_list: value ("," value)*

    comparison: field CMPOP value           -> comparison

    CMPOP: "is" | "not is" | "contains" | "not contains" | "has" | "not has" | "starts with" | "not starts with" | "ends with" | "not ends with" | "=" | "==" | "<>" | "!=" | ">" | "<" | ">=" | "<="

    field: CNAME

    value: ESCAPED_STRING | SQUOTE_STRING | SIGNED_NUMBER | NULL_KEYWORD

    NULL_KEYWORD: /(?i:none|null|nil|empty|missing)/

    SQUOTE_STRING: /'[^'\\]*(?:\\.[^'\\]*)*'/

    %import common.CNAME
    %import common.ESCAPED_STRING
    %import common.SIGNED_NUMBER
    %import common.WS
    %ignore WS
"""

@v_args(inline=True)
class CriteriaTransformer(Transformer):
    def has_expr(self, field, values):
        # Alias for contains_expr
        return self.contains_expr(field, values)
    def field(self, name):
        return str(name)
    def value(self, val):
        s = str(val)
        # Quoted strings are always literal
        if (s.startswith("\"") and s.endswith("\"")) or (s.startswith("'") and s.endswith("'")):
            return s[1:-1]
        # Unquoted null/none/nil/empty are treated as None
        if s.lower() in {"none", "null", "nil", "empty", "missing"}:
            return None
        try:
            return int(s)
        except ValueError:
            try:
                return float(s)
            except ValueError:
                return s
    def in_expr(self, field, values):
        return ('in', field, values)
    def contains_expr(self, field, values):
        # For lists, we want to use contains-any, but for single items, use contains.
        if isinstance(values, list):
            return ('contains_any', field, values)
        return ('comparison', field, 'contains', values)
    # No cmp_op method needed; CMPOP is a terminal and will be passed as a string
    def comparison(self, field, op, value):
        return ('comparison', field, str(op), value)
    def or_(self, left, right):
        return ('or', left, right)
    def and_(self, left, right):
        return ('and', left, right)
    def not_(self, expr):
        return ('not', expr)
    def group(self, expr):
        return expr
    def value_list(self, first, *rest):
        return [first] + list(rest)
    def in_list_in_field(self, values, field):
        return ('in_list_in_field', values, field)


class CriteriaParser:
    def __init__(self):
        self._parser = Lark(GRAMMAR, parser='lalr', transformer=CriteriaTransformer())

    def parse(self, criteria_str):
        return self._parser.parse(criteria_str)
