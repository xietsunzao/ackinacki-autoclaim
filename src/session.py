"""
Session management utilities for HTTP requests with retry logic and connection pooling.
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


def create_session(
    total_retries=3,
    backoff_factor=1,
    status_forcelist=None,
    pool_connections=10,
    pool_maxsize=20,
    allowed_methods=None
):
    """
    Create a requests.Session with automatic retry logic and connection pooling.

    Args:
        total_retries (int): Total number of retry attempts. Default: 3
        backoff_factor (float): Backoff factor for exponential delay between retries.
                               Waits: {backoff_factor} * (2 ** {retry_count - 1}) seconds.
                               Default: 1 (waits 1s, 2s, 4s)
        status_forcelist (list): HTTP status codes to retry on.
                                Default: [429, 500, 502, 503, 504]
        pool_connections (int): Number of connection pools to cache. Default: 10
        pool_maxsize (int): Maximum number of connections per pool. Default: 20
        allowed_methods (list): HTTP methods that are allowed to retry.
                               Default: All standard methods

    Returns:
        requests.Session: Configured session object with retry logic

    Example:
        >>> session = create_session()
        >>> response = session.get('https://api.example.com/data')
        >>> session.close()  # Don't forget to close when done!

        # Custom configuration
        >>> session = create_session(
        ...     total_retries=5,
        ...     backoff_factor=2,
        ...     status_forcelist=[500, 502, 503]
        ... )

    Benefits:
        - Persistent connections (TCP connection reuse)
        - Automatic retry on transient failures
        - Exponential backoff to prevent server overload
        - Connection pooling for better performance
        - Handles rate limiting (HTTP 429)
    """
    # Set default values
    if status_forcelist is None:
        status_forcelist = [429, 500, 502, 503, 504]

    if allowed_methods is None:
        allowed_methods = ["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]

    # Create session
    session = requests.Session()

    # Configure retry strategy
    retry_strategy = Retry(
        total=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=allowed_methods
    )

    # Create HTTP adapter with retry strategy and connection pooling
    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=pool_connections,
        pool_maxsize=pool_maxsize
    )

    # Mount adapter for both HTTP and HTTPS
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


def create_api_session():
    """
    Create a session optimized for API requests.

    Returns:
        requests.Session: Session configured for general API usage

    Example:
        >>> api_session = create_api_session()
        >>> response = api_session.get('https://api.example.com/endpoint')
        >>> api_session.close()
    """
    return create_session(
        total_retries=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        pool_connections=10,
        pool_maxsize=20
    )


def create_auth_session():
    """
    Create a session optimized for authentication requests.

    Returns:
        requests.Session: Session configured for authentication

    Example:
        >>> auth_session = create_auth_session()
        >>> response = auth_session.post('https://api.example.com/auth', json={'token': 'xxx'})
        >>> auth_session.close()
    """
    return create_session(
        total_retries=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        pool_connections=5,  # Fewer connections needed for auth
        pool_maxsize=10
    )
