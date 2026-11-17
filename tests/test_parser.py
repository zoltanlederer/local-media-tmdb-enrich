import pytest
from parser import empty_to_none, get_translation, pick_trailer, runtime_stats, parse_movie, parse_tv, parse_episodes


@pytest.mark.parametrize('text, expected', [
    ('  Dirty Jobs  ', 'Dirty Jobs'),
    ('', None),
    ('  ', None),
    (None, None),
])
def test_empty_to_none(text, expected):
    result = empty_to_none(text)
    assert result == expected


HU_AND_EN = {'translations': {'translations': [
    {'iso_639_1': 'en', 'data': {'title': 'Fast Five'}},
    {'iso_639_1': 'hu', 'data': {'title': 'Halálos iramban'}},
]}}

EN_ONLY = {'translations': {'translations': [
    {'iso_639_1': 'en', 'data': {'title': 'Fast Five'}},
]}}


@pytest.mark.parametrize('details, expected', [
    pytest.param(HU_AND_EN, {'title': 'Halálos iramban'}, id='hungarian-present'),
    pytest.param(EN_ONLY, {}, id='hungarian-missing'),
    pytest.param({}, {}, id='no-translations'),
])
def test_get_translation(details, expected):
    result = get_translation(details)
    assert result == expected


TRAILERS_EARLY = {'videos': {'results': [
    {'site': 'YouTube', 'type': 'Trailer', 'official': True,  'published_at': '2023-01-01', 'key': 'late'},
    {'site': 'YouTube', 'type': 'Trailer', 'official': False, 'published_at': '2010-01-01', 'key': 'unofficial'},
    {'site': 'YouTube', 'type': 'Trailer', 'official': True,  'published_at': '2011-01-01', 'key': 'early'},
]}}

TRAILERS_LATE = {'videos': {'results': [
    {'site': 'YouTube', 'type': 'Trailer', 'official': True,  'published_at': '2023-01-01', 'key': 'late'},
    {'site': 'YouTube', 'type': 'Trailer', 'official': False, 'published_at': '2010-01-01', 'key': 'unofficial'},
]}}

TRAILERS_UNOFFICIAL = {'videos': {'results': [
    {'site': 'YouTube', 'type': 'Trailer', 'official': False, 'published_at': '2010-01-01', 'key': 'unofficial'},
]}}

TRAILERS_VIMEO = {'videos': {'results': [
    {'site': 'Vimeo', 'type': 'Trailer', 'official': False, 'published_at': '2010-01-01', 'key': 'unofficial'},
]}}


@pytest.mark.parametrize('details, expected', [
    pytest.param(TRAILERS_EARLY, 'early', id='official-earliest-wins'),
    pytest.param(TRAILERS_LATE, 'late', id='official-preferred-over-earlier-unofficial'),
    pytest.param(TRAILERS_UNOFFICIAL, 'unofficial', id='unofficial-as-fallback'),
    pytest.param(TRAILERS_VIMEO, None, id='non-youtube-ignored'),
    pytest.param({}, None, id='no-videos'),
])
def test_pick_trailer(details, expected):
    result = pick_trailer(details)
    assert result == expected


SEASONS = {
    'season/0': {'season_number': 0, 'episodes': [{'runtime': 2}, {'runtime': 90}]},  # specials
    'season/1': {'season_number': 1, 'episodes': [{'runtime': 23}, {'runtime': 22}, {'runtime': 46}]},
    'season/2': {'season_number': 2, 'episodes': [{'runtime': 23}, {'runtime': None}]},  # one missing runtime
}


@pytest.mark.parametrize('seasons, expected', [
    pytest.param(SEASONS, {'average': 23, 'total': 114, 'per_season': {0: 92, 1: 91, 2: 23}}, id='specials-and-missing-skipped'),
    pytest.param({}, {'average': None, 'total': 0, 'per_season': {}}, id='empty-show'),
])
def test_runtime_stats(seasons, expected):
    result = runtime_stats(seasons)
    assert result == expected


