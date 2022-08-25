# Copyright 2022 Balacoon

import os

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_score():
    grammars_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."
    )
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("classify.multi_token.attached", "AttachedTokensFst")
    assert (
        grammar.apply("look33")
        == 'tokens { name: "look" } tokens { cardinal { count: "33" } }'
    )
    assert (
        grammar.apply("AT&T-wireless")
        == 'tokens { name: "AT and T" } tokens { name: "wireless" }'
    )
    # allow word to be attached to symbols
    assert (
        grammar.apply("Hello#") == 'tokens { name: "hello" } tokens { name: "hash" }'
    )
