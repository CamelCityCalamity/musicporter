import pytest
from musicporter.criteria_parser import CriteriaParser

def test_parse_simple_and():
    parser = CriteriaParser()
    ast = parser.parse("genre is 'Rock' and rating >= 4")
    expected = (
        'and',
        ('comparison', 'genre', 'is', 'Rock'),
        ('comparison', 'rating', '>=', 4)
    )
    assert ast == expected

def test_and_or_precedence1():
    parser = CriteriaParser()
    ast = parser.parse("genre = 'Rock' and rating = 5 or artist = 'Paul Simon'")
    s = str(ast)
    expected = (
        'or',
        (
            'and',
            ('comparison', 'genre', '=', 'Rock'),
            ('comparison', 'rating', '=', 5)
        ),
        ('comparison', 'artist', '=', 'Paul Simon')
    )
    assert ast == expected

def test_and_or_precedence2():
    parser = CriteriaParser()
    ast = parser.parse("artist = 'Paul Simon' or genre = 'Rock' and rating = 5")
    s = str(ast)
    expected = (
        'or',
        ('comparison', 'artist', '=', 'Paul Simon'),
        (
            'and',
            ('comparison', 'genre', '=', 'Rock'),
            ('comparison', 'rating', '=', 5)
        )
    )
    assert ast == expected

# Test for the 'not' operator
def test_not_operator_starts_with():
    parser = CriteriaParser()
    ast = parser.parse("artist not starts with 'Paul'")
    expected = (
        'comparison', 'artist', 'not starts with', 'Paul'
    )
    assert ast == expected

# Additional tests for other 'not' operators
def test_not_operator_contains():
    parser = CriteriaParser()
    ast = parser.parse("genre not contains 'Rock'")
    expected = (
        'comparison', 'genre', 'not contains', 'Rock'
    )
    assert ast == expected

def test_not_operator_has():
    parser = CriteriaParser()
    ast = parser.parse("artist not has 'Paul Simon'")
    expected = (
        'comparison', 'artist', 'not has', 'Paul Simon'
    )
    assert ast == expected

def test_not_operator_ends_with():
    parser = CriteriaParser()
    ast = parser.parse("album not ends with 'Live'")
    expected = (
        'comparison', 'album', 'not ends with', 'Live'
    )
    assert ast == expected

def test_not_operator_is():
    parser = CriteriaParser()
    ast = parser.parse("rating not is 5")
    expected = (
        'comparison', 'rating', 'not is', 5
    )
    assert ast == expected

