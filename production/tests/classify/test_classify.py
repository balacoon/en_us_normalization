# Copyright 2022 Balacoon

import os

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_classify():
    grammars_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("classify.classify", "ClassifyFst")
    assert (
        grammar.apply("hello world!")
        == 'tokens { name: "hello" } tokens { name: "world" right_punct: "!" }'
    )
