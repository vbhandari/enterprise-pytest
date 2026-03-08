.PHONY: install test test-functional test-regression test-messaging test-performance test-ui test-hypothesis test-contract lint serve help build-ui

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install project with test dependencies
	uv pip install -e ".[test]"

lint: ## Run linter
	ruff check sut/ tests/
	ruff format --check sut/ tests/

format: ## Auto-format code
	ruff check --fix sut/ tests/
	ruff format sut/ tests/

serve: ## Start the SUT server
	uvicorn sut.app.main:app --reload --port 8000

# ---------------------------------------------------------------------------
# Test targets
# ---------------------------------------------------------------------------

test: ## Run all tests (excluding UI and performance)
	pytest tests/ -m "not ui and not performance" -v

test-all: ## Run the complete test suite
	pytest tests/ -v

test-functional: ## Run functional tests
	pytest tests/functional/ -v

test-regression: ## Run regression tests
	pytest tests/regression/ -v

test-messaging: ## Run messaging/event tests
	pytest tests/messaging/ -v

test-performance: ## Run performance benchmarks
	pytest tests/performance/ -v --benchmark-only

test-ui: ## Run Playwright UI tests
	pytest tests/ui/ -v

test-hypothesis: ## Run property-based tests
	pytest tests/hypothesis/ -v

test-contract: ## Run Pact contract tests
	pytest tests/contract/ -v

test-smoke: ## Run smoke tests only
	pytest tests/test_plugin_smoke.py tests/test_fixtures_smoke.py -v

# ---------------------------------------------------------------------------
# UI build
# ---------------------------------------------------------------------------

build-ui: ## Build the React admin UI
	cd sut/admin-ui && npm run build

# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

test-html: ## Run tests and generate HTML report
	pytest tests/ -m "not ui and not performance" --html=reports/report.html --self-contained-html

test-allure: ## Run tests and generate Allure results
	pytest tests/ -m "not ui and not performance" --alluredir=reports/allure-results

test-junit: ## Run tests and generate JUnit XML
	pytest tests/ -m "not ui and not performance" --junitxml=reports/junit.xml

# ---------------------------------------------------------------------------
# Locust
# ---------------------------------------------------------------------------

locust: ## Run Locust load test (requires running SUT)
	locust -f tests/performance/locustfile.py --host http://localhost:8000
