from scanner import clean_folder_name


def test_clean_folder_name_removes_quality_tags():
    result = clean_folder_name('Forrest.Gump.1994.REMASTERED.1080p.BluRay.x265-RARBG')
    assert result == {'title': 'Forrest Gump', 'year': '1994'}