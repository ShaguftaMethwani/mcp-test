"""
tests/test_pulse_builder.py

Phase 3 unit tests for agent/tools/pulse_builder.py
"""

from agent.tools.pulse_builder import build_pulse

def test_build_pulse_format_and_length():
    themes = [
        {"name": "Performance", "summary": "App crashes a lot when opening charts.", "count": 10},
        {"name": "Support", "summary": "Support takes too long to reply to emails.", "count": 5},
        {"name": "UI", "summary": "The new update has bad colors.", "count": 2},
    ]
    quotes = [
        "The app crashed three times today.",
        "Waiting 5 days for a reply.",
        "Can't read the text anymore."
    ]
    actions = [
        "Fix the chart memory leak.",
        "Hire more support staff.",
        "Revert to the old color scheme."
    ]
    
    pulse = build_pulse(themes, quotes, actions, "Aug 1 - Aug 30, 2026")
    
    assert "Weekly Play Store Review Pulse — Aug 1 - Aug 30, 2026" in pulse
    assert "TOP THEMES" in pulse
    assert "1. Performance: App crashes a lot when opening charts." in pulse
    assert "USER QUOTES" in pulse
    assert "• \"The app crashed three times today.\"" in pulse
    assert "ACTION IDEAS" in pulse
    assert "1. Fix the chart memory leak." in pulse
    
    word_count = len(pulse.split())
    assert word_count <= 250


def test_build_pulse_truncates_long_summaries():
    """If the inputs are extremely long, the builder must truncate to stay under 250 words."""
    long_summary = " ".join(["word"] * 300)
    themes = [
        {"name": "Performance", "summary": long_summary, "count": 10},
        {"name": "Support", "summary": long_summary, "count": 5},
        {"name": "UI", "summary": long_summary, "count": 2},
    ]
    quotes = ["Quote 1", "Quote 2", "Quote 3"]
    actions = ["Action 1", "Action 2", "Action 3"]
    
    pulse = build_pulse(themes, quotes, actions, "Aug 1 - Aug 30, 2026")
    
    word_count = len(pulse.split())
    # Given the strict max length, it should aggressively truncate the summaries
    assert word_count <= 250
    assert "..." in pulse
