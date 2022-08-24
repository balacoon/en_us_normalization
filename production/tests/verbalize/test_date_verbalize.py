# Copyright 2022 Balacoon

import os

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_verbalize_date():
    grammars_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("verbalize.date", "DateFst")
    assert (
        grammar.apply("date|month:january|day:5|year:2012|")
        == "january fifth twenty twelve"
    )
    assert (
        grammar.apply("date|day:5|month:january|year:2012|")
        == "the fifth of january twenty twelve"
    )
    assert grammar.apply("date|month:january|day:5|") == "january fifth"
    assert (
        grammar.apply("date|month:january|year:960|era:BC|")
        == "january nine hundred sixty BC"
    )
    assert grammar.apply("date|year:70|era:s|") == "seventies"
    assert grammar.apply("date|year:2010|era:s|") == "twenty tens"
    assert grammar.apply("date|year:2020|era:s|") == "twenty twenties"
    assert grammar.apply("date|year:1900|") == "nineteen hundred"
    assert grammar.apply("date|year:1901|") == "nineteen o one"
