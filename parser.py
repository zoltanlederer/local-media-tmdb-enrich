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


def pick_trailer(details):
    """Return the YouTube key of the best trailer, or None if there isn't one.
    Prefers official trailers; among those, the earliest published one,
    because it's closest to the original release (later ones are often re-releases).
    """
    # 1. Collect only YouTube trailers (no featurettes, bloopers, theme songs)
    trailers = []
    for entry in details.get('videos', {}).get('results', []):
        if entry['site'] == 'YouTube' and entry['type'] == 'Trailer':
            trailers.append(entry)

    if not trailers:
        return None

    # 2. Prefer official trailers, but fall back to unofficial ones if that's all there is
    official = [entry for entry in trailers if entry['official']]
    candidates = official if official else trailers

    # 3. The earliest one: ISO 8601 date strings sort in time order, so min() works directly
    earliest = min(candidates, key=lambda t: t['published_at'])
    return earliest['key']


def pick_image(images, language):
    """Return the file path of the first (highest-voted) image in the given language, or None."""
    for entry in images:
        if entry['iso_639_1'] == language:
            return entry['file_path']
    return None


if __name__ == '__main__':
    with open('cache/tv/1668.json', encoding='utf-8') as f:
        data = json.load(f)
    hu = get_translation(data['details'])
    print(empty_to_none(hu.get('name')))      # Jóbarátok
    print(empty_to_none(hu.get('tagline')))   # None (it's "" in TMDB)

    print(pick_trailer(data['details']))                                   # H29XSxoKp80 (the official 2014 trailer)
    print(pick_image(data['details']['images']['posters'], 'hu'))          # a Hungarian poster path
    print(pick_image(data['details']['images']['logos'], 'en'))            # an English logo path