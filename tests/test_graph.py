from creatoros.app.graph import compute_diff_ratio, route_after_editor


def test_route_after_editor_handles_revision_loop():
    assert route_after_editor({"overall": 6}, 0) == "writer"
    assert route_after_editor({"overall": 8}, 0) == "visual"
    assert route_after_editor({"overall": 5}, 2) == "visual"


def test_compute_diff_ratio_changes_with_edits():
    original = "A direct hook with a simple CTA."
    revised = "A stronger hook with a clearer CTA and better framing."
    ratio = compute_diff_ratio(original, revised)
    assert 0 < ratio < 1
    assert compute_diff_ratio(original, original) == 0.0
