# Cricket MCP Server

A Model Context Protocol (MCP) server that provides comprehensive cricket data from Cricbuzz. This server offers real-time cricket statistics, player information, match schedules, and news updates.

## Features

- **Player Statistics**: Get detailed cricket player stats including batting and bowling records across all formats (Test, ODI, T20)
- **Live Matches**: Fetch currently ongoing cricket matches
- **Match Schedule**: Get upcoming cricket match schedules
- **Cricket News**: Latest cricket news and updates

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Running as an MCP Server

The server can be integrated with MCP clients. Here's how to configure it:

```python
from mcp import MultiServerMCPClient

client = MultiServerMCPClient(
    {
        "cricket": {
            "command": "python",
            "args": ["cricket_server.py"],
            "transport": "stdio",
        }
    }
)
```

For a more flexible setup, you can use environment variables to define the python executable and server script path.

### Running Standalone

For testing purposes, you can run the server directly:

```bash
python cricket_server.py
```

## Available Tools

### 1. get_player_stats
Get comprehensive cricket player statistics.

**Parameters:**
- `player_name` (str): Name of the cricket player
- `match_format` (str, optional): Specific format ("Test", "ODI", "T20"). If not provided, returns all formats.

**Returns:**
- Player basic info (name, country, role, image)
- ICC rankings for batting and bowling
- Detailed batting statistics
- Detailed bowling statistics

**Example:**
```python
# Get all stats for a player
stats = get_player_stats("Virat Kohli")

# Get only T20 stats
t20_stats = get_player_stats("Virat Kohli", "T20")
```

### 2. get_live_matches
Get currently live cricket matches.

**Returns:**
List of live match information including teams and current status.

### 3. get_cricket_schedule
Get upcoming cricket match schedule.

**Returns:**
List of upcoming international cricket matches with dates and details.

### 4. get_cricket_news
Get the latest cricket news.

**Returns:**
List of cricket news articles with headlines, descriptions, timestamps, and categories.

## Data Source

This server scrapes data from Cricbuzz.com and uses Google Search for player profile discovery. Please ensure you comply with the website's terms of service and use responsibly.

## Dependencies

- `fastmcp`: MCP server framework
- `requests`: HTTP library for web scraping
- `beautifulsoup4`: HTML parsing library
- `lxml`: XML/HTML parser
- `googlesearch-python`: Google search API wrapper

## Configuration

The server runs on stdio transport by default. No additional configuration is required for basic usage.

## Error Handling

The server includes comprehensive error handling for:
- Network connectivity issues
- Invalid player names
- Missing data on Cricbuzz
- Search failures

## License

This project is for educational and personal use. Please respect the terms of service of the data sources.

## Contributing

Feel free to submit issues and enhancement requests!

## Disclaimer

This tool scrapes data from public websites. The authors are not responsible for any misuse or violation of website terms of service. Use responsibly and ensure compliance with applicable terms and conditions.
