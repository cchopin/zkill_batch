# CHANGELOG



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
