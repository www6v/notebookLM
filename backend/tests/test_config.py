"""Configuration normalization tests."""

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa as crypto_rsa

from app.config import Settings


def _pem_body(pem_text: str) -> str:
    """Return a single-line PEM body for env-style test inputs."""
    return "".join(
        line.strip()
        for line in pem_text.splitlines()
        if line.strip() and not line.startswith("-----")
    )


def test_alipay_keys_accept_single_line_pkcs8_private_key() -> None:
    """Single-line env keys should be normalized for the Alipay SDK."""
    private_key = crypto_rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    pkcs8_private_key = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    settings = Settings(
        alipay_private_key=_pem_body(pkcs8_private_key),
        alipay_public_key=_pem_body(public_key),
    )

    assert "BEGIN RSA PRIVATE KEY" in settings.alipay_private_key
    assert "BEGIN PUBLIC KEY" in settings.alipay_public_key

    loaded_private_key = serialization.load_pem_private_key(
        settings.alipay_private_key.encode("utf-8"),
        password=None,
    )
    loaded_public_key = serialization.load_pem_public_key(
        settings.alipay_public_key.encode("utf-8")
    )

    assert loaded_private_key is not None
    assert loaded_public_key is not None


def test_alipay_platform_public_key_must_not_match_app_public_key() -> None:
    """Reject using the app public key where the platform key is required."""
    private_key = crypto_rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    pkcs8_private_key = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    app_public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    settings = Settings(
        alipay_private_key=_pem_body(pkcs8_private_key),
        alipay_public_key=_pem_body(app_public_key),
    )

    try:
        settings.validate_alipay_public_key_config()
    except ValueError as exc:
        assert "Alipay platform public key" in str(exc)
    else:
        raise AssertionError("Settings accepted an app public key as platform key")


def test_alipay_fields_load_from_process_env(monkeypatch) -> None:
    """Alipay and Langfuse fields load from process env (overrides config.yaml)."""
    for key in (
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_SECRET_KEY",
        "LANGFUSE_HOST",
        "ALIPAY_APP_ID",
        "ALIPAY_PRIVATE_KEY",
        "ALIPAY_PLATFORM_PUBLIC_KEY",
        "ALIPAY_PUBLIC_KEY",
        "ALIPAY_GATEWAY",
        "DATABASE_URL",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "lf-pk")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "lf-sk")
    monkeypatch.setenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    monkeypatch.setenv("ALIPAY_APP_ID", "test-app-id")
    monkeypatch.setenv("ALIPAY_PRIVATE_KEY", "test-private-key")
    monkeypatch.setenv("ALIPAY_PLATFORM_PUBLIC_KEY", "test-platform-key")
    monkeypatch.setenv("ALIPAY_GATEWAY", "https://openapi.alipay.com/gateway.do")
    monkeypatch.setenv(
        "DATABASE_URL",
        "mysql+aiomysql://u:p@localhost:3306/t",
    )

    settings = Settings()

    assert settings.alipay_app_id == "test-app-id"
    assert settings.alipay_private_key == "test-private-key"
    assert "test-platform-key" in settings.alipay_public_key
    assert "BEGIN PUBLIC KEY" in settings.alipay_public_key
    assert settings.alipay_gateway == "https://openapi.alipay.com/gateway.do"
