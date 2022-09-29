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
from learn_to_normalize.grammar_utils.shortcuts import delete_space, insert_space


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

        symbols = pynini.string_file(get_data_file_path("symbols.tsv")).optimize()
        # penalize adding more symbols, so if there is another option (for example punctuation) - go with that
        multiple_symbols = symbols + pynini.closure(pynutil.add_weight(insert_space, 10) + symbols)
        multiple_symbols = pynutil.insert("name: \"") + multiple_symbols + pynutil.insert("\"")
        cross_hyphen = pynini.cross("-", " } tokens { ")
        optional_cross_hyphen = pynutil.insert(" } tokens { ") + pynini.closure(pynutil.delete("-"), 0, 1)

        # boundary between abbreviation and word is not obvious, so expecting dash as a separator
        abbr_plus_word = abbreviation.fst + cross_hyphen + word.fst

        # boundary between abbreviation and number is obvious, so dash is optional
        abbr_plus_number = abbreviation.fst + optional_cross_hyphen + cardinal.fst

        # try to avoid situations when string with all consonants is classified as word
        word_or_abbr = pynutil.add_weight(word.fst, 1.1) | abbreviation.fst

        # boundary between word and number is also obvious
        word_plus_number = word_or_abbr + optional_cross_hyphen + cardinal.fst
        number_plus_word = cardinal.fst + optional_cross_hyphen + word_or_abbr

        # boundary between word and symbols is obvious
        word_plus_symbols = word_or_abbr + optional_cross_hyphen + multiple_symbols
        symbols_plus_word = multiple_symbols + optional_cross_hyphen + word_or_abbr

        # special case for insta ;)
        hashtag = pynini.cross("#", "name: \"hashtag\"") + insert_space + word_or_abbr

        graph = (
            abbr_plus_word
            | abbr_plus_number
            | pynutil.add_weight(word_plus_number, 1.1)
            | pynutil.add_weight(number_plus_word, 1.1)
            | pynutil.add_weight(word_plus_symbols, 20)  # regular word weight is 10, avoid shadowing word + punct
            | pynutil.add_weight(symbols_plus_word, 20)  # regular word weight is 10, avoid shadowing punct + word
            | hashtag  # hashtag is overshadowed by symbols_plus_word but has higher weight
        )
        self._multi_fst = graph.optimize()
