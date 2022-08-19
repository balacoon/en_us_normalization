# Copyright 2022 Balacoon

import os

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_score():
    grammars_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."
    )
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("classify.multi_token.score", "ScoreFst")
    assert (
        grammar.apply("2 : 1")
        == 'tokens { cardinal { count: "2" } } tokens { name: "to" } tokens { cardinal { count: "1" } }'
    )
    assert (
        grammar.apply("2:1")
        == 'tokens { cardinal { count: "2" } } tokens { name: "to" } tokens { cardinal { count: "1" } }'
    )
