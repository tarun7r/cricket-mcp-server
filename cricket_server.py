from mcp.server.fastmcp import FastMCP
import requests
from bs4 import BeautifulSoup
import re
import time
import json
from googlesearch import search

mcp = FastMCP("Cricket API")

# Add headers to mimic a browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}


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
    try:
        response = requests.get(profile_link, headers=HEADERS, timeout=10)
        response.raise_for_status()
        c = response.text
    except requests.exceptions.ConnectionError as e:
        return {"error": f"Connection error: {str(e)}"}
    except requests.exceptions.Timeout as e:
        return {"error": f"Request timeout: {str(e)}"}
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP error: {str(e)}"}
    except Exception as e:
        return {"error": f"Failed to fetch player profile: {str(e)}"}
    
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
    """
    Get upcoming cricket match schedule from Cricbuzz.
    
    Returns:
        list: A list of dictionaries, each representing a match with series name,
              match description, and a link to the match if available.
    """
    link = "https://www.cricbuzz.com/cricket-schedule/upcoming-series/international"
    try:
        response = requests.get(link, headers=HEADERS, timeout=10)
        response.raise_for_status()
        source = response.text
        page = BeautifulSoup(source, "lxml")
        
        schedule = []
        schedule_container = page.find("div", id="international-list")
        if not schedule_container:
            return [{"error": "Could not find the schedule container"}]

        days = schedule_container.find_all("div", class_="cb-col-100 cb-col")
        for day in days:
            date_tag = day.find("div", class_="cb-lv-grn-strip")
            if not date_tag:
                continue
            
            date = date_tag.text.strip()
            matches = day.find_all("div", class_="cb-ovr-flo cb-col-50 cb-col cb-mtchs-dy-vnu cb-adjst-lst")
            for match in matches:
                match_details = {}
                anchor = match.find("a")
                if anchor:
                    match_details["date"] = date
                    match_details["description"] = anchor.text.strip()
                    url_suffix = anchor.get("href")
                    if url_suffix:
                        match_details["url"] = "https://www.cricbuzz.com" + url_suffix
                    
                    venue_tag = match.find("div", class_="cb-font-12 text-gray cb-ovr-flo")
                    if venue_tag:
                        match_details["venue"] = venue_tag.text.strip()
                    
                    schedule.append(match_details)

        return schedule
    except requests.exceptions.ConnectionError as e:
        return [{"error": f"Connection error: {str(e)}"}]
    except requests.exceptions.Timeout as e:
        return [{"error": f"Request timeout: {str(e)}"}]
    except requests.exceptions.HTTPError as e:
        return [{"error": f"HTTP error: {str(e)}"}]
    except Exception as e:
        return [{"error": f"Failed to get cricket schedule: {str(e)}"}]

