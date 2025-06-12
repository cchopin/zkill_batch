# CHANGELOG

# EVE Killmail Tracker - Version 1.3.0

## Changelog

CHANGELOG

## [1.3.0] - 2025-03-22

### Changed
- Completely revised killmail processing strategy to always fetch the 10 most recent pages from zkillboard
- Removed date-based filtering that limited processing to only newer kills than those in the database

### Removed
- Eliminated the logic to stop processing after finding consecutive existing kills
- Removed code that compared kill dates with the newest kill date in database

### Fixed
- Improved reliability of data collection by ensuring all recent kills are always checked
- Fixed potential missed kills when pages contained a mix of new and existing killmails

### Maintained
- API rate limiting with progressive delays between requests
- Individual kill existence verification to prevent duplicates
- Detailed logging of processing statistics

  

## [1.2.1] - 2025-02-21
### Changed
- Optimized recent killmail loading strategy
- Reduced maximum page depth from unlimited to 10 pages
- Decreased consecutive existing kills threshold from 5 to 3
- Added 7-day lookback limit for empty databases
- Enhanced API error handling for zKillboard responses
- Improved progressive delay between API requests

### Fixed
- Fixed string indices error in kill processing loop
- Added proper handling for zKillboard error messages
- Improved handling of invalid kill data formats
- Better error logging for API response debugging

### Added
- New debug logging for API response structures
- Progressive delay system for API requests
- Kill date validation against newest database entry
- Early exit conditions for older killmails

### Security
- Updated User-Agent string for better API tracking
- Added rate limiting safeguards for zKillboard API

### Dependencies
No changes to dependencies.

---

## [1.2.0] - 2025-02-16
### Added
- **HTML Report Generation:**
  - Monthly HTML reports are now generated with the following components:
    - Daily Statistics (destroyed value and kill count)
    - Kills vs Losses Trend (values in billions)
    - Top 20 Ship Types (with dynamic mouse-over effects)
    - Top Corporation Pilots (with values displayed in billions)
    - Additional Statistics (Global K/D Ratio, ISK Efficiency, and Peak Hour)
  - An index page (`index.html`) is automatically generated listing all reports since January 2025.
- **Automation Enhancements:**
  - `run_report.sh` now activates a virtual environment, generates reports, updates the index, and copies the files to `/var/www/news.eve-goats.fr/`.
  - Per-execution log files are generated for the report generator and killmail batch scripts.
- **Log Rotation Setup:**
  - A logrotate configuration has been provided to manage logs in `/scripts/eve_killmails/logs`.

### Changed
- Updated database schema and entity relationships to support detailed killmail tracking.
- Enhanced error handling with intelligent backoff for API rate limits.
- Improved logging for all scripts.
- Updated automation scripts for backups and killmail fetching.

### Fixed
- Resolved issues with copying generated reports to the web directory.
- Improved handling of API errors and missing data.


## [1.1.1] - 2025-02-15

### Added
- New automation shell scripts:
  - `backup.sh` for automated database and script backups with remote transfer capabilities
  - `run.sh` for automated script execution in virtual environment

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
