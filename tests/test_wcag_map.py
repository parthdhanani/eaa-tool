"""Consistency checks for the rule -> WCAG criterion table."""
import re

import wcag_map

# WCAG 2.2 Level A/AA criteria referenced by the map, with their official names.
KNOWN = {
    "1.1.1": ("Non-text Content", "A"),
    "1.2.1": ("Audio-only (Prerecorded)", "A"),
    "1.2.2": ("Captions (Prerecorded)", "A"),
    "1.3.1": ("Info and Relationships", "A"),
    "2.1.1": ("Keyboard", "A"),
    "2.4.2": ("Page Titled", "A"),
    "2.4.3": ("Focus Order", "A"),
    "2.4.4": ("Link Purpose (In Context)", "A"),
    "2.4.6": ("Headings and Labels", "AA"),
    "3.1.1": ("Language of Page", "A"),
    "3.3.2": ("Labels or Instructions", "A"),
    "4.1.2": ("Name, Role, Value", "A"),
}


def test_every_entry_is_well_formed():
    for rule, entry in wcag_map.WCAG.items():
        assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", rule), rule
        assert len(entry) == 5, rule
        sc, name, level, fix, minutes = entry
        assert re.fullmatch(r"\d\.\d\.\d+", sc), (rule, sc)
        assert level in ("A", "AA"), (rule, level)
        assert fix.strip() and fix.rstrip().endswith("."), rule
        assert isinstance(minutes, int) and minutes > 0, rule


def test_criterion_names_and_levels_are_consistent():
    # Same SC number must always carry the same name and level.
    seen = {}
    for rule, (sc, name, level, _fix, _m) in wcag_map.WCAG.items():
        seen.setdefault(sc, (name, level))
        assert seen[sc] == (name, level), f"{rule}: {sc} mapped inconsistently"
        assert KNOWN.get(sc) == (name, level), f"{rule}: unexpected {sc} {name} {level}"


def test_annotate_mapped_and_fallback():
    a = wcag_map.annotate("img-no-alt")
    assert a["mapped"] is True and a["wcag"] == "1.1.1" and a["level"] == "A"
    assert set(a) == {"wcag", "wcag_name", "level", "fix", "fix_minutes", "mapped"}
    b = wcag_map.annotate("not-a-real-rule")
    assert b["mapped"] is False and b["wcag"] == wcag_map._FALLBACK[0]
    assert b["fix_minutes"] == wcag_map._FALLBACK[4]
