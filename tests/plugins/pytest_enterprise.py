"""
Enterprise Pytest Plugin
========================

Custom pytest plugin that provides:

1. **Registered markers** — functional, regression, performance, messaging, ui, slow
2. **test_meta decorator** — attach traceability metadata (ticket, severity, component)
3. **pytest hooks** — enriched failure reports with request/response context,
   structured logging per test, timing metadata in terminal output
4. **CLI options** — --test-env flag for environment switching
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

import pytest
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from _pytest.nodes import Item
from _pytest.reports import TestReport
from _pytest.terminal import TerminalReporter

logger = logging.getLogger("enterprise.plugin")


# ---------------------------------------------------------------------------
# 1. Marker definitions
# ---------------------------------------------------------------------------

MARKERS: dict[str, str] = {
    "functional": "Functional / feature tests",
    "regression": "Regression and edge-case tests",
    "performance": "Performance and benchmark tests",
    "messaging": "Event broker / messaging tests",
    "ui": "Playwright UI tests",
    "slow": "Tests that take a long time to run",
    "test_meta": "Enterprise test metadata (ticket, severity, component)",
}


def pytest_configure(config: Config) -> None:
    """Register custom markers and the plugin itself."""
    for name, description in MARKERS.items():
        config.addinivalue_line("markers", f"{name}: {description}")

    # Register plugin so pytest knows it's active
    config.pluginmanager.register(EnterprisePlugin(), "enterprise_plugin")


# ---------------------------------------------------------------------------
# 2. CLI options
# ---------------------------------------------------------------------------


def pytest_addoption(parser: Parser) -> None:
    """Add custom CLI options for the enterprise test framework."""
    parser.addoption(
        "--test-env",
        action="store",
        default="local",
        choices=("local", "staging", "ci"),
        help="Target test environment (default: local)",
    )
    parser.addoption(
        "--capture-responses",
        action="store_true",
        default=False,
        help="Capture and attach HTTP request/response pairs to failure reports",
    )


# ---------------------------------------------------------------------------
# 3. test_meta decorator
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MetaInfo:
    """Metadata attached to a test for traceability and reporting."""

    ticket: str | None = None
    severity: str = "normal"
    component: str | None = None
    description: str | None = None
    tags: tuple[str, ...] = field(default_factory=tuple)


def test_meta(
    *,
    ticket: str | None = None,
    severity: str = "normal",
    component: str | None = None,
    description: str | None = None,
    tags: tuple[str, ...] | list[str] = (),
) -> pytest.MarkDecorator:
    """
    Decorator to attach enterprise metadata to a test function.

    Usage::

        @test_meta(ticket="ORD-123", severity="critical", component="orders")
        def test_order_creation(client):
            ...

    The metadata is stored as a pytest marker and can be read by hooks,
    reporters, and assertion helpers.
    """
    return pytest.mark.test_meta(
        meta=MetaInfo(
            ticket=ticket,
            severity=severity,
            component=component,
            description=description,
            tags=tuple(tags),
        )
    )


test_meta.__test__ = False  # Prevent pytest from collecting this as a test function


def get_test_meta(item: Item) -> MetaInfo | None:
    """Extract MetaInfo from a test item, if present."""
    marker = item.get_closest_marker("test_meta")
    if marker is None:
        return None
    return marker.kwargs.get("meta")


# ---------------------------------------------------------------------------
# 4. Request/response capture store (populated by test utilities)
# ---------------------------------------------------------------------------


@dataclass
class CapturedExchange:
    """A single HTTP request/response pair captured during a test."""

    method: str
    url: str
    request_body: Any = None
    status_code: int | None = None
    response_body: Any = None


class ExchangeStore:
    """Per-test store for captured HTTP exchanges. Thread-safe via test isolation."""

    def __init__(self) -> None:
        self._exchanges: list[CapturedExchange] = []

    def record(self, exchange: CapturedExchange) -> None:
        self._exchanges.append(exchange)

    @property
    def exchanges(self) -> list[CapturedExchange]:
        return list(self._exchanges)

    def clear(self) -> None:
        self._exchanges.clear()

    def format_for_report(self) -> str:
        """Format all captured exchanges as a readable string for failure reports."""
        if not self._exchanges:
            return "(no HTTP exchanges captured)"

        lines: list[str] = []
        for i, ex in enumerate(self._exchanges, 1):
            lines.append(f"--- Exchange {i} ---")
            lines.append(f"  {ex.method} {ex.url}")
            if ex.request_body is not None:
                lines.append(f"  Request body: {ex.request_body}")
            if ex.status_code is not None:
                lines.append(f"  Status: {ex.status_code}")
            if ex.response_body is not None:
                body_str = str(ex.response_body)
                if len(body_str) > 500:
                    body_str = body_str[:500] + "..."
                lines.append(f"  Response body: {body_str}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# 5. Plugin class with hooks
# ---------------------------------------------------------------------------


class EnterprisePlugin:
    """Core plugin class implementing pytest hooks."""

    def __init__(self) -> None:
        self._test_timings: dict[str, float] = {}

    # -- Collection phase ---------------------------------------------------

    @pytest.hookimpl(tryfirst=True)
    def pytest_collection_modifyitems(
        self, config: Config, items: list[Item]
    ) -> None:
        """Log collection summary and validate test_meta markers."""
        marker_counts: dict[str, int] = {m: 0 for m in MARKERS}

        for item in items:
            for marker_name in MARKERS:
                if item.get_closest_marker(marker_name):
                    marker_counts[marker_name] += 1

            # Validate severity values in test_meta
            meta = get_test_meta(item)
            if meta and meta.severity not in (
                "blocker",
                "critical",
                "normal",
                "minor",
                "trivial",
            ):
                logger.warning(
                    "Test %s has invalid severity '%s'. "
                    "Expected: blocker, critical, normal, minor, trivial",
                    item.nodeid,
                    meta.severity,
                )

        active = {k: v for k, v in marker_counts.items() if v > 0}
        if active:
            summary = ", ".join(f"{k}={v}" for k, v in active.items())
            logger.info("Collected test breakdown: %s", summary)

    # -- Test execution phase -----------------------------------------------

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_setup(self, item: Item) -> None:
        """Record test start time."""
        self._test_timings[item.nodeid] = time.monotonic()

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_makereport(
        self, item: Item, call: pytest.CallInfo[None]
    ) -> None:
        """Enrich failure reports with metadata and captured exchanges."""
        # We only process the "call" phase (not setup/teardown)
        if call.when != "call":
            return

        # Attach test_meta info to the item for terminal reporting
        meta = get_test_meta(item)
        if meta:
            item.user_properties.append(("test_meta", meta))

        # Attach timing
        start = self._test_timings.pop(item.nodeid, None)
        if start is not None:
            elapsed = time.monotonic() - start
            item.user_properties.append(("duration_s", round(elapsed, 4)))

    @pytest.hookimpl(trylast=True)
    def pytest_runtest_logreport(self, report: TestReport) -> None:
        """Append captured HTTP exchanges to failed test reports."""
        if report.when != "call" or not report.failed:
            return

        # Look for exchange_store data in the report's sections
        # (populated by the fixture via extra reporting)
        exchange_data = None
        for prop_name, prop_val in report.user_properties:
            if prop_name == "exchange_report":
                exchange_data = prop_val
                break

        if exchange_data:
            report.sections.append(("Captured HTTP Exchanges", exchange_data))

    # -- Terminal reporting -------------------------------------------------

    def pytest_terminal_summary(
        self, terminalreporter: TerminalReporter, exitstatus: int, config: Config
    ) -> None:
        """Print enterprise summary at the end of the test run."""
        terminalreporter.write_sep("=", "Enterprise Test Summary")

        # Count by marker
        stats: dict[str, dict[str, int]] = {}
        for report_list_name in ("passed", "failed", "error", "skipped"):
            for report in terminalreporter.stats.get(report_list_name, []):
                for prop_name, prop_val in getattr(report, "user_properties", []):
                    if prop_name == "test_meta" and isinstance(prop_val, MetaInfo):
                        component = prop_val.component or "unclassified"
                        if component not in stats:
                            stats[component] = {"passed": 0, "failed": 0, "skipped": 0}
                        if report_list_name in ("passed",):
                            stats[component]["passed"] += 1
                        elif report_list_name in ("failed", "error"):
                            stats[component]["failed"] += 1
                        elif report_list_name == "skipped":
                            stats[component]["skipped"] += 1

        if stats:
            terminalreporter.write_line("")
            terminalreporter.write_line("Results by component:")
            for component, counts in sorted(stats.items()):
                line = (
                    f"  {component}: "
                    f"{counts['passed']} passed, "
                    f"{counts['failed']} failed, "
                    f"{counts['skipped']} skipped"
                )
                terminalreporter.write_line(line)

        env = config.getoption("--test-env", default="local")
        terminalreporter.write_line(f"\nTest environment: {env}")
