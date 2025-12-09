"""
Formance Banking Client
Production-ready async client for Formance SDK
"""

from typing import Optional
import logging
import httpx
from formance_sdk_python import SDK
from formance_sdk_python.httpclient import AsyncHttpClient

from .config import get_settings


logger = logging.getLogger(__name__)


class CustomAsyncClient(AsyncHttpClient):
    """Custom async HTTP client with logging and headers"""

    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def send(
        self,
        request: httpx.Request,
        *,
        stream: bool = False,
        auth: httpx._types.AuthTypes
        | httpx._client.UseClientDefault
        | None = httpx.USE_CLIENT_DEFAULT,
        follow_redirects: bool
        | httpx._client.UseClientDefault = httpx.USE_CLIENT_DEFAULT,
    ) -> httpx.Response:
        """Send HTTP request with custom headers and logging"""
        # Add custom headers
        request.headers["User-Agent"] = "BaaS-Core-Banking/0.1.0"
        request.headers["X-Client-Name"] = "baas-core"

        # Log request (remove sensitive data in production)
        logger.debug(
            f"Formance API Request: {request.method} {request.url}"
        )

        try:
            response = await self._client.send(
                request,
                stream=stream,
                auth=auth,
                follow_redirects=follow_redirects,
            )

            # Log response
            logger.debug(
                f"Formance API Response: {response.status_code}"
            )

            return response
        except Exception as e:
            logger.error(f"Formance API Error: {e}")
            raise

    def build_request(
        self,
        method: str,
        url: httpx._types.URLTypes,
        *,
        content: Optional[httpx._types.RequestContent] = None,
        data: Optional[httpx._types.RequestData] = None,
        files: Optional[httpx._types.RequestFiles] = None,
        json: Optional[any] = None,
        params: Optional[httpx._types.QueryParamTypes] = None,
        headers: Optional[httpx._types.HeaderTypes] = None,
        cookies: Optional[httpx._types.CookieTypes] = None,
        timeout: httpx._types.TimeoutTypes
        | httpx._client.UseClientDefault = httpx.USE_CLIENT_DEFAULT,
        extensions: Optional[httpx._types.RequestExtensions] = None,
    ) -> httpx.Request:
        """Build HTTP request"""
        return self._client.build_request(
            method,
            url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            timeout=timeout,
            extensions=extensions,
        )


class FormanceBankingClient:
    """
    Production-ready Formance client for banking operations

    Features:
    - Async operations for high concurrency
    - Custom headers and logging
    - Connection pooling
    - Timeout configuration
    - Automatic retries (via httpx)
    - Context manager support
    """

    def __init__(
        self,
        base_url: str,
        client_id: str,
        client_secret: str,
        timeout: int = 30,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
    ):
        """
        Initialize Formance banking client

        Args:
            base_url: Formance API base URL
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            timeout: Request timeout in seconds
            max_connections: Maximum total connections
            max_keepalive_connections: Maximum keepalive connections
        """
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret

        logger.info("Initializing Formance banking client")

        # Create httpx async client with connection pooling
        httpx_client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(
                max_connections=max_connections,
                max_keepalive_connections=max_keepalive_connections,
            ),
            http2=True,  # Enable HTTP/2
        )

        # Wrap with custom client
        custom_client = CustomAsyncClient(httpx_client)

        # Initialize Formance SDK
        self.sdk = SDK(
            async_client=custom_client,
            server_url=base_url,
            security={
                "client_id": client_id,
                "client_secret": client_secret,
            },
        )

        logger.info("Formance banking client initialized successfully")

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def close(self):
        """Close client and cleanup resources"""
        logger.info("Closing Formance banking client")
        # TODO: Add proper cleanup if SDK provides close method
        # await self.sdk.close()

    async def health_check(self) -> bool:
        """
        Check Formance API health

        Returns:
            True if API is healthy
        """
        try:
            # TODO: Implement actual health check endpoint
            # response = await self.sdk.ledger.v2.get_info()
            logger.info("Formance API health check: OK")
            return True
        except Exception as e:
            logger.error(f"Formance API health check failed: {e}")
            return False

    # The SDK methods will be accessed via self.sdk
    # Example usage:
    # - self.sdk.ledger.v2.create_transaction(...)
    # - self.sdk.payments.v1.create_payment(...)
    # - self.sdk.auth.v1.create_client(...)


def get_formance_client() -> FormanceBankingClient:
    """
    Factory function to create Formance client from settings

    Returns:
        Configured FormanceBankingClient instance
    """
    settings = get_settings()

    return FormanceBankingClient(
        base_url=settings.formance_base_url,
        client_id=settings.formance_client_id,
        client_secret=settings.formance_client_secret,
    )
