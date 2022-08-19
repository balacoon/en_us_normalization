# Copyright 2022 Balacoon

import os

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_ordinal():
    grammars_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("classify.ordinal", "OrdinalFst")
    assert grammar.apply("13th") == 'ordinal { order: "13" }'
    assert grammar.apply("23rd") == 'ordinal { order: "23" }'
