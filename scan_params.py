# =============================================================================
# scan_params.py — Centralized scan parameters (the brain of AdvancedScan)
#
# Holds and babysits all runtime options for AdvancedScan.
# Each flag is a button to a feature; more buttons added over time.
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
      keyword  (-k / --keyword)  Filter: only show domains containing this string.
      limit    (-l / --limit)    Stop after N unique domains. 0 = unlimited.
      http     (-r / --http)     Show HTTP status code for each domain.
      exclude  (-e / --exclude)  Skip domains containing this word (ex: cdn, mail).
      cert     (--cert)          Show basic cert info: issuer + expiry date.
      verbose  (-v / --verbose)  With --cert, also show org + country + SAN count.
      ip       (-i / --ip)       Resolve and show the IP address of each domain.
      output   (-o / --output)   Save results to a timestamped file in outputlogs/.

    Usage
    ─────
        params = ScanParams(keyword="bird", limit=10, exclude="cdn")
        params = ScanParams(cert=True, verbose=True)   # full cert details
        params = ScanParams(ip=True, output=True)      # resolve IPs + save to file
        params = ScanParams()                          # all defaults → unlimited, no filter
    """

    def __init__(
        self,
        keyword: str  = "",
        limit:   int  = 0,
        http:    bool = False,
        exclude: str  = "",
        cert:    bool = False,
        verbose: bool = False,
        ip:      bool = False,
        output:  bool = False,
    ):
        self.keyword = keyword.lower().strip()
        self.limit   = max(0, limit)
        self.http    = http
        self.exclude = exclude.lower().strip()
        self.cert    = cert
        self.verbose = verbose
        self.ip      = ip
        self.output  = output

    # ── Helpers ───────────────────────────────────────────────────────────────

    def has_keyword(self) -> bool:
        """Returns True if a keyword filter is active."""
        return bool(self.keyword)

    def has_limit(self) -> bool:
        """Returns True if a scan limit is set."""
        return self.limit > 0

    def has_exclude(self) -> bool:
        """Returns True if an exclusion filter is active."""
        return bool(self.exclude)

    def matches(self, domain: str) -> bool:
        """
        Returns True if the domain passes all active filters.
        Checks keyword inclusion and word exclusion.
        """
        domain_lower = domain.lower()

        if self.has_keyword() and self.keyword not in domain_lower:
            return False

        if self.has_exclude() and self.exclude in domain_lower:
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
        if self.has_exclude():
            parts.append(f"exclude='{self.exclude}'")
        if self.cert:
            parts.append("cert=on" + " (verbose)" if self.verbose else "cert=on")
        if self.ip:
            parts.append("ip=on")
        if self.output:
            parts.append("output=on")
        return "  ".join(parts) if parts else "no filters"

    def __repr__(self) -> str:
        return (
            f"ScanParams(keyword={self.keyword!r}, limit={self.limit}, "
            f"http={self.http}, exclude={self.exclude!r}, "
            f"cert={self.cert}, verbose={self.verbose}, "
            f"ip={self.ip}, output={self.output})"
        )

    # ── Factory ───────────────────────────────────────────────────────────────

    @classmethod
    def from_string(cls, line: str) -> "ScanParams | None":
        """
        Parses a 'scan' command string into a ScanParams instance.
        Syntax: scan [-k keyword] [-l limit] [-r] [-e exclude] [--cert] [-v] [-i] [-o]
        Returns None if parsing fails.

        Example:
            ScanParams.from_string("scan -k bird -l 10 -e cdn --cert -v -i -o")
        """
        parser = argparse.ArgumentParser(prog="scan", add_help=False, exit_on_error=False)
        parser.add_argument("-k", "--keyword", dest="keyword", default="")
        parser.add_argument("-l", "--limit",   dest="limit",   type=int, default=0)
        parser.add_argument("-r", "--http",    dest="http",    action="store_true")
        parser.add_argument("-e", "--exclude", dest="exclude", default="")
        parser.add_argument(       "--cert",   dest="cert",    action="store_true")
        parser.add_argument("-v", "--verbose", dest="verbose", action="store_true")
        parser.add_argument("-i", "--ip",      dest="ip",      action="store_true")
        parser.add_argument("-o", "--output",  dest="output",  action="store_true")

        try:
            tokens = shlex.split(line)
            if tokens and tokens[0].lower() == "scan":
                tokens = tokens[1:]
            args = parser.parse_args(tokens)
            return cls(
                keyword = args.keyword,
                limit   = args.limit,
                http    = args.http,
                exclude = args.exclude,
                cert    = args.cert,
                verbose = args.verbose,
                ip      = args.ip,
                output  = args.output,
            )
        except (argparse.ArgumentError, SystemExit, ValueError):
            return None
