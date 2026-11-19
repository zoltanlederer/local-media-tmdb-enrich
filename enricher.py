"""
Get the full TMDB data for each matched title, from the local cache or the API,
and parse it into the output format.
"""

import time
import json
from pathlib import Path
from tmdb import fetch_details, fetch_seasons
from parser import parse_movie, parse_tv


def cache_path(tmdb_id, media_type):
    """Return the cache file path for a title."""
    return Path('cache') / media_type / f'{tmdb_id}.json'


def get_details(tmdb_id, media_type):
    """Return the full TMDB data for a title, from the cache if possible.

    Only fetches from TMDB when the title isn't cached yet. TV shows also get
    their seasons in English and Hungarian. Nothing is saved if any request fails,
    so a failed title is simply fetched again on the next run.
    """
    cache_file = cache_path(tmdb_id, media_type)

    # 1. Already cached: load it and return it, no requests at all
    if cache_file.exists():
        with open(cache_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data

    # 2. Fetch the main details
    details = fetch_details(tmdb_id, media_type)
    time.sleep(0.25)
    if details is None:
        return None

    data = {'details': details}

    # 3. TV shows: also fetch every season, in both languages
    if media_type == 'tv':
        season_numbers = [s['season_number'] for s in details['seasons']]
        seasons_en = fetch_seasons(tmdb_id, season_numbers, 'en-US')
        seasons_hu = fetch_seasons(tmdb_id, season_numbers, 'hu-HU')
        if seasons_en is None or seasons_hu is None:
            return None  # half a show is worse than none
        data['seasons_en'] = seasons_en
        data['seasons_hu'] = seasons_hu

    # 4. Everything succeeded: now it's safe to save
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    return data


def enrich(matched):
    """Fetch (or load from cache) and parse every matched title.

    Returns the parsed items, plus unmatched entries for titles whose fetch failed.
    """
    items = []
    failed = []
    total = len(matched)

    for i, match in enumerate(matched, start=1): 
        # Check before fetching: get_details() creates the cache file, so checking after would always say "cached"   
        cached = cache_path(match['tmdb_id'], match['media_type']).exists()
        print(f"Enriching {i}/{total}: {match['title']} ({'cached' if cached else 'fetching'})")
        
        data = get_details(match['tmdb_id'], match['media_type'])

        # a failed fetch isn't cached, so the next run tries again
        if data is None:
            print('    fetch failed, will retry on the next run')
            failed.append({
                'title': match['title'],
                'year': None,
                'source_folder': match['source_folder'],
                'source_path': match['source_path'],
                'media_type': match['media_type'],
                'reason': 'fetch_failed'
            })
        else:
            if match['media_type'] == 'movie':
                items.append(parse_movie(data, match))
            elif match['media_type'] == 'tv':
                items.append(parse_tv(data, match))

    return items, failed