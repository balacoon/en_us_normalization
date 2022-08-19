"""
Tokenize and classify rules
===========================

Rules to split input string into tokens and classify them into semiotic classes.
Rules parse tokens into pre-defined fields for each semiotic class, put it
into pre-defined format, which is parsable into protobuf structure and can
be further passed for verbalization, i.e. conversion into spoken form.

Rules for classification of different semiotic classes:

.. autosummary::
    :toctree: generated/
    :nosignatures:
    :template: class.rst

    AbbreviationFst
    AddressFst
    CardinalFst
    DateFst
    DecimalFst
    ElectronicFst
    FractionFst
    MeasureFst
    MoneyFst
    OrdinalFst
    RomanFst
    ShorteningFst
    TelephoneFst
    TimeFst
    VerbatimFst

Acceptor for words that doesn't require normalization:

.. autosummary::
    :toctree: generated/
    :nosignatures:
    :template: class.rst

    WordFst

Sometimes tokens are not separated by whitespace, but
with special connectors. This requires introduction of
multi-token FSTs:

.. automodule:: en_us_normalization.production.classify.multi_token

Combining everything together into single FST:

.. autosummary::
    :toctree: generated/
    :nosignatures:
    :template: class.rst

    ClassifyFst

"""

from en_us_normalization.production.classify.abbreviation import AbbreviationFst
from en_us_normalization.production.classify.address import AddressFst
from en_us_normalization.production.classify.cardinal import CardinalFst
from en_us_normalization.production.classify.cardinal import ClassifyFst
from en_us_normalization.production.classify.date import DateFst
from en_us_normalization.production.classify.decimal import DecimalFst
from en_us_normalization.production.classify.electronic import ElectronicFst
from en_us_normalization.production.classify.fraction import FractionFst
from en_us_normalization.production.classify.measure import MeasureFst
from en_us_normalization.production.classify.money import MoneyFst
from en_us_normalization.production.classify.money import OrdinalFst
from en_us_normalization.production.classify.money import RomanFst
from en_us_normalization.production.classify.money import ShorteningFst
from en_us_normalization.production.classify.money import TelephoneFst
from en_us_normalization.production.classify.money import TimeFst
from en_us_normalization.production.classify.money import VerbatimFst
from en_us_normalization.production.classify.money import WordFst
