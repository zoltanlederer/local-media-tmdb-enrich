import pytest
import scanner
from scanner import clean_folder_name, candidate_titles, has_hungarian_letters, get_movie_folders, ignore_key, is_season_folder


@pytest.mark.parametrize('folder_name, expected_title, expected_year', [
    ('Forrest.Gump.1994.REMASTERED.1080p.BluRay.x265-RARBG', 'Forrest Gump', '1994'),
    ('Forrest Gump 1994 2160p', 'Forrest Gump', '1994'),
    ('Back to the Future 1999', 'Back to the Future', '1999'),
    ('Zzz Fake Movie Title 9999', 'Zzz Fake Movie Title 9999', None),  # 9999 isn't a valid year
    ('Some.Show.COMPLETE.WEBRip.x264', 'Some Show', None),
    ('Mi.szuksegunk.a.Holdra.2011.DVBRip.x264.AC3.Hun-MrX', 'Mi szuksegunk a Holdra', '2011'),
    ('Border.Security.Australias.Frontline.S13.720p.RTLP.WEB-DL.AAC2.0.H.264.HUN-FULCRUM-750kbps',
     'Border Security Australias Frontline', None),
    ('04 Fast Five (2011) EXTENDED (1080p BluRay x265 HEVC 10bit AAC 7.1 Joy)', 'Fast Five', '2011'),
    ('2001 Harry.Potter.and.the.Sorcerers.Stone.2001.Open.Matte.1080p.AMZN.WEB-DL.DD.5.1.H.264', 'Harry Potter and the Sorcerers Stone', '2001'),
    ('Sabrina.The.Teenage.Witch.S01-S07.DVDRip.XviD.Hun.Eng', 'Sabrina The Teenage Witch', None),
    ('Black.Doves.COMPLETE.WEBRip.x264', 'Black Doves', None),
    ('Back to the Future', 'Back to the Future', None),
    ('How I Met Your Mother (2005-2014)', 'How I Met Your Mother', '2005'),
    ('Blade.Runner.2049.2017.1080p.BluRay.x265-RARBG', 'Blade Runner 2049', '2017'),
    ('Godzilla.2000.1999.JAPANESE.1080p.BluRay.x265-VXT', 'Godzilla 2000', '1999'),
])
def test_clean_folder_name(folder_name, expected_title, expected_year):
    result = clean_folder_name(folder_name)
    assert result == {'title': expected_title, 'year': expected_year}


@pytest.mark.parametrize('title, expected', [
    pytest.param('Ausztrál kamionosok (Outback Truckers',
                ['Outback Truckers', 'Ausztrál kamionosok'],
                id='bracket-english-first'),
    pytest.param("Világunk történelme - Andrew Marr's History of the World",
                ["Andrew Marr's History of the World", 'Világunk történelme'],
                id='dash-split-english-first'),
    pytest.param('Friends (Extended, Exclusive & Unseen',
                ['Friends', 'Extended, Exclusive & Unseen'],
                id='bracket-junk-keeps-order'),
    pytest.param('Hawaii Five-0',
                ['Hawaii Five-0'],
                id='dash-without-spaces-not-split'),
    pytest.param('Columbo',
                ['Columbo'],
                id='single-title'),
    pytest.param('Grown Ups 1',
                ['Grown Ups 1', 'Grown Ups'],
                id='trailing-one-also-tried-without'),
])
def test_candidate_titles(title, expected):
    result = candidate_titles(title)
    assert result == expected


@pytest.mark.parametrize('text, expected', [
    ('Jóbarátok', True),
    ('Friends', False),
    pytest.param('ÉLET', True, id='uppercase-accent'),
    pytest.param('', False, id='empty-text'),
])
def test_has_hungarian_letters(text, expected):
    result = has_hungarian_letters(text)
    assert result == expected


def make_file(path):
    """Create an empty file, and any missing folders on the way to it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()


def test_get_movie_folders(tmp_path, monkeypatch):
    monkeypatch.setattr(scanner, 'IGNORED_FOLDERS', ['Sample', 'Collection/Angol'])

    make_file(tmp_path / 'Collection' / 'Movie A' / 'movie.mkv')
    make_file(tmp_path / 'Collection' / 'folder.jpg')
    make_file(tmp_path / 'Movie B' / 'MOVIE.MP4')
    make_file(tmp_path / 'Collection' / 'Movie A' / 'Sample' / 'sample.mkv')
    make_file(tmp_path / 'Collection' / 'Angol' / 'Movie C' / 'movie.mkv')
    make_file(tmp_path / 'Covers' / 'front.jpg')

    result = get_movie_folders(tmp_path)

    assert sorted(folder.name for folder in result) == ['Movie A', 'Movie B']


def test_ignore_key_treats_accent_forms_and_case_as_equal():
    composed = 'Ég'            # É as one character
    decomposed = 'E\u0301g'    # E + combining accent mark, as macOS may store it

    assert ignore_key(composed) == ignore_key(decomposed)
    assert ignore_key('SAMPLE') == ignore_key('sample')


@pytest.mark.parametrize('name, expected', [
    # season folders
    pytest.param('Season 1', True, id='season-word'),
    pytest.param('Season 3 (2007-08)', True, id='season-word-with-years'),
    pytest.param('Évad 7', True, id='evad-word'),
    pytest.param('Dallas 08. évad', True, id='number-then-evad'),
    pytest.param('Scrubs Season 2  [720p AI x265 10bit Joy]', True, id='show-name-then-season-word'),
    pytest.param('South.Park.S10.Dual', True, id='season-token'),
    pytest.param('Frasier S07 (360p re-dvdrip)', True, id='season-token-with-spaces'),
    pytest.param('Volume 03 - The Years of Change', True, id='volume-word'),
    # episode folders
    pytest.param('Angel.S02E17.DVDRip.HUN.ENG.XviD-HT', True, id='episode-token'),
    pytest.param('8.Simple.Rules.S01.E02.DVDRip.XviD.Dual-VHS', True, id='episode-token-with-dot'),
    # language folders
    pytest.param('Hungarian', True, id='language-english-word'),
    pytest.param('!Angol', True, id='language-with-exclamation'),
    # show folders: not seasons
    pytest.param('How I Met Your Mother', False, id='plain-show'),
    pytest.param('Star Wars - The Clone Wars (2008-2020)', False, id='show-with-years'),
    pytest.param('Friends (1994) Season 1-10 S01-S10 (1080p BluRay x265 HEVC 10bit AAC 5.1 Silence)', False, id='complete-pack-range'),
    pytest.param('Sabrina.The.Teenage.Witch.S01-S07.DVDRip.XviD.Hun.Eng', False, id='season-token-range'),
    pytest.param('Modern Family Season 1-11 Complete 720p x264 [Pahe.in]', False, id='season-word-range'),
])
def test_is_season_folder(name, expected):
    assert is_season_folder(name) is expected