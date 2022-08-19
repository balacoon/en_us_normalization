# Copyright 2022 Balacoon

import os

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_shortening():
    grammars_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("classify.shortening", "ShorteningFst")
    assert grammar.apply("mrs") == 'name: "misses"'
    assert grammar.apply("Mrs") == 'name: "misses"'
    assert grammar.apply("Mrs.") == 'name: "misses"'
