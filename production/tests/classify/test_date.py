# Copyright 2022 Balacoon

import os

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_date():
    grammars_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("classify.date", "DateFst")
    assert (
        grammar.apply("jan. 5, 2012")
        == 'date { month: "january" day: "5" year: "2012" }'
    )
    assert (
        grammar.apply("jan. 3rd, 2012")
        == 'date { month: "january" day: "3" year: "2012" }'
    )
    assert grammar.apply("jan 5") == 'date { month: "january" day: "5" }'
    assert grammar.apply("Jan 5") == 'date { month: "january" day: "5" }'
    assert grammar.apply("5 Jan") == 'date { day: "5" month: "january" style_spec_name: "dmy" }'
    assert (
        grammar.apply("5 january 2012")
        == 'date { day: "5" month: "january" year: "2012" style_spec_name: "dmy" }'
    )
    assert (
        grammar.apply("january 960 B.C.")
        == 'date { month: "january" year: "960" era: "BC" }'
    )
    assert (
        grammar.apply("2012-01-05")
        == 'date { year: "2012" month: "january" day: "5" style_spec_name: "dmy" }'
    )
    assert (
        grammar.apply("2012.01.5")
        == 'date { year: "2012" month: "january" day: "5" style_spec_name: "dmy" }'
    )
    assert (
        grammar.apply("02/03/1994")
        == 'date { month: "february" day: "3" year: "1994" }'
    )
    assert (
        grammar.apply("13/03/1994")
        == 'date { day: "13" month: "march" year: "1994" style_spec_name: "dmy" }'
    )
    assert grammar.apply("1921") == 'date { year: "1921" }'
    assert grammar.apply("1960s") == 'date { year: "1960" era: "s" }'
    assert grammar.apply("'70s") == 'date { year: "70" era: "s" }'
