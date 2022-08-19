# Copyright 2022 Balacoon

import os

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_math():
    grammars_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."
    )
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("classify.multi_token.math", "MathFst")
    assert (
        grammar.apply("2x5")
        == 'tokens { cardinal { count: "2" } } tokens { name: "by" } '
        'tokens { cardinal { count: "5" } }'
    )
    assert (
        grammar.apply("3 - 4 + 1.5")
        == 'tokens { cardinal { count: "3" } } tokens { name: "minus" } '
        'tokens { cardinal { count: "4" } } tokens { name: "plus" } '
        'tokens { decimal { integer_part: "1" fractional_part: "5" } }'
    )
