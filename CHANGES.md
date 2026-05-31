# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Sprint 2 UI: live command-center KPIs from `/api/trends`, workflow map from run bundle, delights from latest run, issue annotation agree/disagree/false-positive actions
- Sprint 1 UI: export artifact downloads, compare run selectors wired to `/api/diff`, evidence copy-repro and step timeline deep links
- GitHub Flow repo foundation: CI, PR checks, release workflow, issue/PR templates
- Python unit tests for DSL, preflight SSRF guards, and flaky heuristics
- `CONTRIBUTING.md`, `CODEOWNERS`, Dependabot config

### Changed

- Workflows and recommendations pages use live run bundle data instead of mock Acme fixtures
- `FEATURE_SCOPE.md` reorganized for SELECTIVE EXPANSION execution plan

## [0.1.0] - 2026-05-31

### Added

- Initial monorepo: `launch-rehearsal` CLI, `Frontend_V1` dashboard, product specs
- Multi-agent pipeline: crawl, journeys, personas, LLM, scorecard
- Parallel seeds + FLAKY detection; `open_link` profile fallback
- Dashboard API + artifact serving; Argyle dogfood configs

[Unreleased]: https://github.com/Lapse-AI/TryLapse/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Lapse-AI/TryLapse/releases/tag/v0.1.0
