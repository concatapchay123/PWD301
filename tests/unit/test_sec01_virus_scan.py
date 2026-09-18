"""Unit tests for SEC-01: Fail-Closed ClamAV in FileAsset.virus_scan_status."""

from unittest.mock import MagicMock

from pwd301.models.file_import import FileAsset, FileRevision


def test_sec01_active_asset_with_rejected_revision_is_infected():
    """If an asset is ACTIVE but effective revision is REJECTED, status must be INFECTED."""
    fa = FileAsset()
    fa.status = "ACTIVE"
    rev = MagicMock(spec=FileRevision)
    rev.status = "REJECTED"
    rev.scan_results = []
    fa._effective_revision = MagicMock(return_value=rev)

    assert fa.virus_scan_status == "INFECTED"


def test_sec01_active_asset_with_quarantined_revision_is_pending():
    """If an asset is ACTIVE but revision is QUARANTINED/SCANNING, status must be PENDING."""
    fa = FileAsset()
    fa.status = "ACTIVE"
    rev = MagicMock(spec=FileRevision)
    rev.status = "QUARANTINED"
    rev.scan_results = []
    fa._effective_revision = MagicMock(return_value=rev)

    assert fa.virus_scan_status == "PENDING"

    rev.status = "SCANNING"
    assert fa.virus_scan_status == "PENDING"

    rev.status = "VALIDATING"
    assert fa.virus_scan_status == "PENDING"


def test_sec01_active_asset_with_none_revision_is_pending():
    """If an asset has no revision, status must be PENDING."""
    fa = FileAsset()
    fa.status = "ACTIVE"
    fa._effective_revision = MagicMock(return_value=None)

    assert fa.virus_scan_status == "PENDING"


def test_sec01_only_clean_when_both_active():
    """Status is CLEAN only when both FileAsset and FileRevision are ACTIVE."""
    fa = FileAsset()
    fa.status = "ACTIVE"
    rev = MagicMock(spec=FileRevision)
    rev.status = "ACTIVE"
    rev.scan_results = []
    fa._effective_revision = MagicMock(return_value=rev)

    assert fa.virus_scan_status == "CLEAN"

    fa.status = "PENDING"
    assert fa.virus_scan_status == "PENDING"
