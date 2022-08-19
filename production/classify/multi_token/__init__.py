"""
Tagging with multi-token rules
==============================

In some contexts, semiotic classes are
connected with symbols that needs to be
read out loud. For example "5 x 3" is "five times three",
not "five eks three".
At verbalization, tagged tokens are processed separately,
but at classification a single multi-token FST is needed.

.. autosummary::
    :toctree: generated/
    :nosignatures:
    :template: class.rst

    MathFst
    RangeFst
    ScoreFst
    AttachedTokensFst

"""

from en_us_normalization.production.classify.multi_token.attached import AttachedTokensFst
from en_us_normalization.production.classify.multi_token.math import MathFst
from en_us_normalization.production.classify.multi_token.range import RangeFst
from en_us_normalization.production.classify.multi_token.score import ScoreFst
