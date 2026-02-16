#!/usr/bin/env python3
"""
Scraper LFL avec API LoL Esports publique (pas besoin de clé)
"""

import requests
import json
from datetime import datetime

# API publique LoL Esports
ESPORTS_API = "https://esports-api.lolesports.com/persisted/gw"
HEADERS = {
    'x-api-key': '0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z'
}

TEAM_SHORTS = {
    "Karmine Corp": "KC",
    "Karmine Corp Blue": "KC",
    "Team Vitality.Bee": "VIT",
    "Vitality.Bee": "VIT",
    "Solary": "SLY",
    "Gentle Mates": "GM",
    "BK ROG Esports": "BK",
    "BK ROG": "BK",
    "Team GO": "GO",
    "BDS Academy": "BDS",
    "Team BDS Academy": "BDS",
    "Ici Japon Corp": "IJC",
    "JobLife": "JL",
    "GameWard": "GW"
}

def get_lfl_data():
    """Récupère les données LFL"""
    
    # Récupérer les matchs
    schedule_url = f"{ESPORTS_API}/getSchedule"
    params = {'hl': 'fr-FR', 'leagueId': '105266103462388553'}  # LFL
    
    try:
        response = requests.get(schedule_url, headers=HEADERS, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        events = data.get('data', {}).get('schedule', {}).get('events', [])
        
        matches = []
        for event in events[:15]:
            match_obj = event.get('match', {})
            teams = match_obj.get('teams', [])
            
            if len(teams) < 2:
                continue
            
            team1_name = teams[0].get('name', 'TBD')
            team2_name = teams[1].get('name', 'TBD')
            
            team1_result = teams[0].get('result', {})
            team2_result = teams[1].get('result', {})
            
            team1_wins = team1_result.get('gameWins', 0) if team1_result else 0
            team2_wins = team2_result.get('gameWins', 0) if team2_result else 0
            
            state = event.get('state', 'unstarted')
            start_time = event.get('startTime', '')
            
            if state == 'completed':
                status = 'finished'
            elif state == 'inProgress':
                status = 'live'
            else:
                status = 'scheduled'
            
            # Formater la date
            try:
                dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                date_str = dt.strftime('%d %b - %H:%M')
            except:
                date_str = 'Date TBD'
            
            match = {
                "team1": {
                    "name": team1_name,
                    "short": TEAM_SHORTS.get(team1_name, team1_name[:3].upper()),
                    "score": team1_wins
                },
                "team2": {
                    "name": team2_name,
                    "short": TEAM_SHORTS.get(team2_name, team2_name[:3].upper()),
                    "score": team2_wins
                },
                "date": date_str,
                "status": status
            }
            
            matches.append(match)
        
        print(f"✅ {len(matches)} matchs récupérés")
        
    except Exception as e:
        print(f"❌ Erreur matchs: {e}")
        matches = []
    
    # Récupérer le classement
    standings_url = f"{ESPORTS_API}/getStandings"
    standings = []
    
    try:
        response = requests.get(standings_url, headers=HEADERS, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        stages = data.get('data', {}).get('standings', [])
        
        if stages:
            sections = stages[0].get('stages', [{}])[0].get('sections', [])
            if sections:
                rankings = sections[0].get('rankings', [])
                
                for rank_obj in rankings:
                    teams_list = rank_obj.get('teams', [])
                    if teams_list:
                        team_name = teams_list[0].get('name', 'Unknown')
                        
                        standing = {
                            "rank": rank_obj.get('ordinal', 0),
                            "team": team_name,
                            "short": TEAM_SHORTS.get(team_name, team_name[:3].upper()),
                            "wins": rank_obj.get('wins', 0),
                            "losses": rank_obj.get('losses', 0),
                            "points": rank_obj.get('wins', 0) * 3
                        }
                        standings.append(standing)
        
        print(f"✅ {len(standings)} équipes au classement")
        
    except Exception as e:
        print(f"❌ Erreur classement: {e}")
    
    return matches, standings

def main():
    print("🔄 Récupération données LFL via API LoL Esports...")
    
    matches, standings = get_lfl_data()
    
    lfl_data = {
        'last_update': datetime.utcnow().isoformat() + 'Z',
        'matches': matches,
        'standings': standings
    }
    
    with open('lfl-data.json', 'w', encoding='utf-8') as f:
        json.dump(lfl_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Données sauvegardées")
    print(f"   - {len(matches)} matchs")
    print(f"   - {len(standings)} équipes")
    
    if matches:
        m = matches[0]
        print(f"\nDernier match: {m['team1']['name']} {m['team1']['score']}-{m['team2']['score']} {m['team2']['name']}")

if __name__ == "__main__":
    main()
