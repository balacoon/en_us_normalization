"""
Copyright 2022 Balacoon
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

Verbalizes verbatim - anything that is not classified
"""

import pynini
from en_us_normalization.production.english_utils import get_data_file_path
from en_us_normalization.production.verbalize.cardinal import CardinalFst
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.shortcuts import (
    LOWER,
    NOT_ALPHA,
    SIGMA,
    SPACE,
    TO_LOWER,
    TO_UPPER,
    UPPER,
    delete_extra_space,
    delete_space,
    insert_space,
)


class VerbatimFst(BaseFst):
    """
    Finite state transducer for verbalizing verbatim, i.e. any leftovers after classification into semiotic classes.
    Verbatim verbalization is the last effort. If it comes to it, likely existing semiotic classes require expansion.
    Strategy for verbatim verbalization:

    - sequences of letters are spelled letter by letter (i.e. converted to upper case for pronunciation generation)
    - digits are pronounced digit by digit
    - know symbols ("%" or "&") are converted to spoken form ("percent" or "ampersand")
    - unknown, non-ascii symbols are dropped (we should avoid it as much as possible!)

    Example of input/output strings:

    - verbatim|name:sa12| -> SA one two

    """

    def __init__(self, cardinal: CardinalFst = None):
        """
        constructor of verbatim verbalizer

        Parameters
        ----------
        cardinal: CardinalFst
            verbalizer of cardinal numbers to reuse for numbers expansion
        """
        super().__init__(name="verbatim")
        if cardinal is None:
            cardinal = CardinalFst()

        # expand digits
        digits = cardinal.get_digit_by_digit_fst()
        # expand known symbols
        known_symbols = pynini.string_file(get_data_file_path("symbols.tsv")).optimize()
        # remove unknown symbols
        unknown_symbols = pynini.cross(NOT_ALPHA, " ")
        # partial verbatim verbalization
        self.partial_verbatim = (
            insert_space + digits
            | pynini.closure(insert_space + known_symbols, 1)
            | pynutil.add_weight(unknown_symbols, 1.5)
        )

        self.verbatim_spelling = self._build_verbatim_verbalization(
            letter_case="to_upper"
        )
        self.verbatim_pronunciation = self._build_verbatim_verbalization(
            letter_case="to_lower"
        )
        self.verbatim_as_is = self._build_verbatim_verbalization(letter_case="keep")
        # remove space at the beginning
        graph = self.verbatim_spelling @ pynini.cdrewrite(
            delete_space, "[BOS]", "", SIGMA
        )
        graph = pynutil.delete("name:") + graph + pynutil.delete("|")
        self._single_fst = self.delete_tokens(graph).optimize()

    def _build_verbatim_verbalization(
        self, letter_case: str = "to_upper"
    ) -> pynini.FstLike:
        """
        helper function that builds expansion of letters, known symbols and digits,
        drops unknown symbols. reuses expansion of digits and known/unknown symbols
        that are stored as fields of a class

        Parameters
        ----------
        letter_case: str
            flag that defines what to do with letters

            - to_upper: convert all letters to upper case, so they will be spelled at pronunciation generation
            - to_lower: convert all letters to lower case, so pronunciations will be generated for continuous
              sequences of letters
            - keep: keeps the letters case as is, in case some preprocessing already done
        """
        letters = pynini.accep("-") | SPACE | pynini.accep("'")
        if letter_case == "to_upper":
            letters |= TO_UPPER | UPPER
        elif letter_case == "to_lower":
            letters |= TO_LOWER | LOWER
        elif letter_case == "keep":
            letters |= LOWER | UPPER
        else:
            raise RuntimeError(
                "Unsupported letter case in verbatim verbalization: {}".format(
                    letter_case
                )
            )
        graph = (
            pynutil.add_weight(insert_space, 2.0) + pynini.closure(letters, 1)
            | self.partial_verbatim
        )
        graph = pynini.closure(graph, 1)
        # collapse double spaces
        graph = graph @ pynini.cdrewrite(delete_extra_space, "", "", SIGMA)
        return graph.optimize()

    def get_verbatim_verbalization(
        self, letter_case: str = "to_upper"
    ) -> pynini.FstLike:
        """
        getter for verbatim verbalizer to be reused in other transducers.
        verbalizer inserts white space at the beginning.
        for parameter description - see :py:func:`._build_verbatim_verbalization`.
        """
        if letter_case == "to_upper":
            return self.verbatim_spelling
        elif letter_case == "to_lower":
            return self.verbatim_pronunciation
        elif letter_case == "keep":
            return self.verbatim_as_is
        else:
            raise RuntimeError(
                "Unsupported letter case in verbatim verbalization: {}".format(
                    letter_case
                )
            )
