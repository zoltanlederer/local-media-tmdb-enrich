# Local Media TMDB Enrich

**Turn a messy folder of movies and TV shows into clean, complete metadata.**

Scan your local movie and TV show folders, match every title to [TMDB](https://www.themoviedb.org/), and save the full metadata (including Hungarian translations) to one JSON or CSV file.

The output is plain JSON or CSV, so any app, script or database import can use it.

```
/path/to/Movies  ─┐                                 ┌─ exports/media.json
                  ├─► scan ─► match ─► enrich ─────►├─ exports/unmatched.csv
/path/to/TV      ─┘          (TMDB)   (TMDB+cache)  └─ user_data/manual_fix_matches.csv
```

## Features

- Finds movie and TV show folders in nested libraries (category folders, collections, actor folders, season folders…)
- Cleans messy release names (`Forrest.Gump.1994.REMASTERED.1080p.BluRay.x265-RARBG` → *Forrest Gump*, 1994)
- Handles folder names with two titles, like `Jóbarátok (Friends)` or `Bunyó karácsonyig - Troublemakers`
- Prefers an exact title match, so spin-offs don't steal the match (*Dirty Jobs* vs. *Dirty Jobs: Rowe'd Trip*)
- Fetches everything useful from TMDB in one go: details, cast and crew, keywords, trailers, images, age ratings, recommendations, similar titles, collections
- **Hungarian data**: title, overview, tagline, posters and logos, and for TV shows every season and episode in both English and Hungarian
- Caches every TMDB response, so later runs are fast and don't hit the API again
- A **fix list** for anything that couldn't be matched: fill in the TMDB ID once, and it's used on every run after that
- Reports duplicates (the same title in two folders) instead of silently dropping them

## Requirements

- Python 3.10 or newer
- A free TMDB account and its **API Read Access Token**

To get the token: log in at TMDB → *Settings* → *API* → copy the **API Read Access Token** (the long one, starting with `eyJ`). Not the shorter "API Key".

## Setup

```bash
git clone https://github.com/zoltanlederer/local-media-tmdb-enrich.git
cd local-media-tmdb-enrich

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp config.example.py config.py
```

Open `config.py` and paste your token into `TMDB_READ_TOKEN`.

`config.py` is in `.gitignore`, so your token is never committed.

## Usage

```bash
# Movies only
python3 main.py --movies "/path/to/Movies"

# TV shows only
python3 main.py --tv "/path/to/TV"

# Both (recommended: the output file always contains one complete run)
python3 main.py --movies "/path/to/Movies" --tv "/path/to/TV"

# CSV instead of JSON
python3 main.py --movies "/path/to/Movies" --tv "/path/to/TV" --format csv

# Overwrite existing output without asking (useful for unattended runs)
python3 main.py --movies "/path/to/Movies" --tv "/path/to/TV" --yes
```

| Option | Meaning |
|---|---|
| `--movies PATH` | Folder with your movies |
| `--tv PATH` | Folder with your TV shows |
| `--format json\|csv` | Output format (default: `json`) |
| `--yes` | Don't ask before overwriting an existing output file |

The flag decides the type: everything under `--movies` is searched as a movie, everything under `--tv` as a TV show. A folder name alone can't tell the two apart.

Before any slow work starts, the tool checks your token, your folders and the connection to TMDB, and stops with a clear message if something is wrong.

On **Windows**, use `python` instead of `python3`, and Windows-style paths:

```powershell
python main.py --movies "D:\Media\Movies" --tv "D:\Media\TV"
```

### Keeping the computer awake

A first run on a large library can take an hour. If the computer goes to sleep, the run stops. (Nothing is lost: everything fetched so far is cached, so just start it again.)

**macOS:** put `caffeinate -i` in front of the command. The Mac stays awake until the command finishes:

```bash
caffeinate -i python3 main.py --movies "/path/to/Movies" --tv "/path/to/TV" --yes
```

**Windows:** there's no built-in command for this. Either set *Settings → System → Power → Sleep* to **Never** for the duration of the run, or use the free [Microsoft PowerToys](https://learn.microsoft.com/windows/powertoys/) tool **Awake**, which keeps the PC awake with one click.

**Linux:** put `systemd-inhibit` in front of the command:

