import pytest
import main
from main import normalize, is_exact_match, find_best_match


@pytest.mark.parametrize('text, expected', [
    ('Dirty Jobs', 'dirty jobs'),
    ("Don't Trust the B---- in Apartment 23", 'dont trust the b in apartment 23'),
    ('  Columbo  ', 'columbo'),
])
def test_normalize(text, expected):
    result = normalize(text)
    assert result == expected


@pytest.mark.parametrize('candidate, tmdb_result, expected', [
    pytest.param('Dirty Jobs', {'name': "Dirty Jobs: Rowe'd Trip"}, False, id='spin-off-not-exact'),
    pytest.param('Dirty Jobs', {'name': 'Dirty Jobs'}, True, id='same-name'),
    pytest.param('Sabrina The Teenage Witch', {'name': 'Sabrina, the Teenage Witch'}, True, id='punctuation-ignored'),
    pytest.param('Fast Five', {'title': 'Fast Five'}, True, id='movie-title-field'),
    pytest.param('Jóbarátok', {'name': 'Friends', 'original_name': 'Jóbarátok'}, True, id='original-name-field'),
    pytest.param('Columbo', {}, False, id='no-title-fields'),
])
def test_is_exact_match(candidate, tmdb_result, expected):
    result = is_exact_match(candidate, tmdb_result)
    assert result == expected


def test_find_best_match_prefers_exact_match_further_down(monkeypatch):
    # A fake search: always returns the same two results, without any network request
    def fake_search(title, year, media_type):
        return {'results': [
            {'id': 105977, 'name': "Dirty Jobs: Rowe'd Trip"},
            {'id': 2584, 'name': 'Dirty Jobs'},
        ]}

    monkeypatch.setattr(main, 'search_with_retry', fake_search)

    result, reason = find_best_match(['Dirty Jobs'], None, 'tv')

    assert result['id'] == 2584   # the exact match, not the first result
    assert reason is None


def test_find_best_match_falls_back_to_first_result(monkeypatch):
    def fake_search(title, year, media_type):
        return {'results': [
            {'id': 105977, 'name': "Dirty Jobs: Rowe'd Trip"},
        ]}

    monkeypatch.setattr(main, 'search_with_retry', fake_search)

    result, reason = find_best_match(['Dirty Jobs'], None, 'tv')

    assert result['id'] == 105977
    assert reason is None


def test_find_best_match_reports_failed_request(monkeypatch):
    def fake_search(title, year, media_type):
        return None

    monkeypatch.setattr(main, 'search_with_retry', fake_search)

    result, reason = find_best_match(['Dirty Jobs'], None, 'tv')

    assert result is None
    assert reason == 'fetch_failed'


def test_find_best_match_reports_no_match(monkeypatch):
    def fake_search(title, year, media_type):
        return {'results': []}

    monkeypatch.setattr(main, 'search_with_retry', fake_search)

    result, reason = find_best_match(['Dirty Jobs'], None, 'tv')

    assert result is None
    assert reason == 'no_match'