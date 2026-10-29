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


def parse_movie(data, source_folder):
    """Turn one cached movie into a dictionary in the output format."""
    details = data['details']
    hu = get_translation(details)
    release_date = empty_to_none(details.get('release_date'))

    return {
        'media_type': 'movie',
        'tmdb_id': details['id'],
        'imdb_id': details.get('imdb_id'),
        'source_folder': source_folder,
        'title': details.get('title'),
        'title_hu': empty_to_none(hu.get('title')),
        'original_title': details.get('original_title'),
        'original_language': details.get('original_language'),
        'overview': empty_to_none(details.get('overview')),
        'overview_hu': empty_to_none(hu.get('overview')),
        'tagline': empty_to_none(details.get('tagline')),
        'tagline_hu': empty_to_none(hu.get('tagline')),
        'release_date': release_date,
        'year': int(release_date[:4]) if release_date else None,
        'runtime': details.get('runtime'),
        'status': details.get('status'),
        'genres': [genre['name'] for genre in details.get('genres', [])],
        'keywords': [keyword['name'] for keyword in details.get('keywords', {}).get('keywords', [])],
        'vote_average': details.get('vote_average'),
        'vote_count': details.get('vote_count')
    }


if __name__ == '__main__':
    with open('cache/movie/51497.json', encoding='utf-8') as f:
        movie = json.load(f)
    print(json.dumps(parse_movie(movie, 'test_data_movie'), indent=2, ensure_ascii=False))
    print(parse_movie({'details': {'id': 1}}, 'empty test'))
