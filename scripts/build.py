#!/usr/bin/env python3
"""Static site generator for vertixlabs.netlify.app.

Renders one page per language from ``src/content/<lang>.json`` and the
templates in ``src/templates/`` into ``public/``. Standard library only.

Usage:
    python scripts/build.py           # write the pages to public/
    python scripts/build.py --check   # exit 1 if public/ is out of date
"""

from __future__ import annotations

import argparse
import json
import sys
from html import escape
from pathlib import Path
from string import Template
from typing import Any
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "src" / "content"
TEMPLATE_DIR = ROOT / "src" / "templates"
PUBLIC_DIR = ROOT / "public"

LANGUAGES = ("pt", "en")
DEFAULT_LANG = "pt"
HREFLANG = {"pt": "pt-BR", "en": "en"}
LANGUAGE_NAMES = {"pt": "Português", "en": "English"}

Content = dict[str, Any]


def load_json(path: Path) -> Content:
    return json.loads(path.read_text(encoding="utf-8"))


def load_template(name: str) -> Template:
    return Template((TEMPLATE_DIR / name).read_text(encoding="utf-8"))


def e(value: object) -> str:
    """Escape text for safe use in HTML content and attributes."""
    return escape(str(value), quote=True)


def indent_lines(lines: list[str], spaces: int) -> str:
    pad = " " * spaces
    return "\n".join(pad + line for line in lines)


def list_items(items: list[str], css_class: str = "") -> str:
    attr = f' class="{css_class}"' if css_class else ""
    return "".join(f"<li{attr}>{e(item)}</li>" for item in items)


# ---------------------------------------------------------------- partials


def hreflang_links(site_url: str) -> str:
    links = [
        f'<link rel="alternate" hreflang="{HREFLANG[lang]}" href="{site_url}/{lang}/">'
        for lang in LANGUAGES
    ]
    links.append(f'<link rel="alternate" hreflang="x-default" href="{site_url}/">')
    return indent_lines(links, 2)


def language_switch(current: str, content: Content) -> str:
    other = next(lang for lang in LANGUAGES if lang != current)
    labels = "".join(
        f'<span aria-current="true">{lang.upper()}</span>' if lang == current else f"<span>{lang.upper()}</span>"
        for lang in LANGUAGES
    )
    switch_to = e(content["meta"]["switchTo"])
    return (
        f'        <a class="lang" href="../{other}/" hreflang="{HREFLANG[other]}" '
        f'data-lang="{other}" title="{switch_to}" aria-label="{switch_to}">{labels}</a>'
    )


def nav_links(content: Content, spaces: int) -> str:
    return indent_lines([f'<a href="#{e(i["id"])}">{e(i["label"])}</a>' for i in content["nav"]["items"]], spaces)


def case_studies(section: Content) -> str:
    return "".join(
        '<article class="case">'
        '<div class="case-summary">'
        f'<p class="case-context">{e(item["context"])}</p>'
        f'<h3>{e(item["name"])}</h3>'
        f'<p class="case-outcome">{e(item["outcome"])}</p>'
        "</div>"
        '<div class="case-detail">'
        f'<h4>{e(section["howLabel"])}</h4>'
        f'<ul class="case-steps">{list_items(item["how"])}</ul>'
        f'<h4>{e(section["stackLabel"])}</h4>'
        f'<ul class="tags">{list_items(item["stack"])}</ul>'
        "</div>"
        "</article>"
        for item in section["items"]
    )


def services(section: Content) -> str:
    return "".join(
        f'<div class="service"><h3>{e(item["name"])}</h3><p>{e(item["text"])}</p></div>'
        for item in section["items"]
    )


def stack_groups(section: Content) -> str:
    return "".join(
        '<div class="stack-row">'
        f'<h3>{e(group["name"])}</h3>'
        f'<ul class="tags">{list_items(group["inUse"])}{list_items(group["upcoming"], "is-upcoming")}</ul>'
        "</div>"
        for group in section["groups"]
    )


def json_ld(site: Content) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": site["name"],
        "url": f'{site["url"]}/',
        "logo": f'{site["url"]}/assets/img/icon-512.png',
        "email": site["email"],
        "foundingDate": str(site["founded"]),
        "sameAs": [site["linkedin"], site["github"]],
    }
    # "</" must never appear inside a <script> element.
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


# ------------------------------------------------------------------- pages


