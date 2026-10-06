"""The check command finds each kind of mistake, and passes the shipped vault."""

import subprocess
from pathlib import Path

from quicklearn.check import check_vault, formula_error, main, math_spans

REPO = Path(__file__).parent.parent


def write(root: Path, files: dict[str, str]) -> Path:
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return root


GOOD_QUIZ = "# Prior\n\n1. Pick one\n   - [ ] no\n   - [x] yes\n\n# Learned\n"


def messages(vault: Path) -> list[str]:
    return [f"{p.path.name}:{p.line}:{'W' if p.warning else 'E'}:{p.message}" for p in check_vault(vault)]


def test_shipped_vault_passes():
    assert main([str(REPO / "content")]) == 0


def test_a_clean_vault_has_no_problems(tmp_path):
    vault = write(tmp_path, {
        "outline.md": "- [[ch/chapter|Chapter]]\n",
        "ch/chapter.md": "# Chapter\n\n![[sec]]\n",
        "ch/sec.md": "# Section\n\nText with $x^2$ and\n\n$$\n\\frac{a}{b}\n$$\n",
        "ch/sec.quiz.md": GOOD_QUIZ,
    })
    assert messages(vault) == []


def test_missing_targets(tmp_path):
    vault = write(tmp_path, {
        "outline.md": "- [[ch/chapter|Chapter]]\n- [[nowhere|Gone]]\n",
        "ch/chapter.md": "# Chapter\n\n![[missing]]\n",
    })
    found = messages(vault)
    assert "outline.md:2:E:links nowhere.md, which does not exist" in found
    assert any(m.startswith("chapter.md:3:E:embeds missing") for m in found)


def test_ambiguous_embed_and_unlinked_chapter(tmp_path):
    vault = write(tmp_path, {
        "outline.md": "",
        "ch/chapter.md": "![[sec]]\n",
        "ch/sec.md": "# Section\n",
        "ch/sec.quiz.md": GOOD_QUIZ,
        "other/sec.md": "# Another\n",
    })
    found = messages(vault)
    assert any(m.startswith("chapter.md:1:E:embeds sec, a name other/sec.md has too") for m in found)
    assert "chapter.md:1:W:the outline does not link this chapter" in found


def test_quiz_mistakes(tmp_path):
    quiz = (
        "# Prior\n\n"
        "1. None marked\n   - [ ] a\n   - [ ] b\n"
        "2. Two marked\n   - [x] a\n   - [x] b\n"
        "3. Mixed\n   - [T] a\n   - [x] b\n"
        "4. Fine\n   - [T] a\n   - [F] b\n"
        "5. Free-form, no options\n\n"
        "# Posterior\n"
    )
    vault = write(tmp_path, {
        "outline.md": "- [[ch/chapter|C]]\n",
        "ch/chapter.md": "![[sec]]\n\n![[bare]]\n",
        "ch/sec.md": "# S\n",
        "ch/sec.quiz.md": quiz,
        "ch/bare.md": "# Bare\n",
        "ch/orphan.quiz.md": GOOD_QUIZ,
    })
    found = messages(vault)
    assert "sec.quiz.md:3:E:has 0 options marked [x]; a pick-one question needs exactly one" in found
    assert "sec.quiz.md:6:E:has 2 options marked [x]; a pick-one question needs exactly one" in found
    assert any(m.startswith("sec.quiz.md:9:E:mixes [T]/[F]") for m in found)
    assert any(m.startswith("sec.quiz.md:1:E:unknown part '# Posterior'") for m in found)
    assert any(m.startswith("bare.md:1:W:no bare.quiz.md") for m in found)
    assert any(m.startswith("orphan.quiz.md:1:E:no section") for m in found)
    assert not any(":12:" in m or ":15:" in m for m in found)


def test_a_quiz_file_without_questions_is_a_warning(tmp_path):
    vault = write(tmp_path, {
        "outline.md": "- [[ch/chapter|C]]\n",
        "ch/chapter.md": "![[sec]]\n",
        "ch/sec.md": "# S\n",
        "ch/sec.quiz.md": "# Prior\n\n# Learned\n",
    })
    assert messages(vault) == ["sec.quiz.md:1:W:no questions, so only the tutor can adapt this section"]
    assert main([str(vault)]) == 0
    assert main([str(vault), "--strict"]) == 1


