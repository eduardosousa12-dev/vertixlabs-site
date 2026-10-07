#!/usr/bin/env python3
"""Sanity checks for the generated site in ``public/``.

Fails (exit 1) when a page points at a file or an in-page anchor that does
not exist, or when the language versions drift apart structurally.
"""

from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC_DIR = ROOT / "public"
PAGES = ["index.html", "pt/index.html", "en/index.html"]
SKIP_SCHEMES = ("http://", "https://", "mailto:", "tel:", "//", "data:")


class PageScanner(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.refs: list[str] = []
        self.sections: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"])
        for name in ("href", "src"):
            if values.get(name):
                self.refs.append(values[name])
        if tag == "section":
            self.sections.append(values.get("id") or values.get("class") or "")


def scan(page: Path) -> PageScanner:
    scanner = PageScanner()
    scanner.feed(page.read_text(encoding="utf-8"))
    return scanner


def broken_refs(page: Path, scanner: PageScanner) -> list[str]:
    problems = []
    for ref in scanner.refs:
        if ref.startswith(SKIP_SCHEMES):
            continue
        if ref.startswith("#"):
            if ref[1:] and ref[1:] not in scanner.ids:
                problems.append(f"missing anchor {ref}")
            continue
        target = (page.parent / ref.split("#")[0].split("?")[0]).resolve()
        if ref.endswith("/"):
            target = target / "index.html"
        if not target.is_file():
            problems.append(f"missing file {ref}")
    return problems


def main() -> int:
    errors: list[str] = []
    scanned: dict[str, PageScanner] = {}

    for name in PAGES:
        page = PUBLIC_DIR / name
        if not page.is_file():
            errors.append(f"{name}: page not found")
            continue
        scanned[name] = scan(page)
        errors += [f"{name}: {problem}" for problem in broken_refs(page, scanned[name])]

    pt, en = scanned.get("pt/index.html"), scanned.get("en/index.html")
    if pt and en and pt.sections != en.sections:
        errors.append("pt and en pages have different sections")

    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    print(f"Checked {len(scanned)} pages: no broken links.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