SEASON = {'episodes': [
    {'episode_number': 1, 'name': 'Pilot', 'overview': 'Rachel leaves her fiancé.', 'air_date': '1994-09-22', 'runtime': 23, 'still_path': '/a.jpg'},
    {'episode_number': 2, 'name': 'The One with the Sonogram', 'overview': '', 'air_date': '1994-09-29', 'runtime': 23, 'still_path': None},
    {'episode_number': 3, 'name': 'The One with the Thumb', 'overview': 'Phoebe gets money.', 'air_date': '1994-10-06', 'runtime': 22, 'still_path': '/c.jpg'},
]}

SEASON_HU = {'episodes': [
    {'episode_number': 1, 'name': 'Randi vagy nem randi', 'overview': 'Rachel elhagyja a vőlegényét.'},
    {'episode_number': 3, 'name': 'A hüvelykujj', 'overview': ''},
]}


def test_parse_episodes_matches_hungarian_by_number():
    result = parse_episodes(SEASON, SEASON_HU)

    # episode 2 has no Hungarian twin, and episode 3 keeps its own title (no shifting)
    assert [episode['name_hu'] for episode in result] == ['Randi vagy nem randi', None, 'A hüvelykujj']


def test_parse_episodes_turns_blank_overviews_into_none():
    result = parse_episodes(SEASON, SEASON_HU)

    assert [episode['overview'] for episode in result] == ['Rachel leaves her fiancé.', None, 'Phoebe gets money.']
    assert [episode['overview_hu'] for episode in result] == ['Rachel elhagyja a vőlegényét.', None, None]


def test_parse_episodes_without_hungarian_season():
    result = parse_episodes(SEASON, {})

    assert len(result) == 3
    assert all(episode['name_hu'] is None for episode in result)  # all(…) is a built-in function that returns True if every item is true


MATCH = {'source_folder': 'Test folder', 'source_path': '/media/test'}


def test_parse_movie_with_almost_no_data():
    result = parse_movie({'details': {'id': 1}}, MATCH)

    assert result['media_type'] == 'movie'
    assert result['title'] is None
    assert result['genres'] == []
    assert result['collection'] is None


def test_parse_tv_with_almost_no_data():
    result = parse_tv({'details': {'id': 1}}, MATCH)

    assert result['media_type'] == 'tv'
    assert result['seasons'] == []
    assert result['runtime'] is None


def test_parse_movie_null_collection_becomes_none():
    result = parse_movie({'details': {'id': 13, 'belongs_to_collection': None}}, MATCH)

    assert result['collection'] is None


def test_parse_movie_collection_keeps_only_chosen_fields():
    details = {'id': 51497, 'belongs_to_collection': {
        'id': 9485,
        'name': 'The Fast and the Furious Collection',
        'poster_path': '/p.jpg',
        'backdrop_path': '/b.jpg',
        'extra': 'ignore me',  # a field TMDB might add one day: must not reach the output
    }}
    result = parse_movie({'details': details}, MATCH)

    assert result['collection'] == {
        'id': 9485,
        'name': 'The Fast and the Furious Collection',
        'poster_path': '/p.jpg',
        'backdrop_path': '/b.jpg',
    }


@pytest.mark.parametrize('details, expected', [
    pytest.param({'id': 1, 'release_date': '2011-04-20'}, 2011, id='date-gives-int-year'),
    pytest.param({'id': 1, 'release_date': ''}, None, id='empty-date'),
    pytest.param({'id': 1}, None, id='missing-date'),
])
def test_parse_movie_year_from_release_date(details, expected):
    result = parse_movie({'details': details}, MATCH)

    assert result['year'] == expected


def test_parse_tv_reads_its_own_fields():
    details = {
        'id': 1668,
        'name': 'Friends',
        'first_air_date': '1994-09-22',
        'external_ids': {'imdb_id': 'tt0108778', 'tvdb_id': 79168},
    }

    result = parse_tv({'details': details}, MATCH)

    assert result['title'] == 'Friends'
    assert result['release_date'] == '1994-09-22'
    assert result['year'] == 1994
    assert result['imdb_id'] == 'tt0108778'
    assert result['tvdb_id'] == 79168