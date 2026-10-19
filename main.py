"""
Local Media TMDB Enrich
Scans local movie and TV folders, matches each folder to a TMDB ID,
and (in later steps) enriches every title with full TMDB metadata.
"""

import argparse
import time
import unicodedata
from pathlib import Path
from scanner import get_folders, clean_folder_name
from tmdb import search_tmdb

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
    

def match_folders(folders, media_type):
    """Search TMDB for each folder and sort the results into matched and unmatched lists.

    Every folder ends up in exactly one of the two lists, so no title is lost silently.
    Unmatched entries keep a 'reason' so the user knows what to fix.
    """
    matched = []
    unmatched = []

    total = len(folders)
    for i, folder in enumerate(folders, start=1):
        print(f"Scanning {i}/{total}: {folder.name}")
        clean_folder = clean_folder_name(folder.name)
        # macOS can store accented letters differently from what TMDB expects; NFC makes them consistent
        title = unicodedata.normalize('NFC', clean_folder['title'])

        results = search_with_retry(title, clean_folder['year'], media_type)

        # Decide once, based on the final result, so every folder lands in exactly one list
        if results is None:
            unmatched.append({
                'title': title,  # the cleaned title shows the user what was actually searched
                'year': clean_folder['year'],
                'source_folder': folder.name,
                'media_type': media_type,
                'reason': 'fetch_failed'
            })
        elif len(results['results']) == 0:
            unmatched.append({
                'title': title,
                'year': clean_folder['year'],
                'source_folder': folder.name,
                'media_type': media_type,
                'reason': 'no_match'
            })
        else:
            first = results['results'][0]  # TMDB sorts by relevance, so the first result is the best guess
            matched.append({
                'title': first.get('title') or first.get('name'),  # movies use 'title', TV shows use 'name'
                'tmdb_id': first['id'],
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
    print('MOVIE MATCHED:', movie_matched)
    print('MOVIE UNMATCHED:', movie_unmatched)

if tv:
    tv_folders = get_folders(tv)
    print(f"TV shows: {len(tv_folders)} folders")
    tv_matched, tv_unmatched = match_folders(tv_folders, 'tv')
    print('TV MATCHED:', tv_matched)
    print('TV UNMATCHED:', tv_unmatched)