def test_user_model_importable():
    from notebooklm_shared.models.user import User
    assert User.__tablename__ is not None

def test_all_models_importable():
    from notebooklm_shared.models import (
        User, Notebook, Source, SystemSetting, FeaturedNotebookLink
    )
    assert User is not None
    assert Notebook is not None

def test_base_has_metadata():
    from notebooklm_shared.database import Base
    assert Base.metadata is not None