def render_page(lang: str, content: Content, site: Content) -> str:
    meta, hero = content["meta"], content["hero"]
    site_url = site["url"].rstrip("/")
    mailto = f'mailto:{site["email"]}?subject={quote(content["contact"]["emailSubject"])}'

    values = {
        "lang": meta["lang"],
        "locale": meta["locale"],
        "title": e(meta["title"]),
        "description": e(meta["description"]),
        "canonical_url": f"{site_url}/{lang}/",
        "site_url": site_url,
        "site_name": e(site["name"]),
        "hreflang_links": hreflang_links(site_url),
        "json_ld": json_ld(site),
        "skip_label": e(content["nav"]["skip"]),
        "menu_label": e(content["nav"]["menu"]),
        "nav_links": nav_links(content, spaces=8),
        "nav_cta": e(content["nav"]["cta"]),
        "language_switch": language_switch(lang, content),
        "mailto": e(mailto),
        "email": e(site["email"]),
        "linkedin_url": e(site["linkedin"]),
        "github_url": e(site["github"]),
        "year": site["founded"],
        "hero_kicker": e(hero["kicker"]),
        "hero_title": e(hero["title"]),
        "hero_lead": e(hero["lead"]),
        "hero_primary_cta": e(hero["primaryCta"]),
        "hero_secondary_cta": e(hero["secondaryCta"]),
        "hero_proof": list_items(hero["proof"]),
        "cases_title": e(content["cases"]["title"]),
        "cases": case_studies(content["cases"]),
        "services_title": e(content["services"]["title"]),
        "services": services(content["services"]),
        "stack_title": e(content["stack"]["title"]),
        "stack_lead": e(content["stack"]["lead"]),
        "stack_legend_in_use": e(content["stack"]["legendInUse"]),
        "stack_legend_upcoming": e(content["stack"]["legendUpcoming"]),
        "stack_groups": stack_groups(content["stack"]),
        "about_title": e(content["about"]["title"]),
        "about_paragraphs": "".join(f"<p>{e(p)}</p>" for p in content["about"]["paragraphs"]),
        "about_facts": "".join(
            f'<div><dt>{e(f["label"])}</dt><dd>{e(f["value"])}</dd></div>' for f in content["about"]["facts"]
        ),
        "contact_title": e(content["contact"]["title"]),
        "contact_lead": e(content["contact"]["lead"]),
        "contact_button": e(content["contact"]["button"]),
        "footer_tagline": e(content["footer"]["tagline"]),
        "footer_nav_title": e(content["footer"]["navTitle"]),
        "footer_contact_title": e(content["footer"]["contactTitle"]),
        "footer_rights": e(content["footer"]["rights"]),
        "footer_links": nav_links(content, spaces=8),
    }
    return load_template("page.html").substitute(values)


def render_redirect(site: Content) -> str:
    site_url = site["url"].rstrip("/")
    return load_template("redirect.html").substitute(
        site_name=e(site["name"]),
        default_lang=DEFAULT_LANG,
        supported_langs=json.dumps(list(LANGUAGES)),
        hreflang_links=hreflang_links(site_url),
        language_links=" ".join(f'<a href="{lang}/">{LANGUAGE_NAMES[lang]}</a>' for lang in LANGUAGES),
    )


def render_sitemap(site: Content) -> str:
    site_url = site["url"].rstrip("/")
    alternates = "".join(
        f'<xhtml:link rel="alternate" hreflang="{HREFLANG[lang]}" href="{site_url}/{lang}/"/>' for lang in LANGUAGES
    )
    urls = "\n".join(f"  <url><loc>{site_url}/{lang}/</loc>{alternates}</url>" for lang in LANGUAGES)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        f"{urls}\n</urlset>\n"
    )


def render_robots(site: Content) -> str:
    return f'User-agent: *\nAllow: /\nSitemap: {site["url"].rstrip("/")}/sitemap.xml\n'


def build_outputs() -> dict[Path, str]:
    site = load_json(CONTENT_DIR / "site.json")
    outputs = {
        PUBLIC_DIR / lang / "index.html": render_page(lang, load_json(CONTENT_DIR / f"{lang}.json"), site)
        for lang in LANGUAGES
    }
    outputs[PUBLIC_DIR / "index.html"] = render_redirect(site)
    outputs[PUBLIC_DIR / "sitemap.xml"] = render_sitemap(site)
    outputs[PUBLIC_DIR / "robots.txt"] = render_robots(site)
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="fail if public/ differs from a fresh build")
    args = parser.parse_args()

    outputs = build_outputs()

    if args.check:
        stale = [p for p, html in outputs.items() if not p.exists() or p.read_text(encoding="utf-8") != html]
        for path in stale:
            print(f"out of date: {path.relative_to(ROOT)}", file=sys.stderr)
        if stale:
            print("Run `python scripts/build.py` and commit the result.", file=sys.stderr)
            return 1
        print("public/ is up to date.")
        return 0

    for path, html in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
