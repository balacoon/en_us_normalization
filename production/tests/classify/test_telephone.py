# Copyright 2022 Balacoon

import os

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_telephone():
    grammars_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("classify.telephone", "TelephoneFst")
    assert (
        grammar.apply("+1 123-123-5678-1")
        == 'telephone { country_code: "1" number_part: "123 123 5678" extension: "1" }'
    )
