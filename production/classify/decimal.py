"""
Copyright 2022 Balacoon
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

tokenize and classify decimals
"""

import pynini
from en_us_normalization.production.classify.cardinal import CardinalFst
from en_us_normalization.production.english_utils import get_data_file_path
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.shortcuts import DIGIT, insert_space, delete_space
from learn_to_normalize.grammar_utils.data_loader import load_union


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

    Optionally decimal can have quantity after the number. There are two options:
    full form (for ex. "12 thousands") or short version (for ex. "12k").
    Supported quantities are stored in data/magnitudes.tsv

    Examples for decimals and their tagging:

    - -12.5006 -> decimal { negative: "true" integer_part: "12"  fractional_part: "5006" }
    - 13k -> decimal { integer_part: "13"  quantity: "thousands" }

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
            delete_point
            + pynutil.insert('fractional_part: "')
            + pynini.closure(DIGIT, 1)
            + pynutil.insert('"')
        )

        # 3 options:
        # 1) there is both integer and fractional part
        # 2) there is just integer part
        # 3) there is just fractional part
        both_integer_and_fraction = integer + insert_space + fraction
        decimal_tagged = both_integer_and_fraction | integer | fraction
        optional_minus = pynini.closure(pynutil.insert("negative: ") + pynini.cross("-", '"true" '), 0, 1)
        self._basic_decimal_fst = optional_minus + decimal_tagged
        graph = self.add_quantity(self._basic_decimal_fst)
        self._single_fst = self.add_tokens(graph).optimize()
        self.connect_to_self(connector_in="-", connector_out="to", allow_spaces=True)

    def get_basic_decimal_fst(self):
        """
        getter for reusable basic decimal digits fst, that transduces "12.56" to
        `integer_part: "12"  fractional_part: "56"`. I.e. before adding decimal tag and without quantity.
        """
        return self._basic_decimal_fst

    @staticmethod
    def add_quantity(fst: pynini.FstLike) -> pynini.FstLike:
        """
        helper function to add optional quantity field
        on top of the graph
        """
        # quantity can be in a short form just after a number
        singular_quantity = pynini.string_file(get_data_file_path("magnitudes.tsv"))
        quantity = singular_quantity + pynutil.insert('s')
        # quantity can be in a full form after a space
        magnitudes = load_union(get_data_file_path("magnitudes.tsv"), column=1, case_agnostic=True)
        optional_s = pynini.closure(pynini.accep("s") | pynini.cross("S", "s"), 0, 1)
        quantity |= (delete_space + magnitudes + optional_s)
        quantity = insert_space + pynutil.insert('quantity: "') + quantity + pynutil.insert('"')
        optional_quantity = pynini.closure(quantity, 0, 1)
        fst_quantity = fst + optional_quantity

        # need to add another option when quantity is singular
        one = pynini.accep("1") | pynini.accep("1.0")
        one = pynini.cross(one, "integer_part: \"1\"")
        one += insert_space + pynutil.insert('quantity: "') + singular_quantity + pynutil.insert('"')
        fst_quantity |= one

        return fst_quantity


