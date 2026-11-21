#!/usr/bin/env python3
"""Fix all tool pages: remove hero-bg, plate wrapper, dock, and fix logo dimensions."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"

def fix_tool_page(html: str) -> str:
    """Apply all four structural fixes to a tool page."""

    # 1. Remove the hero-bg block (blobs, gridlines, grain)
    # Pattern: <div aria-hidden="true" class="hero-bg">...blobs...gridlines...grain...</div>
    html = re.sub(
        r'<div\s+aria-hidden="true"\s+class="hero-bg">[^<]*<i\s+class="blob\s+b1"></i>[^<]*<i\s+class="blob\s+b2"></i>[^<]*<div\s+class="gridlines"></div>[^<]*<div\s+class="grain"></div></div>',
        '',
        html
    )

    # 2. Remove the .plate wrapper around .tile.has-logo
    # Pattern: <div class="plate"><div ... class="tile has-logo">...</div></div>
    # Replace with just: <div ... class="tile has-logo">...</div>
    html = re.sub(
        r'<div\s+class="plate">(<div\s+aria-hidden="true"\s+class="tile\s+has-logo">[^<]*<img[^>]*></div>)</div>',
        r'\1',
        html
    )

    # 3. Remove the entire dock floating CTA bar
    # Pattern: <div ... class="dock" id="dock" ...>...</div>
    # The dock appears at the end of the body, before scripts
    html = re.sub(
        r'<div\s+aria-label="[^"]*"\s+class="dock"\s+id="dock"\s+role="region">.*?</div>\s*</div>\s*(?=</main>|<script|<footer)',
        '',
        html,
        flags=re.DOTALL
    )

    # 4. Fix logo image dimensions from 245x256 to 64x64
    # Only fix images with data-logo attribute (tool logos)
    def fix_logo_dims(match):
        img_tag = match.group(0)
        # Fix width="245" -> width="64"
        img_tag = re.sub(r'width="245"', 'width="64"', img_tag)
        # Fix height="256" -> height="64"
        img_tag = re.sub(r'height="256"', 'height="64"', img_tag)
        return img_tag

    html = re.sub(
        r'<img[^>]*data-logo[^>]*>',
        fix_logo_dims,
        html
    )

    return html


def main():
    fixed = 0
    skipped = 0
    errors = []

    for html_file in sorted(TOOLS_DIR.glob("*.html")):
        # Skip utility pages that don't have hero-bg
        if not html_file.name.startswith(('automation-budget-estimator', 'overlap-checker', 'workflow-explorer')):
            pass  # process these

        try:
            original = html_file.read_text(encoding="utf-8")

            # Check if this file has the patterns we need to fix
            has_hero_bg = 'hero-bg' in original
            has_plate = '<div class="plate">' in original
            has_dock = 'id="dock"' in original

            if not (has_hero_bg or has_plate or has_dock):
                skipped += 1
                continue

            fixed_html = fix_tool_page(original)

            # Verify fixes were applied
            changes = []
            if has_hero_bg and 'hero-bg' not in fixed_html:
                changes.append("hero-bg removed")
            elif has_hero_bg:
                errors.append(f"{html_file.name}: hero-bg NOT removed")

            if has_plate:
                # Count plate occurrences — should be reduced
                before_count = original.count('<div class="plate">')
                after_count = fixed_html.count('<div class="plate">')
                if after_count < before_count:
                    changes.append(f"plate wrapper removed ({before_count}->{after_count})")
                elif before_count > 0:
                    # Check if remaining plates are in different contexts
                    pass

            if has_dock and 'id="dock"' not in fixed_html:
                changes.append("dock removed")
            elif has_dock:
                errors.append(f"{html_file.name}: dock NOT removed")

            # Check logo dimensions
            if 'width="245"' in original or 'height="256"' in original:
                if 'width="245"' not in fixed_html and 'height="256"' not in fixed_html:
                    changes.append("logo dims fixed")
                else:
                    errors.append(f"{html_file.name}: logo dims NOT fixed")

            if changes:
                html_file.write_text(fixed_html, encoding="utf-8", newline="\n")
                fixed += 1
                if fixed % 25 == 0:
                    print(f"Fixed {fixed} files so far...")

        except Exception as e:
            errors.append(f"{html_file.name}: {e}")

    print(f"\nDone! Fixed {fixed} files, skipped {skipped} files.")
    if errors:
        print(f"\nErrors ({len(errors)}):")
        for err in errors[:20]:
            print(f"  - {err}")


if __name__ == "__main__":
    main()
