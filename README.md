# SCAN ME — Certificate Transparency Monitor

A real-time domain discovery tool built on Google's Certificate Transparency logs.  
Every time an SSL/TLS certificate is issued anywhere on the internet, this tool sees it — instantly.

---

## What is it for?

Certificate Transparency (CT) logs are public records of every certificate issued by trusted Certificate Authorities.  
This tool taps directly into that stream and lets you watch the internet get new domains in real time.

**Practical use cases:**

| Use case | Example |
|---|---|
| **Brand monitoring** | Watch for phishing domains targeting your company — `scan -k yourcompany` |
| **Threat hunting** | Spot suspicious domains before they go live — `scan -k paypal-secure` |
| **Research** | Observe certificate issuance patterns across any industry |
| **Domain squatting detection** | Track lookalike domains — `scan -k amaz0n` |
| **Personal curiosity** | Just watch the internet breathe in real time |

---

## Features

- **Live CT log feed** — polls Google's Argon2026 CT log continuously
- **Keyword filter** (`-k`) — only see domains that match a word
- **Scan limit** (`-l`) — stop automatically after N domains
- **HTTP status check** (`-r`) — see the live HTTP response code for each domain
- **Animated boot screen** with audio
- **Styled terminal UI** — clean ANSI colors, no external UI framework

---

## Requirements

- Python **3.10** or newer
  → https://www.python.org/downloads/
  → Check **"Add Python to PATH"** during install

---

## Installation

```bash
python -m pip install requests cryptography pygame
```

| Package | Purpose |
|---|---|
| `requests` | HTTP requests to Google CT logs |
| `cryptography` | Decode DER/X.509 certificates |
| `pygame` | Play the boot audio (`booting.mp3`) |

> Use `python -m pip` rather than `pip` alone to make sure packages install into the right Python.

---

## Usage

```bash
python main.py
```

### Menu

```
   C E R T   M O N I T O R

   [ 1 ]  Quick Scan       — live feed, no filter
   [ 2 ]  Help             — scan commands & flags
   [ 3 ]  Exit
```

### Scan commands

Type directly into the prompt:

```bash
scan                        # all domains, unlimited
scan -k bird                # only domains containing "bird"
scan -l 20                  # stop after 20 domains
scan -r                     # show HTTP status per domain
scan -k bank -l 50 -r       # combine all flags
```

### Flags

| Flag | Description |
|---|---|
| `-k keyword` | Filter — only show domains containing this word |
| `-l N` | Stop automatically after N unique domains |
| `-r` | Fetch and show the HTTP status code for each domain |

---

## Network access

The tool connects only to:

```
https://ct.googleapis.com
```

No third-party service. No API key. No account required.

---

## Project structure

```
main.py           — CLI entry point, menu loop
quick_scan.py     — Quick Scan (live feed, no filter)
advanced_scan.py  — Advanced Scan (filters, HTTP check)
scan_params.py    — Parameter model + command parser
ctlog.py          — Google CT log client
boot_screen.py    — Animated boot screen + audio
INSTALL.txt       — Plain-text install instructions
booting.mp3       — Boot audio
```

---

## Stdlib used (no install needed)

`base64` · `time` · `sys` · `json` · `argparse` · `shlex` · `logging`
