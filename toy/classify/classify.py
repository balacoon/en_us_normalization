"""
Copyright 2022 Balacoon

Toy classification grammar
"""

import pynini
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.shortcuts import delete_extra_space, delete_space, insert_space, LOWER, UPPER, TO_LOWER, DIGIT, ALNUM, NOT_SPACE, PUNCT, CHAR


class ClassifyFst(BaseFst):
    """
    Toy classification grammar that

    1. keeps sequences of mixed-case characters as words
    2. makes sequences of digits cardinals
    3. keeps up upper-case characters as abbreviations
    4. removes all the other characters

    toy grammar can be used for tests, can be adjusted for low-resource scenario
    or suit as a learning material.
    """

    def __init__(self):
        super().__init__(name="tokenize_and_classify")

        # 2 and more capitals in a row - abbreviation
        # optional dot after each character
        abbr = pynini.closure(UPPER + pynini.closure(pynutil.delete("."), 0, 1), 2)
        abbr = pynutil.insert("name: \"") + abbr + pynutil.insert("\"")

        # delete unknown symbols
        unknown_symbol = pynini.difference(NOT_SPACE, ALNUM).optimize()
        unknown_symbol = pynutil.add_weight(pynini.cross(unknown_symbol, ""), 10)
        # remove token alltogether if its just unknown symbols
        remove_token = pynutil.add_weight(pynini.closure(unknown_symbol, 1), 10)

        # digits tagged as cardinal
        digits = pynini.closure(DIGIT | unknown_symbol, 1)
        digits = pynutil.insert("cardinal { count: \"") + digits + pynutil.insert("\" }")

        # generic words with mix of cases
        words = pynini.closure((LOWER | TO_LOWER | unknown_symbol), 1)
        words = pynutil.insert("name: \"") + words + pynutil.insert("\"")

        # attached, when digit is merged with a word, or opposite
        words_or_digits = words | digits
        insert_tokens = pynutil.insert(" } tokens { ")
        attached = words_or_digits + pynini.closure(insert_tokens + words_or_digits, 1)

        token = (
            abbr
            | digits
            | pynutil.add_weight(words, 1.01)
            | pynutil.add_weight(attached, 1.02)
        )
        left_punct, right_punct = self.get_punctuation()
        token = pynutil.insert("tokens { ") + left_punct + token + right_punct + pynutil.insert(" }")
        token |= remove_token
        graph = token + pynini.closure(delete_extra_space + token)
        graph = delete_space + graph + delete_space
        self._single_fst = graph.optimize()

    @staticmethod
    def get_punctuation():
        """
        helper function that takes punctuation on the left or right of the token
        and tag it
        """
        punct = pynutil.add_weight(PUNCT, 1.1) | pynini.cross('"', '\\"')
        multiple_punct = delete_space + punct + delete_space
        multiple_punct = pynini.closure(multiple_punct, 1)

        left_punct = pynini.closure(punct, 1)
        # attach dangling punctuation on the left with lower probability
        left_punct |= pynutil.add_weight(multiple_punct, 1.2)
        left_punct = pynini.closure(
            pynutil.insert('left_punct: "') + left_punct + pynutil.insert('" '), 0, 1
        )

        right_punct = pynini.closure(punct, 1)
        # attach dangling punctuation on the right with low probability
        right_punct |= pynutil.add_weight(multiple_punct, 1.1)
        right_punct = pynini.closure(
            pynutil.insert(' right_punct: "') + right_punct + pynutil.insert('"'), 0, 1
        )

        return left_punct.optimize(), right_punct.optimize()