```bash
systemd-inhibit python3 main.py --movies "/path/to/Movies" --tv "/path/to/TV" --yes
```

## Output files

| File | What it is |
|---|---|
| `exports/media.json` (or `media.csv`) | Every matched title with its full metadata. **Overwritten on every run.** |
| `exports/unmatched.csv` | Every folder that didn't make it into the output, and why. **Overwritten on every run.** |
| `user_data/manual_fix_matches.csv` | Your fix list (see below). **Never overwritten**: new rows are only added. |
| `cache/movie/`, `cache/tv/` | Raw TMDB responses, one JSON file per title |

The three folders are created automatically on the first run.

### Reasons in `unmatched.csv`

| Reason | Meaning |
|---|---|
| `no_match` | TMDB found nothing for the cleaned title. Added to the fix list. |
| `duplicate` | The same TMDB title was already matched from another folder (a second copy, another version, another language). Each title appears once in the output. |
| `fetch_failed` | A network or TMDB error. It's tried again automatically on the next run. |

## How folders are detected

**Movies:** a movie folder is a folder that **directly contains a video file** (`.mkv`, `.mp4`, `.avi`, `.m4v`, `.iso`). How deep it is doesn't matter. Category folders, collection folders and cover folders only contain other folders or images, so they're skipped automatically.

**TV shows:** the tool finds every folder with video files, then **walks up** past season, episode and language folders until it reaches the show folder. Ten seasons of one show give one show. Recognized as season/episode/language folders:

- `Season 1`, `Season.1`, `Series 6`, `Évad 7`, `08. évad`, `Volume 03`
- `South.Park.S10…`, `Angel.S02E17…`, `8.Simple.Rules.S01.E02…`
- `Magyar`, `Angol`, `Hungarian`, `English` (also with a leading `!`)

A **range** like `S01-S10` or `Season 1-10` marks a complete-series pack. That folder is treated as the show.

## Ignoring folders and files

Edit `IGNORED_FOLDERS` in `config.py`. Matching ignores upper/lower case and how accents are stored. Three kinds of entries work:

```python
IGNORED_FOLDERS = [
    "Sample",                                   # a folder name, anywhere in the library
    "Harry Potter Collection/!Angol",           # Parent/Folder: only this folder inside that parent
    "Some.Bonus.Clip.2020.1080p.mkv",           # a file name: this video doesn't count
]
```

> **Careful:** an ignored folder is skipped **with everything inside it**. If a category folder like `Uncategorized` has a few loose videos you want to ignore, list the **file names**, not the folder. Otherwise every title inside the category disappears from the output.

## Fixing unmatched titles

After a run, open `user_data/manual_fix_matches.csv`:

| Column | Meaning |
|---|---|
| `source_folder` | The folder name on disk (don't change it) |
| `media_type` | `movie` or `tv`. You may change it: a TV show stored in your movie library can be fixed as `tv`. |
| `tmdb_id` | **Fill this in** |
| `searched_title` | What the tool searched for, as a hint |

To find the ID, search for the title on themoviedb.org and copy the **number from the URL**:

```
https://www.themoviedb.org/tv/873-columbo   →  873
```

Use the TMDB number, **not** the IMDb ID (`tt0060857`).

Leave `tmdb_id` empty for rows you don't want to fix. Run the tool again, and your filled-in titles are matched without searching.

If you edit the file in Excel or Numbers, save it as **CSV UTF-8 (comma-separated)**, or accented letters and columns may break.

## JSON format

```json
{
  "format_version": 1,
  "generated_at": "2026-11-23T20:15:42",
  "items": [ ... ]
}
```

- `generated_at`: when the file was written (local time, ISO 8601).
- `items`: every matched movie and TV show. Use `media_type` to tell them apart.

### `format_version`

`format_version` is the version number of **the file's structure** (which fields exist, what they're called, what type they are), not of the tool. It exists for programs that **read** this file, for example an app that imports it into its own database:

- It only goes up when a change would **break** a reader: a field is renamed or removed, a value changes type (e.g. `year` from text to a number), or the nesting changes.
- **Adding** a new field doesn't change it. A reader that doesn't know the new field can simply ignore it.
- A reader should check it before importing. If the number is higher than the reader knows, it should stop with a clear message instead of guessing, because the data may not mean what it expects.

The current version is `1`.

