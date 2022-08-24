# Copyright 2022 Balacoon

import os

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_verbalize_measure():
    grammars_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("verbalize.measure", "MeasureFst")
    assert (
        grammar.apply("measure|negative:1|integer_part:12|units:kilograms|")
        == "minus twelve kilograms"
    )
    assert (
        grammar.apply("measure|integer_part:12|fractional_part:5|units:kilograms|")
        == "twelve point five kilograms"
    )
    assert (
        grammar.apply(
            "measure|integer_part:23|numerator:4|denominator:5|units:miles per hour|"
        )
        == "twenty three and four fifths miles per hour"
    )
