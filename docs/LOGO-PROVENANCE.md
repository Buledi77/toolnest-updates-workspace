# Logo provenance

Where replaced or unresolved tool logos come from, so brand accuracy can be re-audited.

Rule: a logo may only come from the vendor's own domain (its declared favicon, web-app manifest icon or
vendor-declared Organization `logo`). Never from image searches, screenshots, or a redrawn or approximated mark.
Files keep their existing paths (`/assets/logos/<id>.png`), so the catalog, `data/tools/*.json` and every page that
references them pick up the change without any HTML edits.

## Replaced on 2026-11-27 (generated single-letter placeholder tiles -> official marks)

The previous files were generated letter tiles (commits `0bede64`, `57585a3`, `3c38e37`).

| Tool | File | Official source | Processing |
|---|---|---|---|
| Cursor | `assets/logos/cursor.png` | https://cursor.com/marketing-static/favicon.svg (declared as `<link rel="icon" type="image/svg+xml">` on https://cursor.com/) | SVG rasterized to 128x128 PNG, transparent background |
| Ideogram | `assets/logos/ideogram.png` | https://ideogram.ai/favicon.svg?v=new-brand-20261020 (declared `<link rel="icon">` on https://ideogram.ai/). Same mark as the Organization `logo` in its JSON-LD: https://storage.googleapis.com/ideogram-static/website/images/fd1c0ced12b70513.png | SVG rasterized to 128x128 PNG |
| Bolt.new | `assets/logos/bolt.png` | https://bolt.new/static/pwa-icon-512.png (icon from the web-app manifest linked on https://bolt.new/) | 512x512 PNG resampled to 128x128 (Lanczos) |
| Lovable | `assets/logos/lovable.png` | https://lovable.dev/favicon.svg. The homepage answered 403 to automated requests, so the icon was taken from the conventional path on the same origin; it matches https://lovable.dev/apple-touch-icon.png | SVG rasterized to 128x128 PNG |
| HeyGen | `assets/logos/heygen.png` | https://www.heygen.com/favicon.ico (declared `<link rel="icon">` on https://www.heygen.com/), 48x48 frame | Native 48x48 frame, **not upscaled**. It is the largest official square asset found; the site publishes no apple-touch-icon or SVG |

SVG sources were rasterized in a browser canvas from an inert data-URL image (no script or external loading), after
checking they contain no `<script>`, `foreignObject`, event handlers or external references.

## Unresolved

| Tool | File | Status |
|---|---|---|
| GitHub Copilot | `assets/logos/github-copilot.png` | Still a generated placeholder (letter tile). No official standalone Copilot logo exists to use. |

GitHub's brand guidelines (https://brand.github.com/foundations/logo) state: "Beginning in 2025, GitHub Copilot no
longer has a standalone logo that heros the Copilot icon." Copilot is branded through GitHub product lockups, and
https://github.com/features/copilot publishes only the GitHub (Octocat) mark as its favicon and app icons, which is
another product's mark. To resolve it, either take the official lockup from the GitHub brand toolkit
(https://brand.github.com/GitHub_Logos.zip) or decide explicitly that the GitHub mark should represent Copilot.

## Known limitations (not changed here)

- Eleven logos are low resolution (48-64 px, shown up to 88 px): asana, chatgpt, grammarly, hemingway, hostinger,
  n8n, quillbot, replyio, surferseo, systeme, todoist. They are square and undistorted, only soft.
- The existing logo audit (`scripts/qa_logo_audit.py`) checks that a file exists and is a valid PNG/SVG. It cannot tell
  whether the artwork is the right brand, which is how the placeholders above passed it.
