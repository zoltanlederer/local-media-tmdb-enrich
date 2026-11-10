import csv
from pathlib import Path

MANUAL_MATCHES_FILE = Path('user_data') / 'manual_fix_matches.csv'


def load_manual_matches(path):
    """Return the user's manual matches as a dict keyed by source folder.

    Only rows with a TMDB ID filled in are returned. A missing file means no manual matches yet.
    """
    if not Path(path).exists():
        return {}

    result = {}

    with open(path, 'r', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            tmdb_id = row['tmdb_id'].strip()
            if not tmdb_id:
                continue
            if not tmdb_id.isdigit():
                raise SystemExit(f"{path}: tmdb_id must be a number, got '{tmdb_id}' for {row['source_folder']}")

            media_type = row['media_type'].strip().lower()
            if media_type not in ('movie', 'tv'):
                raise SystemExit(f"{path}: media_type must be 'movie' or 'tv', got '{row['media_type']}' for {row['source_folder']}")
            
            result[row['source_folder']] = {
                'tmdb_id': int(tmdb_id),
                'media_type': media_type,
            }

    return result


if __name__ == '__main__':
    print(load_manual_matches(MANUAL_MATCHES_FILE))