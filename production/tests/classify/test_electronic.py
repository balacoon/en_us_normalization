# Copyright 2022 Balacoon

import os

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_electronic():
    grammars_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("classify.electronic", "ElectronicFst")
    assert (
        grammar.apply("balacoon@gmail.com")
        == 'electronic { username: "balacoon" domain: "gmail.com" }'
    )
    assert grammar.apply("google.com") == 'electronic { domain: "google.com" }'
    assert grammar.apply("www.google.com") == 'electronic { domain: "WWW.google.com" }'
    assert (
        grammar.apply("https://google.ua")
        == 'electronic { protocol: "HTTPS" domain: "google.UA" }'
    )
    assert (
        grammar.apply("https://google.ua/translate&=1231")
        == 'electronic { protocol: "HTTPS" domain: "google.UA" path: "/translate&=1231" }'
    )
    assert (
        grammar.apply("http://cat:dog@www.google.com:8080/?231eds2@90iu")
        == 'electronic { protocol: "HTTP" username: "cat" password: "'
        'dog" domain: "WWW.google.com" port: "8080" path: "/?231eds2@90iu" }'
    )
