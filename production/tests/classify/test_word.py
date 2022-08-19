# Copyright 2022 Balacoon

import os

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_word():
    grammars_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("classify.word", "WordFst")
    assert grammar.apply("hello") == 'name: "hello"'
    assert grammar.apply("don't") == 'name: "don\'t"'
