"""
REST Data Source Service
Performs server-side calls to external REST services defined in metadata and
maps JSON response values into page session state.
"""
from typing import Any, Dict, Optional, Union

import httpx
from sqlalchemy.orm import Session

from ...db import models


class RestClientError(Exception):
    """Raised when an external REST call fails."""


class RestDataSourceService:
    """Service for executing stored REST data sources."""

    ALLOWED_METHODS = ("GET", "POST", "PUT", "DELETE")

    def __init__(self, db: Session, transport: Optional[httpx.BaseTransport] = None):
        self.db = db
        self.transport = transport

    @staticmethod
    def _parse_json_options(value: Any) -> Any:
        """Return dict options stored either as a dict or JSON string."""
        import json
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return {}
        return {}

    def execute(
        self,
        data_source: Union[models.RestDataSource, int],
        payload: Optional[Dict[str, Any]] = None,
    ) -> dict:
        """
        Execute a REST data source.

        Args:
            data_source: The data source model or its ID (looked up in the database).
            payload: Optional request payload. For GET this is merged into the
                query parameters; for POST/PUT/DELETE it is used as the JSON body
                when the stored request_body does not already provide one.

        Returns:
            {"status_code": int, "data": Any, "content_type": str}

        Raises:
            RestClientError: if the source cannot be found, the URL is invalid,
                or the external call fails.
        """
        if isinstance(data_source, int):
            source = self.db.query(models.RestDataSource).filter(
                models.RestDataSource.id == data_source
            ).first()
            if source is None:
                raise RestClientError("REST data source not found")
        else:
            source = data_source

        method = (source.method or "GET").upper()
        if method not in self.ALLOWED_METHODS:
            raise RestClientError(f"Unsupported HTTP method '{source.method}'")

        url = (source.url or "").strip()
        if not url.startswith(("http://", "https://")):
            raise RestClientError("URL must be an absolute http(s) URL")

        query_params = dict(self._parse_json_options(source.query_params) or {})
        headers = dict(self._parse_json_options(source.headers) or {})
        headers.setdefault("Accept", "application/json")
        body: Optional[Dict[str, Any]] = self._parse_json_options(source.request_body) or None

        if payload:
            if method == "GET":
                # Merge payload into query parameters (payload wins)
                query_params.update(payload)
            else:
                if body:
                    merged = dict(body)
                    merged.update(payload)
                    body = merged
                else:
                    body = payload

        timeout = source.timeout if source.timeout and source.timeout > 0 else 30

        try:
            kwargs: Dict[str, Any] = {
                "method": method,
                "url": url,
                "params": query_params,
                "headers": headers,
                "timeout": timeout,
                "follow_redirects": True,
            }
            if body is not None and method in ("POST", "PUT", "DELETE"):
                kwargs["json"] = body

            with httpx.Client(transport=self.transport) as client:
                response = client.request(**kwargs)
        except RestClientError:
            raise
        except Exception as exc:
            raise RestClientError(f"Failed to call REST endpoint '{source.name}': {exc}")

        try:
            data = response.json()
        except ValueError:
            data = response.text

        return {
            "status_code": response.status_code,
            "data": data,
            "content_type": response.headers.get("content-type", ""),
        }

    @staticmethod
    def resolve_path(data: Any, path: str) -> Optional[str]:
        """
        Resolve a dot-separated path into a JSON value.

        e.g. "address.city" -> data["address"]["city"]
        """
        current = data
        for part in str(path).split("."):
            part = part.strip()
            if not part:
                continue
            if isinstance(current, dict):
                if part not in current:
                    return None
                current = current[part]
            elif isinstance(current, list):
                try:
                    current = current[int(part)]
                except (ValueError, IndexError):
                    return None
            else:
                return None
        if current is None:
            return None
        if isinstance(current, (dict, list)):
            return str(current)
        return str(current)

    def apply_response_mapping(
        self,
        data_source: models.RestDataSource,
        data: Any,
        session_id: str,
        page_id: int,
        session_service,
    ) -> Dict[str, str]:
        """
        Map values from the response JSON into page session items using the
        data source's response_mapping ({item_name: dot.path.in.response}).

        Returns a dict of {item_name: value} that were mapped.
        """
        mapping = self._parse_json_options(data_source.response_mapping) or {}
        if not mapping:
            return {}

        mapped = {}
        for item_name, path in mapping.items():
            value = self.resolve_path(data, path)
            if value is not None:
                session_service.set_item(session_id, page_id, item_name, value)
                mapped[item_name] = value
        return mapped