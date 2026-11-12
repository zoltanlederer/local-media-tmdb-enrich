import requests
import time
from config import TMDB_READ_TOKEN, TMDB_BASE_URL

# Sent as a header, not in the URL, so the token never appears in error messages
HEADERS = {'Authorization': f'Bearer {TMDB_READ_TOKEN}'}

# Extra sections to include in each details request (one request instead of many)
APPEND = {
    'movie': 'credits,keywords,videos,translations,images,recommendations,similar,release_dates',
    'tv': 'aggregate_credits,keywords,videos,external_ids,translations,images,recommendations,similar,content_ratings',
}


def check_token():
    """Return True if TMDB accepts the token, so a bad token can stop the run before any work."""
    try:
        response = requests.get(f'{TMDB_BASE_URL}/authentication', headers=HEADERS)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False
    

def search_tmdb(title, media_type, year=None):
    """Search TMDB for a movie or TV show by title and optional year. Returns a dictionary or None.""" 
    try:
        params = {"query": title}
        if year:
            params["year"] = year
        response = requests.get(f'{TMDB_BASE_URL}/search/{media_type}', params=params, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as error: 
        print(f"Something went wrong: {error}")
        return None


def fetch_details(tmdb_id, media_type):
    """Fetch full details for a movie or TV show from TMDB in one API call.

    The extra sections included in the response (credits, keywords, videos, etc.)
    are defined in APPEND, separately for movies and TV shows.
    Returns the full API response as a dictionary, or None if the request fails.
    media_type should be either 'movie' or 'tv'.
    """
    try:
        url = f'{TMDB_BASE_URL}/{media_type}/{tmdb_id}'
        params = {
            'append_to_response': APPEND[media_type],  # which sections, depending on movie or TV
            'include_image_language': 'hu,en,null',   # filter for the images section: Hungarian, English, and no-text images
        }
        response = requests.get(url, params=params, headers=HEADERS)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as error:
        print(f"Something went wrong: {error}")
        return None


def fetch_seasons(tmdb_id, season_numbers, language):
    """Fetch full season data (including episodes) for a TV show.

    TMDB allows at most 20 appended items per request, so the seasons are
    requested in chunks of 20. Returns a dict like {'season/0': {...}, 'season/1': {...}},
    or None if any request fails (half a show's episodes would be misleading).
    """
    url = f'{TMDB_BASE_URL}/tv/{tmdb_id}'
    seasons = {}

    # i jumps 0, 20, 40... so each slice is one chunk of up to 20 season numbers
    for i in range(0, len(season_numbers), 20):
        chunk = season_numbers[i:i + 20]
        params = {
            'append_to_response': ','.join(f'season/{n}' for n in chunk),  # 'season/0,season/1,...'
            'language': language,
        }
        try:
            response = requests.get(url, params=params, headers=HEADERS)
            response.raise_for_status()
        except requests.exceptions.RequestException as error:
            print(f"Something went wrong: {error}")
            return None

        # The response also contains the show's normal fields; keep only the season sections
        for key, value in response.json().items():
            if key.startswith('season/'):
                seasons[key] = value

        time.sleep(0.25)  # a long show makes several requests in a row

    return seasons