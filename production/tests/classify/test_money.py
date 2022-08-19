# Copyright 2022 Balacoon

import os

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_money():
    grammars_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("classify.money", "MoneyFst")
    assert (
        grammar.apply("$12.05")
        == 'money { currency: "$" decimal { integer_part: "12" fractional_part: "05" } }'
    )
    assert grammar.apply("£100,000") == 'money { currency: "£" decimal { integer_part: "100000" } }'
    assert grammar.apply("$1") == 'money { currency: "$" decimal { integer_part: "1" } }'
    assert (
        grammar.apply("1.5$")
        == 'money { decimal { integer_part: "1" fractional_part: "5" } currency: "$" }'
    )
