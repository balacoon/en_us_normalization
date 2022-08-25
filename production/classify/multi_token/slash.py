"""
Copyright Balacoon 2022

tokenize and classify two tokens separated by slash
"""

import pynini
from en_us_normalization.production.classify.word import WordFst
from en_us_normalization.production.classify.abbreviation import AbbreviationFst
from en_us_normalization.production.classify.punctuation_rules import get_punctuation_rules
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.shortcuts import delete_space, insert_space, wrap_token


class SlashFst(BaseFst):
    """
    Slash fst is a situation when two tokens are separated by a slash without spaces.
    For example: AC/DC or radio/video.

    Examples of input / output:

    - AC/DC -> tokens { name: "AC" } tokens { name: "DC" }
    - radio/video -> tokens { name: "radio" } tokens { name: "video" }

    """

    def __init__(
        self,
        abbreviation: AbbreviationFst = None,
        word: WordFst = None,
        left_punct: pynini.FstLike = None,
        right_punct: pynini.FstLike = None,
    ):
        """
        constructor of score transducer

        Parameters
        ----------
        abbreviation: AbbreviationFst
            abbreviation detector to reuse
        word: WordFst
            fst for regular words to reuse
        left_punct: pynini.FstLike
            punctuation to the left of multi-token
        right_punct: pynini.FstLike
            punctuation to the right of multi-token
        """
        super().__init__(name="score")

        # initialize transducers if those are not provided
        # may be needed in testing.
        if abbreviation is None:
            abbreviation = AbbreviationFst()
        if word is None:
            word = WordFst()
        if left_punct is None and right_punct is None:
            left_punct, right_punct = get_punctuation_rules()

        abbr_or_word = abbreviation.fst | pynutil.add_weight(word.fst, 1.1)
        graph = (
            wrap_token(left_punct + abbr_or_word)
            + pynini.cross("/", " ")
            + wrap_token(abbr_or_word + right_punct)
        )
        self.fst = graph.optimize()
