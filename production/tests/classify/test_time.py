# Copyright 2022 Balacoon

import os

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_time():
    grammars_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("classify.time", "TimeFst")
    assert (
        grammar.apply("12:30 a.m. est")
        == 'time { hours: "12" minutes: "30" suffix: "AM" zone: "EST" }'
    )
    assert (
        grammar.apply("2.30 a.m.") == 'time { hours: "2" minutes: "30" suffix: "AM" }'
    )
    assert (
        grammar.apply("02.30 a.m.") == 'time { hours: "2" minutes: "30" suffix: "AM" }'
    )
    assert grammar.apply("2.00 a.m.") == 'time { hours: "2" suffix: "AM" }'
    assert grammar.apply("2 a.m.") == 'time { hours: "2" suffix: "AM" }'
    assert grammar.apply("02:00") == 'time { hours: "2" }'
    assert grammar.apply("02:00") == 'time { hours: "2" }'
    assert grammar.apply("02:05") == 'time { hours: "2" minutes: "5" }'
    assert grammar.apply("2:00") == 'time { hours: "2" }'

    # test multi token functionality
    # range
    assert (
        grammar.apply("12:30 - 12:45")
        == 'time { hours: "12" minutes: "30" } } '
           'tokens { name: "to" } '
           'tokens { time { hours: "12" minutes: "45" }'
    )
