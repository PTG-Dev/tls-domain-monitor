# =============================================================================
# scan_params.py — Centralized scan parameters (the brain of AdvancedScan)
#
# Holds and babysits all runtime options for AdvancedScan.
# Each flag is a button to a feature; some buttons are just placeholders for now.
# Think of it like a remote control with a few “coming soon” lights blinking.
# =============================================================================

import argparse
import logging
import shlex

logger = logging.getLogger(__name__)


class ScanParams:
    """
    Centralizes all parameters for an advanced scan session.

    Flags
    ─────
      keyword  (-k)  Filter: only show domains containing this string.
      limit    (-l)  Stop after N unique domains. 0 = unlimited.
      http     (-r)  Show HTTP status code for each domain (planned).
      regex    (-a)  Filter by regex pattern instead of plain keyword (planned).

    Usage
    ─────
        params = ScanParams(keyword="bird", limit=10)
        params = ScanParams()          # all defaults → unlimited, no filter
    """

    def __init__(
        self,
        keyword: str  = "",
        limit:   int  = 0,
        http:    bool = False,
        regex:   str  = "",
    ):
        self.keyword = keyword.lower().strip()
        self.limit   = max(0, limit)
        self.http    = http      # placeholder!! not yet implemented
        self.regex   = regex     # placeholder!!! not yet

    # ── Helpers ───────────────────────────────────────────────────────────────

    def has_keyword(self) -> bool:
        """Returns True if a keyword filter is active."""
        return bool(self.keyword)

    def has_limit(self) -> bool:
        """Returns True if a scan limit is set."""
        return self.limit > 0

    def matches(self, domain: str) -> bool:
        """
        Returns True if the domain passes the active filters.
        Currently checks keyword only; regex support is planned.
        """
        if self.has_keyword() and self.keyword not in domain.lower():
            return False
        return True

    def summary(self) -> str:
        """Returns a one-line description of active parameters."""
        parts = []
        if self.has_keyword():
            parts.append(f"keyword='{self.keyword}'")
        if self.has_limit():
            parts.append(f"limit={self.limit}")
        if self.http:
            parts.append("http=on")
        if self.regex:
            parts.append(f"regex='{self.regex}'")
        return "  ".join(parts) if parts else "no filters"

    def __repr__(self) -> str:
        return (
            f"ScanParams(keyword={self.keyword!r}, limit={self.limit}, "
            f"http={self.http}, regex={self.regex!r})"
        )

    # ── Factory ───────────────────────────────────────────────────────────────

    @classmethod
    def from_string(cls, line: str) -> "ScanParams | None":
        """
        Parses a 'scan' command string into a ScanParams instance.
        Syntax: scan [-k keyword] [-l limit] [-r] [-a regex]
        Returns None if parsing fails.

        Example:
            ScanParams.from_string("scan -k bird -l 10")
        """
        parser = argparse.ArgumentParser(prog="scan", add_help=False, exit_on_error=False)
        parser.add_argument("-k", dest="keyword", default="")
        parser.add_argument("-l", dest="limit",   type=int, default=0)
        parser.add_argument("-r", dest="http",    action="store_true")
        parser.add_argument("-a", dest="regex",   default="")

        try:
            tokens = shlex.split(line)
            if tokens and tokens[0].lower() == "scan":
                tokens = tokens[1:]
            args = parser.parse_args(tokens)
            return cls(
                keyword = args.keyword,
                limit   = args.limit,
                http    = args.http,
                regex   = args.regex,
            )
        except (argparse.ArgumentError, SystemExit, ValueError):
            return None
