#!/usr/bin/env python3
"""Build a conservative domain-only Xray geosite list from the configured filters."""
import re
import urllib.request
from pathlib import Path

SOURCES = [
    "https://pgl.yoyo.org/adservers/serverlist.php?hostformat=hosts&showintro=0&mimetype=plaintext",
    "https://adaway.org/hosts.txt",
    "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts",
    "https://easylist-downloads.adblockplus.org/antiadblockfilters.txt",
    "https://raw.githubusercontent.com/AdguardTeam/FiltersRegistry/master/filters/filter_1_Russian/filter.txt",
    "https://easylist-downloads.adblockplus.org/easylist.txt",
]
DOMAIN = re.compile(r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$", re.I)
HOSTS = re.compile(r"^(?:0\.0\.0\.0|127\.0\.0\.1|::1)\s+(.+)$")
ABP = re.compile(r"^\|\|([a-z0-9.-]+)\^", re.I)

def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Family-Salahi-Adblock-Geosite/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", "replace")

domains = set()
source_counts = {}
for url in SOURCES:
    text = fetch(url)
    found = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", "!", "[", "@@")):
            continue
        match = HOSTS.match(line)
        if match:
            candidates = match.group(1).split()
            found.update(d.lower().rstrip(".") for d in candidates if DOMAIN.fullmatch(d.rstrip(".")))
            continue
        match = ABP.match(line)
        if match:
            candidate = match.group(1).lower().rstrip(".")
            if DOMAIN.fullmatch(candidate):
                found.add(candidate)
    domains.update(found)
    source_counts[url] = len(found)

if not domains:
    raise SystemExit("No domains parsed; refusing to publish an empty geosite list.")

out = Path("data/category-ads-user")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(
    "# Generated from six upstream ad-filter sources. Domain-only rules.\n"
    + "".join(f"domain:{d}\n" for d in sorted(domains)),
    encoding="utf-8",
)
Path("build-report.txt").write_text(
    "Unique domains: " + str(len(domains)) + "\n"
    + "".join(f"{url}: {count}\n" for url, count in source_counts.items()),
    encoding="utf-8",
)
print(f"Generated {out} with {len(domains)} unique domains")
