"""
Copyright 2022 Balacoon
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

Verbalizes electronic addresses
"""

import pynini
from en_us_normalization.production.verbalize.cardinal import CardinalFst
from en_us_normalization.production.verbalize.verbatim import VerbatimFst
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.shortcuts import (
    NOT_BAR,
    SIGMA,
    delete_space,
    insert_space,
)


class ElectronicFst(BaseFst):
    """
    Finite state transducer for verbalizing electronic addresses.
    Most of the work is done at classification. At verbalization -
    we just need to remove the tags and expand some fields using verbatim or cardinal
    transducers. Specifically:

    - port is expanded with cardinal
    - username is expanded with verbatim, generating pronunciation for sequences of letters
    - password is expanded with verbatim, spelling sequences of letters
    -

    Examples of input/output strings:

    - electronic|username:cdf1|domain:abc.EDU| -> cdf one at abc dot EDU

    """

    def __init__(self, verbatim: VerbatimFst = None, cardinal: CardinalFst = None):
        super().__init__(
            name="electronic",
        )

        if verbatim is None:
            verbatim = VerbatimFst()
        if cardinal is None:
            cardinal = CardinalFst()

        # expand protocol if its there
        # list of protocols is in data/electronic/protocols.tsv
        protocol = pynutil.add_weight(pynini.cross("MAILTO", "mail to"), 0.9)
        protocol |= pynini.closure(NOT_BAR, 1)
        protocol = (
            pynutil.delete("protocol:") + protocol + pynutil.delete("|") + insert_space
        )
        optional_protocol = pynini.closure(protocol, 0, 1)

        # expand username
        # TODO will try to pronounce letters in user name. Might be a bad idea,
        # some detection of abbreviation is needed
        username = verbatim.get_verbatim_verbalization(letter_case="to_lower")
        # remove whitespace in case the field is the first one
        username = username @ pynini.cdrewrite(delete_space, "[BOS]", "", SIGMA)
        username = pynutil.delete("username:") + username + pynutil.delete("|")

        # expand password
        # verbatim prepends with whitespace
        password = verbatim.get_verbatim_verbalization(letter_case="to_upper")
        password = (
            pynini.accep("password")
            + pynutil.delete(":")
            + password
            + pynutil.delete("|")
        )
        optional_password = pynini.closure(insert_space + password, 0, 1)

        # combine username and password
        username_pass = username + optional_password + pynutil.insert(" at ")
        optional_username_pass = pynini.closure(username_pass, 0, 1)

        # expand domain
        # TODO keeps the case of domain. If domain is all consonants lowercase
        # would try to generate pronunciation for it.
        domain = verbatim.get_verbatim_verbalization(letter_case="keep")
        # remove whitespace in front
        domain = domain @ pynini.cdrewrite(delete_space, "[BOS]", "", SIGMA)
        domain = pynutil.delete("domain:") + domain + pynutil.delete("|")

        # expand port if its there
        # verbatim already prepends whitespace in front
        port = cardinal.get_digit_pairs_fst()
        port = (
            pynini.accep("port") + pynini.cross(":", " ") + port + pynutil.delete("|")
        )
        optional_port = pynini.closure(insert_space + port, 0, 1)

        # expand path if its there
        # verbatim already prepends whitespace in front
        path = verbatim.get_verbatim_verbalization(letter_case="to_upper")
        path = pynutil.delete("path:") + path + pynutil.delete("|")
        optional_path = pynini.closure(path, 0, 1)

        # combine everything together
        graph = (
            optional_protocol
            + optional_username_pass
            + domain
            + optional_port
            + optional_path
        )
        self.fst = self.delete_tokens(graph).optimize()
