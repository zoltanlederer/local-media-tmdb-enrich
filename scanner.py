import re
from pathlib import Path
from config import IGNORED_FOLDERS

def get_folders(root_folder):
    """
    Walk through all subfolders recursively, skip anything in the
    IGNORED_FOLDERS list and season folders detected via regex,
    and return a list of folder paths to process.
    """
    folders = []
    for folder in Path(root_folder).rglob('*'):
        # Season folders (e.g. "Season 01", "Season 01 (2010–11)", "S01") are filtered here via regex, not in IGNORED_FOLDERS
        if (folder.is_dir() 
            and folder.name.lower() not in [f.lower() for f in IGNORED_FOLDERS]
            and not re.match(r'^Season\s*\d*', folder.name, re.IGNORECASE)
            and not re.match(r'^S\d{2}$', folder.name, re.IGNORECASE)):
                folders.append(folder)

    return folders

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
        else:
            title = folder[:year.start()] # keep the string from the beginning until the first index of the year
        year = year.group() # extract the matched year string from the match object
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

    return sorted(candidates, key=has_hungarian_letters)


if __name__ == '__main__':
    tests = [
        "Ausztrál kamionosok (Outback Truckers",
        "Világunk történelme - Andrew Marr's History of the World",
        "Friends (Extended, Exclusive & Unseen",
        "Hawaii Five-0",
        "Columbo",
    ]
    for t in tests:
        print(t, '→', candidate_titles(t))

