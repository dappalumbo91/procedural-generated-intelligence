"""Procedural Generated Intelligence.

Rules, seeds, and constraint settling unfold a claim. A theorem settles a
claim. A sourced record links information and does not settle one.
"""

from pgi.engine import unfold
from pgi.model import Request
from pgi.version import RULE_VERSION

__all__ = ["Request", "RULE_VERSION", "unfold"]
