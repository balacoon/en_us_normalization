# Copyright 2022 Balacoon

import os

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_range():
    grammars_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."
    )
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("classify.multi_token.range", "RangeFst")
    assert (
        grammar.apply("2002-2014")
        == 'tokens { date { year: "2002" } } tokens { name: "to" } tokens { date { year: "2014" } }'
    )
