#!/usr/bin/env python3
"""
Script pour récupérer les données LFL en temps réel
Source : Leaguepedia via API Cargo
"""

import requests
import json
from datetime import datetime

# API Cargo de Leaguepedia
CARGO_API = "https://lol.fandom.com/api.php"

def query_cargo(tables, fields, where="", group_by="", order_by="", limit=500):
    """Effectue une requête Cargo sur Leaguepedia"""
    params = {
        "action": "cargoquery",
        "format": "json",
        "tables": tables,
        "fields": fields,
        "limit": limit
    }
    
    if where:
        params["where"] = where
    if group_by:
        params["group_by"] = group_by
    if order_by:
        params["order_by"] = order_by
    
    try:
        response = requests.get(CARGO_API, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Erreur API: {e}")
        return None

def get_lfl_matches():
    """Récupère les matchs LFL récents"""
    
    # Requête pour les matchs LFL 2025
    tables = "MatchSchedule=MS, ScoreboardGames=SG"
    fields = """
        MS.Team1, MS.Team2, MS.Winner, MS.DateTime_UTC,
        SG.Team1Score, SG.Team2Score, MS.BestOf, MS.MatchId
    """
    where = "MS.OverviewPage='LFL/2025 Season/Spring Split' AND MS.DateTime_UTC IS NOT NULL"
    order_by = "MS.DateTime_UTC DESC"
    limit = 50
    
    data = query_cargo(tables, fields, where=where, order_by=order_by, limit=limit)
    
    if not data or 'cargoquery' not in data:
        print("Erreur : Impossible de récupérer les matchs")
        return []
    
    matches = []
    for item in data['cargoquery']:
        title = item['title']
        
        # Parser la date
        match_date = title.get('DateTime UTC', '')
        try:
            dt = datetime.strptime(match_date, '%Y-%m-%d %H:%M:%S')
            now = datetime.utcnow()
            
            # Déterminer le statut
            if dt > now:
                status = 'scheduled'
            elif (now - dt).total_seconds() < 3600 * 3:  # moins de 3h
                status = 'live'
            else:
                status = 'finished'
                
            date_str = dt.strftime('%d %b - %H:%M')
        except:
            date_str = 'Date inconnue'
            status = 'scheduled'
        
        match = {
            'team1': {
                'name': title.get('Team1', 'TBD'),
                'short': title.get('Team1', 'TBD')[:3].upper(),
                'score': int(title.get('Team1Score', 0)) if title.get('Team1Score') else 0
            },
            'team2': {
                'name': title.get('Team2', 'TBD'),
                'short': title.get('Team2', 'TBD')[:3].upper(),
                'score': int(title.get('Team2Score', 0)) if title.get('Team2Score') else 0
            },
            'date': date_str,
            'status': status,
            'winner': title.get('Winner', '')
        }
        
        matches.append(match)
    
    return matches[:10]  # Top 10 matchs les plus récents

def get_lfl_standings():
    """Récupère le classement LFL"""
    
    tables = "TournamentResults=TR"
    fields = """
        TR.Team, TR.Wins, TR.Losses, TR.Place
    """
    where = "TR.OverviewPage='LFL/2025 Season/Spring Split'"
    order_by = "TR.Place ASC"
    
    data = query_cargo(tables, fields, where=where, order_by=order_by)
    
    if not data or 'cargoquery' not in data:
        print("Erreur : Impossible de récupérer le classement")
        return []
    
    standings = []
    for item in data['cargoquery']:
        title = item['title']
        
        team_name = title.get('Team', 'Unknown')
        wins = int(title.get('Wins', 0))
        losses = int(title.get('Losses', 0))
        rank = int(title.get('Place', 0))
        
        standing = {
            'rank': rank,
            'team': team_name,
            'short': team_name[:3].upper(),
            'wins': wins,
            'losses': losses,
            'points': wins * 3  # 3 points par victoire
        }
        
        standings.append(standing)
    
    return standings

def generate_lfl_data():
    """Génère le fichier JSON avec toutes les données LFL"""
    
    print("🔄 Récupération des données LFL...")
    
    # Récupérer les données
    matches = get_lfl_matches()
    standings = get_lfl_standings()
    
    # Structure finale
    lfl_data = {
        'last_update': datetime.utcnow().isoformat() + 'Z',
        'matches': matches,
        'standings': standings
    }
    
    # Sauvegarder dans un fichier JSON
    output_file = 'lfl-data.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(lfl_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Données sauvegardées dans {output_file}")
    print(f"   - {len(matches)} matchs récupérés")
    print(f"   - {len(standings)} équipes au classement")
    print(f"   - Dernière mise à jour : {lfl_data['last_update']}")
    
    return lfl_data

if __name__ == "__main__":
    try:
        data = generate_lfl_data()
        
        # Afficher un aperçu
        print("\n📊 Aperçu des données :")
        print(f"\nDernier match :")
        if data['matches']:
            m = data['matches'][0]
            print(f"  {m['team1']['name']} {m['team1']['score']}-{m['team2']['score']} {m['team2']['name']}")
            print(f"  Status: {m['status']} | Date: {m['date']}")
        
        print(f"\nTop 3 du classement :")
        for standing in data['standings'][:3]:
            print(f"  {standing['rank']}. {standing['team']} - {standing['wins']}V {standing['losses']}D")
            
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
