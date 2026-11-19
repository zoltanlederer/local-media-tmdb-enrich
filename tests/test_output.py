import csv
from output import write_unmatched, write_csv
from parser import parse_movie


def test_write_unmatched(tmp_path):
    path = tmp_path / 'unmatched.csv'

    unmatched = [
        {
            'title': 'Mi szükségünk, a Holdra',
            'year': 2011,
            'media_type': 'tv',
            'reason': 'no_match',
            'source_folder': 'Mi.szuksegunk.a.Holdra.2011.DVBRip.x264.AC3.Hun-MrX',
            'source_path': '/media/tv/Mi.szuksegunk.a.Holdra.2011.DVBRip.x264.AC3.Hun-MrX',
        },
        {
            'title': 'Utazás az Univerzum peremére (Journey to the Edge of the Universe',
            'year': None,
            'media_type': 'tv',
            'reason': 'fetch_failed',
            'source_folder': 'Utazás az Univerzum peremére (Journey to the Edge of the Universe) 2008',
            'source_path': '/media/tv/Utazás az Univerzum peremére (Journey to the Edge of the Universe) 2008',
        },
    ]

    write_unmatched(unmatched, path)

    with open(path, encoding='utf-8-sig') as file:
        rows = list(csv.DictReader(file))

    assert rows == [
        {
            'title': 'Mi szükségünk, a Holdra',
            'year': '2011',
            'media_type': 'tv',
            'reason': 'no_match',
            'source_folder': 'Mi.szuksegunk.a.Holdra.2011.DVBRip.x264.AC3.Hun-MrX',
            'source_path': '/media/tv/Mi.szuksegunk.a.Holdra.2011.DVBRip.x264.AC3.Hun-MrX',
        },
        {
            'title': 'Utazás az Univerzum peremére (Journey to the Edge of the Universe',
            'year': '',
            'media_type': 'tv',
            'reason': 'fetch_failed',
            'source_folder': 'Utazás az Univerzum peremére (Journey to the Edge of the Universe) 2008',
            'source_path': '/media/tv/Utazás az Univerzum peremére (Journey to the Edge of the Universe) 2008',
        },
    ]


MATCH = {'source_folder': 'Test folder', 'source_path': '/media/test'}


def test_write_csv(tmp_path):
    path = tmp_path / 'media.csv'

    details = {
        'id': 1,
        'title': 'Fast Five',
        'release_date': '2011-04-20',
        'genres': [
            {'id': 28, 'name': 'Action'},
            {'id': 53, 'name': 'Thriller'},
            {'id': 80, 'name': 'Crime'},
        ],
    }

    item = parse_movie({'details': details}, MATCH)

    write_csv([item], path)

    with open(path, encoding='utf-8-sig') as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 1
    row = rows[0]

    assert row['title'] == 'Fast Five'
    assert row['year'] == '2011'
    assert row['genres'] == 'Action, Thriller, Crime'
    assert row['number_of_seasons'] == ''