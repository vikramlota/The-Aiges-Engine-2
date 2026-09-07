"""
Optional transformer-based enrichment: auto-detects which ASCI
expert-review categories (health claims, automotive claims, etc.) a
caption's text plausibly touches on, so content_categories doesn't rely
purely on a human remembering to tag it by hand.

Deliberately kept OUT of core rules/engine, which stay pure stdlib and
fast to test. Importing THIS module pulls in `transformers` and a
~0.2-0.4B parameter model -- opt into it only where you actually want
auto-tagging (an ingestion pipeline), not as a hard dependency of the core
rule engine.
"""

CANDIDATE_CATEGORIES = {
    "health_wellness_claims": "a health, medical, or wellness claim such as curing, treating, or healing something",
    "food_beverage_claims": "a nutrition or health claim about a food or beverage product",
    "educational_institutions": "a claim about a course, degree, accreditation, or job placement from an educational institution",
    "automotive_claims": "a safety, performance, or mileage claim about a vehicle",
    "awards_rankings_claims": "a claimed award, ranking, or being the number one choice",
    "children_targeted": "content clearly aimed at or featuring children as the audience",
}

DEFAULT_MODEL = "facebook/bart-large-mnli"

_classifier = None
_classifier_unavailable = False


def _get_classifier(model_name: str = DEFAULT_MODEL):
    global _classifier, _classifier_unavailable
    if _classifier_unavailable:
        raise RuntimeError("claim classifier previously failed to load; not retrying this run")
    if _classifier is None:
        from transformers import pipeline
        _classifier = pipeline("zero-shot-classification", model=model_name)
    return _classifier


def classify_content_categories(caption: str, threshold: float = 0.6, model_name: str = DEFAULT_MODEL) -> list:
    """
    Returns a list of ASCI category keys (matching rules.ASCI_CATEGORIES)
    whose candidate description scores at or above `threshold` against
    this caption, using multi-label zero-shot classification.
    """
    global _classifier_unavailable
    if not caption or not caption.strip():
        return []

    try:
        classifier = _get_classifier(model_name)
    except Exception as e:
        if not _classifier_unavailable:
            print(f"    [!] Claim classifier unavailable ({e}) -- disabling auto-detection for the rest of this run.")
            _classifier_unavailable = True
        return []

    labels = list(CANDIDATE_CATEGORIES.values())
    try:
        result = classifier(caption, candidate_labels=labels, multi_label=True)
    except Exception as e:
        print(f"    [!] Claim classifier failed on this caption ({e}) -- skipping auto-detection for it.")
        return []

    label_to_key = {v: k for k, v in CANDIDATE_CATEGORIES.items()}
    return [
        label_to_key[label]
        for label, score in zip(result["labels"], result["scores"])
        if score >= threshold
    ]
