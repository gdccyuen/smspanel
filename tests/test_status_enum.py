def test_status_enum_exists():
    """Status enum should be defined for message and recipient statuses."""
    from smspanel.models import MessageStatus, RecipientStatus, DeadLetterStatus

    # MessageStatus
    assert hasattr(MessageStatus, "PENDING")
    assert hasattr(MessageStatus, "SENT")
    assert hasattr(MessageStatus, "FAILED")
    assert hasattr(MessageStatus, "PARTIAL")

    # RecipientStatus
    assert hasattr(RecipientStatus, "PENDING")
    assert hasattr(RecipientStatus, "SENT")
    assert hasattr(RecipientStatus, "FAILED")

    # DeadLetterStatus
    assert hasattr(DeadLetterStatus, "PENDING")
    assert hasattr(DeadLetterStatus, "RETRIED")
    assert hasattr(DeadLetterStatus, "ABANDONED")


def test_status_enum_values():
    """Status enums should have correct string values."""
    from smspanel.models import MessageStatus, RecipientStatus, DeadLetterStatus

    assert MessageStatus.PENDING.value == "pending"
    assert MessageStatus.SENT.value == "sent"
    assert MessageStatus.FAILED.value == "failed"
    assert MessageStatus.PARTIAL.value == "partial"

    assert RecipientStatus.PENDING.value == "pending"
    assert RecipientStatus.SENT.value == "sent"
    assert RecipientStatus.FAILED.value == "failed"

    assert DeadLetterStatus.PENDING.value == "pending"
    assert DeadLetterStatus.RETRIED.value == "retried"
    assert DeadLetterStatus.ABANDONED.value == "abandoned"
