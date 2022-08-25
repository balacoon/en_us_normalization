"""
Copyright Balacoon 2022

tokenize and classify scores
"""

import pynini
from en_us_normalization.production.classify.cardinal import CardinalFst
from en_us_normalization.production.classify.punctuation_rules import get_punctuation_rules

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.shortcuts import delete_space, insert_space, wrap_token


class ScoreFst(BaseFst):
    """
    Score is a multi-token, where two cardinals are connected with ":".
    It represents match score. Connecting colon symbol is expanded into "to".
    score transducer reuses cardinal transducer.

    Examples of input / output:

    - 1 : 2 ->
      tokens { cardinal { count: "1" } } tokens { name: "to" } tokens { cardinal { count "2" } }

    """

    def __init__(
        self,
        cardinal: CardinalFst = None,
        left_punct: pynini.FstLike = None,
        right_punct: pynini.FstLike = None,
    ):
        """
        constructor of score transducer

        Parameters
        ----------
        cardinal: CardinalFst
            a cardinal to reuse
        left_punct: pynini.FstLike
            punctuation to the left of multi-token
        right_punct: pynini.FstLike
            punctuation to the right of multi-token
        """
        super().__init__(name="score")

        # initialize transducers if those are not provided
        # may be needed in testing.
        if cardinal is None:
            cardinal = CardinalFst()
        if left_punct is None and right_punct is None:
            left_punct, right_punct = get_punctuation_rules()

        left = wrap_token(left_punct + cardinal.single_fst)
        middle = wrap_token(pynini.cross(":", 'name: "to"'))
        right = wrap_token(cardinal.single_fst + right_punct)
        # either there is no spaces before/after : or there are
        graph = left + pynini.accep(" ") + middle + pynini.accep(" ") + right
        graph |= (left + insert_space + middle + insert_space + right)
        self._multi_fst = graph.optimize()
