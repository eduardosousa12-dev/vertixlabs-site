# Vertix Labs — website

Marketing site for **Vertix Labs**, a technology studio building AI agents, automation and custom software.

**Live:** https://vertixlabs.netlify.app · available in Portuguese (`/pt/`) and English (`/en/`)

## Overview

A fast, dependency-free static site. Copy lives in JSON (one file per language), a small Python
generator renders it into HTML, and Netlify serves the output.

- No framework or `node_modules`: HTML, CSS and vanilla JavaScript
- Bilingual with `hreflang`, canonical URLs and a sitemap; the root picks the visitor's language
- Accessible by default: semantic landmarks, skip link, keyboard-friendly menu, `prefers-reduced-motion`
- CI fails the build if the committed pages drift from the content or contain broken links

## Project structure

```
.
├── public/                 # deployed as-is by Netlify
│   ├── index.html          # language redirect
│   ├── pt/ · en/           # generated pages
│   └── assets/             # css, js and images
├── src/
│   ├── content/            # site.json + pt.json / en.json (all copy)
│   └── templates/          # page and redirect templates
├── scripts/
│   ├── build.py            # renders src/ into public/
│   └── check.py            # link and anchor checks
├── netlify.toml
└── .github/workflows/ci.yml
```

## Development

Requires Python 3.10+. There is nothing to install.

```bash
python scripts/build.py           # regenerate public/
python scripts/check.py           # verify links and anchors
python -m http.server -d public   # preview at http://localhost:8000
```

To change text, edit `src/content/pt.json` and `src/content/en.json`, run the build and commit
both the content and the regenerated pages. Contact details and the site URL live in
`src/content/site.json`.

## Deployment

Netlify deploys every push to `main`. Configuration is in `netlify.toml`: the `public/` folder is
published without a build step, plus security and cache headers.

## License

© 2026 Vertix Labs. All rights reserved.
