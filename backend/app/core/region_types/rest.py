"""
REST Data Source Region Renderer
Renders regions of type 'rest' which display data fetched server-side from an
external REST service (defined by a RestDataSource in metadata).
"""
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session
import json
import html as html_module

from ...db import models
from ..session.service import SessionService
from ..rest import RestDataSourceService, RestClientError


def _parse_options(region: models.Region) -> Dict[str, Any]:
    if not region.template_options:
        return {}
    try:
        if isinstance(region.template_options, dict):
            return dict(region.template_options)
        return json.loads(region.template_options)
    except (json.JSONDecodeError, TypeError):
        return {}


def _table_html(rows: List[Dict[str, Any]]) -> str:
    """Render a list of dicts as an HTML table."""
    if not rows:
        return "<div class='rest-empty'><p>No data returned by REST data source.</p></div>"

    columns = list(dict.fromkeys(key for row in rows for key in row.keys()))

    parts = ["<table class='report-table rest-table'>", "<thead><tr>"]
    for column in columns:
        parts.append(f"<th>{html_module.escape(str(column))}</th>")
    parts.append("</tr></thead><tbody>")

    for row in rows:
        parts.append("<tr>")
        for column in columns:
            parts.append(f"<td>{html_module.escape(str(row.get(column, '')))}</td>")
        parts.append("</tr>")

    parts.append("</tbody></table>")
    return "\n".join(parts)


def _object_html(data: Dict[str, Any]) -> str:
    """Render a single JSON object as a key/value table."""
    parts = ["<table class='rest-detail'>"]
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            display = html_module.escape(json.dumps(value))
        else:
            display = html_module.escape(str(value))
        parts.append(
            f"<tr><th>{html_module.escape(str(key))}</th><td>{display}</td></tr>"
        )
    parts.append("</table>")
    return "\n".join(parts)


def render_rest_region(
    region: models.Region,
    db: Session,
    session_id: str,
    page_id: int,
    session_service: Optional[SessionService] = None,
) -> str:
    """
    Render a 'rest' region by executing its configured REST data source.

    Configuration (stored in region.template_options):
        data_source_id: ID of a RestDataSource row (preferred)
        url:            Inline URL (used when data_source_id is absent)
        method:         HTTP method for inline sources (default GET)
        headers:        Request headers for inline sources
        query_params:   Query parameters for inline sources
    """
    if session_service is None:
        session_service = SessionService(db)

    options = _parse_options(region)
    source_id = options.get("data_source_id") or options.get("rest_data_source_id")

    service = RestDataSourceService(db)

    try:
        if source_id:
            source = db.query(models.RestDataSource).filter(
                models.RestDataSource.id == int(source_id)
            ).first()
            if not source:
                raise RestClientError("Configured REST data source not found")
            result = service.execute(source)
            data = result["data"]
            # Map response values into page session items
            if source.response_mapping:
                service.apply_response_mapping(
                    source, data, session_id, page_id, session_service
                )
        else:
            url = (options.get("url") or "").strip()
            if not url:
                return (
                    "<div class='rest-error'><p>No REST data source configured "
                    "for this region.</p></div>"
                )
            headers = options.get("headers") or {}
            query_params = options.get("query_params") or {}
            inline = models.RestDataSource(
                application_id=region.page.application_id,
                name=region.name,
                url=url,
                method=options.get("method", "GET"),
                headers=headers if isinstance(headers, dict) else {},
                query_params=query_params if isinstance(query_params, dict) else {},
                is_active=True,
            )
            result = service.execute(inline)
            data = result["data"]
    except RestClientError as exc:
        return (
            "<div class='rest-error'>"
            "<h3>Error calling REST data source</h3>"
            f"<p>{html_module.escape(str(exc))}</p>"
            "</div>"
        )

    if isinstance(data, list):
        rows = [row for row in data if isinstance(row, dict)]
        return _table_html(rows)
    if isinstance(data, dict):
        return _object_html(data)

    return f"<div class='rest-data'><pre>{html_module.escape(str(data))}</pre></div>"