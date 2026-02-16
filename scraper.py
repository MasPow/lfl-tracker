#!/usr/bin/env python3
"""
SCRAPER LFL QUI MARCHE VRAIMENT
Simple, robuste, avec logs pour débugger
"""

import requests
import json
from datetime import datetime

print("=" * 50)
print("🔥 SCRAPER LFL v2.0")
print("=" * 50)

# API LoL Esports publique
HEADERS = {'x-api-key': '0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z'}
LFL_LEAGUE_ID = '105266103462388553'

# Mapping des noms d'équipes
TEAMS = {
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

def get_short_name(full_name):
    """Récupère le nom court d'une équipe"""
    return TEAMS.get(full_name, full_name[:3].upper())

def fetch_matches():
    """Récupère les matchs LFL"""
    print("\n📊 Récupération des matchs...")
    
    url = "https://esports-api.lolesports.com/persisted/gw/getSchedule"
    params = {'hl': 'fr-FR', 'leagueId': LFL_LEAGUE_ID}
    
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        
        events = data.get('data', {}).get('schedule', {}).get('events', [])
        print(f"✅ API a retourné {len(events)} événements")
        
        matches = []
        for event in events[:15]:
            try:
                match_obj = event.get('match', {})
                if not match_obj:
                    continue
                
                teams = match_obj.get('teams', [])
                if len(teams) < 2:
                    continue
                
                # Noms des équipes
                team1_name = teams[0].get('name', 'TBD')
                team2_name = teams[1].get('name', 'TBD')
                
                # Scores
                team1_result = teams[0].get('result', {}) or {}
                team2_result = teams[1].get('result', {}) or {}
                team1_wins = team1_result.get('gameWins', 0) or 0
                team2_wins = team2_result.get('gameWins', 0) or 0
                
                # Statut
                state = event.get('state', 'unstarted')
                if state == 'completed':
                    status = 'finished'
                elif state == 'inProgress':
                    status = 'live'
                else:
                    status = 'scheduled'
                
                # Date
                start_time = event.get('startTime', '')
                try:
                    dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    date_str = dt.strftime('%d %b - %H:%M')
                except:
                    date_str = 'TBD'
                
                match = {
                    "team1": {
                        "name": team1_name,
                        "short": get_short_name(team1_name),
                        "score": team1_wins
                    },
                    "team2": {
                        "name": team2_name,
                        "short": get_short_name(team2_name),
                        "score": team2_wins
                    },
                    "date": date_str,
                    "status": status
                }
                
                matches.append(match)
                print(f"   ✓ {team1_name} vs {team2_name} ({status})")
                
            except Exception as e:
                print(f"   ⚠️ Erreur parsing match: {e}")
                continue
        
        print(f"\n✅ {len(matches)} matchs valides récupérés")
        return matches
        
    except Exception as e:
        print(f"❌ Erreur API matchs: {e}")
        return []

def fetch_standings():
    """Récupère le classement LFL"""
    print("\n📊 Récupération du classement...")
    
    url = "https://esports-api.lolesports.com/persisted/gw/getStandings"
    params = {'hl': 'fr-FR', 'leagueId': LFL_LEAGUE_ID}
    
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        
        stages = data.get('data', {}).get('standings', [])
        if not stages:
            print("⚠️ Pas de stages dans la réponse")
            return []
        
        # Prendre le premier stage
        stage = stages[0].get('stages', [{}])[0]
        sections = stage.get('sections', [])
        
        if not sections:
            print("⚠️ Pas de sections dans le stage")
            return []
        
        rankings = sections[0].get('rankings', [])
        print(f"✅ API a retourné {len(rankings)} équipes")
        
        standings = []
        for rank_obj in rankings:
            try:
                teams_list = rank_obj.get('teams', [])
                if not teams_list:
                    continue
                
                team_name = teams_list[0].get('name', 'Unknown')
                wins = rank_obj.get('wins', 0) or 0
                losses = rank_obj.get('losses', 0) or 0
                ordinal = rank_obj.get('ordinal', 0) or 0
                
                standing = {
                    "rank": ordinal,
                    "team": team_name,
                    "short": get_short_name(team_name),
                    "wins": wins,
                    "losses": losses,
                    "points": wins * 3
                }
                
                standings.append(standing)
                print(f"   {ordinal}. {team_name} - {wins}V {losses}D")
                
            except Exception as e:
                print(f"   ⚠️ Erreur parsing équipe: {e}")
                continue
        
        print(f"\n✅ {len(standings)} équipes valides")
        return standings
        
    except Exception as e:
        print(f"❌ Erreur API classement: {e}")
        return []

def main():
    """Fonction principale"""
    
    # Récupérer les données
    matches = fetch_matches()
    standings = fetch_standings()
    
    # Créer le fichier JSON
    lfl_data = {
        'last_update': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'matches': matches,
        'standings': standings
    }
    
    # Sauvegarder
    with open('lfl-data.json', 'w', encoding='utf-8') as f:
        json.dump(lfl_data, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 50)
    print(f"✅ SUCCÈS - Fichier créé !")
    print(f"   📅 Dernière MAJ: {lfl_data['last_update']}")
    print(f"   ⚽ Matchs: {len(matches)}")
    print(f"   🏆 Équipes: {len(standings)}")
    print("=" * 50)
    
    # Afficher un aperçu
    if matches:
        print(f"\n📋 Premier match:")
        m = matches[0]
        print(f"   {m['team1']['name']} {m['team1']['score']}-{m['team2']['score']} {m['team2']['name']}")
        print(f"   Date: {m['date']} | Status: {m['status']}")
    
    if standings:
        print(f"\n🏆 Top 3:")
        for s in standings[:3]:
            print(f"   {s['rank']}. {s['team']} - {s['wins']}V {s['losses']}D ({s['points']} pts)")
    
    # Vérifier si c'est vide
    if not matches and not standings:
        print("\n⚠️  WARNING: Données vides ! L'API n'a rien retourné.")
        print("   Vérifier manuellement si la LFL est en cours.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
