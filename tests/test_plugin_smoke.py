"""Smoke tests to verify the enterprise plugin infrastructure works."""

from __future__ import annotations

import pytest

from tests.plugins.pytest_enterprise import (
    CapturedExchange,
    ExchangeStore,
    MetaInfo,
    get_test_meta,
    test_meta,
)


class TestTestMetaDecorator:
    """Verify the @test_meta decorator attaches metadata correctly."""

    @test_meta(ticket="SMOKE-001", severity="critical", component="plugin")
    def test_meta_is_attached(self, request: pytest.FixtureRequest) -> None:
        meta = get_test_meta(request.node)
        assert meta is not None
        assert meta.ticket == "SMOKE-001"
        assert meta.severity == "critical"
        assert meta.component == "plugin"

    @test_meta(tags=["smoke", "infrastructure"])
    def test_meta_defaults(self, request: pytest.FixtureRequest) -> None:
        meta = get_test_meta(request.node)
        assert meta is not None
        assert meta.severity == "normal"
        assert meta.ticket is None
        assert meta.tags == ("smoke", "infrastructure")

    def test_no_meta_returns_none(self, request: pytest.FixtureRequest) -> None:
        meta = get_test_meta(request.node)
        assert meta is None


class TestExchangeStore:
    """Verify the HTTP exchange capture store."""

    def test_record_and_retrieve(self) -> None:
        store = ExchangeStore()
        exchange = CapturedExchange(
            method="POST",
            url="/auth/login",
            request_body={"email": "a@b.com"},
            status_code=200,
            response_body={"token": "abc"},
        )
        store.record(exchange)
        assert len(store.exchanges) == 1
        assert store.exchanges[0].method == "POST"

    def test_clear(self) -> None:
        store = ExchangeStore()
        store.record(CapturedExchange(method="GET", url="/health"))
        store.clear()
        assert len(store.exchanges) == 0

    def test_format_for_report(self) -> None:
        store = ExchangeStore()
        store.record(CapturedExchange(method="GET", url="/products", status_code=200))
        report = store.format_for_report()
        assert "GET /products" in report
        assert "Status: 200" in report

    def test_empty_format(self) -> None:
        store = ExchangeStore()
        assert "(no HTTP exchanges captured)" in store.format_for_report()


class TestExchangeStoreFixture:
    """Verify the exchange_store fixture injection."""

    def test_fixture_is_injected(self, exchange_store: ExchangeStore) -> None:
        assert isinstance(exchange_store, ExchangeStore)
        assert len(exchange_store.exchanges) == 0


class TestMetaInfoDataclass:
    """Verify MetaInfo is frozen and has correct defaults."""

    def test_frozen(self) -> None:
        meta = MetaInfo(ticket="X-1")
        with pytest.raises(AttributeError):
            meta.ticket = "X-2"  # type: ignore[misc]

    def test_defaults(self) -> None:
        meta = MetaInfo()
        assert meta.severity == "normal"
        assert meta.tags == ()
        assert meta.component is None


@pytest.mark.functional
@test_meta(ticket="SMOKE-002", severity="normal", component="markers")
def test_marker_and_meta_together(request: pytest.FixtureRequest) -> None:
    """Verify markers and test_meta can be combined on a single test."""
    markers = [m.name for m in request.node.iter_markers()]
    assert "functional" in markers
    assert "test_meta" in markers
