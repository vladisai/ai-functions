"""Fix LaTeX commands that markdown2's latex extra mishandles.

Four bugs in the markdown2 → latex2mathml pipeline:
1. _convert_double_match does .replace("\\n", "") which eats \\n in \\nabla, \\nu, \\newline etc.
2. \\bm{...} is not supported by latex2mathml.
3. The latex extra ignores \\$, so a dollar amount like \\$5 opens inline math.
4. A paragraph that opens with inline math turns into a raw HTML block, losing its markdown.

Fix: pre-process content before ui.markdown(extras=["latex"]) to work around all four.
"""

from __future__ import annotations

import re

from nicegui import ui

from quicklearn.ui.figures import client_page_folder, resolve_figures, trusted_html

# Commands where markdown2's \\n stripping breaks things.
# We replace them with a safe placeholder before markdown2 runs, then
# monkey-patch is not needed — latex2mathml handles these commands fine.
_NABLA_PLACEHOLDER = "QLNABLA"  # safe: no backslash-n
_NU_PLACEHOLDER = "QLNU"

# Pre-processing: run BEFORE passing to ui.markdown
def _fix_latex(text: str) -> str:
    """Replace problematic LaTeX commands with latex2mathml-compatible alternatives."""
    # \\bm{...} → \\boldsymbol{...}  (latex2mathml supports boldsymbol but not bm)
    text = text.replace("\\bm{", "\\boldsymbol{")
    # \\nabla → placeholder (markdown2 eats the \\n)
    text = text.replace("\\nabla", f"\\{_NABLA_PLACEHOLDER}")
    # \\nu → placeholder (same \\n issue)
    text = text.replace("\\nu", f"\\{_NU_PLACEHOLDER}")
    # \\$ → HTML entity, since markdown2 would open inline math at the escaped dollar
    text = text.replace("\\$", "&#36;")
    # A line opening with inline math becomes a line opening with <math>, which markdown2
    # takes for a raw HTML block running to the next line-ending </math>. A zero-width
    # space keeps the line a paragraph.
    text = re.sub(r"^(?=\$(?!\$))", "&#8203;", text, flags=re.MULTILINE)
    return text


# Post-processing: we need to intercept AFTER markdown2 but BEFORE sending to client.
# Since ui.markdown processes content internally, we monkey-patch markdown2's latex extra
# to restore our placeholders before latex2mathml converts them.
_original_convert_single = None
_original_convert_double = None
_patched = False


def _restore_placeholders(text: str) -> str:
    """Restore our placeholders back to real LaTeX commands."""
    text = text.replace(f"\\{_NABLA_PLACEHOLDER}", "\\nabla")
    text = text.replace(f"\\{_NU_PLACEHOLDER}", "\\nu")
    return text


def _patch_markdown2() -> None:
    """Monkey-patch markdown2's latex extra to fix the \\n stripping bug."""
    global _patched, _original_convert_single, _original_convert_double
    if _patched:
        return

    from markdown2 import Latex

    _original_convert_single = Latex._convert_single_match
    _original_convert_double = Latex._convert_double_match

    def fixed_convert_single(self, match):
        content = _restore_placeholders(match.group(1))
        return self.converter.convert(content)

    def fixed_convert_double(self, match):
        content = _restore_placeholders(match.group(1))
        # Fix: strip actual newlines (not the literal string \\n)
        content = content.replace("\n", "")
        return self.converter.convert(content, display="block")

    Latex._convert_single_match = fixed_convert_single
    Latex._convert_double_match = fixed_convert_double
    _patched = True


def _fix_unicode_bullets(text: str) -> str:
    """Convert Unicode bullet lines (•) to proper markdown list syntax."""
    return re.sub(r"^•\s*", "- ", text, flags=re.MULTILINE)


def _fix_list_spacing(text: str) -> str:
    """Put a blank line before a list that follows a line of text.

    markdown2 starts a list only after a blank line, and models often skip it,
    which runs the list into the paragraph above.
    """
    return re.sub(r"^((?!\s|[-*+] |\d+\. ).*\S.*)\n(?=[-*+] |\d+\. )", r"\1\n\n", text, flags=re.MULTILINE)


def math_markdown(text: str, classes: str = "", extras: tuple[str, ...] = ()) -> ui.markdown:
    """Render markdown with LaTeX, working around markdown2/latex2mathml bugs.

    extras: markdown2 extras on top of latex and tables.
    Figures and iframes resolve against the page's vault folder, see ui/figures.py.
    """
    _patch_markdown2()
    fixed = _fix_latex(text)
    fixed = _fix_unicode_bullets(fixed)
    fixed = _fix_list_spacing(fixed)
    fixed = resolve_figures(fixed, client_page_folder())
    return ui.markdown(fixed, extras=["latex", "tables", *extras], sanitize=not trusted_html(fixed)).classes(classes)


def update_math_markdown(el: ui.markdown, text: str) -> None:
    """Replace the text of a math_markdown element in place, with the same fixes and figure links."""
    fixed = _fix_unicode_bullets(_fix_latex(text))
    fixed = resolve_figures(fixed, client_page_folder(el.client))
    # The browser's sanitizer drops iframes, so only a vault iframe turns it off
    el._props["sanitize"] = not trusted_html(fixed)
    el.content = fixed
