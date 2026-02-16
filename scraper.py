#!/usr/bin/env python3
"""
Scraper LFL avec API Riot Games officielle
Nécessite une clé API Riot : https://developer.riotgames.com
"""

import requests
import json
from datetime import datetime
import os

# Ta clé API Riot (à mettre dans les secrets GitHub)
RIOT_API_KEY = os.environ.get('RIOT_API_KEY', 'RGAPI-YOUR-KEY-HERE')

# Endpoints API
ESPORTS_API = "https://esports-api.lolesports.com/persisted/gw"
LEAGUES_ENDPOINT = f"{ESPORTS_API}/getLeagues?hl=fr-FR"
SCHEDULE_ENDPOINT = f"{ESPORTS_API}/getSchedule?hl=fr-FR"
STANDINGS_ENDPOINT = f"{ESPORTS_API}/getStandings?hl=fr-FR"

# Headers pour l'API eSports (pas besoin de clé API pour celle-ci)
HEADERS = {
    'x-api-key': '0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z',  # Clé publique LoL Esports
    'Accept': 'application/json'
}

# Mapping des logos
TEAM_LOGOS = {
    "Karmine Corp": "KC",
    "Vitality.Bee": "VIT",
    "Solary": "SLY",
    "Gentle Mates": "GM",
    "BK ROG": "BK",
    "Team GO": "GO",
    "BDS Academy": "BDS",
    "Ici Japon Corp": "IJC",
    "JobLife": "JL",
    "GameWard": "GW"
}

def get_lfl_league_id():
    """Récupère l'ID de la LFL"""
    try:
        response = requests.get(LEAGUES_ENDPOINT, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Chercher la LFL
        for league in data.get('data', {}).get('leagues', []):
            if league.get('slug') == 'lfl':
                return league.get('id')
        
        print("⚠️ LFL non trouvée")
        return None
    except Exception as e:
        print(f"❌ Erreur récupération league ID: {e}")
        return None

def get_lfl_matches(league_id):
    """Récupère les matchs LFL récents"""
    try:
        url = f"{SCHEDULE_ENDPOINT}&leagueId={league_id}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        matches = []
        events = data.get('data', {}).get('schedule', {}).get('events', [])
        
        for event in events[:10]:  # Top 10 matchs
            match_data = event.get('match', {})
            teams = match_data.get('teams', [])
            
            if len(teams) != 2:
                continue
            
            team1 = teams[0].get('name', 'TBD')
            team2 = teams[1].get('name', 'TBD')
            
            # Récupérer les scores
            games = match_data.get('games', [])
            team1_wins = sum(1 for game in games if game.get('teams', [{}])[0].get('side') == teams[0].get('side') and game.get('state') == 'completed')
            team2_wins = sum(1 for game in games if game.get('teams', [{}])[1].get('side') == teams[1].get('side') and game.get('state') == 'completed')
            
            # Déterminer le statut
            state = event.get('state', 'unstarted')
            if state == 'completed':
                status = 'finished'
            elif state == 'inProgress':
                status = 'live'
            else:
                status = 'scheduled'
            
            # Date
            start_time = event.get('startTime')
            if start_time:
                dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                date_str = dt.strftime('%d %b - %H:%M')
            else:
                date_str = 'À déterminer'
            
            match = {
                "team1": {
                    "name": team1,
                    "short": TEAM_LOGOS.get(team1, team1[:3].upper()),
                    "score": team1_wins
                },
                "team2": {
                    "name": team2,
                    "short": TEAM_LOGOS.get(team2, team2[:3].upper()),
                    "score": team2_wins
                },
                "date": date_str,
                "status": status
            }
            
            matches.append(match)
        
        print(f"✅ {len(matches)} matchs récupérés")
        return matches
        
    except Exception as e:
        print(f"❌ Erreur récupération matchs: {e}")
        return []

def get_lfl_standings(league_id):
    """Récupère le classement LFL"""
    try:
        url = f"{STANDINGS_ENDPOINT}&leagueId={league_id}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        standings = []
        stages = data.get('data', {}).get('standings', [])
        
        if not stages:
            print("⚠️ Pas de classement disponible")
            return []
        
        # Prendre le dernier stage (le plus récent)
        latest_stage = stages[-1]
        teams = latest_stage.get('stages', [{}])[0].get('sections', [{}])[0].get('rankings', [])
        
        for idx, team_data in enumerate(teams, 1):
            team_name = team_data.get('teams', [{}])[0].get('name', 'Unknown')
            
            standing = {
                "rank": idx,
                "team": team_name,
                "short": TEAM_LOGOS.get(team_name, team_name[:3].upper()),
                "wins": team_data.get('wins', 0),
                "losses": team_data.get('losses', 0),
                "points": team_data.get('wins', 0) * 3  # 3 points par victoire
            }
            standings.append(standing)
        
        print(f"✅ {len(standings)} équipes au classement")
        return standings
        
    except Exception as e:
        print(f"❌ Erreur récupération classement: {e}")
        return []

def generate_lfl_data():
    """Génère le fichier JSON avec toutes les données"""
    print("🔄 Récupération des données LFL via API Riot...")
    
    # Récupérer l'ID de la LFL
    league_id = get_lfl_league_id()
    
    if not league_id:
        print("❌ Impossible de continuer sans ID de league")
        return None
    
    print(f"✅ LFL League ID: {league_id}")
    
    # Récupérer les données
    matches = get_lfl_matches(league_id)
    standings = get_lfl_standings(league_id)
    
    # Structure finale
    lfl_data = {
        'last_update': datetime.utcnow().isoformat() + 'Z',
        'matches': matches,
        'standings': standings
    }
    
    # Sauvegarder
    output_file = 'lfl-data.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(lfl_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Données sauvegardées dans {output_file}")
    print(f"   - {len(matches)} matchs")
    print(f"   - {len(standings)} équipes")
    print(f"   - Dernière MAJ : {lfl_data['last_update']}")
    
    return lfl_data

if __name__ == "__main__":
    try:
        data = generate_lfl_data()
        
        if data:
            print("\n📊 Aperçu des données :")
            print(f"\nDernier match :")
            if data['matches']:
                m = data['matches'][0]
                print(f"  {m['team1']['name']} {m['team1']['score']}-{m['team2']['score']} {m['team2']['name']}")
                print(f"  Status: {m['status']} | Date: {m['date']}")
            
            print(f"\nTop 3 du classement :")
            for standing in data['standings'][:3]:
                print(f"  {standing['rank']}. {standing['team']} - {standing['wins']}V {standing['losses']}D")
        else:
            print("❌ Échec de génération des données")
            exit(1)
            
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        exit(1)
