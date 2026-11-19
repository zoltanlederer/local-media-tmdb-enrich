"""
Local Media TMDB Enrich
Scans local movie and TV folders, matches each folder to a TMDB ID,
enriches every title with full TMDB metadata, and writes it to a JSON file.
"""

import argparse
import time
import json
from pathlib import Path
from config import TMDB_READ_TOKEN
from scanner import get_folders
from tmdb import fetch_details, fetch_seasons, check_token
from parser import parse_movie, parse_tv
from output import write_json, write_unmatched, write_csv
from manual_matches import load_manual_matches, add_unmatched, MANUAL_MATCHES_FILE
from matcher import match_folders


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


def main():
    """Parse the command line, validate the input, and run the scan from start to finish."""
    # --- Command-line arguments ---
    parser = argparse.ArgumentParser(description='Scan local media and enrich metadata from TMDB')
    parser.add_argument('--movies', help='Path to the movies folder')
    parser.add_argument('--tv', help='Path to the TV shows folder')
    parser.add_argument('--format', default='json', choices=['json', 'csv'], help='Output format: json (default) or csv')
    parser.add_argument('--yes', action='store_true', help='Overwrite existing output files without asking')
    args = parser.parse_args()

    movies = args.movies
    tv = args.tv
    output_format = args.format

    # --- Validation: check all input before any slow work starts (fail fast) ---
    if not TMDB_READ_TOKEN or TMDB_READ_TOKEN.startswith('YOUR_'):
        parser.error('Add your TMDB Read Access Token to config.py (see config.example.py)')

    if (not movies) and (not tv):
        parser.error('Provide at least one folder: --movies and/or --tv')

    # 'movies and ...' guards against Path(None), which would crash when --movies isn't given
    if movies and (not Path(movies).is_dir()):
        parser.error(f"--movies is not a folder: {movies}")

    if tv and (not Path(tv).is_dir()):
        parser.error(f"--tv is not a folder: {tv}")

    # network check
    print('Checking the TMDB connection...')
    if not check_token():
        parser.error('TMDB rejected the token, or TMDB is unreachable. Check TMDB_READ_TOKEN in config.py and your internet connection.')

    unmatched_file = Path('exports') / 'unmatched.csv'
    output_file = Path('exports') / f'media.{output_format}'  # media.json or media.csv
    if output_file.exists() and not args.yes:
        answer = input(f'{output_file} already exists. Overwrite it? [y/N] ')
        if answer.strip().lower() != 'y':
            print('Cancelled. Nothing was changed.')
            raise SystemExit

    manual_matches = load_manual_matches(MANUAL_MATCHES_FILE)

    # --- Scan and match ---
    # The flag decides the media type, because a folder name alone can't tell a movie from a TV show
    movie_matched, movie_unmatched = [], []   # empty by default, in case --movies isn't given
    tv_matched, tv_unmatched = [], []

    if movies:
        movie_folders = get_folders(movies)
        print(f"Movies: {len(movie_folders)} folders")
        movie_matched, movie_unmatched = match_folders(movie_folders, 'movie', manual_matches)

    if tv:
        tv_folders = get_folders(tv)
        print(f"TV shows: {len(tv_folders)} folders")
        tv_matched, tv_unmatched = match_folders(tv_folders, 'tv', manual_matches)

    # --- Enrich: fetch or load each title, and parse it into the output format ---
    items, failed = enrich(movie_matched + tv_matched)
    unmatched = movie_unmatched + tv_unmatched + failed

    write_unmatched(unmatched, unmatched_file)
    add_unmatched(MANUAL_MATCHES_FILE, unmatched)

    if output_format == 'csv':
        write_csv(items, output_file)
    else:
        write_json(items, output_file)

    total_movies = sum(1 for item in items if item['media_type'] == 'movie')
    total_tv = sum(1 for item in items if item['media_type'] == 'tv')
    total_unmatched = len(unmatched)

    print(60 * '-')
    print('Done')
    print(f"  {'Movies:':<12}{total_movies}")
    print(f"  {'TV shows:':<12}{total_tv}")
    print(f"  {'Unmatched:':<12}{total_unmatched}" + (f"  → {unmatched_file}" if total_unmatched else ''))
    print(f"  {'Fix list:':<12}{MANUAL_MATCHES_FILE}")
    print(f"  {'Output:':<12}{output_file}")
    print(60 * '-')


if __name__ == '__main__':
    main()