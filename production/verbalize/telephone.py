"""
Copyright 2022 Balacoon
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

Verbalizes telephone numbers
"""


import pynini
from en_us_normalization.production.verbalize.cardinal import CardinalFst
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.shortcuts import insert_space


class TelephoneFst(BaseFst):
    """
    Finite state transducer for verbalizing telephone numbers.
    Telephone numbers consist of digits in different fields.
    For now, all the number parts are read digit-by-digit.

    Examples of input/output strings:

    - telephone|country_code:1|number_part:123 123 5678|extension:1| ->
      one one two three one two three five six seven eight one

    """

    def __init__(self, cardinal: CardinalFst = None):
        super().__init__(name="telephone")
        if cardinal is None:
            cardinal = CardinalFst()

        # optional country code part
        country_code = (
            pynutil.delete("country_code:")
            + cardinal.get_digit_by_digit_fst()
            + pynutil.delete("|")
        )
        country_code_optional = pynini.closure(country_code + insert_space, 0, 1)

        # telephone numer itself
        # add a weight to enter digit_by_digit expansion in order to stay inside of it
        # as long as continuous number spans.
        number = pynutil.add_weight(cardinal.get_digit_by_digit_fst(), 1.1)
        # TODO notify about breaks between telephone number blocks
        number = pynini.closure(pynini.accep(" ") | number, 1)
        number = pynutil.delete("number_part:") + number + pynutil.delete("|")

        # optional extension
        extension = cardinal.get_digit_by_digit_fst()
        extension = pynutil.delete("extension:") + extension + pynutil.delete("|")
        optional_extension = pynini.closure(insert_space + extension, 0, 1)

        graph = country_code_optional + number + optional_extension
        self.fst = self.delete_tokens(graph).optimize()
