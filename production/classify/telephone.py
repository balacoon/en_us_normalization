"""
Copyright 2022 Balacoon
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

tokenize and classify telephone numbers
"""

import pynini
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.shortcuts import DIGIT, delete_space, insert_space


class TelephoneFst(BaseFst):
    """
    Finite state transducer for classifying telephone numbers.
    Telephone numbers consit of:

    - country code (optional): +\*\*\*
    - number part separated by dashes or brackets: \*\*\*-\*\*\*-\*\*\*\*, or (\*\*\*) \*\*\*-\*\*\*\*
    - extension at the end of number (optional): 1-9999

    Examples of input/output strings:

    - +1 123-123-5678-1 ->
      telephone { country_code: "1" number_part: "123 123 5678" extension: "1" }

    """

    def __init__(self):
        super().__init__(name="telephone")

        delete_dash = pynutil.delete("-")
        delete_optional_dash = pynini.closure(delete_dash, 0, 1)
        fix_space = delete_space + insert_space

        # country code of format "+***"
        country_code = pynutil.delete("+") + pynini.closure(DIGIT, 1, 3)
        country_code = (
            pynutil.insert('country_code: "') + country_code + pynutil.insert('"')
        )
        optional_country_code = pynini.closure(
            country_code + delete_optional_dash + fix_space, 0, 1
        )

        # number of format "***-***-****", or "(***) ***-****"
        # "***-"
        simple_number_prefix = pynini.closure(DIGIT, 3, 3) + delete_dash
        # "(***)-"
        bracket_number_prefix = (
            pynutil.delete("(")
            + pynini.closure(DIGIT, 3, 3)
            + pynutil.delete(")")
            + delete_optional_dash
            + delete_space
        )
        number_prefix = simple_number_prefix | bracket_number_prefix
        # "***-****"
        number_suffix = (
            insert_space
            + pynini.closure(DIGIT, 3, 3)
            + delete_dash
            + insert_space
            + pynini.closure(DIGIT, 4, 4)
        )
        number = number_prefix + number_suffix
        number = pynutil.insert('number_part: "') + number + pynutil.insert('"')

        # extension of format "-****"
        extension = delete_dash + pynini.closure(DIGIT, 1, 4)
        extension = (
            insert_space
            + pynutil.insert('extension: "')
            + extension
            + pynutil.insert('"')
        )
        optional_extension = pynini.closure(extension, 0, 1)

        graph = optional_country_code + number + optional_extension
        final_graph = self.add_tokens(graph)
        self.fst = final_graph.optimize()
