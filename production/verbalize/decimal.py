"""
Copyright 2022 Balacoon
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

Verbalizes decimal numbers
"""

import pynini
from en_us_normalization.production.verbalize.cardinal import CardinalFst
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.shortcuts import insert_space, LOWER


class DecimalFst(BaseFst):
    """
    Finite state transducer for verbalizing decimal, i.e. number with integer and fractional part.
    Integer part is verbalized as a cardinal number. Fraction part is verbalized digit by digit.
    "point" is inserted in front of fractional part.

    Grammar heavily reuses transducer for Cardinals.

    Examples of input/output string:

    - decimal|negative:1|integer_part:12|fractional_part:5006| -> minus twelve point five o o six

    """

    def __init__(self, cardinal: CardinalFst = None):
        super().__init__(name="decimal")
        if cardinal is None:
            cardinal = CardinalFst()

        # expand digits one by one for fractional part
        fractional = (
            pynutil.insert("point")
            + pynutil.delete("fractional_part:")
            + insert_space
            + cardinal.get_digit_by_digit_fst()
            + pynutil.delete("|")
        )
        # reuse cardinal to expand integer part of decimal
        integer = (
            pynutil.delete("integer_part:")
            + cardinal.get_cardinal_expanding_fst()
            + pynutil.delete("|")
        )
        # expand quantity - just remove tags if any
        quantity = (
            pynutil.delete("quantity:")
            + pynini.closure(LOWER, 1)
            + pynutil.delete("|")
        )
        optional_quantity = pynini.closure(insert_space + quantity, 0, 1)

        # 3 cases: when there is only integer, only fraction or both
        both = integer + insert_space + fractional
        graph = integer | fractional | both
        optional_sign = pynini.closure(pynini.cross("negative:1|", "minus "), 0, 1)
        self.graph = optional_sign + graph + optional_quantity
        self.fst = self.delete_tokens(self.graph).optimize()

    def get_graph(self):
        """
        helper function that returns the whole decimal verbalization graph
        without token name deletion. this is needed if the whole decimal
        graph is reused in another semiotic class (for ex. measure)
        """
        return self.graph
