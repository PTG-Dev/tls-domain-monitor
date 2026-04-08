
# =============================================================================
# quick_scan.py — Quick Scan module (because patience is overrated)
#
# Launches a live CT log stalker instantly.
# Watches new TLS certificates pop up worldwide like popcorn!!!!
# Shows freshly minted domains in real time.
# Keeps track of unique domains and a running counter - because counting is fun, right?
# Warning: may cause mild obsession with newly born websites.
# =============================================================================


from ctlog import CTLogClient, CertRecord


# ─────────────────────────────────────────────────────────────────────────────
# QuickScan — Live certificate domain capture
# ─────────────────────────────────────────────────────────────────────────────

class QuickScan:
    """
    Launches a real-time scan of Certificate Transparency logs.

    - Polls Google CT log directly
    - Prints each new domain as it is discovered
    - Tracks unique domains with a set to avoid duplicates
    - Displays a running counter
    - Stops cleanly on CTRL+C
    """

    def __init__(self):
        # Set to store unique domains and avoid duplicate output
        self.seen_domains: set[str] = set()

        # Total number of unique domains discovered so far
        self.domain_count: int = 0

    # ── Display helpers ───────────────────────────────────────────────────────

    def _print_header(self) -> None:
        """Prints the scan session header."""
        _M = "\033[38;5;183m"
        _R = "\033[0m"
        print(
            f"\n"
            f"{_M}{'=' * 60}{_R}\n"
            f"  QUICK SCAN — Real-time Certificate Transparency Monitor\n"
            f"  Press CTRL+C to stop the scan\n"
            f"{_M}{'=' * 60}{_R}\n"
        )

    def _print_domain(self, domain: str, source: str) -> None:
        """Prints a single discovered domain in a clean, readable format."""
        _M = "\033[38;5;183m"
        _R = "\033[0m"
        print(f"  {_M}[{_R}{self.domain_count:>6}{_M}]{_R}  {domain:<50}  ({source})")

    # ── Callback ──────────────────────────────────────────────────────────────

    def _handle_cert(self, record: CertRecord) -> None:
        """
        Callback passed to CTLogClient.
        Called with every incoming CertRecord.
        Filters duplicates and prints new domains.
        """
        for domain in record.domains:

            # Skip wildcard prefixes (*.example.com → keep example.com clean)
            clean_domain = domain.lstrip("*.")

            # Skip empty or already-seen domains
            if not clean_domain or clean_domain in self.seen_domains:
                continue

            # Register the domain as seen
            self.seen_domains.add(clean_domain)
            self.domain_count += 1

            # Display the new domain
            self._print_domain(clean_domain, record.source)

    # ── Entry point ───────────────────────────────────────────────────────────

    def run(self) -> None:
        """
        Starts the quick scan session.
        Polls the CT log and streams domains until interrupted.
        """
        self._print_header()

        client = CTLogClient(on_new_cert=self._handle_cert)

        try:
            client.start()

        except KeyboardInterrupt:
            # CTRL+C — print a clean summary and exit gracefully
            print()
            print("=" * 60)
            print(f"  Scan stopped by user.")
            print(f"  Total unique domains captured: {self.domain_count}")
            print("=" * 60)
