import ipaddress
import socket
from urllib.parse import urlparse
from backend.app.core.exceptions import SSRFSecurityError, InvalidInputError

PRIVATE_IP_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

def validate_url_security(url_str: str) -> str:
    """
    Validate that the URL is HTTP/HTTPS and does not target private IPs,
    loopback addresses, cloud metadata endpoints, or local intranet services.
    """
    if not url_str or not isinstance(url_str, str) or not url_str.strip():
        raise InvalidInputError("URL string must not be empty.")
    
    url_str = url_str.strip()

    try:
        parsed = urlparse(url_str)
    except Exception as e:
        raise InvalidInputError(f"Malformed URL: {e}")

    # If scheme is missing (e.g. 'example.com/page'), default to https
    if not parsed.scheme:
        url_str = "https://" + url_str
        try:
            parsed = urlparse(url_str)
        except Exception as e:
            raise InvalidInputError(f"Malformed URL: {e}")

    if parsed.scheme not in ("http", "https"):
        raise SSRFSecurityError(url_str, f"Scheme '{parsed.scheme}' is not supported. Only HTTP and HTTPS are allowed.")

    hostname = parsed.hostname
    if not hostname:
        raise InvalidInputError("URL missing valid hostname.")

    hostname_lower = hostname.lower()
    if hostname_lower in ("localhost", "127.0.0.1", "0.0.0.0", "::1", "metadata.google.internal"):
        raise SSRFSecurityError(url_str, "Requests to localhost or cloud metadata are disallowed.")

    # Resolve IP address to prevent DNS rebinding or private IP bypass
    try:
        ip_info = socket.getaddrinfo(hostname, None)
        for entry in ip_info:
            ip_str = entry[4][0]
            ip_obj = ipaddress.ip_address(ip_str)
            for private_net in PRIVATE_IP_NETWORKS:
                if ip_obj in private_net or ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
                    raise SSRFSecurityError(url_str, f"Target resolves to private/restricted IP ({ip_str}).")
    except socket.gaierror:
        # Host cannot be resolved or domain is unreachable
        pass
    except SSRFSecurityError:
        raise
    except Exception:
        pass

    return url_str
