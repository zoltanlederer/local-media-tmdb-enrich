"""
Find media folders on disk and turn their messy names into searchable titles.

Movie folders are found by the video files they contain; TV folders by name, skipping season folders.
Release junk (quality, codecs, groups) is stripped from folder names, and names that hold two titles are split into candidates.
"""

import re
import os
import unicodedata
from pathlib import Path
from config import IGNORED_FOLDERS


VIDEO_EXTENSIONS = {'.mkv', '.mp4', '.avi', '.m4v', '.iso'}
LANGUAGE_FOLDERS = {'magyar', 'angol', 'hungarian', 'english'}


def ignore_key(text):
    """Return the text in the form used for ignore-list comparisons: NFC-normalized and lowercase."""
    return unicodedata.normalize('NFC', text).lower()


def is_season_folder(name):
    """Return True if the folder name looks like a season, episode or language folder inside a show."""
    text = ignore_key(name)   # lowercase + NFC, so 'Évad' matches however macOS stored the accent

    # 1. A range ('S01-S10', 'Season 1-11') means a complete-series pack: that's the show itself.
    #    This check must come first, because the season checks below would match inside a range.
    if re.search(r's\d{2}\s*-\s*s?\d{2}', text) or re.search(r'(season|series)[\s._]*\d+\s*-\s*\d+', text):
        return False

    # 2. Language folders inside a show: 'Magyar', '!Angol', 'Hungarian'
    if text.lstrip('!') in LANGUAGE_FOLDERS:
        return True

    # 3. A season word followed by a number: 'Season 1', 'Évad 7', 'Scrubs Season 2', 'Volume 03',
    #    also with dots or underscores in between ('Silicon.Valley.Season.1') and the British 'Series 6'
    if re.search(r'\b(season|series|évad|volume)[\s._]*\d+', text):
        return True

    # 4. A number followed by 'évad': 'Dallas 08. évad'
    if re.search(r'\b\d+\.?\s*évad\b', text):
        return True

    # 5. A season token, optionally with an episode: 'S10', 'S02E17', 'S01.E02'
    if re.search(r'\bs\d{2}(\.?e\d{2})?\b', text):
        return True

    return False


def get_movie_folders(root_folder):
    """Return every folder that directly contains a video file, skipping ignored folders and files."""
    ignored = {ignore_key(name) for name in IGNORED_FOLDERS}
    folders = []

    for dirpath, dirnames, filenames in os.walk(root_folder):
        parent = Path(dirpath).name   # the current folder's own name, e.g. 'Harry Potter Collection'

        # Prune: keep only the subfolders that aren't ignored.
        # Changing dirnames in place ([:]) tells os.walk not to go into the removed ones.
        dirnames[:] = [
            name for name in dirnames
            if ignore_key(name) not in ignored
            and ignore_key(f'{parent}/{name}') not in ignored
        ]
        dirnames.sort()   # in place, so os.walk visits subfolders alphabetically: same order every run

        # Video check: does this folder directly contain a video file that isn't ignored?
        has_video = False
        for filename in filenames:
            if Path(filename).suffix.lower() in VIDEO_EXTENSIONS and ignore_key(filename) not in ignored:
                has_video = True
                break

        # If yes: add the folder as a Path
        if has_video:
            folders.append(Path(dirpath))

    return folders


def get_tv_folders(root_folder):
    """Return one folder per TV show: video folders walked up past season, episode and language folders."""
    root = Path(root_folder)
    shows = set()

    for folder in get_movie_folders(root_folder):
        # Walk up while the folder is a season, episode or language folder,
        # e.g. 'Jim Szerint A Világ/Évad 7' → 'Jim Szerint A Világ'.
        # 'show != root' stops the walk at the top, so it never climbs out of the TV library.
        show = folder
        while is_season_folder(show.name) and show != root:
            show = show.parent

        # The root itself is never a show (loose videos, or a season folder right under the root)
        if show != root:
            shows.add(show)   # a set: ten seasons of one show give one entry

    return sorted(shows)   # same order every run


def clean_folder_name(folder_name):
    """ Clean up a messy folder name and return a dictionary with title and year """

    folder = re.sub(r'^\d{1,3}\s*[-\s]\s*', '', folder_name) # strip number prefixes like 01, 09 - from the start. Matches 1 to 3 digits at the start, optionally followed by space, hyphen, space
    year = re.search(r'\b\d{4}\b', folder) # find any 4-digit number
  
    if year and (1910 <= int(year.group()) <= 2090): # Check if it is a year
        if year.start() == 0: # If the year is at the start, extract the title from after it
            title = folder[year.end():] # (everything after the year) keep only the string from the end index of the year until the end of the string
            second_year = re.search(r'\b\d{4}\b', title) # checking if there is a year in the string again
            if second_year: # cut title at the second year to remove remaining junk
                title = title[:second_year.start()] # then keep the string from the beginning until the first index of the year
            year = year.group()
        else:
            # Is the year directly followed by another one? e.g. 'Blade.Runner.2049.2017'
            next_year = re.match(r'[. ](\d{4})\b', folder[year.end():])
            if next_year and (1910 <= int(next_year.group(1)) <= 2090):  # e.g. 'Blade.Runner.2049.2017': 2049 is part of the title
                title = folder[:year.end()]   # the first number belongs to the title: 'Blade.Runner.2049'
                year = next_year.group(1)     # the second one is the real year: '2017'
            else:
                title = folder[:year.start()] # normal case: everything before the year
                year = year.group()
    else:
        title = folder
        year = None

    # find quality markers like 1080p — everything from this point onwards is junk
    quality_markers = re.search(
        r'\b(1080p|720p|480p|2160p|4K|3D|S\d{2}|WEBRip|WEB-DL|BDRip|DVDRip|DVBRip|XviD|COMPLETE)\b',
        title,
        re.IGNORECASE
    ) 

    if quality_markers:
        title = title[:quality_markers.start()] # keep the string from the beginning until the first index of the quality marker

    title = title.replace('.', ' ') # replace dots with spaces
    title = title.strip('- ()') # strip leading/trailing junk characters
    title = title.strip() # strip any remaining whitespace

    return {'title': title, 'year': year}


def has_hungarian_letters(text):
    """Return True if the text contains Hungarian accented letters."""
    for char in text.lower():
        if char in 'áéíóöőúüű':
            return True
    return False


def candidate_titles(title):
    """Split a cleaned title into possible search titles, using brackets and ' - ' as separators."""
    # Step 1: split off the bracket text, if there is any
    match = re.search(r'\(([^)]*)\)?', title)
    if match:
        parts = [title[:match.start()], match.group(1)]  # outside and inside
    else:
        parts = [title]

    # Step 2: split every part on ' - ' (with spaces, so 'Hawaii Five-0' stays whole)
    candidates = []
    for part in parts:
        for piece in part.split(' - '):
            piece = piece.strip()
            if piece:  # skip empty strings, e.g. when a title starts with '('
                candidates.append(piece)

    # Step 3: uploaders sometimes add ' 1' to the first film of a series ('Grown Ups 1'),
    # so also try the title without it. The original stays first, in case the 1 is real.
    extra = [candidate[:-2] for candidate in candidates if candidate.endswith(' 1')]
    candidates = candidates + extra

    return sorted(candidates, key=has_hungarian_letters)