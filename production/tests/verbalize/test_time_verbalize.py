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
    assert grammar.apply("time|hours:07|minutes:1|") == "seven o one"

    # seconds and milliseconds
    assert (
        grammar.apply("time|hours:3|minutes:15|seconds:25|milliseconds:1|")
        == "three hours fifteen minutes twenty five seconds and one millisecond"
    )
    assert (
        grammar.apply("time|hours:0|minutes:1|seconds:0|milliseconds:25|")
        == "zero hours one minute zero seconds and twenty five milliseconds"
    )
    assert (
        grammar.apply("time|hours:1|seconds:8|milliseconds:3|")
        == "one hour zero minutes eight seconds and three milliseconds"
    )
