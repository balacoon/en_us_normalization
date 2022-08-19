# Copyright 2022 Balacoon

import os

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_cardinal():
    grammars_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("classify.address", "AddressFst")
    assert (
        grammar.apply("1599 Curabitur Rd. Bandera South Dakota 45149")
        == 'address { house: "1599" street_name: "Curabitur" street_type: "road" town: "Bandera" '
        'state: "south dakota" zip: "45149" }'
    )
    assert (
        grammar.apply("123 N Malanyuka St. SE, Apt #23 San-Francisco CA 45149-3214")
        == 'address { house: "123" pre_directional: "north" street_name: "Malanyuka" street_type: "street" '
        'post_directional: "south east" suite_type: "apartment" suite_number: "23" town: "San Francisco" '
        'state: "california" zip: "451493214" }'
    )
