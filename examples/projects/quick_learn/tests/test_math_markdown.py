"""Markdown that markdown2 mishandles: escaped dollars, paragraphs opening with math, lists after text."""

import markdown2
from quicklearn.ui.math_markdown import _fix_latex, _fix_list_spacing, _patch_markdown2


def test_escaped_dollars_are_text_not_math():
    _patch_markdown2()
    text = r"A tip of \$5 with probability $0.5$, or \$20."
    html = markdown2.markdown(_fix_latex(text), extras=["latex"])
    assert html.count("<math") == 1
    assert "&#36;5 with probability" in html
    assert "&#36;20." in html


def test_paragraph_opening_with_math_keeps_its_markdown():
    _patch_markdown2()
    text = "$X$ is a variable. Write $Y$.\n\nThe **tower property**: for $a$,\n\n$$b = c.$$\n"
    html = markdown2.markdown(_fix_latex(text), extras=["latex"])
    assert "<strong>tower property</strong>" in html
    assert html.count("<p>") == 2


def test_list_right_after_text_is_a_list():
    text = "Two kinds of walk-ins:\n- a trim\n- a color\n  that takes longer\n- a cut\n\nSteps:\n1. one\n2. two\n"
    html = markdown2.markdown(_fix_list_spacing(text))
    assert html.count("<ul>") == 1 and html.count("<li>") == 5
    assert html.count("<ol>") == 1
