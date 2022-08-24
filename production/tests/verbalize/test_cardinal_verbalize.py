# Copyright 2022 Balacoon

import os

import pynini

from learn_to_normalize.grammar_utils.grammar_loader import GrammarLoader


def test_verbalize_cardinal():
    grammars_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("verbalize.cardinal", "CardinalFst")
    assert grammar.apply("cardinal|negative:1|count:23|") == "minus twenty three"
    assert grammar.apply("cardinal|prefix:#|count:21|") == "number twenty one"
    assert (
        grammar.apply("cardinal|count:1231|") == "one thousand two hundred thirty one"
    )
    assert (
        grammar.apply("cardinal|count:4123212|")
        == "four million one hundred twenty three thousand two hundred twelve"
    )


def _apply_fst(fst: pynini.FstLike, inpt: str) -> str:
    lattice = inpt @ fst
    return pynini.shortestpath(lattice, nshortest=1, unique=True).string()


def test_digit_by_digit_fst():
    grammars_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("verbalize.cardinal", "CardinalFst")
    fst = grammar.get_digit_by_digit_fst()
    assert _apply_fst(fst, "1") == "one"
    assert _apply_fst(fst, "12") == "one two"
    assert _apply_fst(fst, "1230") == "one two three o"


def test_digit_pairs_fst():
    grammars_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    loader = GrammarLoader(grammars_dir)
    grammar = loader.get_grammar("verbalize.cardinal", "CardinalFst")
    fst = grammar.get_digit_pairs_fst()
    assert _apply_fst(fst, "1") == "one"
    assert _apply_fst(fst, "01") == "o one"
    assert _apply_fst(fst, "11") == "eleven"
    assert _apply_fst(fst, "234") == "two thirty four"
    assert _apply_fst(fst, "2304") == "twenty three o four"
