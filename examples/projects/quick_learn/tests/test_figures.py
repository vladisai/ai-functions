"""Figures and embedded pages: the /vault route, links resolved against the page's vault folder,
the iframe that may render unsanitized, and the figures of the shipped lectures."""

import re
from pathlib import Path

import markdown2
import pytest
from conftest import REPO, write
from fastapi import FastAPI
from fastapi.testclient import TestClient
from quicklearn.agents.adapter import load_prompt
from quicklearn.reader.store import PERSONAL_DIR
from quicklearn.ui.content_renderer import TEXT_EXTRAS
from quicklearn.ui.figures import add_vault_route, page_folder, resolve_figures, trusted_html, vault_file
from quicklearn.ui.math_markdown import _fix_latex, _patch_markdown2
from quicklearn.vault.chapter import parse_page
from quicklearn.vault.links import render_links
from quicklearn.vault.outline import parse_outline

CONTENT = REPO / "content"
IFRAME = (
    '<iframe src="lecture_2/stepper.html?theme=light" title="Stepper" '
    'style="width:100%;height:700px;border:0"></iframe>'
)


@pytest.fixture
def vault(tmp_path: Path) -> Path:
    return write(tmp_path / "vault", {
        "lectures/lecture_2.md": "# Lecture 2\n",
        "lectures/lecture_2/fig.svg": "<svg/>",
        "lectures/lecture_2/stepper.html": "<html></html>",
        f"{PERSONAL_DIR}/tester/lectures/lecture_2/v_1/fig.svg": "<svg/>",
        ".obsidian/app.json": "{}",
    })


def test_vault_file_serves_figures_but_not_markdown_hidden_files_or_reader_folders(vault: Path):
    assert vault_file(vault, "lectures/lecture_2/fig.svg") == (vault / "lectures/lecture_2/fig.svg").resolve()
    assert vault_file(vault, "lectures/lecture_2/stepper.html")
    for path in ("lectures/lecture_2.md", f"{PERSONAL_DIR}/tester/lectures/lecture_2/v_1/fig.svg",
                 ".obsidian/app.json", "lectures/lecture_2/missing.svg", "../vault/lectures/lecture_2.md",
                 "lectures/../../outside.svg", "lectures"):
        assert vault_file(vault, path) is None, path


def test_vault_route(vault: Path, tmp_path: Path):
    (tmp_path / "outside.svg").write_text("<svg/>")
    app = FastAPI()
    add_vault_route(app, lambda: vault)
    client = TestClient(app)
    response = client.get("/vault/lectures/lecture_2/fig.svg")
    assert response.status_code == 200 and response.text == "<svg/>"
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert client.get("/vault/lectures/lecture_2/stepper.html", params={"theme": "light"}).status_code == 200
    for path in ("lectures/lecture_2.md", f"{PERSONAL_DIR}/tester/lectures/lecture_2/v_1/fig.svg",
                 "lectures/lecture_2/missing.svg", "lectures/%2E%2E/%2E%2E/outside.svg"):
        assert client.get(f"/vault/{path}").status_code == 404, path


def test_page_folder_is_the_folder_of_the_page_in_the_vault():
    assert page_folder("lectures/lecture_2") == "lectures"
    assert page_folder("book/probability/chapter") == "book/probability"
    assert page_folder("preface") == ""


def test_resolve_figures_against_the_page_folder():
    text = (
        "![A figure](lecture_2/fig.svg)\n\n*Figure: its caption.*\n\n"
        "![[lecture_2/other fig.png|Another]] and ![[lecture_2/third.svg]]\n\n"
        f"{IFRAME}\n\n"
        "![web](https://example.com/x.png) ![root](/vault/a.svg) [a link](lecture_2/fig.svg) ![up](../book/x.svg)\n"
    )
    resolved = resolve_figures(text, "lectures")
    assert "![A figure](/vault/lectures/lecture_2/fig.svg)" in resolved
    assert "*Figure: its caption.*" in resolved
    expected = "![Another](/vault/lectures/lecture_2/other%20fig.png) and ![](/vault/lectures/lecture_2/third.svg)"
    assert expected in resolved
    assert 'src="/vault/lectures/lecture_2/stepper.html?theme=light"' in resolved
    assert "![web](https://example.com/x.png) ![root](/vault/a.svg) [a link](lecture_2/fig.svg)" in resolved
    assert "![up](/vault/book/x.svg)" in resolved
    assert resolve_figures(text, None) == text
    # A rewrite in the reader's version folder keeps the links, and they resolve the same way
    assert resolve_figures(resolve_figures(text, "lectures"), "lectures") == resolved


