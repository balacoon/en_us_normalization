# Copyright 2022 Balacoon

import os

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_verbalize_money():
    grammars_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("verbalize.money", "MoneyFst")
    assert (
        grammar.apply(
            "money|negative:1|integer_part:1|currency:$|fractional_part:53|currency:$|"
        )
        == "minus one dollar fifty three cents"
    )
    assert (
        grammar.apply("money|integer_part:0|currency:$|fractional_part:5|currency:$|")
        == "zero dollars fifty cents"
    )
    assert grammar.apply("money|fractional_part:0|currency:$|") == "zero cents"
    assert grammar.apply("money|fractional_part:1|currency:$|") == "ten cents"
    assert grammar.apply("money|fractional_part:01|currency:$|") == "one cent"
