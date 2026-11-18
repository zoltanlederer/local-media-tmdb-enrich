import pytest
import csv
from manual_matches import load_manual_matches, add_unmatched


def test_load_manual_matches_missing_file_returns_empty_dict(tmp_path):
    path = tmp_path / 'missing.csv'

    result = load_manual_matches(path)

    assert result == {}


def test_load_manual_matches_with_a_valid_row(tmp_path):
    path = tmp_path / 'manual_fix_matches.csv'
    path.write_text("source_folder,media_type,tmdb_id,searched_title\nColumbo,tv,873,Columbo\n", encoding='utf-8')

    result = load_manual_matches(path)

    assert result == {'Columbo': {'tmdb_id': 873, 'media_type': 'tv'}}


def test_load_manual_matches_blank_tmdb_id_skipped(tmp_path):
    path = tmp_path / 'manual_fix_matches.csv'
    path.write_text("source_folder,media_type,tmdb_id,searched_title\nColumbo,tv,873,Columbo\nSome Show,tv,,\n", encoding='utf-8')

    result = load_manual_matches(path)

    assert result == {'Columbo': {'tmdb_id': 873, 'media_type': 'tv'}}
    assert 'Some Show' not in result


def test_load_manual_matches_non_numeric_id_stops(tmp_path):
    path = tmp_path / 'manual_fix_matches.csv'
    path.write_text('source_folder,media_type,tmdb_id,searched_title\nColumbo,tv,tt0060857,Columbo\n', encoding='utf-8')

    with pytest.raises(SystemExit, match='Columbo'):
        load_manual_matches(path)


def test_load_manual_matches_invalid_media_type_stops(tmp_path):
    path = tmp_path / 'manual_fix_matches.csv'
    path.write_text('source_folder,media_type,tmdb_id,searched_title\nThe Fast and the Furious,film,9799,The Fast and the Furious\n', encoding='utf-8')

    with pytest.raises(SystemExit, match='The Fast and the Furious'):
        load_manual_matches(path)


def test_load_manual_matches_media_type_is_normalized(tmp_path):
    path = tmp_path / 'manual_fix_matches.csv'
    path.write_text('source_folder,media_type,tmdb_id,searched_title\nColumbo, TV ,873,Columbo\n', encoding='utf-8')

    result = load_manual_matches(path)

    assert result == {'Columbo': {'tmdb_id': 873, 'media_type': 'tv'}}


def test_add_unmatched_new_file(tmp_path):
    path = tmp_path / 'manual_fix_matches.csv'

    unmatched = [{
        'title': 'Columbo',
        'year': 1971,
        'source_folder': 'Columbo',
        'source_path': '/media/tv/Columbo',
        'media_type': 'tv',
        'reason': 'no_match'
    }]

    add_unmatched(path, unmatched)

    with open(path, encoding='utf-8-sig') as file:
        rows = list(csv.DictReader(file))

    assert rows == [
        {'source_folder': 'Columbo', 'media_type': 'tv', 'tmdb_id': '', 'searched_title': 'Columbo'},
    ]


def test_add_unmatched_only_no_match_added(tmp_path):
    path = tmp_path / 'manual_fix_matches.csv'

    unmatched = [
        {
            'title': 'Friends',
            'year': 1994,
            'source_folder': 'Friends',
            'source_path': '/media/tv/Friends',
            'media_type': 'tv',
            'reason': 'fetch_failed',
        },
        {
            'title': 'Columbo',
            'year': 1971,
            'source_folder': 'Columbo',
            'source_path': '/media/tv/Columbo',
            'media_type': 'tv',
            'reason': 'no_match',
        },
    ]

    add_unmatched(path, unmatched)

    with open(path, encoding='utf-8-sig') as file:
        rows = list(csv.DictReader(file))

    assert rows == [
        {'source_folder': 'Columbo', 'media_type': 'tv', 'tmdb_id': '', 'searched_title': 'Columbo'},
    ]


def test_add_unmatched_an_existing_file_is_respected(tmp_path):
    path = tmp_path / 'manual_fix_matches.csv'
    path.write_text("source_folder,media_type,tmdb_id,searched_title\nColumbo,tv,873,Columbo\n", encoding='utf-8-sig')

    unmatched = [
        {
            'title': 'Some Show',
            'year': 1990,
            'source_folder': 'Some Show',
            'source_path': '/media/tv/Some_Show',
            'media_type': 'tv',
            'reason': 'no_match',
        },
        {
            'title': 'Columbo',
            'year': 1971,
            'source_folder': 'Columbo',
            'source_path': '/media/tv/Columbo',
            'media_type': 'tv',
            'reason': 'no_match',
        },
    ]

    add_unmatched(path, unmatched)

    with open(path, encoding='utf-8-sig') as file:
        rows = list(csv.DictReader(file))

    assert rows == [
        {'source_folder': 'Columbo', 'media_type': 'tv', 'tmdb_id': '873', 'searched_title': 'Columbo'},
        {'source_folder': 'Some Show', 'media_type': 'tv', 'tmdb_id': '', 'searched_title': 'Some Show'},
    ]