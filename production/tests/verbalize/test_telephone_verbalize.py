# Copyright 2022 Balacoon

import os

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_verbalize_telephone():
    grammars_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("verbalize.telephone", "TelephoneFst")
    assert (
        grammar.apply("telephone|country_code:1|number_part:123 123 5678|extension:1|")
        == "one one two three one two three five six seven eight one"
    )
