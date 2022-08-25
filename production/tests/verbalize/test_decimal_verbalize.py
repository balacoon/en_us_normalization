# Copyright 2022 Balacoon

import os

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_verbalize_decimal():
    grammars_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("verbalize.decimal", "DecimalFst")
    assert (
        grammar.apply("decimal|negative:1|integer_part:12|fractional_part:5006|")
        == "minus twelve point five o o six"
    )
    assert (
        grammar.apply("decimal|integer_part:1|fractional_part:12|")
        == "one point one two"
    )
    assert grammar.apply("decimal|fractional_part:05|") == "point o five"
    assert grammar.apply("decimal|integer_part:21|") == "twenty one"
    assert grammar.apply("decimal|integer_part:1|fractional_part:5|quantity:thousands|") == "one point five thousands"
