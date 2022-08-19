# Copyright 2022 Balacoon

import os

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_fraction():
    grammars_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("classify.fraction", "FractionFst")
    assert (
        grammar.apply("25 1/2")
        == 'fraction { integer_part: "25" numerator: "1" denominator: "2" }'
    )
    assert grammar.apply("3/4") == 'fraction { numerator: "3" denominator: "4" }'
    assert (
        grammar.apply("500,000 3 / 7")
        == 'fraction { integer_part: "500000" numerator: "3" denominator: "7" }'
    )