### A movie item

From a real run (shortened: long lists cut to a few entries):

```json
{
  "media_type": "movie",
  "tmdb_id": 51497,
  "source_folder": "04 Fast Five (2011) EXTENDED (1080p BluRay x265 HEVC 10bit AAC 7.1 Joy) [UTR]",
  "source_path": "/path/to/Movies/Fast & Furious (Film Series)/04 Fast Five (2011) EXTENDED (1080p BluRay x265 HEVC 10bit AAC 7.1 Joy) [UTR]",
  "original_language": "en",
  "overview": "Former cop Brian O'Conner partners with ex-con Dom Toretto on the opposite side of the law. Since Brian and Mia Toretto broke Dom out of custody, they've blown across many borders to elude authorities. Now backed into a corner in Rio de Janeiro, they must pull one last job in order to gain their freedom.",
  "overview_hu": "Amióta Brian és Mia Toretto kiszabadította Domot a fogságból, számos határon átsüvítettek, hogy kijátsszák a hatóságokat. Most Rio de Janeiróban húzták meg magukat, és el kell vállalniuk egy utolsó balhét, hogy elnyerjék szabadságukat.",
  "tagline": "Get the fifth gear.",
  "tagline_hu": null,
  "status": "Released",
  "genres": ["Action", "Thriller", "Crime"],
  "vote_average": 7.246,
  "vote_count": 9252,
  "poster_path": "/gEfQjjQwY7fh5bI4GlG0RrBu7Pz.jpg",
  "poster_path_hu": "/k1uVomVAMk3E6tADZtqXnkSuVGk.jpg",
  "backdrop_path": "/tQN9JEQ4N4aqej7O6AkQtt0dLpt.jpg",
  "logo_path": "/flzR8SPSafPeDHfDu1d8YgXsIgq.png",
  "logo_path_hu": null,
  "trailer_key": "uSDNZeRX_1Y",
  "recommendations": [13804, 168259, 136797],
  "similar": [11460, 11462, 11546],
  "imdb_id": "tt1596343",
  "title": "Fast Five",
  "title_hu": "Halálos iramban: Ötödik sebesség",
  "original_title": "Fast Five",
  "release_date": "2011-04-20",
  "year": 2011,
  "runtime": 131,
  "keywords": ["car race", "heist", "street race", "sequel"],
  "cast": [
    {
      "id": 12835,
      "name": "Vin Diesel",
      "character": "Dominic Toretto",
      "profile_path": "/nZdVry7lnUkE24PnXakok9okvL4.jpg"
    },
    {
      "id": 8167,
      "name": "Paul Walker",
      "character": "Brian O'Conner",
      "profile_path": "/q2PLqKHYCs35HR7QybaNPH3JT96.jpg"
    }
  ],
  "directors": [
    { "id": 58189, "name": "Justin Lin" }
  ],
  "collection": {
    "id": 9485,
    "name": "The Fast and the Furious Collection",
    "poster_path": "/zOCnMPoUxgJK1RFPfN4PcnT16gr.jpg",
    "backdrop_path": "/z5A5W3WYJc3UVEWljSGwdjDgQ0j.jpg"
  }
}
```

- `recommendations` and `similar` are TMDB IDs of other movies, in TMDB's order (up to 20 each).
- `cast` has up to 50 people, in billing order.
- `collection` is `null` when the movie isn't part of a series.

### A TV show item

TV items have the same shared fields as movies (`media_type` is `"tv"`, plus `source_folder`, `overview`, `genres`, images, `trailer_key`, `recommendations`…). Only the TV-specific part is shown here, from a real run (shortened):

