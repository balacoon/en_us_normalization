"""
Copyright 2022 Balacoon
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

expand shortenings
"""

from en_us_normalization.production.english_utils import get_data_file_path
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.data_loader import load_mapping


class ShorteningFst(BaseFst):
    """
    Finite state transducer for discovering shortenings, such as Mrs. or prof.
    All shortenings and their mappings are stored in:

    - shortenings/case_agnostic.tsv - shortenings that should be expanded for any case
    Shortenings are expanded immediately, so no need to separate verbalization
    or dedicated semiotic class.

    Examples of input/output strings:

    - mrs. ->
      name: "misses"
    """

    def __init__(self):
        super().__init__(name="shortening")
        graph = load_mapping(
            get_data_file_path("shortenings", "case_agnostic.tsv"),
            key_case_agnostic=True,
            key_with_dot=True,
        )
        graph |= load_mapping(
            get_data_file_path("shortenings", "cased.tsv"), key_case_agnostic=False
        )
        graph = pynutil.insert('name: "') + graph + pynutil.insert('"')
        self.fst = graph.optimize()
