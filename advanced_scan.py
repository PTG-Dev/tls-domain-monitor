# =============================================================================
# advanced_scan.py — Advanced Scan module
#
# Extends the CT log scanner with keyword filtering, scan limits,
# and HTTP status checks. Parameters are passed via ScanParams.
# =============================================================================

import logging

import requests

from ctlog       import CTLogClient, CertRecord
from scan_params import ScanParams

logger = logging.getLogger(__name__)

_M  = "\033[38;5;183m"   # pale mauve
_DI = "\033[2m"           # dim
_R  = "\033[0m"           # reset


# ─────────────────────────────────────────────────────────────────────────────
# AdvancedScan — Filtered, configurable CT log scanner
# ─────────────────────────────────────────────────────────────────────────────

class AdvancedScan:
    """
    Filtered real-time scan of Certificate Transparency logs.

    Supports:
      - Keyword filtering  (-k)  : only show domains containing a keyword
      - Scan limit         (-l)  : stop after N unique domains
      - HTTP status check  (-r)  : show HTTP response code per domain  [planned]
      - Regex filter       (-a)  : filter by regex pattern              [planned]

    Usage:
        params = ScanParams(keyword="bank", limit=20)
        AdvancedScan(params).run()
    """

    def __init__(self, params: ScanParams | None = None):
        self.params       = params or ScanParams()
        self.seen_domains: set[str] = set()
        self.domain_count: int      = 0
        self._stop:        bool     = False

    # ── Display helpers ───────────────────────────────────────────────────────

    def _print_header(self) -> None:
        """Prints the scan session header with active parameters."""
        print(
            f"\n"
            f"{_M}{'=' * 60}{_R}\n"
            f"  ADVANCED SCAN — Certificate Transparency Monitor\n"
            f"  {_DI}{self.params.summary()}{_R}\n"
            f"  Press CTRL+C to stop\n"
            f"{_M}{'=' * 60}{_R}\n"
        )

    def _print_domain(self, domain: str, source: str, extra: str = "") -> None:
        """Prints a single matched domain with optional extra info."""
        extra_str = f"  {_DI}{extra}{_R}" if extra else ""
        print(f"  {_M}[{_R}{self.domain_count:>6}{_M}]{_R}  {domain:<50}  ({source}){extra_str}")

    def _print_summary(self) -> None:
        """Prints the end-of-scan summary."""
        print(
            f"\n"
            f"{_M}{'=' * 60}{_R}\n"
            f"  Scan stopped.\n"
            f"  Domains matched : {self.domain_count}\n"
            f"  Filter          : {self.params.summary()}\n"
            f"{_M}{'=' * 60}{_R}\n"
        )

    # ── HTTP check (placeholder) ──────────────────────────────────────────────

    def _get_http_status(self, domain: str) -> str:
        """
        Fetches the HTTP status code for https://<domain>.
        Returns the code as a string, or '???' on failure.
        Placeholder — enabled only when params.http is True.
        """
        try:
            response = requests.get(
                f"https://{domain}",
                timeout    = 5,
                allow_redirects = True,
            )
            return str(response.status_code)
        except Exception:
            return "NaN"

    # ── Callback ──────────────────────────────────────────────────────────────

    def _handle_cert(self, record: CertRecord) -> None:
        """
        Callback passed to CTLogClient.
        Applies keyword filter, deduplicates, checks limit, optionally fetches HTTP status.
        """
        if self._stop:
            return

        for domain in record.domains:
            clean = domain.lstrip("*.")

            if not clean or clean in self.seen_domains:
                continue

            if not self.params.matches(clean):
                continue

            self.seen_domains.add(clean)
            self.domain_count += 1

            extra = ""
            if self.params.http:
                extra = f"HTTP {self._get_http_status(clean)}"

            self._print_domain(clean, record.source, extra)

            if self.params.has_limit() and self.domain_count >= self.params.limit:
                logger.info(f"Limit of {self.params.limit} domains reached.")
                self._stop = True
                return

    # ── Entry point ───────────────────────────────────────────────────────────

    def run(self) -> None:
        """Starts the scan with the configured ScanParams."""
        self._print_header()

        client = CTLogClient(on_new_cert=self._handle_cert)

        try:
            client.start()
        except KeyboardInterrupt:
            pass
        finally:
            self._print_summary()

