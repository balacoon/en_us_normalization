"""
Copyright 2022 Balacoon
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

tokenize and classify decimals
"""

import pynini
from en_us_normalization.production.classify.cardinal import CardinalFst
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.shortcuts import DIGIT, insert_space


class DecimalFst(BaseFst):
    """
    Finite state transducer for classifying decimal, i.e. numbers with fractional part.
    There are 3 options to accept in fst:

    - both integer and fractional part are present, for ex. "12.5006"
    - only fractional part is present, for ex. ".35"
    - only integer part is present, for ex. "12". This one can be handled by cardinal semiotic class,
      but it is kept in decimal as well, since decimal can be a part of composite semiotic class, such as
      `measure`

    Integer part of decimal - can be any cardinal or a single "0" for cases such as "0.5"
    Fractional part can be any sequence of digits after the dot

    Examples ofr decimals and their tagging:

    - -12.5006 ->
      decimal { negative: "true" integer_part: "12"  fractional_part: "5006" }

    TODO: add handling of abbreviated quantities, for ex. .5B -> decimal { fractional_part: "5" quantity: "billion" }
    """

    def __init__(self, cardinal: CardinalFst = None):
        """
        constructor for decimal fst

        Parameters
        ----------
        cardinal: CardinalFst
            a cardinal fst to reuse digits fst from it. If not provided, will be initialized from scratch.
        """
        super().__init__(name="decimal")
        if cardinal is None:
            cardinal = CardinalFst()

        delete_point = pynutil.delete(".")
        digits = cardinal.get_digits_fst() | pynini.accep("0")
        integer = pynutil.insert('integer_part: "') + digits + pynutil.insert('"')
        fraction = (
            pynutil.insert('fractional_part: "')
            + pynini.closure(DIGIT, 1)
            + pynutil.insert('"')
        )

        # 3 options:
        # 1) there is both integer and fractional part
        # 2) there is just integer part
        # 3) there is just fractional part
        both_integer_and_fraction = integer + insert_space + delete_point + fraction
        only_integer = integer
        only_fraction = delete_point + fraction
        decimal_tagged = both_integer_and_fraction | only_integer | only_fraction
        self.decimal_tagged_signed = cardinal.get_optional_minus() + decimal_tagged
        final_graph = self.add_tokens(self.decimal_tagged_signed)
        self.fst = final_graph.optimize()

    def get_decimal_fst(self):
        """
        getter for reusable decimal digits fst, that transduces "12.56" to
        "{ integer_part: "12"  fractional_part: "56" }"
        """
        return self.decimal_tagged_signed
