# Copyright 2022 Balacoon

import os

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_verbatim():
    grammars_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("classify.verbatim", "VerbatimFst")
    assert grammar.apply("n33dful") == 'verbatim { name: "n33dful" }'
    # check that quotation mark is properly handled (i.e. it is escaped)
    assert grammar.apply('123hell"$') == 'verbatim { name: "123hell\\"$" }'
