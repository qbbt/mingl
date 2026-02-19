# Changelog

All notable changes to this project will be documented in this file.

## [1.5.1] - 2026-02-18

### Added
- **Repo Governance:** Established rules for environment isolation and agent permissions in `README.md`.
- **UI Improvements:** Added hover effects to frontend buttons for better haptic feedback.

### Fixed
- **Python Compatibility:** Updated backend schemas and routers to use `typing.Optional` and `typing.Union` for Python 3.9 compatibility.
- **Router Registration:** Registered missing `analytics` and `status` routers in `app/main.py`.
