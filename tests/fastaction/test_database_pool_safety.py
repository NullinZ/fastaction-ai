from fastaction.persistence.store import _engine_options
from fastaction.settings import FastActionSettings


def test_postgres_pool_uses_bounded_defaults_and_recovery_guards():
    options = _engine_options(
        "postgresql://example.invalid/fastaction",
        FastActionSettings(),
    )

    assert options["pool_size"] == 5
    assert options["max_overflow"] == 5
    assert options["pool_timeout"] == 5
    assert options["pool_recycle"] == 1800
    assert options["pool_use_lifo"] is True
    assert options["pool_reset_on_return"] == "rollback"
    assert options["connect_args"]["connect_timeout"] == 5
    assert "idle_in_transaction_session_timeout=60000" in options["connect_args"]["options"]


def test_sqlite_keeps_lightweight_pool_configuration():
    assert _engine_options("sqlite:///fastaction.db", FastActionSettings()) == {
        "pool_pre_ping": True
    }
