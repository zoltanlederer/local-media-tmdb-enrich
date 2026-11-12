import pytest
from scanner import clean_folder_name


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
])
def test_clean_folder_name(folder_name, expected_title, expected_year):
    result = clean_folder_name(folder_name)
    assert result == {'title': expected_title, 'year': expected_year}