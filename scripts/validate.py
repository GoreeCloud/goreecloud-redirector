#!/usr/bin/env python3
import json
import re
import sys
import zipfile
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
errors = []

def fail(message):
    errors.append(message)

def read(path):
    p = ROOT / path
    if not p.is_file():
        fail(f"missing required file: {path}")
        return ""
    return p.read_text(encoding="utf-8")

try:
    manifest = json.loads(read("manifest.json"))
except Exception as exc:
    fail(f"manifest.json is invalid JSON: {exc}")
    manifest = {}

try:
    rules = json.loads(read("rules.json"))
except Exception as exc:
    fail(f"rules.json is invalid JSON: {exc}")
    rules = []

if manifest.get("manifest_version") != 3:
    fail("manifest_version must be 3")
if manifest.get("version") != "0.2.0":
    fail("manifest version must be 0.2.0")
gecko = manifest.get("browser_specific_settings", {}).get("gecko", {})
if gecko.get("id") != "redirector@goreecloud.com":
    fail("Firefox extension ID changed unexpectedly")
if gecko.get("data_collection_permissions", {}).get("required") != ["none"]:
    fail("manifest must declare no data collection")
if gecko.get("strict_min_version") != "140.0":
    fail("strict_min_version must be 140.0")
if manifest.get("host_permissions") != ["https://keep.google.com/*"]:
    fail("built-in host permission must remain limited to keep.google.com")
if set(manifest.get("permissions", [])) != {"declarativeNetRequest", "storage"}:
    fail("unexpected required API permissions")
if set(manifest.get("optional_host_permissions", [])) != {"http://*/*", "https://*/*"}:
    fail("optional host permissions changed unexpectedly")

if len(rules) != 1:
    fail("rules.json must contain exactly one built-in rule")
else:
    rule = rules[0]
    expected_regex = r"^https://keep\.google\.com(?:[/?].*)?$"
    if rule.get("condition", {}).get("regexFilter") != expected_regex:
        fail("built-in rule regex changed unexpectedly")
    if rule.get("action", {}).get("redirect", {}).get("url") != "https://memos.goreecloud.com/":
        fail("built-in destination changed unexpectedly")
    if rule.get("condition", {}).get("resourceTypes") != ["main_frame"]:
        fail("built-in rule must affect main_frame only")

regex = re.compile(r"^https://keep\.google\.com(?:[/?].*)?$")
for url in (
    "https://keep.google.com",
    "https://keep.google.com/",
    "https://keep.google.com/u/0/",
    "https://keep.google.com/?foo=bar",
):
    if not regex.match(url):
        fail(f"built-in regex should match {url}")
for url in (
    "http://keep.google.com/",
    "https://keep.google.com.evil.example/",
    "https://notkeep.google.com/",
    "https://google.com/keep.google.com/",
):
    if regex.match(url):
        fail(f"built-in regex must not match {url}")

for icon in (16, 32, 48, 64, 96, 128):
    path = ROOT / f"icons/redirector-{icon}.png"
    if not path.is_file() or path.stat().st_size < 50:
        fail(f"missing or empty raster icon: {path.relative_to(ROOT)}")
svg = read("icons/redirector.svg")
if "<svg" not in svg or "viewBox=\"0 0 128 128\"" not in svg:
    fail("redirector.svg must be a plain scalable SVG with a viewBox")

class ResourceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for key in ("src", "href"):
            if key in attrs:
                self.urls.append(attrs[key])

for html in ("popup.html", "options.html"):
    content = read(html)
    if 'data-glaze-ui="1.0.0"' not in content:
        fail(f"{html} must declare Glaze UI 1.0.0")
    parser = ResourceParser(); parser.feed(content)
    for url in parser.urls:
        if re.match(r"^(?:https?:)?//", url):
            fail(f"remote UI resource is not allowed in {html}: {url}")

for source in ("popup.js", "options.js", "styles.css"):
    content = read(source)
    lowered = content.lower()
    for needle in ("google-analytics", "googletagmanager", "segment.com", "mixpanel", "sentry.io"):
        if needle in lowered:
            fail(f"analytics/telemetry reference found in {source}: {needle}")

options_js = read("options.js")
for required in ("browser.permissions.request", "browser.declarativeNetRequest.updateDynamicRules", "duplicate", "redirect loop"):
    if required not in options_js:
        fail(f"options.js missing expected safety behavior: {required}")

styles = read("styles.css")
for required in ("--target: 44px", "prefers-reduced-motion", "prefers-contrast", "forced-colors", "backdrop-filter"):
    if required not in styles:
        fail(f"styles.css missing Glaze/accessibility contract token: {required}")

for path in ROOT.rglob("*"):
    if path.is_file() and path.name in {".env", "amo-credentials.json"}:
        fail(f"credential file must not exist in source: {path.relative_to(ROOT)}")

if errors:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    sys.exit(1)
print("GoreeCloud Redirector validation passed.")
