# Copyright 2022 Balacoon

import os

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_cardinal():
    grammars_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("classify.cardinal", "CardinalFst")
    assert grammar.apply("-23") == 'cardinal { negative: "true" count: "23" }'
    assert grammar.apply("1231") == 'cardinal { count: "1231" }'
    assert grammar.apply("4,123,212") == 'cardinal { count: "4123212" }'
    assert grammar.apply("# 21") == 'cardinal { prefix: "number" count: "21" }'
    assert grammar.apply("No 1") == 'cardinal { prefix: "number" count: "1" }'

    # test multi token functionality
    # range
    assert (
        grammar.apply("12 - 15")
        == 'cardinal { count: "12" } } tokens { name: "to" } tokens { cardinal { count: "15" }'
    )
    assert (
        grammar.apply("1 : 2")
        == 'cardinal { count: "1" } } tokens { name: "to" } tokens { cardinal { count: "2" }'
    )
