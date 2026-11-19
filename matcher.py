"""
Match each scanned folder to a TMDB title.

Tries every candidate title from the folder name, prefers an exact title match,
and sorts the folders into matched and unmatched lists. Manual matches from the
fix list skip the search.
"""

import unicodedata
import time
import re
from tmdb import search_tmdb, fetch_details, fetch_seasons, check_token
from scanner import get_folders, clean_folder_name, candidate_titles



def normalize(text):
    """Lowercase the text, remove punctuation, and strip spaces at the ends."""
    return re.sub(r'[^\w\s]', '', text).lower().strip()


def is_exact_match(candidate, result):
    """Return True if any of the result's titles equals the candidate, ignoring case and punctuation."""
    target = normalize(candidate) # normalise once, not four times
    for field in ('title', 'original_title', 'name', 'original_name'):
        value = result.get(field) # None if this result doesn't have the field
        if value and normalize(value) == target:
            return True
    return False


def search_with_retry(title, year, media_type):
    """Search TMDB with the year, and retry once without it if nothing was found."""
    results = search_tmdb(title=title, year=year, media_type=media_type)
    time.sleep(0.25)  # stay well under TMDB's rate limit

    # The year in a folder name is sometimes wrong, so retry once without it.
    # The 'is not None' check comes first, so len() never runs on a failed request.
    if results is not None and len(results['results']) == 0:
        results = search_tmdb(title=title, year=None, media_type=media_type)
        time.sleep(0.25)
    
    return results


def find_best_match(candidates, year, media_type):
    """Try each candidate title and return (result, reason).

    An exact title match wins immediately. Otherwise the first result of the
    first candidate that found anything is used as a fallback.
    """
    fallback = None
    request_failed = False

    for candidate in candidates:
        response = search_with_retry(candidate, year, media_type)

        if response is None:
            request_failed = True # remember it, but other candidates may still work
            continue

        # Check every result, not just the first: the exact one may be further down
        for result in response['results']:
            if is_exact_match(candidate, result):
                return result, None

        # No exact match: keep the first result of the first candidate that found anything
        if fallback is None and response['results']:
            fallback = response['results'][0]

    if fallback:
        return fallback, None
    if request_failed:
        return None, 'fetch_failed'
    return None, 'no_match'


def match_folders(folders, media_type, manual_matches):
    """Search TMDB for each folder and sort the results into matched and unmatched lists.

    Each folder name can produce several candidate titles (e.g. a Hungarian and an
    English title); find_best_match() tries them and prefers an exact title match.
    Every folder ends up in exactly one of the two lists, so no title is lost silently.
    Unmatched entries keep a 'reason' so the user knows what to fix.
    Folders listed in the manual matches file skip the search and use the user’s TMDB ID and type.
    """
    matched = []
    unmatched = []
    seen = set()  # (media_type, tmdb_id) pairs already matched, to catch duplicate folders

    total = len(folders)
    for i, folder in enumerate(folders, start=1):
        print(f"Scanning {i}/{total}: {folder.name}")

        # The user's manual match wins: no search needed
        if folder.name in manual_matches:
            manual = manual_matches[folder.name]
            key = (manual['media_type'], manual['tmdb_id'])
            if key not in seen:
                seen.add(key)
                matched.append({
                    'title': folder.name,  # the real title comes from TMDB when the details are parsed
                    'tmdb_id': manual['tmdb_id'],
                    'source_folder': folder.name,
                    'source_path': str(folder.resolve()),
                    'media_type': manual['media_type'],  # the user's type, which may differ from the folder's flag
                })
                print('    manual match')
            continue  # skip the search for this folder

        clean_folder = clean_folder_name(folder.name)
        # macOS can store accented letters differently from what TMDB expects; NFC makes them consistent
        title = unicodedata.normalize('NFC', clean_folder['title'])

        # Folder names often hold two titles, so try each one, English-looking first
        candidates = candidate_titles(title)
        # All the search decisions (retry, exact match, fallback) live in find_best_match()
        result, reason = find_best_match(candidates, clean_folder['year'], media_type)

        # result is None only when no candidate found anything; reason says why
        if result is None:
            unmatched.append({
                'title': title,  # the cleaned title shows the user what was actually searched
                'year': clean_folder['year'],
                'source_folder': folder.name,
                'source_path': str(folder.resolve()),
                'media_type': media_type,
                'reason': reason  # 'no_match' or 'fetch_failed', decided by find_best_match()
            })
        else:
            key = (media_type, result['id'])
            if key in seen:
                # Same title already matched from another folder: report it instead of dropping it
                unmatched.append({
                    'title': title,
                    'year': clean_folder['year'],
                    'source_folder': folder.name,
                    'source_path': str(folder.resolve()),
                    'media_type': media_type,
                    'reason': 'duplicate'
                })
            else:
                seen.add(key)
                matched.append({
                    'title': result.get('title') or result.get('name'),  # movies use 'title', TV shows use 'name'
                    'tmdb_id': result['id'],
                    'source_folder': folder.name,  # the original name, so the user can find the folder on disk
                    'source_path': str(folder.resolve()),  # full path, so MediaHome can find the folder on disk
                    'media_type': media_type
                })

    return matched, unmatched