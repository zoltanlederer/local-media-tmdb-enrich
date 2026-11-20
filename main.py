"""
Local Media TMDB Enrich
Scans local movie and TV folders, matches each folder to a TMDB ID,
enriches every title with full TMDB metadata, and writes it to a JSON or CSV file.
"""

import argparse
from pathlib import Path
from config import TMDB_READ_TOKEN
from scanner import get_folders, get_movie_folders
from tmdb import check_token
from output import write_json, write_unmatched, write_csv
from manual_matches import load_manual_matches, add_unmatched, MANUAL_MATCHES_FILE
from matcher import match_folders
from enricher import enrich


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
        print('Finding movie folders...')
        movie_folders = get_movie_folders(movies)
        print(f"Movie folders: {len(movie_folders)}")
        movie_matched, movie_unmatched = match_folders(movie_folders, 'movie', manual_matches)

    if tv:
        print('Finding TV folders...')
        tv_folders = get_folders(tv)
        print(f"TV shows folders: {len(tv_folders)}")
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