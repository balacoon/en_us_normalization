# Copyright 2022 Balacoon

import os

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_score():
    grammars_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."
    )
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("classify.multi_token.slash", "SlashFst")
    assert (
        grammar.apply("AC/DC") == 'tokens { name: "AC" } tokens { name: "DC" }'
    )
    assert (
        grammar.apply("radio/video") == 'tokens { name: "radio" } tokens { name: "video" }'
    )
