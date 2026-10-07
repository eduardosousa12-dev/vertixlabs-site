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

Content = dict[str, Any]


def load_json(path: Path) -> Content:
    return json.loads(path.read_text(encoding="utf-8"))


def load_template(name: str) -> Template:
    return Template((TEMPLATE_DIR / name).read_text(encoding="utf-8"))


def e(value: object) -> str:
    """Escape text for safe use in HTML content and attributes."""
    return escape(str(value), quote=True)


def join(parts: list[str], indent: int = 0) -> str:
    pad = " " * indent
    return "\n".join(pad + part for part in parts)


# ---------------------------------------------------------------- partials


def hreflang_links(site_url: str) -> str:
    links = [
        f'<link rel="alternate" hreflang="{HREFLANG[lang]}" href="{site_url}/{lang}/">'
        for lang in LANGUAGES
    ]
    links.append(f'<link rel="alternate" hreflang="x-default" href="{site_url}/">')
    return join(links, indent=2)


def language_switch(current: str, content: Content) -> str:
    other = next(lang for lang in LANGUAGES if lang != current)
    labels = "<i>|</i>".join(
        f'<span class="on">{lang.upper()}</span>' if lang == current else f"<span>{lang.upper()}</span>"
        for lang in LANGUAGES
    )
    switch_to = e(content["meta"]["switchTo"])
    return (
        f'        <a class="lang" href="../{other}/" hreflang="{HREFLANG[other]}" lang="{HREFLANG[other]}" '
        f'data-lang="{other}" title="{switch_to}" aria-label="{switch_to}">{labels}</a>'
    )


def nav_links(content: Content, indent: int) -> str:
    return join([f'<a href="#{e(i["id"])}">{e(i["label"])}</a>' for i in content["nav"]["items"]], indent)


def chips(items: list[str], css_class: str = "") -> str:
    attr = f' class="{css_class}"' if css_class else ""
    return "".join(f"<li{attr}>{e(item)}</li>" for item in items)


def system_cards(section: Content) -> str:
    cards = []
    for item in section["items"]:
        solution = "".join(f"<li>{e(step)}</li>" for step in item["solution"])
        cards.append(
            '<article class="card reveal">'
            f'<div class="card-top"><span class="num">{e(item["number"])}</span><span class="tag">{e(item["tag"])}</span></div>'
            f'<h3>{e(item["name"])}</h3>'
            f'<p class="card-sub">{e(item["summary"])}</p>'
            f'<div class="pair"><span class="label">{e(section["problemLabel"])}</span><p>{e(item["problem"])}</p></div>'
            f'<div class="pair"><span class="label">{e(section["solutionLabel"])}</span><ul class="ticks">{solution}</ul></div>'
            f'<p class="status"><i aria-hidden="true"></i>{e(item["status"])}</p>'
            f'<ul class="mini-chips" aria-label="Stack">{chips(item["stack"])}</ul>'
            "</article>"
        )
    return "".join(cards)


def upcoming_cards(section: Content) -> str:
    return "".join(
        '<article class="soon-card reveal">'
        f'<span class="badge">{e(section["badge"])}</span>'
        f'<h4>{e(item["name"])}</h4>'
        f'<p>{e(item["description"])}</p>'
        f'<p class="soon-stack">{e(item["stack"])}</p>'
        "</article>"
        for item in section["items"]
    )


def stack_groups(section: Content) -> str:
    return "".join(
        '<div class="stack-group reveal">'
        f'<h3>{e(group["name"])}</h3>'
        f'<ul class="stack-chips">{chips(group["inUse"])}{chips(group["upcoming"], "soon")}</ul>'
        "</div>"
        for group in section["groups"]
    )


