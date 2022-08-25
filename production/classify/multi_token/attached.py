"""
Copyright Balacoon 2022

tokenize and classify merged tokens
"""

import pynini
from en_us_normalization.production.english_utils import get_data_file_path
from en_us_normalization.production.classify.abbreviation import AbbreviationFst
from en_us_normalization.production.classify.cardinal import CardinalFst
from en_us_normalization.production.classify.punctuation_rules import get_punctuation_rules
from en_us_normalization.production.classify.word import WordFst
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.shortcuts import delete_space, insert_space, wrap_token


class AttachedTokensFst(BaseFst):
    """
    Attached tokens tries to deal with multi-token string which have
    `dash` as a separator or doesn't have any separator at all.
    For example "look33" or "AT&T-wireless". This FST takes advantage of the
    fact that boundary between some semiotic classes is fairly obvious.

    Examples of input / output:

    - look33 ->
      tokens { name: "look" } tokens { cardinal { count: "33" } }
    - AT&T-wireless ->
      tokens { name: "AT and T" } tokens { name: "wireless" }

    """

    def __init__(
        self,
        cardinal: CardinalFst = None,
        abbreviation: AbbreviationFst = None,
        word: WordFst = None,
        left_punct: pynini.FstLike = None,
        right_punct: pynini.FstLike = None,
    ):
        """
        constructor of transducer handling attached (merged) tokens

        Parameters
        ----------
        cardinal: CardinalFst
            a cardinal to reuse
        abbreviation: AbbreviationFst
            abbreviation to reuse
        word: WordFst
            word to reuse
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
        if abbreviation is None:
            abbreviation = AbbreviationFst()
        if word is None:
            word = WordFst()
        if left_punct is None and right_punct is None:
            left_punct, right_punct = get_punctuation_rules()

        symbols = pynini.string_file(get_data_file_path("symbols.tsv")).optimize()
        multiple_symbols = symbols + pynini.closure(insert_space + symbols)
        delete_hyphen = insert_space + pynutil.delete("-")
        optional_delete_hyphen = insert_space + pynini.closure(
            pynutil.delete("-"), 0, 1
        )
        # boundary between abbreviation and word is not obvious, so expecting dash as a separator
        abbr_plus_word = (
            wrap_token(left_punct + abbreviation.fst)
            + delete_hyphen
            + wrap_token(word.fst + right_punct)
        )
        # boundary between abbreviation and number is obvious, so dash is optional
        abbr_plus_number = (
            wrap_token(left_punct + abbreviation.fst)
            + optional_delete_hyphen
            + wrap_token(cardinal.fst + right_punct)
        )
        # boundary between word and number is also obvious
        word_plus_number = (
            wrap_token(left_punct + word.fst)
            + optional_delete_hyphen
            + wrap_token(cardinal.fst + right_punct)
        )
        # boundary between word and symbols is obvious
        word_plus_symbols = (
            wrap_token(left_punct + word.fst)
            + optional_delete_hyphen
            + wrap_token(pynutil.insert("name: \"") + multiple_symbols + pynutil.insert("\"") + right_punct)
        )
        # same as above, important to add for hashtags for example
        symbols_plus_word = (
            wrap_token(left_punct + pynutil.insert("name: \"") + multiple_symbols + pynutil.insert("\""))
            + optional_delete_hyphen
            + wrap_token(word.fst + right_punct)
        )
        graph = (
            abbr_plus_word
            | abbr_plus_number
            | pynutil.add_weight(word_plus_number, 1.1)
            | pynutil.add_weight(word_plus_symbols, 90.0)  # this duplicates word+punctuation, so requires high weight
            | pynutil.add_weight(symbols_plus_word, 90.0)  # also low prob not to shadow punctuation + word
        )
        self._multi_fst = graph.optimize()
