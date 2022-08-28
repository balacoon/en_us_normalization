"""
Copyright 2022 Balacoon
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

tokenize and classify electronic addresses
"""

import pynini
from en_us_normalization.production.english_utils import get_data_file_path
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.data_loader import load_union
from learn_to_normalize.grammar_utils.shortcuts import ALPHA, CHAR, DIGIT, NOT_SPACE, TO_UPPER, NOT_PUNCT


class ElectronicFst(BaseFst):
    """
    Finite state transducer for classifying electronic: as URLs, email addresses, etc.
    Electronic semiotic class can contain multiple optional fields:

    - protocol - in front of urls there can be a protocol, such as "http://" or "mailto://"
    - username - before domain, there might be a used name, separated with "@".
      Most common case - username in email address, for ex "clement@balacoon.com".
      Within username there might be a password separated with a colon symbol, for ex. "user:123@gmail.com"
    - domain - smth that goes after protocol and username. can represent the whole URL, the only non-optional
      in electronic address. domain may have optional prefix, such as "www." and mandatory suffix that helps
      to identify domain. Suffixes are 2-3 letters long (such as "com" or "io"), can be repeated (for ex. "com.ua")
      and separated with a dot. Usually suffixes should be spelled in pronunciation, but in some cases,
      they should be pronounced as a regular word (for ex. "com").
    - port - optional digits after domain separated with colon symbol, for ex. "google.com:8080"
    - path - something that follow domain after a slash "/". Could be any symbols.

    Examples of strings that should be classified as electronic semiotic classes and their tagging:

    - cdf1@abc.edu ->
      electronic { username: "cdf1" domain: "abc.edu" }
    - http://cat:dog@www.google.com:8080/?231eds2@90iu ->
      electronic { protocol: "http" username: "cat" password: "dog" domain: "www.google.com"
      port: "8080" path: "/?231eds2@90iu" }

    """

    def __init__(self):
        super().__init__(name="electronic")
        protocol = self._get_protocol_fst()
        username = self._get_username_fst()
        domain = self._get_domain_fst()

        # options for domain:
        # 1. protocol + user + domain << should be more probable
        # 2. user + domain << should be less probable
        # 3. protocol + domain
        # 4. domain
        protocol_username_domain = (
            pynutil.add_weight(protocol + username + domain, 0.9)
            | (protocol + domain)
            | pynutil.add_weight(username + domain, 2.0)
            | domain
        )

        # port is optional after domain
        port = pynini.closure(DIGIT, 1)
        port = pynini.cross(":", ' port: "') + port + pynutil.insert('"')
        protocol_username_domain_port = protocol_username_domain + pynini.closure(
            port, 0, 1
        )

        # after domain there could be optional path
        path = pynini.closure(pynutil.add_weight(NOT_SPACE, 1.01)) +  pynini.closure(NOT_PUNCT)
        path = (
            pynutil.insert(' path: "')
            + pynini.accep("/")
            + path
            + pynutil.insert('"')
        )
        protocol_username_domain_port_path = (
            protocol_username_domain_port + pynini.closure(path, 0, 1)
        )
        final_graph = self.add_tokens(protocol_username_domain_port_path)
        self._single_fst = final_graph.optimize()

    @staticmethod
    def _get_protocol_fst() -> pynini.FstLike:
        """
        helper function that composes fst that accepts electronic protocols, such as "http://"
        """
        # read protocols from should be spelled out.
        # they are converted to upper case to signalize that
        with open(get_data_file_path("electronic", "protocols.tsv"), "r") as fp:
            protocols = fp.readlines()
        protocols = [
            pynini.accep(x.strip()) @ pynini.closure(TO_UPPER) for x in protocols
        ]
        protocols = pynini.union(*protocols)
        spoken_protocols = load_union(
            get_data_file_path("electronic", "spoken_protocols.tsv")
        )
        protocols |= spoken_protocols
        remove_optional_slashes = pynutil.delete(pynini.closure("/"))
        protocols = (
            pynutil.insert('protocol: "')
            + protocols
            + pynini.cross(":", '" ')
            + remove_optional_slashes
        )
        return protocols

    @staticmethod
    def _get_username_fst() -> pynini.FstLike:
        """
        helper function that composes fst to accept username in electronic addresses.
        optional field after protocol and before domain separated with "@"
        """
        alpha_or_digit = ALPHA | DIGIT
        accepted_symbols = load_union(get_data_file_path("symbols.tsv"), column=0)
        except_symbols = "/\\:"
        except_symbols = [pynini.accep(x) for x in except_symbols]
        except_symbols = pynini.union(*except_symbols)
        accepted_symbols = pynini.difference(accepted_symbols, except_symbols).optimize()
        # alpha characters, digits and limited set of symbols can appear in name
        username = alpha_or_digit + pynini.closure(alpha_or_digit | accepted_symbols)
        username = pynutil.insert('username: "') + username + pynutil.insert('"')
        # password is optional part of username
        password = (
            pynini.cross(":", ' password: "')
            + pynini.closure(CHAR, 1)
            + pynutil.insert('"')
        )
        password = pynini.closure(password, 0, 1)
        username = username + password + pynini.cross("@", " ")
        return username

    @staticmethod
    def _get_domain_fst() -> pynini.FstLike:
        """
        helper function that composes fst to accept domains.
        domain can be recognized by suffix, such as "edu" or "com.ua".
        """
        alpha_or_digit = ALPHA | DIGIT
        # domain name [a-z][0-9]\-
        domain = alpha_or_digit + pynini.closure(alpha_or_digit | pynini.accep("-"))
        # domain prefix, i.e. www.
        domain_prefix = pynini.cross("www.", "WWW.") | pynutil.add_weight(
            pynini.accep(""), 1.1
        )
        # domain suffix has at least two letters, i.e. "com.ua" or "eu"
        domain_suffix = pynutil.add_weight(
            pynini.closure(ALPHA, 2, 3) @ pynini.closure(TO_UPPER), 1.1
        )
        domain_suffix |= load_union(
            get_data_file_path("electronic", "spoken_domains.tsv")
        )
        domain_suffix = pynini.closure("." + domain_suffix, 1)
        domain = domain_prefix + domain + domain_suffix
        domain = pynutil.insert('domain: "') + domain + pynutil.insert('"')
        return domain
