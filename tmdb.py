import requests
from config import TMDB_API_KEY

def search_tmdb(title, media_type, year=None):
    """ Search TMDB for a movie or TV show by title and optional year. Returns a dictionary or None. """
    base_url = 'https://api.themoviedb.org/3/search/'   
    try:
        params = {"api_key": TMDB_API_KEY, "query": title}
        if year:
            params["year"] = year
        response = requests.get(base_url + media_type, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as error: 
        print(f"Something went wrong: {error}")
        return None
