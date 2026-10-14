import argparse
from pathlib import Path
from scanner import get_folders

parser = argparse.ArgumentParser(description='Scan local media and enrich metadata from TMDB')
parser.add_argument('--movies', help='Path to the movies folder')
parser.add_argument('--tv', help='Path to the TV shows folder')
parser.add_argument('--format', default='json', choices=['json', 'csv'], help='Output format: json (default) or csv')
args = parser.parse_args()

movies = args.movies
tv = args.tv
output_format = args.format

if (not movies) and (not tv):
    parser.error('Provide at least one folder: --movies and/or --tv')

if movies and (not Path(movies).is_dir()):
    parser.error(f"--movies is not a folder: {movies}")

if tv and (not Path(tv).is_dir()):
    parser.error(f"--tv is not a folder: {tv}")

if movies:
    movie_folders = get_folders(movies)    
    print(f"Movies: {len(movie_folders)} folders")

if tv:
    tv_folders = get_folders(tv)
    print(f"TV shows: {len(tv_folders)} folders")
