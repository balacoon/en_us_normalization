# Copyright 2022 Balacoon

import os

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_verbalize_fraction():
    grammars_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("verbalize.fraction", "FractionFst")
    # regular expansion
    assert (
        grammar.apply("fraction|integer_part:23|numerator:4|denominator:5|")
        == "twenty three and four fifths"
    )
    # having negative field
    assert (
        grammar.apply("fraction|negative:1|integer_part:1|numerator:17|denominator:25|")
        == "minus one and seventeen twenty fifths"
    )
    # single-word fraction (1/2)
    assert (
        grammar.apply("fraction|integer_part:17|numerator:1|denominator:2|")
        == "seventeen and a half"
    )
    # custom denominator in a fraction
    assert (
        grammar.apply("fraction|integer_part:1|numerator:5|denominator:4|")
        == "one and five quarters"
    )
    # numerator is 1, i.e. singular denominator
    assert (
        grammar.apply("fraction|integer_part:1|numerator:1|denominator:4|")
        == "one and a quarter"
    )
    # integer part is absent for single-word fraction and numerator is 1
    assert grammar.apply("fraction|numerator:1|denominator:2|") == "one half"
    # integer part is absent for single-word fraction
    assert grammar.apply("fraction|numerator:3|denominator:2|") == "three halves"