def process_steps(section: Content) -> str:
    return "".join(
        f'<li class="step reveal"><span class="step-n">{index:02d}</span>'
        f'<h3>{e(step["title"])}</h3><p>{e(step["text"])}</p></li>'
        for index, step in enumerate(section["steps"], start=1)
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
    meta = content["meta"]
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
        "nav_links": nav_links(content, indent=8),
        "nav_cta": e(content["nav"]["cta"]),
        "language_switch": language_switch(lang, content),
        "mailto": e(mailto),
        "email": e(site["email"]),
        "linkedin_url": e(site["linkedin"]),
        "github_url": e(site["github"]),
        "year": site["founded"],
        # Trusted markup: these two fields contain an <em> by design.
        "hero_title": content["hero"]["titleHtml"],
        "contact_title": content["contact"]["titleHtml"],
        "hero_eyebrow": e(content["hero"]["eyebrow"]),
        "hero_lead": e(content["hero"]["lead"]),
        "hero_primary_cta": e(content["hero"]["primaryCta"]),
        "hero_secondary_cta": e(content["hero"]["secondaryCta"]),
        "hero_focus_label": e(content["hero"]["focusLabel"]),
        "hero_focus": chips(content["hero"]["focus"]),
        "facts": "".join(
            f'<div class="fact"><strong>{e(f["value"])}</strong><span>{e(f["label"])}</span></div>'
            for f in content["facts"]
        ),
        "systems_eyebrow": e(content["systems"]["eyebrow"]),
        "systems_title": e(content["systems"]["title"]),
        "systems_lead": e(content["systems"]["lead"]),
        "systems": system_cards(content["systems"]),
        "upcoming_eyebrow": e(content["upcoming"]["eyebrow"]),
        "upcoming_title": e(content["upcoming"]["title"]),
        "upcoming": upcoming_cards(content["upcoming"]),
        "stack_eyebrow": e(content["stack"]["eyebrow"]),
        "stack_title": e(content["stack"]["title"]),
        "stack_legend_in_use": e(content["stack"]["legendInUse"]),
        "stack_legend_upcoming": e(content["stack"]["legendUpcoming"]),
        "stack_groups": stack_groups(content["stack"]),
        "process_eyebrow": e(content["process"]["eyebrow"]),
        "process_title": e(content["process"]["title"]),
        "process_steps": process_steps(content["process"]),
        "capabilities_eyebrow": e(content["capabilities"]["eyebrow"]),
        "capabilities_title": e(content["capabilities"]["title"]),
        "capabilities": chips(content["capabilities"]["items"]),
        "about_eyebrow": e(content["about"]["eyebrow"]),
        "about_title": e(content["about"]["title"]),
        "about_paragraphs": "".join(f"<p>{e(p)}</p>" for p in content["about"]["paragraphs"]),
        "about_facts": "".join(
            f'<div><dt>{e(f["label"])}</dt><dd>{e(f["value"])}</dd></div>' for f in content["about"]["facts"]
        ),
        "faq_eyebrow": e(content["faq"]["eyebrow"]),
        "faq_title": e(content["faq"]["title"]),
        "faq_items": "".join(
            f'<details><summary>{e(i["question"])}</summary><p>{e(i["answer"])}</p></details>'
            for i in content["faq"]["items"]
        ),
        "contact_lead": e(content["contact"]["lead"]),
        "contact_button": e(content["contact"]["button"]),
        "footer_tagline": e(content["footer"]["tagline"]),
        "footer_nav_title": e(content["footer"]["navTitle"]),
        "footer_contact_title": e(content["footer"]["contactTitle"]),
        "footer_rights": e(content["footer"]["rights"]),
        "footer_links": nav_links(content, indent=8),
    }
    return load_template("page.html").substitute(values)


def render_redirect(site: Content) -> str:
    site_url = site["url"].rstrip("/")
    names = {"pt": "Português", "en": "English"}
    return load_template("redirect.html").substitute(
        site_name=e(site["name"]),
        default_lang=DEFAULT_LANG,
        supported_langs=json.dumps(list(LANGUAGES)),
        hreflang_links=hreflang_links(site_url),
        language_links=" · ".join(f'<a href="{lang}/">{names[lang]}</a>' for lang in LANGUAGES),
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
