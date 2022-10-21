"""
Copyright Balacoon 2022
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

fsts to capture punctuation marks
"""

from typing import Tuple

import pynini
from pynini.lib import pynutil

from en_us_normalization.production.english_utils import UNK_SYMBOLS
from learn_to_normalize.grammar_utils.shortcuts import PUNCT, delete_space


def get_punctuation_rules() -> Tuple[pynini.FstLike, pynini.FstLike]:
    """
    Rules to capture and tag punctuation marks. Should be applied to any tokens.
    Punctuation marks are generally on the right of the token, but they can be on the left too
    (for example opening quotation symbol).
    Punctuation rules are not stand-alone graphs, but additions
    to final classification graphs.

    If punctuation mark is stand alone (for ex. dash), it is attached to the token on the left.
    This is ensured in rule for right punctuation.

    Returns
    -------
    left_punct: pynini.FstLike
        transducer for punctuation marks on the left of the token
    right_punct: pynini.FstLike
        transducer for punctuation marks on the right of the token
    """
    punct = pynutil.add_weight(PUNCT, 1.1) | pynini.cross('"', '\\"')
    multiple_punct = delete_space + punct + delete_space
    # delete unknown symbols if they are mixed with punctuation marks
    multiple_punct = (
        pynini.closure(UNK_SYMBOLS)
        + multiple_punct
        + pynini.closure(multiple_punct | UNK_SYMBOLS)
    )

    left_punct = pynutil.add_weight(pynini.closure(punct, 1), 1.2)
    # attach dangling punctuation on the left with lower probability
    left_punct |= pynutil.add_weight(multiple_punct, 1.1)
    left_punct = pynutil.insert('left_punct: "') + left_punct + pynutil.insert('" ')

    right_punct = pynini.closure(punct, 1)
    # attach dangling punctuation on the right with low probability
    right_punct |= pynutil.add_weight(multiple_punct, 1.1)
    right_punct = pynutil.insert(' right_punct: "') + right_punct + pynutil.insert('"')

    return left_punct.optimize(), right_punct.optimize()
