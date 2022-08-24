# Copyright 2022 Balacoon

import os

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_verbalize_verbatim():
    grammars_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("verbalize.verbatim", "VerbatimFst")
    assert grammar.apply("verbatim|name:sa12|") == "SA one two"
    assert (
        grammar.apply("verbatim|name:sdfoij32#4||")
        == "SDFOIJ three two hash four vertical bar"
    )