def test_quiz_tags(tmp_path):
    page_quiz = (
        "# Prior\n\n"
        "1. Tagged [[ch/chapter#Inline]] [[sec]]\n   - [x] a\n   - [ ] b\n"
        "2. Untagged\n   - [x] a\n   - [ ] b\n"
        "3. Wrong tag [[chapter#Nowhere]]\n   - [x] a\n   - [ ] b\n"
    )
    vault = write(tmp_path, {
        "outline.md": "- [[ch/chapter|C]]\n- [[lecture|L]]\n",
        "ch/chapter.md": "# C\n\n![[sec]]\n\n# Inline\n\nText.\n",
        "ch/chapter.quiz.md": page_quiz,
        "ch/sec.md": "# S\n",
        "ch/sec.quiz.md": "# Learned\n\n1. On another page [[other]]\n   - [x] a\n   - [ ] b\n",
        "lecture.md": "# Lecture\n\n## Part\n\nText.\n",
        "lecture.quiz.md": "# Prior\n\n1. Fine [[lecture#Part]]\n   - [x] a\n   - [ ] b\n",
    })
    # The page quiz is checked and is no orphan; a section's untagged questions are fine
    assert sorted(messages(vault)) == [
        "chapter.quiz.md:6:W:has no tag, so a miss rewrites no section and only goes to the notes",
        "chapter.quiz.md:9:E:the tag [[chapter#Nowhere]] names no section of chapter.md",
        "sec.quiz.md:3:E:the tag [[other]] names no section of chapter.md",
    ]


def test_duplicate_block_ids(tmp_path):
    vault = write(tmp_path, {
        "outline.md": "- [[ch/chapter|C]]\n",
        "ch/chapter.md": "![[sec]]\n\n![[sec]]\n",
        "ch/sec.md": "# S\n",
        "ch/sec.quiz.md": GOOD_QUIZ,
    })
    assert any("blocks have the id sec;" in m for m in messages(vault))


def test_math_spans_follow_markdown2():
    text = "Cost \\$5 and $a$, `$code$`\n\n```\n$x\n```\n\n$$\nb\n$$ and $open\n"
    spans, stray = math_spans(text)
    assert [latex for _, latex in spans] == ["a", "\nb\n"]
    assert [text[i:i + 5] for i in stray] == ["$open"]


def test_formula_errors():
    assert formula_error(r"\frac{a}{b}") is None
    assert formula_error(r"\mathbb{E}[X] = \sum_x x\,p(x)") is None
    assert formula_error(r"\bm{x}^\top \bm{y}") is None
    assert formula_error(r"\frac{a}{b") == "a { is not closed"
    assert formula_error(r"a}") == "a } closes no {"
    assert formula_error(r"\{x\}") is None
    assert formula_error(r"\arg \max_a Q") == "unknown command \\arg"
    assert formula_error(r"\left( x") is not None


def test_math_problems_have_lines(tmp_path):
    vault = write(tmp_path, {"outline.md": "", "page.md": "fine $x$\n\nbad $\\frac{a}{b$\n\nopen $x\n"})
    found = messages(vault)
    assert any(m.startswith("page.md:3:E:$\\frac{a}{b$: a { is not closed") for m in found)
    assert any(m.startswith("page.md:5:E:a $ that is not closed") for m in found)


def test_tracked_reader_files_fail(tmp_path):
    vault = write(tmp_path, {"outline.md": "", "personalization_data/default/reader.md": "secret\n"})
    subprocess.run(["git", "init", "-q", str(vault)], check=True)
    assert messages(vault) == []  # on disk but not tracked
    subprocess.run(["git", "-C", str(vault), "add", "-f", "personalization_data"], check=True)
    assert messages(vault) == [
        "reader.md:0:E:git tracks this reader file; remove it with git rm --cached"
    ]


def test_reader_folders_are_not_checked(tmp_path):
    vault = write(tmp_path, {
        "outline.md": "",
        "personalization_data/default/book/ch/v_1/sec.md": "bad $\\frac{a$\n",
    })
    assert messages(vault) == []


def test_quizzes_of_inline_sections_and_pages(tmp_path):
    vault = write(tmp_path, {
        "outline.md": "- [[ch/chapter|Chapter]]\n- [[lectures/lecture_1|Lecture 1]]\n",
        "ch/chapter.md": "# Chapter\n\n## Intro\n\nText.\n\n## Quizzed\n\nMore text.\n",
        "ch/quizzed.quiz.md": "# Prior\n\n1. Pick\n   - [ ] a\n   - [ ] b\n",
        "lectures/lecture_1.md": "# Lecture 1\n\n## Learning\n\nText.\n\n## Other\n\nText.\n",
        "lectures/lecture_1.learning.quiz.md": GOOD_QUIZ,
        "lectures/lecture_1.other.quiz.md": "# Learned\n\n1. Pick\n   - [ ] a\n   - [ ] b\n",
        "lectures/lecture_1.gone.quiz.md": GOOD_QUIZ,
    })
    found = messages(vault)
    # An inline section without a quiz file is fine; a bad quiz of one is an error
    assert not any(m.startswith("chapter.md") for m in found)
    assert any(m.startswith("quizzed.quiz.md:") and ":E:" in m for m in found)
    assert any(m.startswith("lecture_1.other.quiz.md:") and ":E:" in m for m in found)
    assert not any(m.startswith("lecture_1.learning.quiz.md") for m in found)
    assert any(m.startswith("lecture_1.gone.quiz.md:") and "no section of the page has this name" in m for m in found)
