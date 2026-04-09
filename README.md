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
- **Keyword filter** (`-k` / `--keyword`) — only see domains that match a word
- **Exclude filter** (`-e` / `--exclude`) — skip domains containing a word (ex: cdn, mail)
- **Scan limit** (`-l` / `--limit`) — stop automatically after N domains
- **HTTP status check** (`-r` / `--http`) — see the live HTTP response code for each domain
- **Cert info** (`--cert`) — show issuer + expiry date for each certificate
- **Verbose cert** (`--cert -v`) — also show org, country, and SAN count
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
python -m pip install requests cryptography
```

| Package | Purpose |
|---|---|
| `requests` | HTTP requests to Google CT logs |
| `cryptography` | Decode DER/X.509 certificates |

> Use `python -m pip` rather than `pip` alone to make sure packages install into the right Python.

---

# Linux Installation Guide

## INSTALLING BASE TOOLS

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git -y
```

## VERIFICATION

```bash
python3 --version
pip3 --version
git --version
```

## CLONE THE PROJECT

```bash
cd ~
git clone https://github.com/PTG-Dev/tls-domain-monitor.git
cd tls-domain-monitor
```

## CREATE A VIRTUAL ENVIRONMENT

```bash
python3 -m venv venv
```

## ACTIVATE THE ENVIRONMENT

```bash
source venv/bin/activate
```

## INSTALL DEPENDENCIES

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### IF requirements.txt DOES NOT EXIST

```bash
pip install requests cryptography aiohttp
```

## RUN THE PROGRAM

```bash
ls
python main.py
```

### OR DEPENDING ON AVAILABLE FILE

```bash
python3 main.py
```



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
scan                                    # all domains, unlimited
scan -k bird                            # only domains containing "bird"
scan --keyword bird                     # same with long flag
scan -l 20                              # stop after 20 domains
scan -r                                 # show HTTP status per domain
scan -e cdn                             # skip domains containing "cdn"
scan --cert                             # show issuer + expiry date
scan --cert -v                          # show full cert info
scan -i                                 # resolve and show IP address
scan -o                                 # save results to outputlogs/
scan -k bank -e cdn -l 50 -r --cert -i -o  # combine flags
```

### Flags

| Flag | Long | Description |
|---|---|---|
| `-k word` | `--keyword` | Filter — only show domains containing this word |
| `-e word` | `--exclude` | Exclude — skip domains containing this word |
| `-l N` | `--limit` | Stop automatically after N unique domains |
| `-r` | `--http` | Fetch and show the HTTP status code for each domain |
| | `--cert` | Show cert info — issuer + expiry date |
| `-v` | `--verbose` | With `--cert`: also show org, country, SAN count |
| `-i` | `--ip` | Resolve and show the IP address of each domain |
| `-o` | `--output` | Save results to a timestamped file in `outputlogs/` |

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
