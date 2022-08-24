# Copyright 2022 Balacoon

import os

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_verbalize_roman():
    grammars_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("verbalize.roman", "RomanFst")
    assert grammar.apply("roman|count:25|") == "twenty five"
    assert grammar.apply("roman|prefix:chapter|count:26|") == "chapter twenty six"
    assert grammar.apply("roman|prefix:george|order:1|") == "george the first"
