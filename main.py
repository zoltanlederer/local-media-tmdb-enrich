import argparse

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

print('movies:', movies)
print('tv:', tv)
print('output_format:', output_format)