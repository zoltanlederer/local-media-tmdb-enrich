import json
import csv
from pathlib import Path
from datetime import datetime

FORMAT_VERSION = 1
CSV_COLUMNS = [
    'media_type', 'tmdb_id', 'imdb_id', 'tvdb_id', 'title', 'title_hu', 'original_title',
    'year', 'release_date', 'runtime', 'total_runtime',
    'number_of_seasons', 'number_of_episodes', 'status',
    'genres', 'vote_average', 'vote_count',
    'directors', 'creators', 'cast', 'collection', 'keywords',
    'overview', 'overview_hu', 'source_folder', 'source_path',
]


def names(people):
    """Join the names of a list of people into one comma-separated string."""
    return ', '.join(person['name'] for person in people)


def flatten_item(item):
    """Turn one item into a flat row for the CSV: lists become comma-separated text."""
    return {
        'media_type': item['media_type'],
        'tmdb_id': item['tmdb_id'],
        'imdb_id': item['imdb_id'],
        'tvdb_id': item.get('tvdb_id'),
        'title': item['title'],
        'title_hu': item['title_hu'],
        'original_title': item['original_title'],
        'year': item['year'],
        'release_date': item['release_date'],
        'runtime': item['runtime'],
        'total_runtime': item.get('total_runtime'),
        'number_of_seasons': item.get('number_of_seasons'),
        'number_of_episodes': item.get('number_of_episodes'),
        'status': item['status'],
        'genres': ', '.join(item['genres']),
        'vote_average': item['vote_average'],
        'vote_count': item['vote_count'],
        'directors': names(item.get('directors', [])),   # only the names
        'creators': names(item.get('creators', [])),
        'cast': names(item.get('cast', [])),
        'collection': (item.get('collection') or {}).get('name'),
        'keywords': ', '.join(item['keywords']),
        'overview': item['overview'],
        'overview_hu': item['overview_hu'],
        'source_folder': item['source_folder'],
        'source_path': item['source_path']
    }


def write_json(items, path):
    """Write the items to a JSON file, wrapped with the format version and the creation time."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)  # make sure the exports folder exists
    
    data = {
        'format_version': FORMAT_VERSION,
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'items': items
    }

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)  # indented, because people open this file


def write_unmatched(unmatched, path):
    """Write the unmatched folders to a CSV, so the user can review and fix them.

    The columns are fixed, so the file has the same layout even when the list is empty.
    """
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['title', 'year', 'media_type', 'reason', 'source_folder', 'source_path']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unmatched)


def write_csv(items, path):
    """Write the items as a flat CSV overview, one row per title. Lists become comma-separated text; seasons and episodes are left out (they’re only in the JSON)."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=CSV_COLUMNS )
        writer.writeheader()
        writer.writerows(flatten_item(item) for item in items)