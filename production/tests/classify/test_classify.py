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

    # disambiguate time and decimal
    assert grammar.apply("1.30") == 'tokens { decimal { integer_part: "1" fractional_part: "30" } }'
    assert grammar.apply("1.30 PM") == 'tokens { time { hours: "1" minutes: "30" suffix: "PM" } }'

    # disambiguate word + symbol vs word + punctiuation
    assert grammar.apply("hello,") == 'tokens { name: "hello" right_punct: "," }'
    assert grammar.apply("hello#") == 'tokens { name: "hello" } tokens { name: "hash" }'