def test_only_a_vault_iframe_turns_the_sanitizer_off():
    iframe = resolve_figures(IFRAME, "lectures")
    assert trusted_html(f"Some *text* with $a^2$.\n\n{iframe}\n\n<!-- note: a note -->\n\n![f](/vault/x.svg)\n")
    assert not trusted_html("No raw HTML at all.\n")
    assert not trusted_html(IFRAME)  # not resolved, so not a vault file
    assert not trusted_html('<iframe src="https://example.com/"></iframe>')
    assert not trusted_html(f"{iframe}\n\n<script>alert(1)</script>\n")
    assert not trusted_html(iframe.replace("<iframe ", '<iframe onload="alert(1)" '))
    assert not trusted_html(f"{iframe}\n\n[click](javascript:alert(1))\n")
    assert not trusted_html(f"{iframe}\n\n<img src=x onerror=alert(1)>\n")


def test_image_embeds_are_figures_not_sections(tmp_path: Path):
    vault = write(tmp_path / "vault", {"page.md": "# Page\n\n## Part\n\nText.\n\n![[page/fig.svg]]\n\n![[missing]]\n"})
    doc = parse_page(vault / "page.md", vault)
    assert doc.missing_embeds == [(9, "missing")]
    assert "![[page/fig.svg]]" in doc.sections["part"].body
    assert render_links("![[page/fig.svg]] and [[other|Other]]", lambda path: None) == "![[page/fig.svg]] and Other"


def test_rewrite_prompt_keeps_figures_verbatim():
    prompt = load_prompt("rewrite")
    assert "iframe" in prompt and "caption" in prompt and "character for character" in prompt


def _pages() -> list[tuple[str, Path]]:
    targets = [e.target for e in parse_outline(CONTENT / "outline.md") if e.kind == "chapter" and e.link]
    return [(t, CONTENT / f"{t}.md") for t in targets]


@pytest.mark.parametrize(("target", "page"), _pages(), ids=lambda v: str(v))
def test_every_figure_of_the_shipped_vault_is_served_and_renders(target: str, page: Path):
    _patch_markdown2()
    for section in parse_page(page, CONTENT).sections.values():
        fixed = resolve_figures(_fix_latex(section.body), page_folder(target))
        for url in re.findall(r"\]\((/vault/[^)\s]+)\)|src=\"(/vault/[^\"]+)\"", fixed):
            path = next(part for part in url if part).removeprefix("/vault/").split("?")[0]
            assert vault_file(CONTENT, path.replace("%20", " ")), f"{page.name}: {path}"
        html = markdown2.markdown(fixed, extras=["latex", "tables", *TEXT_EXTRAS])
        # No figure is left with a link the browser would resolve against the page's route
        assert not re.search(r'<(img|iframe)[^>]*src="(?!/vault/|https?:)', html), section.name
        # Every $...$ became MathML
        assert not re.search(r"\$[^$\s]", re.sub(r"<math.*?</math>", "", html, flags=re.S)), section.name
        if "<iframe" in section.body:
            assert trusted_html(fixed) and '<iframe src="/vault/lectures/lecture_2/kv_cache_stepper.html' in html


def test_the_lectures_have_their_figures():
    lecture_2 = (CONTENT / "lectures" / "lecture_2.md").read_text()
    assert lecture_2.count("![") == 15 and lecture_2.count("<iframe") == 1
    assert (CONTENT / "lectures" / "lecture_3.md").read_text().count("![") == 24
