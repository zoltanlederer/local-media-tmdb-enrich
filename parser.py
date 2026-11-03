import json
import statistics

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


def runtime_stats(seasons):
    """Return average (median), total and per-season runtimes in minutes.

    The average is the median, so double-length episodes don't pull it up.
    Specials (season 0) are kept out of average and total.
    """
    runtimes = []       # every regular episode, for the average and total
    per_season = {}     # season number → minutes

    for season in seasons.values():
        number = season['season_number']
        season_runtimes = [episode['runtime'] for episode in season['episodes'] if episode.get('runtime') ]
        per_season[number] = sum(season_runtimes)

        if number != 0:
            runtimes.extend(season_runtimes)  # add them all to the main list            

    return {
        'average': round(statistics.median(runtimes)) if runtimes else None,  # Median: sort all the values and take the middle one
        'total': sum(runtimes),
        'per_season': per_season,
    }
            

def parse_common(details, match):
    """Return the fields that movies and TV shows read the same way."""
    hu = get_translation(details)
    images = details.get('images', {})

    return {
        'media_type': None,
        'tmdb_id': details['id'],
        'source_folder': match['source_folder'],
        'source_path': match['source_path'],
        'original_language': details.get('original_language'),
        'overview': empty_to_none(details.get('overview')),
        'overview_hu': empty_to_none(hu.get('overview')),
        'tagline': empty_to_none(details.get('tagline')),
        'tagline_hu': empty_to_none(hu.get('tagline')),
        'status': details.get('status'),
        'genres': [genre['name'] for genre in details.get('genres', [])],
        'vote_average': details.get('vote_average'),
        'vote_count': details.get('vote_count'),
        'poster_path': details.get('poster_path'),
        'poster_path_hu': pick_image(images.get('posters', []), 'hu'),
        'backdrop_path': details.get('backdrop_path'),
        'logo_path': pick_image(images.get('logos', []), 'en'),
        'logo_path_hu': pick_image(images.get('logos', []), 'hu'),
        'trailer_key': pick_trailer(details),
        'recommendations': [r['id'] for r in details.get('recommendations', {}).get('results', [])],
        'similar': [r['id'] for r in details.get('similar', {}).get('results', [])],
    }


def parse_movie(data, match):
    """Turn one cached movie into a dictionary in the output format.
    
    match is the entry from the matched list, which holds the folder info.
    """
    details = data['details']
    hu = get_translation(details)
    release_date = empty_to_none(details.get('release_date'))
    credits = details.get('credits', {})
    crew = credits.get('crew', [])
    cast = credits.get('cast', [])
    collection = details.get('belongs_to_collection') or {}  # null in TMDB → {} so .get() is safe

    return parse_common(details, match) | {
        'media_type': 'movie',
        'imdb_id': details.get('imdb_id'),
        'title': details.get('title'),
        'title_hu': empty_to_none(hu.get('title')),
        'original_title': details.get('original_title'),
        'release_date': release_date,
        'year': int(release_date[:4]) if release_date else None,
        'runtime': details.get('runtime'),
        'keywords': [keyword['name'] for keyword in details.get('keywords', {}).get('keywords', [])],
        'cast': [
            {
                'id': person['id'],
                'name': person['name'],
                'character': person.get('character'),
                'profile_path': person.get('profile_path'),  # None when TMDB has no photo
            }
            for person in cast[:10]  # already sorted by billing order
        ],
        'directors': [
            {'id': person['id'], 'name': person['name']}
            for person in crew if person.get('job') == 'Director'
        ],
        'collection': {
            'id': collection.get('id'),
            'name': collection.get('name'),
            'poster_path': collection.get('poster_path'),
            'backdrop_path': collection.get('backdrop_path'),
        } if collection else None
    }