```json
{
  "media_type": "tv",
  "tmdb_id": 1668,
  "imdb_id": "tt0108778",
  "tvdb_id": 79168,
  "title": "Friends",
  "title_hu": "Jóbarátok",
  "original_title": "Friends",
  "release_date": "1994-09-22",
  "year": 1994,
  "last_air_date": "2004-05-06",
  "number_of_seasons": 10,
  "number_of_episodes": 228,
  "runtime": 23,
  "total_runtime": 5452,
  "keywords": ["new york city", "roommates"],
  "cast": [
    {
      "id": 4491,
      "name": "Jennifer Aniston",
      "character": "Rachel Green",
      "episode_count": 228,
      "profile_path": "/PBSCmHDFdCMBhjx0EbXpTw4Z94.jpg"
    }
  ],
  "creators": [
    { "id": 163461, "name": "Marta Kauffman" },
    { "id": 1216352, "name": "David Crane" }
  ],
  "seasons": [
    {
      "season_number": 1,
      "name": "Season 1",
      "name_hu": "1. évad",
      "overview": null,
      "overview_hu": "Hat barát New Yorkban – Monica, Ross, Rachel, Chandler, Joey és Phoebe – próbál boldogulni a munka, a párkapcsolatok és a húszas éveik mindennapjai között.",
      "air_date": "1994-09-22",
      "poster_path": "/odCW88Cq5hAF0ZFVOkeJmeQv1nV.jpg",
      "total_runtime": 550,
      "episodes": [
        {
          "episode_number": 1,
          "name": "Pilot",
          "name_hu": "Randi vagy nem randi, ez itt a kérdés",
          "overview": "After Rachel leaves her fiancé at the altar, she moves in with Monica and finds that independence is not so easy, particularly without Daddy's credit cards.",
          "overview_hu": "Rachel elhagyja a vőlegényét, Barry-t az esküvő napján és beköltözik Monica-hoz.",
          "air_date": "1994-09-22",
          "runtime": 23,
          "still_path": "/Slm6IczgHJWpR4dIv33IRtNrq5.jpg"
        }
      ]
    }
  ]
}
```

- `runtime` is the **median** episode length in minutes, and `total_runtime` is the sum of all episodes. Specials (season 0) don't count towards either.
- `seasons` includes season 0 (specials) when TMDB has one, sorted by `season_number`.
- `cast` uses the whole show's cast, with `episode_count` for how many episodes each person appears in.

### Notes for all items

- Missing data is `null` (or `[]` for lists), never an empty string.
- `title_hu` can be `null` when TMDB has no Hungarian title. Fall back to `title`.
- Image paths are TMDB paths. Full URL: `https://image.tmdb.org/t/p/w500` + the path.
- `trailer_key` is a YouTube video ID: `https://www.youtube.com/watch?v=` + the key.

The CSV export has one row per title with the most important columns. Lists (genres, cast…) become comma-separated text. Seasons and episodes are JSON-only.

## Real-world numbers

From a library of about 3,200 movie folders and 480 TV shows on a network drive:

| | |
|---|---|
| First run (empty cache) | ~1 hour |
| Later runs (cached) | ~30–40 minutes, almost all of it TMDB search |
| Cache size | ~725 MB (about 0.12 MB per movie, 0.8 MB per TV show) |
| Matched automatically | ~93% |

Most of the time is spent waiting for the network, not computing.

## Running the tests

```bash
pytest        # a short summary: one dot per passing test
pytest -v     # verbose: every test listed by name, with PASSED or FAILED
```

The tests need a `config.py` to exist (copy `config.example.py`, no real token needed). They use no network and don't touch your real files.

## Limitations

- **Matching is a best guess.** When there's no exact title match, the first search result is used. Spot-check unusual titles.
- **Search results aren't cached**, so every run searches every folder again. Only the details are cached.
- **The cache only grows** and is never refreshed. Delete a file in `cache/` to re-fetch that title, or the whole folder to start fresh.
- **Duplicates are reported, not merged.** The output contains each TMDB title once.
- Some naming styles still need the fix list: actor names in front of the title, Hungarian titles typed without accents, `A.K.A.` names, roman numerals.
- `source_path` contains your full local paths. Keep that in mind before sharing `media.json`.
- Developed and tested on macOS. It uses only cross-platform Python, so Windows and Linux should work, but they haven't been tested with a real library yet.

## Project structure

```
main.py             command line, validation, runs the steps in order
scanner.py          finds movie and TV folders, cleans folder names
matcher.py          picks the right TMDB result for each folder
enricher.py         gets full details from the cache or TMDB
tmdb.py             TMDB API requests (token, retries, timeouts)
parser.py           turns TMDB data into the output format
output.py           writes media.json / media.csv / unmatched.csv
manual_matches.py   reads and updates the fix list
tests/              pytest tests
```

## License

MIT. See [LICENSE](LICENSE).

This product uses the TMDB API but is not endorsed or certified by TMDB.