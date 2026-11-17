import pytest
from manual_matches import load_manual_matches


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