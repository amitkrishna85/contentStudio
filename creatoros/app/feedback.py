from __future__ import annotations

from typing import Any


def compute_engagement_score(impressions: int, likes: int, comments: int, shares: int, clicks: int) -> float:
    """Compute a weighted engagement rate."""
    return round((likes + 2 * comments + 3 * shares + clicks) / max(impressions, 1), 4)


def simulate_engagement(brief: str, hook_style: str | None = None, length: int | None = None, angle: str | None = None, post_hour: int | None = None, hashtags: int = 0) -> dict[str, Any]:
    """Generate plausible engagement metrics with a hidden bias favoring strong hooks and shorter posts."""
    hook_bias = 1.25 if hook_style and "question" in str(hook_style).lower() else 1.0
    length_bias = 1.2 if (length or 0) < 600 else 0.75
    angle_bias = 1.15 if angle and "practical" in str(angle).lower() else 1.0
    hour_bias = 1.1 if post_hour in {9, 10, 11, 12, 18, 19} else 0.9
    hashtag_bias = 1.05 if hashtags >= 2 else 0.95
    base = 1200
    impressions = max(50, int(base * hook_bias * length_bias * angle_bias * hour_bias * hashtag_bias))
    likes = max(10, int(impressions * 0.08))
    comments = max(2, int(impressions * 0.02))
    shares = max(1, int(impressions * 0.01))
    clicks = max(0, int(impressions * 0.03))
    engagement = compute_engagement_score(impressions, likes, comments, shares, clicks)
    return {
        "impressions": impressions,
        "likes": likes,
        "comments": comments,
        "shares": shares,
        "clicks": clicks,
        "engagement_score": engagement,
    }
