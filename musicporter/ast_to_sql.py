class ASTtoSQL:
    def __init__(self):
        pass

    def to_sql(self, ast):
        """
        Returns a tuple: (sql_string, params_list)
        """
        if isinstance(ast, tuple):
            node_type = ast[0]
            if node_type == 'and':
                left_sql, left_params = self.to_sql(ast[1])
                right_sql, right_params = self.to_sql(ast[2])
                return f"({left_sql} AND {right_sql})", left_params + right_params
            elif node_type == 'or':
                left_sql, left_params = self.to_sql(ast[1])
                right_sql, right_params = self.to_sql(ast[2])
                return f"({left_sql} OR {right_sql})", left_params + right_params
            elif node_type == 'not':
                inner_sql, inner_params = self.to_sql(ast[1])
                return f"NOT ({inner_sql})", inner_params
            elif node_type == 'comparison':
                field, op, value = ast[1], ast[2], ast[3]
                if value is None:
                    if op in ('is', '=', '=='):
                        return f"{field} IS NULL", []
                    elif op in ('is not', '!=', '<>','not is'):
                        return f"{field} IS NOT NULL", []
                # Handle negated string operators
                if op in ('contains', 'has'):
                    return f"{field} LIKE ?", [f"%{value}%"]
                elif op in ('not contains', 'not has'):
                    return f"{field} NOT LIKE ?", [f"%{value}%"]
                elif op == 'starts with':
                    return f"{field} LIKE ?", [f"{value}%"]
                elif op == 'not starts with':
                    return f"{field} NOT LIKE ?", [f"{value}%"]
                elif op == 'ends with':
                    return f"{field} LIKE ?", [f"%{value}"]
                elif op == 'not ends with':
                    return f"{field} NOT LIKE ?", [f"%{value}"]
                elif op in ('is', '=='):
                    return f"{field} = ?", [value]
                elif op in ('is not', '<>', '!=', 'not is'):
                    return f"{field} != ?", [value]
                else:
                    return f"{field} {op} ?", [value]
            elif node_type == 'in':
                field, values = ast[1], ast[2]
                placeholders = ', '.join(['?'] * len(values))
                return f"{field} IN ({placeholders})", list(values)
            elif node_type == 'contains_any':
                field, values = ast[1], ast[2]
                # Only allow string values for contains_any
                for v in values:
                    if not isinstance(v, str):
                        raise TypeError(f"'contains' or 'has' with a list only supports string values, got {type(v)}: {v}")
                like_clauses = [f"{field} LIKE ?" for _ in values]
                params = [f"%{v}%" for v in values]
                return f"({' OR '.join(like_clauses)})", params
            else:
                raise NotImplementedError(f"AST node type '{node_type}' not implemented.")
        else:
            raise NotImplementedError("AST node format not recognized.")
