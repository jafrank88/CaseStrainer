"""Regression: party-line disagreements must not be treated as the same case name."""

import pytest

from src.utils.mismatch_utils import names_equivalent


@pytest.mark.parametrize(
    ("a", "b"),
    [
        ("Barr v. Lee", "Barr v. Roane"),
        ("Miller v. Parker", "Zagorski v. Parker"),
    ],
)
def test_party_line_disagreement_not_equivalent(a, b):
    assert not names_equivalent(a, b, verified=True, canonical_url="https://example.com/opinion")
    assert not names_equivalent(b, a, verified=True, canonical_url="https://example.com/opinion")


def test_same_case_still_equivalent():
    assert names_equivalent("Smith v. Jones", "Smith v. Jones", verified=True)


def test_acme_corp_variants_not_party_mismatch():
    """Corporate wording variants on the same side should remain equivalent."""
    assert names_equivalent(
        "Acme Corp v. Smith",
        "Acme Corporation v. Smith",
        verified=True,
        canonical_url="https://example.com/x",
    )


def test_verifying_display_follows_document_when_cluster_name_mismatch():
    from src.utils.cluster_display_utils import apply_display_fields_to_cluster

    cluster = {
        "has_name_mismatch": True,
        "citations": [
            {
                "verified": True,
                "name_mismatch": True,
                "canonical_name": "Barr v. Roane",
                "canonical_date": "2020-01-01",
                "canonical_url": "https://court.example/opinion/1",
                "url": "https://court.example/opinion/1",
                "extracted_case_name": "Barr v. Lee",
                "extracted_date": "2020",
            }
        ],
    }
    apply_display_fields_to_cluster(cluster)
    # verifying_* = CourtListener / canonical caption; submitted_* = document extraction
    assert "Roane" in cluster["verifying_display_name"]
    assert "Lee" in cluster["submitted_display_name"]
    assert "Roane" not in cluster["submitted_display_name"]
