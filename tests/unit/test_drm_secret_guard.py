import pytest

from pwd301.services.video_drm_service import VideoDRMKeyAuthError, generate_key_token


def test_drm_never_signs_with_implicit_default_outside_app():
    with pytest.raises(VideoDRMKeyAuthError):
        generate_key_token(1, 1, 1)
