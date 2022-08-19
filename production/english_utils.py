"""
Copyright 2022 Balacoon

Helpers specific to english grammars
"""

import os

import pynini
from pynini.examples import plurals
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.shortcuts import SIGMA


def get_data_dir() -> str:
    """
    getter for absolute path to data dir
    of english grammars

    Returns
    -------
    data_dir: str
        path to data dir
    """
    grammars_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(grammars_dir, "data")
    return data_dir


def get_data_file_path(*args) -> str:
    """
    getter for absolute path to data file

    Parameters
    ----------
    args:
        path elements, i.e. directory and file name

    Returns
    -------
    path: str
        absolute path to the file
    """
    return os.path.join(get_data_dir(), *args)


suppletive_path = get_data_file_path("suppletive.tsv")
suppletive = pynini.string_file(suppletive_path)
_c = pynini.union(
    "b",
    "c",
    "d",
    "f",
    "g",
    "h",
    "j",
    "k",
    "l",
    "m",
    "n",
    "p",
    "q",
    "r",
    "s",
    "t",
    "v",
    "w",
    "x",
    "y",
    "z",
)
_ies = SIGMA + _c + pynini.cross("y", "ies")
_es = SIGMA + pynini.union("s", "sh", "ch", "x", "z") + pynutil.insert("es")
_s = SIGMA + pynutil.insert("s")

graph_plural = plurals._priority_union(
    suppletive,
    plurals._priority_union(_ies, plurals._priority_union(_es, _s, SIGMA), SIGMA),
    SIGMA,
).optimize()

SINGULAR_TO_PLURAL = graph_plural
PLURAL_TO_SINGULAR = pynini.invert(graph_plural)
