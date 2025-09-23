import pytest
from musicporter.ast_to_sql import ASTtoSQL

def test_to_sql_simple_and():
    ast = (
        'and',
        ('comparison', 'genre', 'is', 'Rock'),
        ('comparison', 'rating', '>=', 4)
    )
    expected_sql = "(genre = ? AND rating >= ?)"
    expected_params = ['Rock', 4]
    sql, params = ASTtoSQL().to_sql(ast)
    assert sql == expected_sql
    assert params == expected_params

def test_to_sql_not_contains():
    ast = ('comparison', 'artist', 'not contains', 'Simon')
    expected_sql = "artist NOT LIKE ?"
    expected_params = ["%Simon%"]
    sql, params = ASTtoSQL().to_sql(ast)
    assert sql == expected_sql
    assert params == expected_params

def test_to_sql_not_has():
    ast = ('comparison', 'genre', 'not has', 'jazz')
    expected_sql = "genre NOT LIKE ?"
    expected_params = ["%jazz%"]
    sql, params = ASTtoSQL().to_sql(ast)
    assert sql == expected_sql
    assert params == expected_params

def test_to_sql_not_starts_with():
    ast = ('comparison', 'album', 'not starts with', 'Greatest')
    expected_sql = "album NOT LIKE ?"
    expected_params = ["Greatest%"]
    sql, params = ASTtoSQL().to_sql(ast)
    assert sql == expected_sql
    assert params == expected_params

def test_to_sql_not_ends_with():
    ast = ('comparison', 'title', 'not ends with', 'Remix')
    expected_sql = "title NOT LIKE ?"
    expected_params = ["%Remix"]
    sql, params = ASTtoSQL().to_sql(ast)
    assert sql == expected_sql
    assert params == expected_params

def test_to_sql_not_is():
    ast = ('comparison', 'year', 'not is', 1984)
    expected_sql = "year != ?"
    expected_params = [1984]
    sql, params = ASTtoSQL().to_sql(ast)
    assert sql == expected_sql
    assert params == expected_params

def test_to_sql_not_is_null():
    ast = ('comparison', 'composer', 'not is', None)
    expected_sql = "composer IS NOT NULL"
    expected_params = []
    sql, params = ASTtoSQL().to_sql(ast)
    assert sql == expected_sql
    assert params == expected_params
