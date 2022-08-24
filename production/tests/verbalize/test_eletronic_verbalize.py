# Copyright 2022 Balacoon

import os

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_verbalize_electronic():
    grammars_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("verbalize.electronic", "ElectronicFst")
    assert (
        grammar.apply("electronic|username:balacoon|domain:gmail.com|")
        == "balacoon at gmail dot com"
    )
    assert grammar.apply("electronic|domain:google.com|") == "google dot com"
    assert (
        grammar.apply("electronic|protocol:HTTPS|domain:google.UA|")
        == "HTTPS google dot UA"
    )
    assert (
        grammar.apply(
            "electronic|protocol:HTTPS|domain:google.UA|path:/translate&=1231|"
        )
        == "HTTPS google dot UA slash TRANSLATE and equal sign one two three one"
    )
    assert (
        grammar.apply(
            "electronic|protocol:HTTP|username:cat|password:dog|domain:WWW.google.com|port:8080|path:/?231eds2@90iu|"
        )
        == "HTTP cat password DOG at WWW dot google dot com port eighty eighty slash question mark two three one EDS "
        "two at sign nine o IU"
    )
