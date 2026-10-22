"""
Local Media TMDB Enrich
Scans local movie and TV folders, matches each folder to a TMDB ID,
and (in later steps) enriches every title with full TMDB metadata.
"""

import argparse
import time
import unicodedata
import re
import json
from pathlib import Path
from scanner import get_folders, clean_folder_name, candidate_titles
from tmdb import search_tmdb, fetch_details

def normalize(text):
    """Lowercase the text, remove punctuation, and strip spaces at the ends."""
    return re.sub(r'[^\w\s]', '', text).lower().strip()


def is_exact_match(candidate, result):
    """Return True if any of the result's titles equals the candidate, ignoring case and punctuation."""
    target = normalize(candidate) # normalise once, not four times
    for field in ('title', 'original_title', 'name', 'original_name'):
        value = result.get(field) # None if this result doesn't have the field
        if value and normalize(value) == target:
            return True
    return False


def search_with_retry(title, year, media_type):
    """Search TMDB with the year, and retry once without it if nothing was found."""
    results = search_tmdb(title=title, year=year, media_type=media_type)
    time.sleep(0.25)  # stay well under TMDB's rate limit

    # The year in a folder name is sometimes wrong, so retry once without it.
    # The 'is not None' check comes first, so len() never runs on a failed request.
    if results is not None and len(results['results']) == 0:
        results = search_tmdb(title=title, year=None, media_type=media_type)
        time.sleep(0.25)
    
    return results


def find_best_match(candidates, year, media_type):
    """Try each candidate title and return (result, reason).

    An exact title match wins immediately. Otherwise the first result of the
    first candidate that found anything is used as a fallback.
    """
    fallback = None
    request_failed = False

    for candidate in candidates:
        response = search_with_retry(candidate, year, media_type)

        if response is None:
            request_failed = True # remember it, but other candidates may still work
            continue

       # Check every result, not just the first: the exact one may be further down
        for result in response['results']:
            if is_exact_match(candidate, result):
                return result, None

        # No exact match: keep the first result of the first candidate that found anything
        if fallback is None and response['results']:
            fallback = response['results'][0]

    if fallback:
        return fallback, None
    if request_failed:
        return None, 'fetch_failed'
    return None, 'no_match'


def match_folders(folders, media_type):
    """Search TMDB for each folder and sort the results into matched and unmatched lists.

    Each folder name can produce several candidate titles (e.g. a Hungarian and an
    English title); find_best_match() tries them and prefers an exact title match.
    Every folder ends up in exactly one of the two lists, so no title is lost silently.
    Unmatched entries keep a 'reason' so the user knows what to fix.
    """
    matched = []
    unmatched = []
    seen = set()  # (media_type, tmdb_id) pairs already matched, to catch duplicate folders

    total = len(folders)
    for i, folder in enumerate(folders, start=1):
        print(f"Scanning {i}/{total}: {folder.name}")
        clean_folder = clean_folder_name(folder.name)
        # macOS can store accented letters differently from what TMDB expects; NFC makes them consistent
        title = unicodedata.normalize('NFC', clean_folder['title'])

        # Folder names often hold two titles, so try each one, English-looking first
        candidates = candidate_titles(title)
        # All the search decisions (retry, exact match, fallback) live in find_best_match()
        result, reason = find_best_match(candidates, clean_folder['year'], media_type)

        # result is None only when no candidate found anything; reason says why
        if result is None:
            unmatched.append({
                'title': title,  # the cleaned title shows the user what was actually searched
                'year': clean_folder['year'],
                'source_folder': folder.name,
                'media_type': media_type,
                'reason': reason  # 'no_match' or 'fetch_failed', decided by find_best_match()
            })
        else:
            key = (media_type, result['id'])
            if key in seen:
                # Same title already matched from another folder: report it instead of dropping it
                unmatched.append({
                    'title': title,
                    'year': clean_folder['year'],
                    'source_folder': folder.name,
                    'media_type': media_type,
                    'reason': 'duplicate'
                })
            else:
                seen.add(key)
                matched.append({
                    'title': result.get('title') or result.get('name'),  # movies use 'title', TV shows use 'name'
                    'tmdb_id': result['id'],
                    'source_folder': folder.name,  # the original name, so the user can find the folder on disk
                    'media_type': media_type
                })

    return matched, unmatched


# --- Command-line arguments ---
parser = argparse.ArgumentParser(description='Scan local media and enrich metadata from TMDB')
parser.add_argument('--movies', help='Path to the movies folder')
parser.add_argument('--tv', help='Path to the TV shows folder')
parser.add_argument('--format', default='json', choices=['json', 'csv'], help='Output format: json (default) or csv')
args = parser.parse_args()

movies = args.movies
tv = args.tv
output_format = args.format

# --- Validation: check all input before any slow work starts (fail fast) ---
if (not movies) and (not tv):
    parser.error('Provide at least one folder: --movies and/or --tv')

# 'movies and ...' guards against Path(None), which would crash when --movies isn't given
if movies and (not Path(movies).is_dir()):
    parser.error(f"--movies is not a folder: {movies}")

if tv and (not Path(tv).is_dir()):
    parser.error(f"--tv is not a folder: {tv}")

# --- Scan and match ---
# The flag decides the media type, because a folder name alone can't tell a movie from a TV show
if movies:
    movie_folders = get_folders(movies)
    print(f"Movies: {len(movie_folders)} folders")
    movie_matched, movie_unmatched = match_folders(movie_folders, 'movie')
    # print('MOVIE MATCHED:', movie_matched)
    # print('MOVIE UNMATCHED:', movie_unmatched)
    print('MOVIE MATCHED:', movie_matched[0])
    
    details = fetch_details(movie_matched[0]['tmdb_id'], 'movie')
    with open('sample_movie.json', 'w', encoding='utf-8') as f:
        json.dump(details, f, indent=2, ensure_ascii=False)

if tv:
    tv_folders = get_folders(tv)
    print(f"TV shows: {len(tv_folders)} folders")
    tv_matched, tv_unmatched = match_folders(tv_folders, 'tv')
    # print('TV MATCHED:', tv_matched)
    # print('TV UNMATCHED:', tv_unmatched)
    print('TV MATCHED:', tv_matched[10])

    details = fetch_details(tv_matched[10]['tmdb_id'], 'tv')
    with open('sample_tv.json', 'w', encoding='utf-8') as f:
        json.dump(details, f, indent=2, ensure_ascii=False)