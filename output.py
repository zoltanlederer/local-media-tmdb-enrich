import json
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
