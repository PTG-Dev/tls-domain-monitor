# =============================================================================
# advanced_scan.py — Advanced Scan module
#
# Because “just scanning everything” is so last version
# This upgraded scanner comes with:
#   - keyword filtering (a.k.a. Ctrl+F on steroids),
#   - scan limits (so your CPU doesn’t file a complaint),
#   - HTTP status checks (because 404s have feelings too).
#
# All powered by ScanParams™ — because hardcoding is a crime.
# =============================================================================

import logging
import socket
from datetime import datetime
from pathlib  import Path

import requests

from ctlog       import CTLogClient, CertRecord
from scan_params import ScanParams

logger = logging.getLogger(__name__)

_M  = "\033[38;5;183m"   # pale mauve
_DI = "\033[2m"           # dim
_BL = "\033[38;5;75m"    # blue (IP)
_OR = "\033[38;5;214m"   # orange (HTTP)
_R  = "\033[0m"           # reset


# ─────────────────────────────────────────────────────────────────────────────
# AdvancedScan — configurable CT scanner, because chaos needs limits
# ─────────────────────────────────────────────────────────────────────────────

class AdvancedScan:
    """
    Filtered real-time scan of Certificate Transparency logs.

    Supports:
      - Keyword filtering  (-k / --keyword)  : only show domains containing a keyword
      - Scan limit         (-l / --limit)     : stop after N unique domains
      - HTTP status check  (-r / --http)      : show HTTP response code per domain
      - Exclude filter     (-e / --exclude)   : skip domains containing a word
      - Cert info          (--cert)           : show issuer + expiry date
      - Verbose cert       (--cert -v)        : also show org + country + SAN count
      - IP resolve         (-i / --ip)        : resolve and show the domain IP
      - Output to file     (-o / --output)    : save results to outputlogs/

    Usage:
        params = ScanParams(keyword="bank", limit=20)
        AdvancedScan(params).run()
    """

    _OUTPUT_DIR = Path(__file__).parent / "outputlogs"

    def __init__(self, params: ScanParams | None = None):
        self.params       = params or ScanParams()
        self.seen_domains: set[str] = set()
        self.domain_count: int      = 0
        self._stop:        bool     = False
        self._output_file           = self._open_output_file() if self.params.output else None

    # ── Output file thing ─────────────────────────────────────────────────────────

    def _open_output_file(self):
        """
        Creates and opens a timestamped output file in outputlogs/.
        Filename format: YYYY-MM-DD_HH-MM-SS.txt
        """
        self._OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".txt"
        filepath = self._OUTPUT_DIR / filename
        logger.info(f"Output file: {filepath}")
        return open(filepath, "w", encoding="utf-8")

    def _write_to_file(self, domain: str, extra: str, cert_info: str, ip: str) -> None:
        """Writes a matched domain and its metadata to the output file."""
        if self._output_file is None:
            return
        line = domain
        if ip:
            line += f"  ip={ip}"
        if extra:
            line += f"  {extra}"
        if cert_info:
            line += f"  {cert_info}"
        self._output_file.write(line + "\n")
        self._output_file.flush()

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

    def _print_domain(self, domain: str, source: str, extra: str = "", cert_info: str = "", ip: str = "") -> None:
        """Prints a single matched domain with optional extra info and cert info on a separate line."""
        ip_str    = f"  {_BL}ip={ip}{_R}" if ip else ""
        extra_str = f"  {_OR}{extra}{_R}" if extra else ""
        print(f"  {_M}[{_R}{self.domain_count:>6}{_M}]{_R}  {domain:<50}  ({source}){ip_str}{extra_str}")
        if cert_info:
            print(f"           {_DI}{cert_info}{_R}")
            print()

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

    # ── IP resolve.... ────────────────────────────────────────────────────────────

    def _resolve_ip(self, domain: str) -> str:
        """
        Resolves the domain to an IPv4 address.
        Returns the IP string, or an empty string on failure.
        """
        try:
            return socket.gethostbyname(domain)
        except Exception:
            return ""

    # ── HTTP check ────────────────────────────────────────────────────────────

    def _get_http_status(self, domain: str) -> str:
        """
        Fetches the HTTP status code for https://<domain>.
        Returns the code as a string, or 'NaN' on failure.
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

    # ── Cert info ─────────────────────────────────────────────────────────────

    def _format_cert_info(self, record: CertRecord) -> str:
        """
        Returns a short cert summary: issuer + expiry date.
        Shown when --cert is active.
        """
        parts = []
        if record.issuer:
            parts.append(f"issuer={record.issuer}")
        if record.not_after:
            parts.append(f"expires={record.not_after}")
        return "  ".join(parts)

    def _format_cert_verbose(self, record: CertRecord) -> str:
        """
        Returns a full cert summary: issuer + expiry + org + country + SAN count.
        Shown when --cert and -v / --verbose are both active.
        """
        parts = []
        if record.issuer:
            parts.append(f"issuer={record.issuer}")
        if record.not_after:
            parts.append(f"expires={record.not_after}")
        if record.org:
            parts.append(f"org={record.org}")
        if record.country:
            parts.append(f"country={record.country}")
        parts.append(f"SANs={len(record.domains)}")
        return "  ".join(parts)

    # ── Callback! ──────────────────────────────────────────────────────────────

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
            cert_info = ""
            ip = ""

            if self.params.ip:
                ip = self._resolve_ip(clean)

            if self.params.http:
                extra = f"HTTP {self._get_http_status(clean)}"

            if self.params.cert:
                cert_info = (
                    self._format_cert_verbose(record)
                    if self.params.verbose
                    else self._format_cert_info(record)
                )

            self._print_domain(clean, record.source, extra, cert_info, ip)

            if self.params.output:
                self._write_to_file(clean, extra, cert_info, ip)

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
            if self._output_file:
                self._output_file.close()
                logger.info("Output file closed.")

