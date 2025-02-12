# EVE Online Killmail Tracker

A Python tool to fetch and store EVE Online corporation killmails using zKillboard and ESI (EVE Swagger Interface) APIs.

## Features

- Automatic killmail retrieval for a specific corporation
- PostgreSQL database storage
- API rate limit handling
- Support for both historical mode (up to January 1st, 2025) and update mode
- Detailed operation logging

## Prerequisites

- Python 3.8+
- PostgreSQL 14+
- Python packages listed in `requirements.txt`

## Installation

1. Clone the repository
```bash
git clone git@github.com:cchopin/zkill_batch.git
cd zkill_batch
```

2. Install Python dependencies
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with the following variables:
```plaintext
DB_NAME=eve_killmails
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
CORPORATION_ID=your_corp_id
```

4. Initialize the database by running the SQL script
```bash
psql -U postgres -f eve_killmails.sql
```

## Usage

Run the main script:
```bash
python main.py
```

The script will:
1. Connect to the database
2. Fetch killmails from zKillboard
3. Enrich data through the ESI API
4. Store results in the PostgreSQL database

## Database Structure

- `systems`: Solar system information
- `ship_types`: Ship type data
- `ships`: Specific ship information
- `pilots`: Pilot data
- `killmails`: Main killmail data

## Logging

Logs are stored in the `logs/` directory and contain detailed information about script execution.

## Development Mode

To set up a development environment:

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Unix/macOS
venv\Scripts\activate     # On Windows
```

2. Install development dependencies:
```bash
pip install -r requirements.txt
```

## Error Handling

The script includes robust error handling for:
- API connection issues
- Rate limiting
- Database connection problems
- Data parsing errors

## Contributing

1. Fork the project
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -am 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Best Practices

When contributing, please:
- Follow PEP 8 style guidelines
- Add docstrings to new functions
- Update the README if needed
- Include appropriate error handling
- Add logging for significant operations


## Contact

For questions or suggestions, please open an issue on GitHub.

## Acknowledgments

- EVE Online for providing the ESI API
- zKillboard for their public API
- The EVE Online development community
