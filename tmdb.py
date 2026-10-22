import requests
from config import TMDB_API_KEY, TMDB_BASE_URL

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
    """Fetch movie or TV show data from TMDB including credits, keywords and videos in one API call.

    Returns the full API response as a dictionary, or None if the request fails.
    media_type should be either 'movie' or 'tv'.
    """
    try:
        url = f'{TMDB_BASE_URL}/{media_type}/{tmdb_id}'
        params = {'api_key': TMDB_API_KEY, 'append_to_response': 'credits,keywords,videos'}
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as error:
        print(f"Something went wrong: {error}")
        return None