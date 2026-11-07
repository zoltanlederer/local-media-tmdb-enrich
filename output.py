import json
import csv
from pathlib import Path
from datetime import datetime

FORMAT_VERSION = 1


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