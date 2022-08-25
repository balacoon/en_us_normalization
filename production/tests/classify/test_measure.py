# Copyright 2022 Balacoon

import os

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_measure():
    grammars_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("classify.measure", "MeasureFst")
    assert (
        grammar.apply("-12kg")
        == 'measure { decimal { negative: "true" integer_part: "12" } units: "kilograms" }'
    )
    assert (
        grammar.apply("1hr")
        == 'measure { decimal { integer_part: "1" } units: "hour" }'
    )
    assert (
        grammar.apply("300,000 km/s")
        == 'measure { decimal { integer_part: "300000" } units: "kilometers per second" }'
    )
    assert (
        grammar.apply(".5 kg")
        == 'measure { decimal { fractional_part: "5" } units: "kilograms" }'
    )
    # make sure "k" is not interpreted as quantity
    assert (
        grammar.apply("1.5kg")
        == 'measure { decimal { integer_part: "1" fractional_part: "5" } units: "kilograms" }'
    )
    assert (
        grammar.apply("1/2 kg")
        == 'measure { fraction { numerator: "1" denominator: "2" } units: "kilograms" '
        'style_spec_name: "with_explicit_fraction" }'
    )

    # test multi token functionality
    # range
    assert (
        grammar.apply("3kg - 5kg")
        == 'measure { decimal { integer_part: "3" } units: "kilograms" } } '
           'tokens { name: "to" } '
           'tokens { measure { decimal { integer_part: "5" } units: "kilograms" }'
    )
