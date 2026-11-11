import csv
from pathlib import Path

MANUAL_MATCHES_FILE = Path('user_data') / 'manual_fix_matches.csv'
FIELDNAMES = ['source_folder', 'media_type', 'tmdb_id', 'searched_title']


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


def add_unmatched(path, unmatched):
    """Append no_match folders that aren't in the file yet, with an empty tmdb_id for the user to fill in.

    Existing rows are never changed, so the user's edits are safe.
    """
    path = Path(path)
    is_new = not path.exists()

    # Read: which folders are already in the file (filled in or not)?
    existing = set()
    if not is_new:
        with open(path, 'r', encoding='utf-8-sig') as csvfile:
            existing = {row['source_folder'] for row in csv.DictReader(csvfile)}

    # Pick: only no_match folders that aren't listed yet
    new_rows = [
        {
            'source_folder': entry['source_folder'],
            'media_type': entry['media_type'],
            'tmdb_id': '',                       # left empty for the user to fill in
            'searched_title': entry['title'],    # helps the user search TMDB's website
        }
        for entry in unmatched
        if entry['reason'] == 'no_match' and entry['source_folder'] not in existing
    ]

    if not new_rows:
        return  # nothing new: don't touch the file at all

    # Write: append, so existing rows stay exactly as the user left them
    path.parent.mkdir(parents=True, exist_ok=True)
    encoding = 'utf-8-sig' if is_new else 'utf-8'  # the BOM belongs only at the very start of a file
    with open(path, 'a', newline='', encoding=encoding) as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
        if is_new:
            writer.writeheader()
        writer.writerows(new_rows)


if __name__ == '__main__':
    test_unmatched = [
        {'title': 'Fake Show', 'source_folder': 'Fake.Show.S01', 'media_type': 'tv', 'reason': 'no_match'},
        {'title': 'Forrest Gump', 'source_folder': 'Forrest Gump 1994 2160p', 'media_type': 'movie', 'reason': 'duplicate'},
    ]
    add_unmatched(MANUAL_MATCHES_FILE, test_unmatched)
    print(load_manual_matches(MANUAL_MATCHES_FILE))