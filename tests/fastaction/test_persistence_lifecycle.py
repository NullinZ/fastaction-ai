import ast
import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy.engine import make_url

from fastaction.persistence import store


@pytest.fixture
def owners(monkeypatch):
    store.close_fastaction_persistence()
    events, engines = [], []
    settings = SimpleNamespace(database_url="sqlite://")

    class Engine:
        dialect = SimpleNamespace(name="sqlite")

        def __init__(self, url):
            self.url = make_url(url)
            self.disposed = 0

        def dispose(self):
            self.disposed += 1

    def create(url, **kwargs):
        engine = Engine(url)
        engines.append(engine)
        return engine

    class Session:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            events.append("session.close")

        def commit(self):
            events.append("commit")

    monkeypatch.setattr(store, "persistence_enabled", lambda: True)
    monkeypatch.setattr(store, "get_settings", lambda: settings)
    monkeypatch.setattr(store, "_engine_options", lambda *args: {})
    monkeypatch.setattr(store, "create_engine", create)
    monkeypatch.setattr(store, "sessionmaker", lambda **kwargs: Session)
    monkeypatch.setattr(store.FastActionBase.metadata, "create_all", lambda **kwargs: None)
    monkeypatch.setattr(store, "_seed_defaults", lambda *args: events.append("seed"))
    monkeypatch.setattr(store, "load_runtime_from_store", lambda *args: events.append("load"))
    try:
        yield SimpleNamespace(engines=engines, events=events, settings=settings, Session=Session)
    finally:
        store.close_fastaction_persistence()


def test_repeated_and_concurrent_init_reuses_owned_engine_without_skipping_seed_or_load(owners):
    with ThreadPoolExecutor(max_workers=12) as threads:
        list(threads.map(store.initialize_fastaction_persistence, range(100)))
    assert len(owners.engines) == 1
    assert owners.events.count("seed") == owners.events.count("load") == 100
    assert owners.events.count("session.close") == 100
    store.close_fastaction_persistence()
    assert owners.engines[0].disposed == 1
    assert not store.is_initialized()
    store.close_fastaction_persistence()
    assert owners.engines[0].disposed == 1


@pytest.mark.parametrize("phase", ["create_all", "seed", "commit", "load"])
def test_partial_init_releases_only_its_owned_engine(owners, monkeypatch, phase):
    def fail(*args, **kwargs):
        raise RuntimeError("synthetic " + phase)

    if phase == "create_all":
        monkeypatch.setattr(store.FastActionBase.metadata, "create_all", fail)
    elif phase == "commit":
        monkeypatch.setattr(owners.Session, "commit", fail)
    else:
        monkeypatch.setattr(store, "_seed_defaults" if phase == "seed" else "load_runtime_from_store", fail)
    with pytest.raises(RuntimeError, match="synthetic"):
        store.initialize_fastaction_persistence(object())
    assert owners.engines[0].disposed == 1
    assert not store.is_initialized() and store._session_factory is None and store._owned_engine is None


def test_replacement_and_injected_owners_are_never_disposed_by_us(owners):
    store.initialize_fastaction_persistence(object())
    owners.settings.database_url = "sqlite:///different-owned-target"
    store.initialize_fastaction_persistence(object())
    assert len(owners.engines) == 2 and owners.engines[0].disposed == 1
    foreign = SimpleNamespace(dialect=SimpleNamespace(name="sqlite"))
    store.initialize_fastaction_persistence(object(), engine=foreign)
    assert owners.engines[1].disposed == 1 and store._owned_engine is None
    store.initialize_fastaction_persistence(object(), session_factory=owners.Session)
    store.close_fastaction_persistence()
    assert all(engine.disposed == 1 for engine in owners.engines)


def test_failed_dispose_retains_owner_for_explicit_retry(owners, monkeypatch):
    store.initialize_fastaction_persistence(object())
    engine = owners.engines[0]
    original = engine.dispose

    def fail():
        raise RuntimeError("synthetic dispose")

    monkeypatch.setattr(engine, "dispose", fail)
    with pytest.raises(RuntimeError, match="synthetic dispose"):
        store.close_fastaction_persistence()
    assert not store.is_initialized() and store._owned_engine is engine
    monkeypatch.setattr(engine, "dispose", original)
    store.close_fastaction_persistence()
    assert engine.disposed == 1 and store._owned_engine is None


def test_development_startup_failure_still_closes_persistence():
    source = Path(__file__).resolve().parents[2] / "scripts/dev_app.py"
    node = next(n for n in ast.parse(source.read_text()).body if isinstance(n, ast.AsyncFunctionDef) and n.name == "lifespan")
    events = []

    def fail(runtime):
        events.append("init")
        raise RuntimeError("synthetic init")

    scope = dict(asynccontextmanager=asynccontextmanager, FastAPI=object, runtime=object(),
                 initialize_fastaction_persistence=fail, close_fastaction_persistence=lambda: events.append("close"))
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), "exec"), scope)

    async def run():
        with pytest.raises(RuntimeError, match="synthetic init"):
            async with scope["lifespan"](object()):
                raise AssertionError("Startup must fail before yield")

    asyncio.run(run())
    assert events == ["init", "close"]
