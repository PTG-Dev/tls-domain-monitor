# =============================================================================
# ctlog.py — the internet's keyhole: legally surveils every new TLS certificate
#
# Polls the Google Argon CT log directly (because why not go straight to the source).
# Parses incoming certificates and extracts fresh domains hot off the wire.
# Interface: CertRecord + CTLogClient.
# =============================================================================

import base64
import logging
import time

import requests
from cryptography import x509
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Takes messy certs and makes them less painful.
# ─────────────────────────────────────────────────────────────────────────────

class CertRecord:
    """
    Stores extracted data from a single certificate transparency log entry.
    Provides clean string representations for display and debugging.
    """

    def __init__(
        self,
        domains:   list[str],
        source:    str = "unknown",
        issuer:    str = "",
        not_after: str = "",
        org:       str = "",
        country:   str = "",
    ):
        self.domains   = domains     # List of domains from the certificate
        self.source    = source      # Log source name (e.g. 'Google Argon2026')
        self.issuer    = issuer      # Certificate Authority name
        self.not_after = not_after   # Expiry date (YYYY-MM-DD)
        self.org       = org         # Organization from Subject (if present)
        self.country   = country     # Country from Subject (if present)

    def __repr__(self) -> str:
        return f"CertRecord(domains={self.domains!r}, source={self.source!r})"

    def __str__(self) -> str:
        return f"[{self.source}] {', '.join(self.domains)}"

    def __len__(self) -> int:
        # Returns the number of domains in this certificate record
        return len(self.domains)


# ─────────────────────────────────────────────────────────────────────────────
# Watches the internet get born… one certificate at a time.
# ─────────────────────────────────────────────────────────────────────────────

class CTLogClient:
    """
    Polls the Google Argon CT log directly and exposes a callback interface.
    No third-party service required — reads straight from the source.

    Usage:
        client = CTLogClient(on_new_cert=my_function)
        client.start()
    """

    CT_LOG_URL   = "https://ct.googleapis.com/logs/us1/argon2026h1/ct/v1/"
    LOG_NAME     = "Google Argon2026h1"
    POLL_INTERVAL = 5    # seconds between polls
    BATCH_SIZE    = 64   # certificates fetched per request

    def __init__(self, on_new_cert):
        self.on_new_cert  = on_new_cert
        self._last_index  = None

    # ── CT log REST helpers — 2 endpoints, 1 useful JSON key, infinite DER pain ────────────

    def _get_tree_size(self) -> int:
        """Returns the current number of entries in the CT log."""
        r = requests.get(self.CT_LOG_URL + "get-sth", timeout=10)
        r.raise_for_status()
        return r.json()["tree_size"]

    def _get_entries(self, start: int, end: int) -> list:
        """Fetches a batch of log entries [start, end] inclusive."""
        r = requests.get(
            self.CT_LOG_URL + "get-entries",
            params={"start": start, "end": end},
            timeout=10,
        )
        r.raise_for_status()
        return r.json().get("entries", [])

    # ── Certificate parser (i spend 3h here))────────────────────────────────────────────────────

    def _parse_entry(self, entry: dict) -> CertRecord | None:
        """
        Decodes a raw CT log entry and extracts domain names.

        CT log entries use a binary Merkle Tree Leaf structure:
          - bytes 0–1   : version + leaf_type
          - bytes 2–9   : timestamp (8 bytes)
          - bytes 10–11 : entry_type  (0 = x509, 1 = precert)
          - x509   → bytes 12–14 = cert length, then DER cert
          - precert → extra_data[0:3] = length of pre-certificate DER
        """
        try:
            leaf  = base64.b64decode(entry["leaf_input"])
            etype = int.from_bytes(leaf[10:12], "big")

            if etype == 0:  # x509_entry — cert is in leaf_input
                cert_len = int.from_bytes(leaf[12:15], "big")
                cert_der = leaf[15 : 15 + cert_len]
            else:           # precert_entry — full cert is in extra_data
                extra    = base64.b64decode(entry["extra_data"])
                cert_len = int.from_bytes(extra[0:3], "big")
                cert_der = extra[3 : 3 + cert_len]

            cert    = x509.load_der_x509_certificate(cert_der, default_backend())
            san     = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
            domains = san.value.get_values_for_type(x509.DNSName)

            # Get the cert infos
            try:
                cn_attrs = cert.issuer.get_attributes_for_oid(x509.NameOID.COMMON_NAME)
                issuer   = cn_attrs[0].value if cn_attrs else ""
            except Exception:
                issuer = ""

            # not_valid_after: the timestamp that causes a 3am incident nobody predicted
            try:
                not_after = cert.not_valid_after_utc.strftime("%Y-%m-%d")
            except AttributeError:
                not_after = cert.not_valid_after.strftime("%Y-%m-%d")  # type: ignore[attr-defined]
            except Exception:
                not_after = ""

            # Subject.O: legal name of whoever will forget to renew this cert
            try:
                org_attrs = cert.subject.get_attributes_for_oid(x509.NameOID.ORGANIZATION_NAME)
                org       = org_attrs[0].value if org_attrs else ""
            except Exception:
                org = ""

            # Subject.C: two letters that were accurate when the cert was issued — probably
            try:
                country_attrs = cert.subject.get_attributes_for_oid(x509.NameOID.COUNTRY_NAME)
                country       = country_attrs[0].value if country_attrs else ""
            except Exception:
                country = ""

            return CertRecord(
                domains   = list(domains),
                source    = self.LOG_NAME,
                issuer    = issuer,
                not_after = not_after,
                org       = org,
                country   = country,
            )

        except Exception:
            return None

    # ── start() — the function that never returns unless something has gone wrong ──

    def start(self) -> None:
        """
        Starts polling the CT log and streaming certificates until interrupted.
        """
        logger.info("Connected to CT log — listening for certificates...")

        self._last_index = self._get_tree_size() - 1

        while True:
                tree_size = self._get_tree_size()
                if tree_size <= self._last_index + 1:
                    time.sleep(self.POLL_INTERVAL)
                    continue  # no new entries yet

                start = self._last_index + 1
                end   = min(tree_size - 1, start + self.BATCH_SIZE - 1)

                for entry in self._get_entries(start, end):
                    record = self._parse_entry(entry)
                    if record and len(record) > 0:
                        self.on_new_cert(record)

                self._last_index = end
                time.sleep(self.POLL_INTERVAL)
