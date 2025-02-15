# CHANGELOG

## [1.1.0] - 2025-02-15

### Added
- New database tables for enhanced data tracking:
    - `corporations` table for tracking both victim and attacker corporations
    - `killmail_attackers` table for detailed attacker information
- Database migration scripts:
    - `backfill_attackers.py` for populating attacker data
    - `backfill_corporations.py` for updating corporation information
- Enhanced error handling with intelligent backoff for API rate limits
- Support for both historical and update modes
- Initial framework for HTML report generation

### Changed
- Updated database schema with new entity relationships
- Improved logging with more detailed error information
- Enhanced kill processing with attacker information tracking
- Modified main script to handle new data structure
- Updated documentation with new features and database schema

### Fixed
- Improved API rate limit handling
- Enhanced error recovery for failed requests
- Better handling of missing or invalid data
