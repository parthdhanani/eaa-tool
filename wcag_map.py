"""
Maps scorm-kit a11y rule ids to WCAG 2.2 success criteria, conformance level,
a plain-language fix, and a rough remediation time. The EU Accessibility Act
(EAA, in force since June 2025) points at EN 301 549, which adopts WCAG Level A
and AA; so every criterion below is EAA-relevant, flagged by level.

fix_minutes is a deliberately conservative per-occurrence estimate used only to
give teams a planning number, not a billing figure.
"""

# rule id -> (WCAG SC number, SC name, level A/AA, plain-language fix, minutes/occurrence)
WCAG = {
    "doc-no-lang":          ("3.1.1", "Language of Page",        "A",  "Set a lang attribute on the <html> element (e.g. lang=\"en\") so screen readers pronounce content correctly.", 2),
    "doc-no-title":         ("2.4.2", "Page Titled",             "A",  "Add a descriptive <title> to the page so learners and assistive tech know where they are.", 2),
    "doc-empty-title":      ("2.4.2", "Page Titled",             "A",  "Fill in the <title> with a meaningful description of the slide or page.", 2),
    "img-no-alt":           ("1.1.1", "Non-text Content",        "A",  "Add an alt attribute: describe the image, or use alt=\"\" if it is purely decorative.", 3),
    "img-alt-filename":     ("1.1.1", "Non-text Content",        "A",  "Replace the filename-looking alt text with a real description of what the image shows.", 3),
    "img-redundant-alt":    ("1.1.1", "Non-text Content",        "A",  "Remove alt text that just repeats the adjacent link or caption; use alt=\"\" so it is not read twice.", 3),
    "video-no-track":       ("1.2.2", "Captions (Prerecorded)",  "A",  "Add a <track kind=\"captions\"> with a caption file so deaf and hard-of-hearing learners can follow.", 30),
    "audio-no-transcript":  ("1.2.1", "Audio-only (Prerecorded)","A",  "Provide a text transcript near the audio so the content is available without sound.", 20),
    "heading-skip":         ("1.3.1", "Info and Relationships",  "A",  "Do not skip heading levels (h2 to h4); use sequential levels so the document outline is correct.", 5),
    "heading-no-h1":        ("2.4.6", "Headings and Labels",     "AA", "Give the page a single top-level <h1> so its structure is clear to assistive tech.", 5),
    "link-no-text":         ("2.4.4", "Link Purpose (In Context)","A", "Give the link visible text (or an aria-label) describing where it goes.", 3),
    "link-generic-text":    ("2.4.4", "Link Purpose (In Context)","A", "Replace generic text like \"click here\" with text that describes the destination.", 3),
    "button-no-name":       ("4.1.2", "Name, Role, Value",       "A",  "Give the button visible text or an aria-label so its purpose is announced.", 3),
    "form-input-no-label":  ("3.3.2", "Labels or Instructions",  "A",  "Associate a <label> with the form control (for/id), so its purpose is announced.", 4),
    "div-click-no-role":    ("2.1.1", "Keyboard",                "A",  "Make the clickable element keyboard-operable: use a <button>, or add role + tabindex + key handlers.", 8),
    "tabindex-positive":    ("2.4.3", "Focus Order",             "A",  "Remove positive tabindex values; let the natural DOM order drive focus, use tabindex=\"0\" at most.", 4),
    "iframe-no-title":      ("4.1.2", "Name, Role, Value",       "A",  "Add a title attribute to the <iframe> describing its embedded content.", 2),
    "table-no-headers":     ("1.3.1", "Info and Relationships",  "A",  "Mark header cells with <th> (and scope) so data tables are navigable by screen reader.", 6),
    "aria-bad-attr":        ("4.1.2", "Name, Role, Value",       "A",  "Fix the misspelled aria-* attribute; invalid ARIA is ignored and can mislead assistive tech.", 3),
    "aria-hidden-focusable":("4.1.2", "Name, Role, Value",       "A",  "Do not put focusable elements inside aria-hidden=\"true\"; remove the hidden flag or the element from the tab order.", 5),
}

# Fallback for any rule the engine adds before this map is updated.
_FALLBACK = ("4.1.1", "Parsing / Robust", "A", "Review against WCAG 2.2; this check is not yet mapped to a specific criterion.", 5)


def annotate(rule_id):
    sc, name, level, fix, minutes = WCAG.get(rule_id, _FALLBACK)
    return {
        "wcag": sc,
        "wcag_name": name,
        "level": level,
        "fix": fix,
        "fix_minutes": minutes,
        "mapped": rule_id in WCAG,
    }
