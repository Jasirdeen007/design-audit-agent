"""Prompt helpers for Level 3 autonomous regression scans."""

from __future__ import annotations


def build_regression_context_prompt(
    page_name: str,
    page_url: str,
    pixel_diff_percentage: float,
    dynamic_regions_filtered: int,
) -> str:
    minimum = "fewer than 5 findings only if the visible diff is tiny" if pixel_diff_percentage < 2 else "at least 5 findings"
    return (
        "This is a Level 3 autonomous UI regression scan, not a manual before/after review.\n"
        f"Page name: {page_name}\n"
        f"Page URL: {page_url}\n"
        f"Precomputed pixel diff: {pixel_diff_percentage:.4f}%\n"
        f"Dynamic regions filtered before comparison: {dynamic_regions_filtered}\n"
        "Dynamic timestamps, counters, loading indicators, and session tokens have already been masked; "
        "do not flag masked dynamic content as regressions.\n"
        "Focus on real layout breaks, color shifts, spacing changes, unreadable text, typography changes, "
        "and WCAG contrast regressions across the full page including backgrounds and surfaces.\n"
        "Every finding must include confidence plus evidence in pixel_measurements: affected_region and "
        "page_pixel_diff_percentage. Use the supplied precomputed diff percentage exactly for page_pixel_diff_percentage.\n"
        f"Return {minimum} when the diff is visually significant, using the existing Level 2 JSON schema."
    )
