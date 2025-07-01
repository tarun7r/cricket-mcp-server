# Cricket MCP Server Configuration

This file contains configuration examples for integrating the Cricket MCP Server with various MCP clients.

## Basic Configuration

```python
# Replace with your actual MCP client import
# For example: from mcp_client import Client
# or: from your_mcp_library import MultiServerMCPClient

# Basic server configuration
cricket_config = {
    "cricket": {
        "command": "python",
        "args": ["cricket_server.py"],
        "transport": "stdio",
    }
}

# Initialize client (replace with your actual MCP client)
# client = YourMCPClient(cricket_config)
```

## Your Specific Usage Pattern

Based on your request, here's the exact configuration:

```python
self.client = MultiServerMCPClient(
    {
        "cricket": {
            "command": "python",
            "args": ["cricket_server.py"],
            "transport": "stdio",
        }
    }
)
```

## Usage Examples

### 1. Get Player Statistics

```python
# Get all format stats
result = await client.call_tool("cricket", "get_player_stats", {
    "player_name": "Virat Kohli"
})

# Get specific format stats
result = await client.call_tool("cricket", "get_player_stats", {
    "player_name": "Virat Kohli",
    "match_format": "T20"
})
```

### 2. Get Live Matches

```python
result = await client.call_tool("cricket", "get_live_matches", {})
```

### 3. Get Match Schedule

```python
result = await client.call_tool("cricket", "get_cricket_schedule", {})
```

### 4. Get Cricket News

```python
result = await client.call_tool("cricket", "get_cricket_news", {})
```

## Environment Variables (Optional)

You can set these environment variables for better configuration:

```bash
export CRICKET_SERVER_PATH="cricket_server.py"
export PYTHON_PATH="/usr/bin/python3"  # or your preferred Python executable
```

Then use in configuration:

```python
import os

cricket_config = {
    "cricket": {
        "command": os.getenv("PYTHON_PATH", "python"),
        "args": [os.getenv("CRICKET_SERVER_PATH", "cricket_server.py")],
        "transport": "stdio",
    }
}
```

## Testing the Configuration

```python
async def test_cricket_server():
    client = MultiServerMCPClient(cricket_config)
    
    try:
        await client.connect()
        
        # Test with a simple call
        result = await client.call_tool("cricket", "get_cricket_news", {})
        print("Server is working!")
        print(f"Found {len(result)} news items")
        
    except Exception as e:
        print(f"Server test failed: {e}")
    
    finally:
        await client.disconnect()
```
