# Copyright 2022 Balacoon

import os

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_verbalize_time():
    grammars_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("verbalize.time", "TimeFst")
    assert (
        grammar.apply("time|hours:12|minutes:30|suffix:AM|zone:EST|")
        == "twelve thirty AM EST"
    )
    assert grammar.apply("time|hours:12|") == "twelve o'clock"
    assert grammar.apply("time|hours:12|minutes:00|") == "twelve o'clock"
    assert grammar.apply("time|hours:07|minutes:10|") == "seven ten"
    assert grammar.apply("time|hours:07|minutes:01|") == "seven o one"
