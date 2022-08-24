# Copyright 2022 Balacoon

import os

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_verbalize_ordinal():
    grammars_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("verbalize.ordinal", "OrdinalFst")
    assert grammar.apply("ordinal|order:13|") == "thirteenth"
    assert grammar.apply("ordinal|order:21|") == "twenty first"
    assert grammar.apply("ordinal|order:60|") == "sixtieth"