def parse_tv(data, match):
    """Turn one cached TV show into a dictionary in the output format.
    
    match is the entry from the matched list, which holds the folder info.
    """
    details = data['details']
    hu = get_translation(details)
    release_date = empty_to_none(details.get('first_air_date'))
    credits = details.get('credits', {})
    crew = credits.get('crew', [])
    cast = credits.get('cast', [])
    collection = details.get('belongs_to_collection') or {}  # null in TMDB → {} so .get() is safe
    # runtime = 

    return parse_common(details, match) | {
        'media_type': 'tv',
        'imdb_id': details['external_ids']['imdb_id'],
        'tvdb_id': details['external_ids']['tvdb_id'],
        'title': details.get('name'),
        'title_hu': empty_to_none(hu.get('name')),
        'original_title': details.get('original_name'),
        'release_date': release_date,
        'year': int(release_date[:4]) if release_date else None,
        'last_air_date': empty_to_none(details.get('last_air_date')),
        'number_of_seasons': details.get('number_of_seasons'),
        'number_of_episodes': details.get('number_of_episodes'),
        'runtime': details.get('runtime'),
        'keywords': [keyword['name'] for keyword in details.get('keywords', {}).get('keywords', [])],
        'cast': [
            {
                'id': person['id'],
                'name': person['name'],
                'character': person.get('character'),
                'profile_path': person.get('profile_path'),  # None when TMDB has no photo
            }
            for person in cast[:10]  # already sorted by billing order
        ],
        'directors': [
            {'id': person['id'], 'name': person['name']}
            for person in crew if person.get('job') == 'Director'
        ],
        'collection': {
            'id': collection.get('id'),
            'name': collection.get('name'),
            'poster_path': collection.get('poster_path'),
            'backdrop_path': collection.get('backdrop_path'),
        } if collection else None
    }


# def parse_movie(data, match):
#     """Turn one cached movie into a dictionary in the output format.
    
#     match is the entry from the matched list, which holds the folder info.
#     """
#     details = data['details']
#     hu = get_translation(details)
#     release_date = empty_to_none(details.get('release_date'))
#     credits = details.get('credits', {})
#     crew = credits.get('crew', [])
#     cast = credits.get('cast', [])
#     images = details.get('images', {})
#     collection = details.get('belongs_to_collection') or {}  # null in TMDB → {} so .get() is safe

#     return {
#         'media_type': 'movie',
#         'tmdb_id': details['id'],
#         'imdb_id': details.get('imdb_id'),
#         'source_folder': match['source_folder'],
#         'source_path': match['source_path'],
#         'title': details.get('title'),
#         'title_hu': empty_to_none(hu.get('title')),
#         'original_title': details.get('original_title'),
#         'original_language': details.get('original_language'),
#         'overview': empty_to_none(details.get('overview')),
#         'overview_hu': empty_to_none(hu.get('overview')),
#         'tagline': empty_to_none(details.get('tagline')),
#         'tagline_hu': empty_to_none(hu.get('tagline')),
#         'release_date': release_date,
#         'year': int(release_date[:4]) if release_date else None,
#         'runtime': details.get('runtime'),
#         'status': details.get('status'),
#         'genres': [genre['name'] for genre in details.get('genres', [])],
#         'keywords': [keyword['name'] for keyword in details.get('keywords', {}).get('keywords', [])],
#         'vote_average': details.get('vote_average'),
#         'vote_count': details.get('vote_count'),
#         'cast': [
#             {
#                 'id': person['id'],
#                 'name': person['name'],
#                 'character': person.get('character'),
#                 'profile_path': person.get('profile_path'),  # None when TMDB has no photo
#             }
#             for person in cast[:10]  # already sorted by billing order
#         ],
#         'directors': [
#             {'id': person['id'], 'name': person['name']}
#             for person in crew if person.get('job') == 'Director'
#         ],
#         'poster_path': details.get('poster_path'),
#         'poster_path_hu': pick_image(images.get('posters', []), 'hu'),
#         'backdrop_path': details.get('backdrop_path'),
#         'logo_path': pick_image(images.get('logos', []), 'en'),
#         'logo_path_hu': pick_image(images.get('logos', []), 'hu'),
#         'trailer_key': pick_trailer(details),
#         'collection': {
#             'id': collection.get('id'),
#             'name': collection.get('name'),
#             'poster_path': collection.get('poster_path'),
#             'backdrop_path': collection.get('backdrop_path'),
#         } if collection else None,
#         'recommendations': [r['id'] for r in details.get('recommendations', {}).get('results', [])],
#         'similar': [r['id'] for r in details.get('similar', {}).get('results', [])],
#     }


if __name__ == '__main__':
    with open('cache/movie/51497.json', encoding='utf-8') as f:
        movie = json.load(f)
    test_match = {'source_folder': 'Fast Five test', 'source_path': '/media/movies/Fast Five test'}
    print(json.dumps(parse_movie(movie, test_match), indent=2, ensure_ascii=False))
    print(parse_movie({'details': {'id': 1}}, test_match))
