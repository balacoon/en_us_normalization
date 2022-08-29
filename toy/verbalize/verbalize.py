"""
Copyright 2022 Balacoon

Toy verbalization grammar
"""

import os

import pynini
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.shortcuts import insert_space


class VerbalizeFst(BaseFst):
    """
    Toy verbalization grammar that expands cardinals.
    The rest is handled at classification.
    """
    def __init__(self):
        super().__init__(name="verbalize")
        verbalize_dir = os.path.dirname(os.path.abspath(__file__))
        numbers_path = os.path.join(verbalize_dir, "digits.tsv")
        digit_by_digit = pynini.string_file(numbers_path)
        digit_by_digit = digit_by_digit + pynini.closure(insert_space + digit_by_digit)
        graph = pynutil.delete("cardinal|count:") + digit_by_digit + pynutil.delete("|")
        self._single_fst = graph.optimize()
