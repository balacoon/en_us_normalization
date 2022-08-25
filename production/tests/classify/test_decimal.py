# Copyright 2022 Balacoon

import os

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_decimal():
    grammars_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("classify.decimal", "DecimalFst")
    assert (
        grammar.apply("-23.45")
        == 'decimal { negative: "true" integer_part: "23" fractional_part: "45" }'
    )
    assert grammar.apply("100") == 'decimal { integer_part: "100" }'
    assert grammar.apply(".5") == 'decimal { fractional_part: "5" }'
    assert grammar.apply("1M") == 'decimal { integer_part: "1" quantity: "million" }'
    assert grammar.apply("13.5k") == 'decimal { integer_part: "13" fractional_part: "5" quantity: "thousands" }'
