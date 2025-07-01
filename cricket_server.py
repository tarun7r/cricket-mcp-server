from mcp.server.fastmcp import FastMCP
import requests
from bs4 import BeautifulSoup
import re
import time
import json
from googlesearch import search

mcp = FastMCP("Cricket API")


@mcp.tool()
def get_player_stats(player_name: str, match_format: str = None) -> dict:
    """
    Get comprehensive cricket player statistics including batting and bowling data from Cricbuzz.
    
    Args:
        player_name (str): The name of the cricket player.
        match_format (str, optional): The match format to get stats for. Can be "Test", "ODI", or "T20". 
                                      If not provided, all stats are returned.
    
    Returns:
        dict: A dictionary containing complete player statistics including:
              - Basic info (name, country, role, image)
              - ICC rankings for batting and bowling
              - Detailed batting stats (matches, runs, average, strike rate, centuries, fifties)
              - Detailed bowling stats (balls, runs, wickets, best figures, economy, five-wicket hauls)
              If match_format is specified, returns stats for that format only.
    """
    query = f"{player_name} cricbuzz"
    profile_link = None
    try:
        results = search(query, num_results=5)
        for link in results:
            if "cricbuzz.com/profiles/" in link:
                profile_link = link
                print(f"Found profile: {profile_link}")
                break
                
        if not profile_link:
            return {"error": "No player profile found"}
    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}
    
    # Get player profile page
    c = requests.get(profile_link).text
    cric = BeautifulSoup(c, "lxml")
    profile = cric.find("div", id="playerProfile")
    pc = profile.find("div", class_="cb-col cb-col-100 cb-bg-white")
    
    # Name, country and image
    name = pc.find("h1", class_="cb-font-40").text
    country = pc.find("h3", class_="cb-font-18 text-gray").text
    image_url = None
    images = pc.findAll('img')
    for image in images:
        image_url = image['src']
        break  # Just get the first image

    # Personal information and rankings
    personal = cric.find_all("div", class_="cb-col cb-col-60 cb-lst-itm-sm")
    role = personal[2].text.strip()
    
    icc = cric.find_all("div", class_="cb-col cb-col-25 cb-plyr-rank text-right")
    # Batting rankings
    tb = icc[0].text.strip()   # Test batting
    ob = icc[1].text.strip()   # ODI batting
    twb = icc[2].text.strip()  # T20 batting
    
    # Bowling rankings
    tbw = icc[3].text.strip()  # Test bowling
    obw = icc[4].text.strip()  # ODI bowling
    twbw = icc[5].text.strip() # T20 bowling

    # Summary of the stats
    summary = cric.find_all("div", class_="cb-plyr-tbl")
    batting = summary[0]
    bowling = summary[1]

    # Batting statistics
    bat_rows = batting.find("tbody").find_all("tr")
    batting_stats = {}
    for row in bat_rows:
        cols = row.find_all("td")
        format_name = cols[0].text.strip().lower()  # e.g., "Test", "ODI", "T20"
        batting_stats[format_name] = {
            "matches": cols[1].text.strip(),
            "runs": cols[3].text.strip(),
            "highest_score": cols[5].text.strip(),
            "average": cols[6].text.strip(),
            "strike_rate": cols[7].text.strip(),
            "hundreds": cols[12].text.strip(),
            "fifties": cols[11].text.strip(),
        }

    # Bowling statistics
    bowl_rows = bowling.find("tbody").find_all("tr")
    bowling_stats = {}
    for row in bowl_rows:
        cols = row.find_all("td")
        format_name = cols[0].text.strip().lower()  # e.g., "Test", "ODI", "T20"
        bowling_stats[format_name] = {
            "balls": cols[3].text.strip(),
            "runs": cols[4].text.strip(),
            "wickets": cols[5].text.strip(),
            "best_bowling_innings": cols[9].text.strip(),
            "economy": cols[7].text.strip(),
            "five_wickets": cols[11].text.strip(),
        }

    # Create player stats dictionary
    player_data = {
        "name": name,
        "country": country,
        "image": image_url,
        "role": role,
        "rankings": {
            "batting": {
                "test": tb,
                "odi": ob,
                "t20": twb
            },
            "bowling": {
                "test": tbw,
                "odi": obw,
                "t20": twbw
            }
        },
        "batting_stats": batting_stats,
        "bowling_stats": bowling_stats
    }

    if match_format:
        match_format = match_format.lower()
        if match_format in batting_stats:
            return {
                "name": name,
                "country": country,
                "role": role,
                "batting_stats": batting_stats[match_format],
                "bowling_stats": bowling_stats.get(match_format, {})
            }
        else:
            return {"error": f"No {match_format} stats found for {player_name}"}

    return player_data

@mcp.tool()
def get_cricket_schedule() -> list:
    """Get upcoming cricket match schedule from Cricbuzz"""
    link = f"https://www.cricbuzz.com/cricket-schedule/upcoming-series/international"
    source = requests.get(link).text
    page = BeautifulSoup(source, "lxml")

    # Find all match containers
    match_containers = page.find_all("div", class_="cb-col-100 cb-col")

    matches = []

    # Iterate through each match container
    for container in match_containers:
        # Extract match details
        date = container.find("div", class_="cb-lv-grn-strip text-bold")
        match_info = container.find("div", class_="cb-col-100 cb-col")
        
        if date and match_info:
            match_date = date.text.strip()
            match_details = match_info.text.strip()
            matches.append(f"{match_date} - {match_details}")
    
    return matches

@mcp.tool()
def get_live_matches() -> list:
    """Get live cricket matches from Cricbuzz"""
    link = f"https://www.cricbuzz.com/cricket-match/live-scores"
    source = requests.get(link).text
    page = BeautifulSoup(source, "lxml")

    page = page.find("div", class_="cb-col cb-col-100 cb-bg-white")
    matches = page.find_all("div", class_="cb-scr-wll-chvrn cb-lv-scrs-col")

    live_matches = []

    for i in range(len(matches)):
        live_matches.append(matches[i].text.strip())
    
    return live_matches


@mcp.tool()
def get_cricket_news() -> list:
    """Get the latest cricket news"""
    link = "https://www.cricbuzz.com/cricket-news"
    try:
        source = requests.get(link).text
        page = BeautifulSoup(source, "lxml")

        # Find all news story containers
        stories = page.find_all("div", class_="cb-nws-lst-rt")

        # Alternative selectors if the above doesn't work
        if not stories:
            stories = page.find_all("div", class_="cb-col-100 cb-col")

        news_list = []
        for story in stories:
            news_item = {}
            
            headline_tag = story.find("a", class_="cb-nws-hdln")
            if headline_tag:
                news_item["headline"] = headline_tag.get_text().strip()

            description_tag = story.find("div", class_="cb-nws-intr")
            if description_tag:
                news_item["description"] = description_tag.get_text().strip()

            timestamp_tag = story.find("div", class_="cb-nws-time")
            if timestamp_tag:
                news_item["timestamp"] = timestamp_tag.get_text().strip()

            category_tag = story.find("div", class_="cb-nws-cat")
            if category_tag:
                news_item["category"] = category_tag.get_text().strip()
            
            if news_item: # Add only if we found something
                news_list.append(news_item)
        
        return news_list

    except Exception as e:
        return [{"error": f"Failed to get cricket news: {str(e)}"}]


if __name__ == "__main__":
    import json
    print("--- Testing get_cricket_news ---")
    news = get_cricket_news()
    print(json.dumps(news, indent=2))
    print("--- End of test ---")
    mcp.run(transport="stdio")