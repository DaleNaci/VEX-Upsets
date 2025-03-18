import os
import sys

import requests # type: ignore
from dotenv import load_dotenv # type: ignore


load_dotenv()

API_KEY = os.getenv("ROBOTEVENTS_TOKEN")
BASE_URL = "https://www.robotevents.com/api/v2"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}


def main():
    if len(sys.argv) != 2:
        print("Invalid arguments.")
        exit(1)

    event_id = get_event_id(sys.argv[1])
    
    match_list_data = get_match_list(event_id)
    match_list = simplify_match_list_data(match_list_data)
    
    team_rankings_data = get_ranking_list(event_id)
    team_rankings = simply_team_ranking_data(team_rankings_data)
        
    find_upsets(match_list, team_rankings)


def get_event_id(sku: str):
    url = f"{BASE_URL}/events"
    params = {"sku": sku}

    response = requests.get(url, headers=HEADERS, params=params)

    if response.status_code != 200:
        print("Error:", response.status_code, response.text)
        return None

    data = response.json()

    try:
        return data["data"][0]["id"]
    except:
        print("Path not found in JSON response.")
        return None
    

def get_match_list(event_id: int):
    url = f"{BASE_URL}/events/{event_id}/divisions/1/matches"
    match_list = []

    while url:
        response = requests.get(url, headers=HEADERS)

        if response.status_code != 200:
            print("Error:", response.status_code, response.text)
            return None

        data = response.json()

        if "data" in data:
            match_list.extend(data["data"])

        if "meta" in data and "next_page_url" in data["meta"]:
            url = data["meta"]["next_page_url"]
        else:
            url = None

    return match_list


def simplify_match_list_data(match_list_data: list):
    rtn = []

    for match in match_list_data:
        if match["round"] != 2:
            continue

        d = {}

        d["matchnum"] = match["matchnum"]
        d["bluescore"] = match["alliances"][0]["score"]
        d["redscore"] = match["alliances"][1]["score"]
        d["blue1"] = match["alliances"][0]["teams"][0]["team"]["name"]
        d["blue2"] = match["alliances"][0]["teams"][1]["team"]["name"]
        d["red1"] = match["alliances"][1]["teams"][0]["team"]["name"]
        d["red2"] = match["alliances"][1]["teams"][1]["team"]["name"]

        rtn.append(d)
    
    return rtn


def get_ranking_list(event_id: int):
    url = f"{BASE_URL}/events/{event_id}/divisions/1/rankings"
    ranking_list = []

    while url:
        response = requests.get(url, headers=HEADERS)

        if response.status_code != 200:
            print("Error:", response.status_code, response.text)
            return None
    
        data = response.json()

        if "data" in data:
            ranking_list.extend(data["data"])
        
        if "meta" in data and "next_page_url" in data["meta"]:
            url = data["meta"]["next_page_url"]
        else:
            url = None
    
    return ranking_list


def simply_team_ranking_data(team_rankings_data: list):
    rtn = {}

    for ranking in team_rankings_data:
        team_name = ranking["team"]["name"]
        rank = ranking["rank"]

        rtn[team_name] = rank
    
    return rtn


def find_upsets(match_list: list, team_rankings: dict):
    upsets = []

    for match in match_list:
        blue1_rank = team_rankings[match["blue1"]]
        blue2_rank = team_rankings[match["blue2"]]
        red1_rank = team_rankings[match["red1"]]
        red2_rank = team_rankings[match["red2"]]

        match["blue_avg"] = (blue1_rank + blue2_rank) / 2
        match["red_avg"] = (red1_rank + red2_rank) / 2
        match["avg_diff"] = abs(match["blue_avg"] - match["red_avg"])

        if (match["blue_avg"] > match["red_avg"] and match["bluescore"] > match["redscore"]) \
                or (match["blue_avg"] < match["red_avg"] and match["bluescore"] < match["redscore"]):
            upsets.append(match)
    
    sorted_upsets = sorted(upsets, key=lambda x: x["avg_diff"], reverse=True)

    for upset in sorted_upsets:
        print(f"Qualification #{upset["matchnum"]}")
        print(f"[B] {upset["blue1"]} {upset["blue2"]}   {upset["bluescore"]} - {upset["redscore"]}   {upset["red1"]} {upset["red2"]} [R]")
        print("Blue average ranking:", upset["blue_avg"])
        print("Red average ranking:", upset["red_avg"])
        print("Average difference:", upset["avg_diff"])

        print()

if __name__ == "__main__":
    main()