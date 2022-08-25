"""
Copyright 2022 Balacoon
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

tokenize and classify roman numbers
"""

import pynini
from en_us_normalization.production.classify.cardinal import CardinalFst
from en_us_normalization.production.english_utils import get_data_file_path
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.data_loader import load_union
from learn_to_normalize.grammar_utils.shortcuts import CHAR, SIGMA, insert_space


class RomanFst(BaseFst):
    """
    Finite state transducer for classifying romans (III, IV, etc).
    In order to convert roman numbers, mappings from data files are used:

    - roman/digit_teen.tsv - contains mapping for numbers from 1 to 49.
    - roman/ties.tsv - contains mapping for dozens, i.e. 50, 60, ...
    - roman/hunderds.tsv - contains mapping for hundreds, i.e. 100, 200, ...

    Roman transducer reuses cardinal transducer to accept digits.
    Depending on the context, specifically predecessing word, it should be possible
    to define if the roman digit is cardinal or ordinal.

    - roman/cardinal_prefixes.tsv - contains cardinal prefixes, such as "Chapter"
    - roman/ordinal_prefixes.tsv - contains ordinal prefixes, such as "George"

    In case roman number doesn't have a known prefix, i.e. standalone roman number,
    it should be treated carefully. Typical mistakes:

    - roman number can be confused with abbreviation
    - roman number that consists of a single character, such as "I".
    - "XXX" - denotes pornographic materials, should have bigger weight

    Examples of transducer input/output:

    - IV ->
      roman { cardinal { count: "4" } }
    - George I ->
      roman { prefix: "george" ordinal { order: "1" } }
    - CHAPTER XIX ->
      roman { prefix: "chapter" cardinal { count: "1" } }
    """

    def __init__(self, cardinal: CardinalFst = None):
        """
        cosntructor for roman numbers transducer

        Parameters
        ----------
        cardinal: CardinalFst
            transducer for cardinal numbers to reuse.
            if not provided, will be created from scratch
        """
        super().__init__(name="roman")
        if cardinal is None:
            cardinal = CardinalFst()

        digit_teen = pynini.string_file(get_data_file_path("roman", "digit_teen.tsv"))
        ties = pynini.string_file(get_data_file_path("roman", "ties.tsv"))
        hundreds = pynini.string_file(get_data_file_path("roman", "hundreds.tsv"))

        # any roman number
        roman = digit_teen | ties
        roman |= ties + insert_space + digit_teen
        roman |= (
            hundreds
            + pynini.closure(insert_space + ties, 0, 1)
            + pynini.closure(insert_space + digit_teen, 0, 1)
        )
        roman = roman @ pynini.cdrewrite(
            pynini.cross("00 ", ""), "", "", SIGMA
        )  # remove zeros introduced by "hundreds"
        roman = roman @ pynini.cdrewrite(
            pynini.cross("0 ", ""), "", "", SIGMA
        )  # removes zero introduces by "ties"

        cardinal_roman_prefix = (
            self._load_prefixes("cardinal_prefixes.tsv") + roman @ cardinal.single_fst
        )
        # make ordinal from roman
        ordinal_roman = (
            pynutil.insert('ordinal { order: "')
            + roman @ cardinal.get_digits_fst()
            + pynutil.insert('" }')
        )
        ordinal_roman_prefix = (
            self._load_prefixes("ordinal_prefixes.tsv")
            + ordinal_roman
        )

        # stand alone roman - should have at least two digits, should be digits/teens at most
        standalone_roman = pynini.closure(CHAR, 2) @ digit_teen
        standalone_roman = standalone_roman @ cardinal.single_fst

        graph = standalone_roman | ordinal_roman_prefix | cardinal_roman_prefix
        self._single_fst = self.add_tokens(graph).optimize()
        self.connect_to_self(connector_in="-", connector_out="to")

    @staticmethod
    def _load_prefixes(name: str) -> pynini.FstLike:
        """
        helper function to load prefixes of roman numbers from a file

        Parameters
        ----------
        name: str
            name of data file in roman data directory
        """
        prefixes = load_union(get_data_file_path("roman", name), case_agnostic=True)
        return (
            pynutil.insert('prefix: "')
            + prefixes
            + pynutil.insert('"')
            + pynini.accep(" ")
        )
