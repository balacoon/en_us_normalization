# Copyright 2022 Balacoon

import os

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_roman():
    grammars_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("classify.roman", "RomanFst")
    assert grammar.apply("IV") == 'roman { cardinal { count: "4" } }'
    assert grammar.apply("XXXII") == 'roman { cardinal { count: "32" } }'
    assert (
        grammar.apply("CHAPTER XI")
        == 'roman { prefix: "chapter" cardinal { count: "11" } }'
    )
    assert (
        grammar.apply("George II")
        == 'roman { prefix: "george" ordinal { order: "2" } }'
    )

    # test multi token functionality
    # range
    assert (
        grammar.apply("III - VIII")
        == 'roman { cardinal { count: "3" } } } '
           'tokens { name: "to" } '
           'tokens { roman { cardinal { count: "8" } }'
    )
