"""
Copyright 2022 Balacoon
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

tokenizes and classifies cardinals
"""

import pynini
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.shortcuts import DIGIT, delete_space


class CardinalFst(BaseFst):
    """
    Finite state transducer for classifying cardinals - numbers expressing amount.
    Most of the work is done in verbalization of cardinals, in classifying only few things to take into account

    - there shouldn't be too many digits. If there are too many, pronounce them letter by letter.
      for now the limit is 6.
    - number can be negative, i.e. have "-" in front of it
    - amount can't start with zero
    - cardinal numbers can be separate with commas, for ex.: 1,000,000
    - cardinal number can be pre-pended with prefix, for ex "#"

    Examples of cardinals:
    - -23 -> cardinal { negative: "true"  count: "23" }
    - 4,123 -> cardinal { count: "4123" }
    - # 21 -> cardinal { prefix: "number" count: "21" }

    """

    def __init__(self):
        super().__init__(name="cardinal")
        digit_except_zero = pynini.difference(DIGIT, pynini.accep("0"))
        # if digits only has more than 6 digits - leave it up to verbatim
        digits_only = digit_except_zero + pynini.closure(DIGIT, 0, 5)
        digits_with_coma = (
            digit_except_zero
            + pynini.closure(DIGIT, 0, 2)
            + pynini.closure(pynutil.delete(",") + pynini.closure(DIGIT, 3, 3))
        )
        self.digits = digits_only | digits_with_coma
        self.digits.optimize()
        number_prefix = pynini.accep("No") | pynini.accep("NO") | pynini.accep("no")
        number_prefix += pynini.closure(pynutil.delete("."))
        number_prefix |= pynini.accep("#")
        number_prefix = pynini.cross(number_prefix, "number")
        optional_prefix = pynini.closure(
            pynutil.insert('prefix: "') + number_prefix + delete_space + pynutil.insert('" '), 0, 1
        )
        optional_minus = pynini.closure(
            pynutil.insert("negative: ") + pynini.cross("-", '"true" '), 0, 1
        )
        self.digits_tagged = (
            pynutil.insert('count: "') + self.digits + pynutil.insert('"')
        )
        graph = optional_prefix + optional_minus + self.digits_tagged
        self._single_fst = self.add_tokens(graph)
        self.connect_to_self(connector_in="-", connector_out=None)
        self.connect_to_self(connector_in=":", connector_out="to", connector_spaces="none_or_one", weight=3.0)
        self.connect_to_self(connector_in=["x", "÷", "+"], connector_out=["by", "divided by", "plus"],
                             connector_spaces="none_or_one", to_closure=True)

    def get_digits_fst(self) -> pynini.FstLike:
        """
        getter for reusable fst with cardinal digits that can be reused in other transducers
        """
        return self.digits
