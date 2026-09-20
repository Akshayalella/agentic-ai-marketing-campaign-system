from app.agents.content_review_agent import ContentReviewBrandComplianceAgent


def review(guidelines, body, tone="Professional"):
    return ContentReviewBrandComplianceAgent().run({
        "brief": {"brand_guidelines": guidelines, "brand_tone": tone},
        "content": [{
            "platform": "LinkedIn",
            "content_type": "post",
            "topic": "test",
            "body": body,
            "scheduled_date": "2026-09-20",
        }],
    })["reviewed_content"][0]


def test_brand_prohibited_term_is_flagged():
    out = review("Avoid the word cheap.", "Our cheap plan is simple.")
    assert out["review_status"] == "rejected"
    assert "prohibited term" in out["review_notes"].lower()


def test_brand_required_phrase_is_enforced():
    out = review("Must include Learn more.", "Explore the platform today.")
    assert out["review_status"] == "rejected"
    assert "required phrase" in out["review_notes"].lower()


def test_brand_max_length_is_enforced():
    out = review("Maximum 20 characters.", "This content is definitely longer than twenty characters.")
    assert out["review_status"] == "rejected"
    assert "exceeds 20 characters" in out["review_notes"]


def test_brand_no_emoji_is_enforced():
    out = review("No emojis.", "Launch your campaign 🚀")
    assert out["review_status"] == "rejected"
    assert "emojis" in out["review_notes"].lower()


def test_compliant_brand_guidelines_pass():
    out = review("Must include Learn more. Maximum 80 characters. No emojis.", "Learn more about our platform.")
    assert out["review_status"] == "approved_for_human_review"
    assert "PASS" in out["review_notes"]
