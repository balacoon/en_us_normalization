# Copyright 2022 Balacoon

import os

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_abbreviation():
    grammars_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("classify.abbreviation", "AbbreviationFst")
    assert grammar.apply("F.B.I.") == 'name: "FBI"'
    assert grammar.apply("F...B") == 'name: "FB"'  # no matter the separation between consonants
    assert grammar.apply("FBI") == 'name: "FBI"'
    assert grammar.apply("f.b.i.") == 'name: "FBI"'
    assert grammar.apply("IEEE") == 'name: "IEEE"'
    assert grammar.apply("wwe's") == 'name: "WWE\'S"'
    assert grammar.apply("USAs") == 'name: "USA\'S"'

    # multi-token
    # slash
    assert grammar.apply("AC/DC") == 'name: "AC" } tokens { name: "DC"'
