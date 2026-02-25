#!/usr/bin/env python3
"""
SCRAPER LFL QUI MARCHE VRAIMENT
Simple, robuste, avec logs pour débugger
"""

import json
import os
import re
import time
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import ProxyHandler, Request, build_opener

print("=" * 50)
print("🔥 SCRAPER LFL v2.2")
print("=" * 50)

# API LoL Esports publique
DEFAULT_API_KEYS = [
    os.getenv('LFL_API_KEY', '').strip(),
    # Clé historique (fallback)
    '0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z',
]
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


DEFAULT_TIMEOUT = 20
RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 1.5


def _fetch_once(url, params, opener, api_key):
    query = urlencode(params)
    req = Request(
        f"{url}?{query}",
        headers={
            "x-api-key": api_key,
            "User-Agent": "Mozilla/5.0 (compatible; LFLTrackerBot/2.2)",
            "Accept": "application/json",
        },
    )
    with opener.open(req, timeout=DEFAULT_TIMEOUT) as response:
        return json.loads(response.read().decode('utf-8'))




def discover_api_keys(openers):
    """Tente d'extraire une clé API depuis le site officiel LoL Esports."""
    candidates = [key for key in DEFAULT_API_KEYS if key]
    target_url = 'https://lolesports.com/fr-FR/schedule'

    for _, opener in openers:
        try:
            req = Request(target_url, headers={"User-Agent": "Mozilla/5.0"})
            with opener.open(req, timeout=DEFAULT_TIMEOUT) as response:
                html = response.read().decode('utf-8', errors='ignore')

            # Exemple rencontré: "x-api-key":"..."
            found = re.findall(r'"x-api-key"\s*:\s*"([A-Za-z0-9_-]{20,})"', html)
            for key in found:
                if key and key not in candidates:
                    candidates.append(key)

            if found:
                print(f"   ℹ️ {len(found)} clé(s) API potentielle(s) trouvée(s) depuis lolesports.com")
                break
        except Exception:
            continue

    if not candidates:
        raise RuntimeError("Aucune clé API disponible. Défini LFL_API_KEY dans ton environnement.")

    return candidates


def _build_openers():
    # default opener: respecte les proxys système (utile sur certains runners)
    default_opener = build_opener()
    # no-proxy opener: contourne les proxys qui renvoient parfois des 403 tunnel
    direct_opener = build_opener(ProxyHandler({}))
    return [
        ("proxy-env", default_opener),
        ("direct", direct_opener),
    ]


def fetch_json(url, params):
    last_error = None
    openers = _build_openers()
    api_keys = discover_api_keys(openers)

    for api_key in api_keys:
        key_hint = f"...{api_key[-6:]}" if len(api_key) > 6 else "(short)"
        for mode, opener in openers:
            for attempt in range(1, RETRY_ATTEMPTS + 1):
                try:
                    data = _fetch_once(url, params, opener, api_key)
                    if attempt > 1:
                        print(f"   ℹ️ Requête OK en mode {mode} (tentative {attempt})")
                    print(f"   ✅ Clé API utilisée: {key_hint}")
                    return data
                except (HTTPError, URLError, TimeoutError, ValueError) as error:
                    last_error = error
                    print(f"   ⚠️ Échec clé {key_hint} | {mode} tentative {attempt}/{RETRY_ATTEMPTS}: {error}")
                    if attempt < RETRY_ATTEMPTS:
                        time.sleep(RETRY_DELAY_SECONDS * attempt)

    raise RuntimeError(f"Impossible de récupérer l'API après retries: {last_error}")


def fetch_matches():
    """Récupère les matchs LFL"""
    print("\n📊 Récupération des matchs...")
    
    url = "https://esports-api.lolesports.com/persisted/gw/getSchedule"
    params = {'hl': 'fr-FR', 'leagueId': LFL_LEAGUE_ID}
    
    try:
        data = fetch_json(url, params)
        
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
                    "startTime": start_time,
                    "date_iso": start_time,
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
        return None

def fetch_standings():
    """Récupère le classement LFL"""
    print("\n📊 Récupération du classement...")
    
    url = "https://esports-api.lolesports.com/persisted/gw/getStandings"
    params = {'hl': 'fr-FR', 'leagueId': LFL_LEAGUE_ID}
    
    try:
        data = fetch_json(url, params)
        
        stages = data.get('data', {}).get('standings', [])
        if not stages:
            print("⚠️ Pas de stages dans la réponse")
            return []
        
        sections = []
        for standing in stages:
            for stage in standing.get('stages', []):
                sections.extend(stage.get('sections', []))
        
        if not sections:
            print("⚠️ Pas de sections dans le stage")
            return []
        
        rankings = []
        for section in sections:
            rankings.extend(section.get('rankings', []))
        print(f"✅ API a retourné {len(rankings)} équipes")
        
        standings = []
        seen = set()
        for rank_obj in rankings:
            try:
                teams_list = rank_obj.get('teams', [])
                if not teams_list:
                    continue

                team_name = teams_list[0].get('name', 'Unknown')
                wins = rank_obj.get('wins', 0) or 0
                losses = rank_obj.get('losses', 0) or 0
                ordinal = rank_obj.get('ordinal', 0) or 0

                if (ordinal, team_name) in seen:
                    continue
                seen.add((ordinal, team_name))

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
        return None

def main():
    """Fonction principale"""

    existing_data = {}
    try:
        with open('lfl-data.json', 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    except Exception:
        existing_data = {}

    # Récupérer les données
    matches = fetch_matches()
    standings = fetch_standings()

    if matches is None:
        cached_matches = existing_data.get('matches', [])
        matches = cached_matches
        matches_source = 'cache' if cached_matches else 'unavailable'
    else:
        matches_source = 'api'

    if standings is None:
        cached_standings = existing_data.get('standings', [])
        standings = cached_standings
        standings_source = 'cache' if cached_standings else 'unavailable'
    else:
        standings_source = 'api'

    # Éviter d'écraser un bon fichier avec des données totalement indisponibles
    if matches_source == 'unavailable' and standings_source == 'unavailable' and existing_data:
        print('⚠️ API indisponible et aucun fallback exploitable nouveau: conservation du fichier existant.')
        return 1

    # Créer le fichier JSON
    lfl_data = {
        'last_update': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'matches': matches,
        'standings': standings,
        'scrape_status': {
            'matches_source': matches_source,
            'standings_source': standings_source
        }
    }
    
    # Sauvegarder
    with open('lfl-data.json', 'w', encoding='utf-8') as f:
        json.dump(lfl_data, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 50)
    print(f"✅ SUCCÈS - Fichier créé !")
    print(f"   📅 Dernière MAJ: {lfl_data['last_update']}")
    print(f"   ⚽ Matchs: {len(matches)}")
    print(f"   🏆 Équipes: {len(standings)}")
    print(f"   🧭 Source matchs: {lfl_data['scrape_status']['matches_source']}")
    print(f"   🧭 Source classement: {lfl_data['scrape_status']['standings_source']}")
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
