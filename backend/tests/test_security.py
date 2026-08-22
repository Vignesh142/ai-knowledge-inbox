import pytest
from backend.app.core.security import validate_url_security
from backend.app.core.exceptions import SSRFSecurityError, InvalidInputError

def test_valid_public_urls():
    valid_urls = [
        "https://en.wikipedia.org/wiki/Artificial_intelligence",
        "http://example.com/articles/rag-tutorial",
        "https://github.com/fastapi/fastapi",
    ]
    for u in valid_urls:
        validated = validate_url_security(u)
        assert validated.startswith("http")

def test_blocks_localhost_and_private_ips():
    forbidden_urls = [
        "http://localhost:8080/secret",
        "http://127.0.0.1:5000",
        "http://10.0.0.1/admin",
        "http://192.168.1.1/router",
        "http://169.254.169.254/latest/meta-data/",
        "http://[::1]/internal",
    ]
    for u in forbidden_urls:
        with pytest.raises(SSRFSecurityError):
            validate_url_security(u)

def test_blocks_invalid_protocols_or_empty():
    invalid = [
        "",
        "file:///etc/passwd",
        "ftp://ftp.server.com",
        "gopher://server.com",
    ]
    for u in invalid:
        with pytest.raises((SSRFSecurityError, InvalidInputError)):
            validate_url_security(u)
