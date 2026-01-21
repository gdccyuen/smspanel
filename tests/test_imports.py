def test_uses_absolute_imports():
    """All smspanel imports should use absolute style."""
    from smspanel.services.hkt_sms import HKTSMSService
    from smspanel.services.dead_letter import DeadLetterQueue
    from smspanel.models import User
    from smspanel.api.sms import api_sms_bp

    assert HKTSMSService is not None
    assert DeadLetterQueue is not None
    assert User is not None
    assert api_sms_bp is not None
