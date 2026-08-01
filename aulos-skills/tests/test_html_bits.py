"""Shared html_bits coerce path (META-001 §3.5)."""

from aulos_skills.html_bits import html_li, html_p, point_text, point_texts


def test_point_text_coerces_dict_and_str():
    assert point_text("listen for the bass") == "listen for the bass"
    assert point_text({"cue": "bass line"}) == "cue: bass line"
    assert point_text(None) == ""
    assert point_text({"a": "1", "b": "2"}) == "a: 1; b: 2"


def test_point_texts_limit():
    assert point_texts([{"x": 1}, "two", ""], limit=2) == ["x: 1", "two"]


def test_html_li_escapes_and_skips_empty():
    assert html_li(["a", "", {"k": "v"}]) == "<li>a</li><li>k: v</li>"
    assert html_li(["<script>"]) == "<li>&lt;script&gt;</li>"


def test_html_p_optional_scrub():
    assert html_p("hi") == "<p>hi</p>"
    assert html_p("  ") == ""
    assert html_p("leak", scrub=lambda t: t.replace("leak", "clean")) == "<p>clean</p>"
