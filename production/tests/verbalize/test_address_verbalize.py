# Copyright 2022 Balacoon

import os

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_verbalize_address():
    grammars_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("verbalize.address", "AddressFst")
    assert (
        grammar.apply(
            "address|house:1599|street_name:Curabitur|street_type:road|town:Bandera|state:south dakota|zip:45149|"
        )
        == "fifteen ninety nine curabitur road bandera south dakota four five one four nine"
    )
    assert (
        grammar.apply(
            "address|house:123|pre_directional:north|street_name:Malanyuka|street_type:street|"
            "post_directional:south east|suite_type:apartment|suite_number:23|town:San Francisco|"
            "state:california|zip:451493214|"
        )
        == "one twenty three north malanyuka street south east apartment twenty three san francisco california four "
        "five one four nine three two one four"
    )
