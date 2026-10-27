import json

def empty_to_none(text):
    """Return None for missing or blank text, otherwise the text without surrounding spaces."""
    if text is None or not text.strip():
        return None
    return text.strip()

def get_translation(details, language='hu'):
    """Return the translation data for a language, or an empty dict if TMDB has none."""
    for entry in details.get('translations', {}).get('translations', []):
        if entry['iso_639_1'] == language:
            return entry['data']
    return {}

if __name__ == '__main__':
    with open('cache/tv/1668.json', encoding='utf-8') as f:
        data = json.load(f)
    hu = get_translation(data['details'])
    print(empty_to_none(hu.get('name')))      # Jóbarátok
    print(empty_to_none(hu.get('tagline')))   # None (it's "" in TMDB)