"""
Copyright 2022 Balacoon
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

Verbalizes cardinal numbers
"""

import pynini
from en_us_normalization.production.english_utils import get_data_file_path
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.shortcuts import DIGIT, insert_space


class CardinalFst(BaseFst):
    """
    Finite state transducer for verbalizing cardinal number. A pretrained FAR is used
    to avoid writing down all the rules for number expansion.
    Check verbalizer specification for list of possible fields.

    Apart from cardinal expansion, grammar also provides some fsts to be reused in other
    semiotic classes:

    - expand number digit by digit
    - expand number grouping digits in to pairs

    Examples of input/output strings:

    - cardinal|negative:1|count:23| -> minus twenty three
    - cardinal|prefix:number|count:21| -> number twenty one

    """

    def __init__(self):
        super().__init__(name="cardinal")

        self.cardinal_far = pynini.Far(
            get_data_file_path("numbers", "cardinal_number_verbalizer.far")
        ).get_fst()
        integer = pynutil.delete("count:") + self.cardinal_far + pynutil.delete("|")

        optional_sign = pynini.closure(pynini.cross("negative:1|", "minus "), 0, 1)
        number = pynutil.delete("prefix:") + pynini.accep("number") + pynini.cross("|", " ")
        optional_number = pynini.closure(number, 0, 1)
        numbers = optional_number + optional_sign + integer
        self._single_fst = self.delete_tokens(numbers).optimize()

        # few fsts that are not directly used for cardinal expansion, but are useful for other
        # semiotic classes.
        # 1. read a number digit by digit
        digit_by_digit = pynini.string_file(get_data_file_path("numbers", "digit.tsv"))
        digit_by_digit = pynini.invert(digit_by_digit) | pynini.cross("0", "o")
        # with closure and without to avoid whitespace at the beginning
        self.separate_digit_far = digit_by_digit + pynini.closure(
            insert_space + digit_by_digit
        )

        # 2. read a number grouping digits in pairs
        two_digits = pynini.cross("0", "o ") + digit_by_digit
        two_digits |= pynutil.add_weight((DIGIT + DIGIT) @ self.cardinal_far, 1.1)
        # forces 2 digits or more
        digit_pair_far = (
            pynini.closure(digit_by_digit + insert_space, 0, 1)
            + two_digits
            + pynini.closure(insert_space + two_digits, 0, 1)
        )
        # could be just one digit
        self.digit_pair_far = digit_by_digit | digit_pair_far

    def get_cardinal_expanding_fst(self):
        """
        helper function that provides and fst to expand
        cardinals. can be reused by other semiotic classes.
        simply attach to your own FST or cross with permissive FST
        to limit number of digits for expansion.
        """
        return self.cardinal_far

    def get_digit_by_digit_fst(self):
        """
        helper function that provides fst to expand
        numbers digit by digit.
        It can be used in verbatim, decimal, etc.
        """
        return self.separate_digit_far

    def get_digit_pairs_fst(self):
        """
        helper function that provides fst to
        expand numbers by digit pairs, i.e.
        "2012 -> twenty twelve"
        """
        return self.digit_pair_far
