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