@mcp.tool()
def get_match_details(match_url: str) -> dict:
    """
    Get detailed scorecard for a specific cricket match from a Cricbuzz URL.
    
    Args:
        match_url (str): The URL of the match on Cricbuzz (can be obtained from get_live_matches).
        
    Returns:
        dict: A dictionary containing match details including:
              - Match title and result.
              - A scorecard for each innings with batting and bowling stats.
    """
    if not match_url or "cricbuzz.com" not in match_url:
        return {"error": "A valid Cricbuzz match URL is required."}
        
    try:
        response = requests.get(match_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        source = response.text
        page = BeautifulSoup(source, "lxml")
    except requests.exceptions.ConnectionError as e:
        return {"error": f"Connection error: {str(e)}"}
    except requests.exceptions.Timeout as e:
        return {"error": f"Request timeout: {str(e)}"}
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP error: {str(e)}"}
    except Exception as e:
        return {"error": f"Failed to fetch or parse match page: {str(e)}"}

    match_data = {}

    # Extract title and result
    title_tag = page.find("h1", class_="cb-nav-hdr")
    if title_tag:
        match_data["title"] = title_tag.text.strip()
    
    result_tag = page.find("div", class_="cb-nav-text")
    if result_tag:
        match_data["result"] = result_tag.text.strip()

    # Scorecard
    scorecard = {}
    innings_divs = page.find_all("div", id=re.compile(r"^inning_\d+$"))

    for i, inning_div in enumerate(innings_divs):
        inning_key = f"inning_{i+1}"
        inning_data = {"batting": [], "bowling": []}
        
        inning_title_tag = inning_div.find("div", class_="cb-scrd-hdr-rw")
        if inning_title_tag:
             inning_data["title"] = inning_title_tag.text.strip()
        
        # Batting stats
        batsmen = inning_div.find_all("div", class_=lambda x: x and x.startswith('cb-col cb-col-w-'))
        for batsman in batsmen:
            cols = batsman.find_all("div", class_=lambda x: x and x.startswith('cb-col cb-col-w-'))
            if len(cols) > 1 and "batsman" in cols[0].text.lower(): # Header row
                continue

            if len(cols) >= 7:
                player_name = cols[0].text.strip()
                if "Extras" in player_name or not player_name:
                    continue
                
                inning_data["batting"].append({
                    "player": player_name,
                    "dismissal": cols[1].text.strip(),
                    "R": cols[2].text.strip(),
                    "B": cols[3].text.strip(),
                    "4s": cols[4].text.strip(),
                    "6s": cols[5].text.strip(),
                    "SR": cols[6].text.strip(),
                })

        # Bowling stats
        bowlers_section = inning_div.find("div", class_="cb-col-bowlers")
        if bowlers_section:
            bowlers = bowlers_section.find_all("div", class_="cb-scrd-itms")
            for bowler in bowlers:
                cols = bowler.find_all("div", class_=lambda x: x and x.startswith('cb-col cb-col-w-'))
                if len(cols) > 1 and "bowler" in cols[0].text.lower(): # Header row
                    continue
                
                if len(cols) >= 6:
                    player_name = cols[0].text.strip()
                    if not player_name:
                        continue
                    
                    inning_data["bowling"].append({
                        "player": player_name,
                        "O": cols[1].text.strip(),
                        "M": cols[2].text.strip(),
                        "R": cols[3].text.strip(),
                        "W": cols[4].text.strip(),
                        "Econ": cols[5].text.strip(),
                    })
        
        scorecard[inning_key] = inning_data
    
    match_data["scorecard"] = scorecard
    return match_data

@mcp.tool()
def get_live_matches() -> list:
    """Get live cricket matches from Cricbuzz.
    
    Returns:
        list: A list of dictionaries, each containing the match description and a URL.
              Example: [{"match": "IND vs AUS...", "url": "https://..."}]
    """
    link = "https://www.cricbuzz.com/cricket-match/live-scores"
    try:
        response = requests.get(link, headers=HEADERS, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        source = response.text
        page = BeautifulSoup(source, "lxml")

        container = page.find("div", id="page-wrapper")
        if not container:
            return [{"error": "Could not find the main page wrapper"}]
            
        matches = container.find_all("div", class_="cb-mtch-lst")
        live_matches = []

        for match in matches:
            description_tag = match.find("a", class_="text-hvr-underline")
            if description_tag:
                match_text = description_tag.text.strip()
                url_suffix = description_tag.get("href")
                
                if url_suffix:
                    url = "https://www.cricbuzz.com" + url_suffix
                    live_matches.append({"match": match_text, "url": url})
        
        return live_matches

    except requests.exceptions.ConnectionError as e:
        return [{"error": f"Connection error: {str(e)}"}]
    except requests.exceptions.Timeout as e:
        return [{"error": f"Request timeout: {str(e)}"}]
    except requests.exceptions.HTTPError as e:
        return [{"error": f"HTTP error: {str(e)}"}]
    except Exception as e:
        return [{"error": f"Failed to get live matches: {str(e)}"}]


@mcp.tool()
def get_cricket_news() -> list:
    """
    Get the latest cricket news from Cricbuzz.
    
    Returns:
        list: A list of dictionaries, each containing news details including headline,
              description, timestamp, category, and a direct URL to the article.
    """
    link = "https://www.cricbuzz.com/cricket-news"
    try:
        response = requests.get(link, headers=HEADERS, timeout=10)
        response.raise_for_status()
        source = response.text
        page = BeautifulSoup(source, "lxml")

        news_list = []
        news_container = page.find("div", id="news-list")
        if not news_container:
            return [{"error": "Could not find the news container"}]

        stories = news_container.find_all("div", class_="cb-col cb-col-100 cb-lst-itm cb-pos-rel cb-lst-itm-lg")

        for story in stories:
            news_item = {}
            
            headline_tag = story.find("a", class_="cb-nws-hdln-ancr")
            if headline_tag:
                news_item["headline"] = headline_tag.get("title", "").strip()
                news_item["url"] = "https://www.cricbuzz.com" + headline_tag.get("href", "")

            description_tag = story.find("div", class_="cb-nws-intr")
            if description_tag:
                news_item["description"] = description_tag.text.strip()

            time_tag = story.find("span", class_="cb-nws-time")
            if time_tag:
                news_item["timestamp"] = time_tag.text.strip()

            category_tag = story.find("div", class_="cb-nws-time")
            if category_tag:
                category_text = category_tag.text.strip()
                if "•" in category_text:
                    parts = category_text.split("•")
                    if len(parts) > 1:
                        news_item["category"] = parts[1].strip()

            if news_item:
                news_list.append(news_item)

        return news_list
    except requests.exceptions.ConnectionError as e:
        return [{"error": f"Connection error: {str(e)}"}]
    except requests.exceptions.Timeout as e:
        return [{"error": f"Request timeout: {str(e)}"}]
    except requests.exceptions.HTTPError as e:
        return [{"error": f"HTTP error: {str(e)}"}]
    except Exception as e:
        return [{"error": f"Failed to get cricket news: {str(e)}"}]


@mcp.tool()
def get_icc_rankings(category: str) -> dict:
    """
    Fetches official ICC cricket rankings for various categories. Use this tool to answer questions about top players and teams in Test, ODI, and T20 formats.

    For example, you can answer questions like:
    - "Who are the top 10 ODI batsmen?"
    - "Show me the test bowling rankings."
    - "What are the T20 team rankings?"
    - "icc ranking odi batsman"

    Args:
        category (str): The ranking category. Must be one of: "batting", "bowling", "all-rounder", or "teams".
                        
    Returns:
        dict: A dictionary with rankings for Test, ODI, and T20 formats. 
              Each format contains a list of players or teams with their position, name, country, and rating.
    """
    if category not in ["batting", "bowling", "all-rounder", "teams"]:
        return {"error": "Invalid category. Choose from 'batting', 'bowling', 'all-rounder', 'teams'."}

    # The 'all-rounder' category is spelled as 'all-rounder' in the URL
    url_category = category if category != "all-rounder" else "all-rounder"
    link = f"https://www.cricbuzz.com/cricket-stats/icc-rankings/men/{url_category}"

    try:
        response = requests.get(link, headers=HEADERS, timeout=10)
        response.raise_for_status()
        source = response.text
        page = BeautifulSoup(source, "lxml")

        rankings = {}
        
        # Define formats to scrape
        formats = ["test", "odi", "t20"]
        
        # Map category to the format used in ng-show directive
        category_map = {
            "batting": "batsmen",
            "bowling": "bowlers",
            "all-rounder": "allrounders",
            "teams": "teams"
        }
        angular_category = category_map.get(category)

        for f in formats:
            format_key = f"{angular_category}-{f}s" # e.g., batsmen-tests
            if f == 't20':
                 format_key = f"{angular_category}-t20s"

            # Find the container for the specific format
            format_container = page.find("div", {"ng-show": f"'{format_key}' == act_rank_format"})
            
            if not format_container:
                continue

            ranking_list = []
            
            if category == "teams":
                # Find all team rows
                rows = format_container.find_all("div", class_="cb-col cb-col-100 cb-font-14 cb-brdr-thin-btm text-center")
                for row in rows:
                    position = row.find("div", class_="cb-col cb-col-20 cb-lst-itm-sm").text.strip()
                    team_name = row.find("div", class_="cb-col cb-col-50 cb-lst-itm-sm text-left").text.strip()
                    rating = row.find_all("div", class_="cb-col cb-col-14 cb-lst-itm-sm")[0].text.strip()
                    points = row.find_all("div", class_="cb-col cb-col-14 cb-lst-itm-sm")[1].text.strip()

                    ranking_list.append({
                        "position": position,
                        "team": team_name,
                        "rating": rating,
                        "points": points
                    })
            else:
                # Find all player rows
                rows = format_container.find_all("div", class_="cb-col cb-col-100 cb-font-14 cb-lst-itm text-center")

                for row in rows:
                    position = row.find("div", class_="cb-col cb-col-16 cb-rank-tbl cb-font-16").text.strip()
                    rating = row.find("div", class_="cb-col cb-col-17 cb-rank-tbl pull-right").text.strip()
                    
                    player_info = row.find("div", class_="cb-col cb-col-67 cb-rank-plyr")
                    player_name = player_info.find("a").text.strip()
                    country = player_info.find("div", class_="cb-font-12 text-gray").text.strip()

                    ranking_list.append({
                        "position": position,
                        "player": player_name,
                        "country": country,
                        "rating": rating
                    })
            
            rankings[f] = ranking_list

        return rankings

    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}


if __name__ == "__main__":
    # test the icc rankings
    rankings = get_icc_rankings("batting")
    print(json.dumps(rankings, indent=2))
    mcp.run(transport="stdio")