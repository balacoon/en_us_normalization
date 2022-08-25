"""
Copyright 2022 Balacoon
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

Verbalizes money
"""

import pynini
from en_us_normalization.production.english_utils import (
    get_data_file_path,
    singular_to_plural_fst,
)
from en_us_normalization.production.verbalize.cardinal import CardinalFst
from en_us_normalization.production.verbalize.decimal import DecimalFst
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.shortcuts import DIGIT, NOT_BAR, insert_space


class MoneyFst(BaseFst):
    """
    Finite state transducer for verbalizing money. During tokenization,
    amount is split into integer and fraction part. During verbalization, those
    are expanded reusing transducers from cardinal verbalizer. The reason not to use decimal transducer,
    is because fraction part of money behaves slightly differently.
    For instance:

        "integer_part:12|fractional_part:5|" should be "twelve dollars fifty cents".

    The only task is to expand currency symbol appropriately: into major and minor versions.
    This is done using expansions provided in the data files:

    - data/currency/major.tsv
    - data/currency/minor.tsv - it is not so straightforward to convert plural/singular,
      so two data files are maintained.
    - data/currency/minor_plural.tsv

    For example "$" is expanded to "dollars" and "cents".
    Additionally, money verbalizer has to take care of changing form of major/minor currencies
    to plural or singular depending on the predecessing number.

    Examples of input/output strings:

    - money|integer_part:12|currency:$|fractional_part:05|currency:$| -> twelve dollars and five cents

    """

    def __init__(self, cardinal: CardinalFst = None, decimal: DecimalFst = None):
        """
        constructor of money verbalizer

        Parameters
        ----------
        cardinal: CardinalFst
            reusing cardinal transducer to expand integer/fraction parts of money
        decimal: DecimalFst
            reusing decimal transducer to expand money when there is explicit quantity
        """
        super().__init__(name="money")
        if cardinal is None:
            cardinal = CardinalFst()
        if decimal is None:
            decimal = DecimalFst(cardinal=cardinal)

        # verbalize integer part together with currency
        major_currency = pynini.string_file(
            get_data_file_path("currency", "major.tsv")
        ).optimize()
        # special case of singular amount
        integer_part_singular = (
            pynini.cross("integer_part:1|currency:", "one ")
            + major_currency
            + pynutil.delete("|")
        )
        # plural currency
        major_currency = major_currency @ singular_to_plural_fst()
        integer_part_plural = (
            pynutil.delete("integer_part:")
            + cardinal.get_cardinal_expanding_fst()
            + pynutil.delete("|")
            + pynini.cross("currency:", " ")
            + major_currency
            + pynutil.delete("|")
        )
        # plural amount has less weight
        integer_part = integer_part_singular | pynutil.add_weight(
            integer_part_plural, 1.1
        )

        # just delete fractional part if its zeros
        currency = pynini.closure(NOT_BAR, 1)
        one_or_two_zeros = pynini.closure("0", 1, 2)
        fraction_part_zeros = (
            pynini.accep("fractional_part:") + one_or_two_zeros + pynini.accep("|")
        )
        fraction_part_zeros = (
            fraction_part_zeros
            + pynini.accep("currency:")
            + currency
            + pynini.accep("|")
        )
        fraction_part_zeros_removed = pynutil.delete(fraction_part_zeros)
        fraction_part_zeros_removed = pynutil.add_weight(
            fraction_part_zeros_removed, 0.95
        )

        # special case of zeros for fractional part that should be spoken out loud
        minor_currency = pynini.string_file(
            get_data_file_path("currency", "minor_plural.tsv")
        ).optimize()
        minor_currency = (
            insert_space
            + pynutil.delete("currency:")
            + minor_currency
            + pynutil.delete("|")
        )
        fraction_part_zeros = pynini.cross(one_or_two_zeros, "zero")
        fraction_part_zeros = (
            pynutil.delete("fractional_part:")
            + fraction_part_zeros
            + pynutil.delete("|")
        )
        fraction_part_zeros_spoken = fraction_part_zeros + minor_currency
        fraction_part_zeros_spoken = pynutil.add_weight(fraction_part_zeros_spoken, 0.9)

        # verbalize special case when fractional is singular
        minor_currency_singular = pynini.string_file(
            get_data_file_path("currency", "minor.tsv")
        ).optimize()
        fraction_part_singular = pynini.cross("fractional_part:01|currency:", "one ")
        fraction_part_singular = (
            fraction_part_singular + minor_currency_singular + pynutil.delete("|")
        )

        # verbalize plural fractional
        fraction_no_front_zero = pynutil.delete("0") + DIGIT
        fraction_extra_back_zero = DIGIT + pynutil.insert("0")
        fraction_two_digits = DIGIT + DIGIT
        fraction = (
            fraction_no_front_zero
            | fraction_extra_back_zero
            | pynutil.add_weight(fraction_two_digits, 1.1)
        )
        fraction = fraction @ cardinal.get_cardinal_expanding_fst()
        fraction = pynutil.delete("fractional_part:") + fraction + pynutil.delete("|")
        fraction_plural = fraction + minor_currency
        fraction_part = fraction_part_singular | pynutil.add_weight(
            fraction_plural, 1.1
        )

        optional_sign = pynini.closure(pynini.cross("negative:1|", "minus "), 0, 1)
        graph = (
            integer_part
            | fraction_part
            | fraction_part_zeros_spoken
            | (integer_part + fraction_part_zeros_removed)
            | (integer_part + insert_space + fraction_part)
        )
        graph = optional_sign + graph
        # another option is money with quantity
        graph_with_quantity = (
            decimal.get_graph()
            + pynini.cross("currency:", " of ")
            + major_currency
            + pynutil.delete("|")
        )
        # add to general graph but slightly less probable
        graph |= pynutil.add_weight(graph_with_quantity, 1.1)
        self.fst = self.delete_tokens(graph).optimize()
