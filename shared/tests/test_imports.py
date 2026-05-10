def test_package_importable():
    import notebooklm_shared
    assert notebooklm_shared is not None


def test_settings_importable():
    from notebooklm_shared.config import settings
    assert settings is not None
    assert hasattr(settings, 'database_url')
