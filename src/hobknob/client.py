# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.
# Hobknob is the cli tool for using and managing the Hob appllication server
# from the command line. It provides a simple interface to the Hob API.


from typing import Type, TypeVar, Optional, Union, Dict, Any, AsyncGenerator
from pydantic import BaseModel
import httpx
from enum import Enum

from hobknob.config import ConfigStateInterface, get_config

# Type variable for Pydantic models
T = TypeVar("T", bound=BaseModel)


class ClientType(Enum):
    Synchronous = "synchronous"
    Asynchronous = "asynchronous"
    Dual = "dual"


class HTTPClient:
    def __init__(
        self,
        base_url: str,
        headers: Optional[Dict[str, str]] = None,
        mode: ClientType = ClientType.Dual,
        config: Optional[ConfigStateInterface] = None,
    ):
        self.base_url = base_url
        self.headers = headers or {}
        if mode is ClientType.Synchronous or mode is ClientType.Dual:
            self.client = httpx.Client(base_url=self.base_url, headers=self.headers)
        if mode is ClientType.Asynchronous or mode is ClientType.Dual:
            self.async_client = httpx.AsyncClient(
                base_url=self.base_url, headers=self.headers
            )
        self._jwt_token: Optional[str] = None
        self.config_instance = config

    def get_jwt_token(self) -> Optional[str]:
        """Get the JWT token for authorization."""
        return self._jwt_token

    def set_jwt_token(self, token: str):
        self._jwt_token = token
        """Set a JWT token for authorization."""
        self.headers["Authorization"] = f"Bearer {token}"
        if hasattr(self, "client"):
            self.client.headers.update(self.headers)
        if hasattr(self, "async_client"):
            self.async_client.headers.update(self.headers)

    def set_headers(self, headers: Dict[str, str]):
        """Set additional headers."""
        self.headers.update(headers)
        if hasattr(self, "client"):
            self.client.headers.update(self.headers)
        if hasattr(self, "async_client"):
            self.async_client.headers.update(self.headers)

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], BaseModel]] = None,
        form_data: bool = False,
        response_model: Optional[Type[T]] = None,
    ) -> Union[T, httpx.Response]:
        """Make a synchronous HTTP request."""
        if isinstance(data, BaseModel):
            data = data.model_dump()
        if form_data:
            # Use url-encoded form data
            response = self.client.request(method, endpoint, params=params, data=data)
        else:
            response = self.client.request(method, endpoint, params=params, json=data)
        response.raise_for_status()

        if response_model:
            return_data = response.json()
            if isinstance(return_data, list):
                return [response_model.model_validate(item) for item in return_data]  # type: ignore
            else:
                return response_model.model_validate(return_data)
        else:
            return response

    async def _request_async(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], BaseModel]] = None,
        form_data: bool = False,
        response_model: Optional[Type[T]] = None,
    ) -> Union[T, httpx.Response]:
        """Make an asynchronous HTTP request."""
        if isinstance(data, BaseModel):
            data = data.model_dump_json()  # type: ignore
        if form_data:
            # Use url-encoded form data
            response = await self.async_client.request(
                method, endpoint, params=params, data=data  # type: ignore
            )
        else:
            response = await self.async_client.request(
                method, endpoint, params=params, json=data  # type: ignore
            )

        if response.status_code == 401:
            self._jwt_token = None
            config = get_config()
            config.remove_state("token")

        response.raise_for_status()

        # If the response contains a new JWT token, update the client
        auth_header = response.headers.get("Authorization")
        if auth_header:

            new_token = auth_header.split()[1]
            self.set_jwt_token(new_token)
            if not self.config_instance:
                _config = get_config()
            else:
                _config = self.config_instance
            _config.update_state({"token": new_token})

        if response_model:
            return_data = response.json()
            if isinstance(return_data, list):
                return [response_model.model_validate(item) for item in return_data]  # type: ignore
            else:
                return response_model.model_validate(return_data)
        else:
            return response

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        response_model: Optional[Type[T]] = None,
    ):
        return self._request(
            "GET", endpoint, params=params, response_model=response_model
        )

    async def get_async(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        response_model: Optional[Type[T]] = None,
    ):
        return await self._request_async(
            "GET", endpoint, params=params, response_model=response_model
        )

    def post(
        self,
        endpoint: str,
        data: Optional[Union[Dict[str, Any], BaseModel]] = None,
        form_data: bool = False,
        response_model: Optional[Type[T]] = None,
    ):
        return self._request(
            "POST",
            endpoint,
            data=data,
            form_data=form_data,
            response_model=response_model,
        )

    async def post_async(
        self,
        endpoint: str,
        data: Optional[Union[Dict[str, Any], BaseModel]] = None,
        form_data: bool = False,
        response_model: Optional[Type[T]] = None,
    ):
        return await self._request_async(
            "POST",
            endpoint,
            data=data,
            form_data=form_data,
            response_model=response_model,
        )

    def put(
        self,
        endpoint: str,
        data: Optional[Union[Dict[str, Any], BaseModel]] = None,
        response_model: Optional[Type[T]] = None,
    ):
        return self._request("PUT", endpoint, data=data, response_model=response_model)

    async def put_async(
        self,
        endpoint: str,
        data: Optional[Union[Dict[str, Any], BaseModel]] = None,
        response_model: Optional[Type[T]] = None,
    ):
        return await self._request_async(
            "PUT", endpoint, data=data, response_model=response_model
        )

    def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        response_model: Optional[Type[T]] = None,
    ):
        return self._request(
            "DELETE", endpoint, params=params, response_model=response_model
        )

    async def delete_async(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        response_model: Optional[Type[T]] = None,
    ):
        return await self._request_async(
            "DELETE", endpoint, params=params, response_model=response_model
        )

    async def stream_get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[bytes, None]:
        """
        Perform a GET request and stream the response.

        Args:
            endpoint (str): The API endpoint to call.
            params (Optional[Dict[str, Any]]): Query parameters for the request.

        Yields:
            AsyncGenerator[bytes, None]: Chunks of response content.
        """
        async with self.async_client.stream("GET", endpoint, params=params) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes():
                yield chunk

    async def stream_post(
        self, endpoint: str, data: dict, params: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Perform a POST request and stream the response.

        Args:
            endpoint (str): The API endpoint to call.
            data (dict): The JSON body to send.
            params (Optional[Dict[str, Any]]): Query parameters for the request.

        Yields:
            AsyncGenerator[str, None]: Chunks of the streamed response.
        """
        async with self.async_client.stream(
            "POST", endpoint, json=data, params=params
        ) as response:
            response.raise_for_status()
            async for chunk in response.aiter_text():
                yield chunk

    def close(self):
        """Close the synchronous client."""
        if hasattr(self, "client"):
            self.client.close()

    async def close_async(self):
        """Close the asynchronous client."""
        if hasattr(self, "async_client"):
            await self.async_client.aclose()


_client: Optional[HTTPClient] = None


def get_client() -> HTTPClient:
    global _client
    if _client is None:
        raise RuntimeError("Configuration has not been set.")
    return _client


def set_client(client: HTTPClient):
    global _client
    _client = client
