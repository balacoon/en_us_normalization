"""
Copyright 2022 Balacoon
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

tokenize and classify fractions
"""

import pynini
from classify.cardinal import CardinalFst
from english_utils import get_data_file_path
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.shortcuts import delete_space, insert_space


class FractionFst(BaseFst):
    """
    Finite state transducer for classifying fraction, for ex. "23 4/5".
    Fractions consists of

    - optional integer part
    - numerator of the fraction
    - denominator of the fraction

    Sometimes fraction is specified with specialized character, for ex. "¾".
    Those are enumerated in numbers/fractions.tsv, which also provides
    proper tagging

    Examples of input and tagged output:

    - "23 4/5" ->
      fraction { integer_part: "23" numerator: "4" denominator: "5" }

    """

    def __init__(self, cardinal: CardinalFst = None):
        """
        constructor of fraction fst

        Parameters
        ----------
        cardinal: CardinalFst
            transducer for cardinal digits to reuse.
            if not provided, cardinal fst will be created from scratch
        """
        super().__init__(name="fraction")
        if cardinal is None:
            cardinal = CardinalFst()

        # integer part of fraction - just a cardinal
        integer_part = (
            pynutil.insert('integer_part: "')
            + cardinal.get_digits_fst()
            + pynutil.insert('"')
        )
        optional_integer = pynini.closure(
            integer_part + delete_space + insert_space, 0, 1
        )
        # fraction - two cardinals separated with "/"
        fraction_separator = delete_space + pynutil.delete("/") + delete_space
        numerator = (
            pynutil.insert('numerator: "')
            + cardinal.get_digits_fst()
            + pynutil.insert('" ')
        )
        denominator = (
            pynutil.insert('denominator: "')
            + cardinal.get_digits_fst()
            + pynutil.insert('"')
        )
        fraction = numerator + fraction_separator + denominator

        # fraction can be a single specialized character
        fraction |= pynini.string_file(get_data_file_path("numbers", "fractions.tsv"))
        # in resulting graph, count part of fraction is optional
        self.fraction = cardinal.get_optional_minus() + optional_integer + fraction

        final_graph = self.add_tokens(self.fraction)
        self.fst = final_graph.optimize()
