import requests
from config import TMDB_API_KEY, TMDB_BASE_URL

# Extra sections to include in each details request (one request instead of many)
APPEND = {
    'movie': 'credits,keywords,videos,translations,images,recommendations,similar',
    'tv': 'aggregate_credits,keywords,videos,external_ids,translations,images,recommendations,similar',
}

def search_tmdb(title, media_type, year=None):
    """ Search TMDB for a movie or TV show by title and optional year. Returns a dictionary or None. """ 
    try:
        params = {"api_key": TMDB_API_KEY, "query": title}
        if year:
            params["year"] = year
        response = requests.get(f'{TMDB_BASE_URL}/search/{media_type}', params=params)
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
            'api_key': TMDB_API_KEY,
            'append_to_response': APPEND[media_type],  # which sections, depending on movie or TV
            'include_image_language': 'hu,en,null',   # filter for the images section: Hungarian, English, and no-text images
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as error:
        print(f"Something went wrong: {error}")
        return None