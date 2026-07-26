"""
Report Region Renderer
Renders regions of type 'report' which display data from SQL queries.
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
import json

from ...db import models


def render_report_region(region: models.Region, db: Session, session_id: str, page_id: int) -> str:
    """
    Render a report region.

    Args:
        region: The region database object
        db: Database session
        session_id: The current session ID
        page_id: The current page ID

    Returns:
        HTML string containing the report table
    """
    # Get the report query from the region's template_options or a dedicated column
    # For this implementation, we'll assume the SQL query is stored in template_options
    # under a 'source' key or similar

    sql_query = ""
    if region.template_options:
        try:
            options = region.template_options if isinstance(region.template_options, dict) else {}
            if isinstance(options, str):
                options = json.loads(options)

            # Look for the SQL query in common locations
            sql_query = (
                options.get("source") or
                options.get("sql_query") or
                options.get("query") or
                ""
            )
        except (json.JSONDecodeError, TypeError):
            # If it's not JSON, maybe the template_options is the raw SQL
            sql_query = str(region.template_options)

    if not sql_query:
        return "<div class='report-region'><p>No SQL query defined for this report.</p></div>"

    # Substitute session items in the SQL query
    from ..rendering.service import RenderingService
    # We need to create a temporary renderer to access the substitution method
    # In a real implementation, we'd extract this to a utility function
    renderer = RenderingService(db)
    # Temporarily set the session service - this is not ideal but works for MVP
    # A better approach would be to move the substitution logic to a utility class
    substituted_sql = renderer._substitute_strings(sql_query, session_id, page_id)

    try:
        # Execute the query
        result = db.execute(substituted_sql)

        # Get column names
        columns = list(result.keys()) if hasattr(result, 'keys') else []
        if not columns and hasattr(result, 'fetchone'):
            # If it's a legacy result object
            first_row = result.fetchone()
            if first_row:
                # Try to get column names from cursor description
                # This depends on the DB-API implementation
                pass

        # For SQLAlchemy 2.0, result.keys() should work
        # If not, we'll need to handle it differently
        rows = []
        for row in result:
            rows.append([str(cell) if cell is not None else "" for cell in row])

    except Exception as e:
        return f"""
        <div class='report-region'>
            <div class='report-error'>
                <h3>Error executing report query</h3>
                <p>{str(e)}</p>
                <p>Query: {substituted_sql[:200]}...</p>
            </div>
        </div>
        """

    # If we have no columns, try to get them from the result
    if not columns and rows:
        # This is a fallback - in a real implementation we'd get proper column names
        columns = [f"Column {i+1}" for i in range(len(rows[0]))] if rows else []
    elif not columns and not rows:
        columns = ["No data"]

    # Build the HTML table
    html_parts = [
        f"<div class='report-region' data-region-id='{region.id}'>",
        f"  <div class='report-header'>",
        f"    <h3>{region.name}</h3>",
        f"  </div>",
        f"  <div class='report-body'>",
        f"    <table class='report-table'>",
        f"      <thead>",
        f"        <tr>"
    ]

    # Add header cells
    for column in columns:
        html_parts.append(f"          <th>{column}</th>")

    html_parts.extend([
        f"        </tr>",
        f"      </thead>",
        f"      <tbody>"
    ])

    # Add data rows
    for row in rows:
        html_parts.append(f"        <tr>")
        for cell in row:
            html_parts.append(f"          <td>{cell}</td>")
        html_parts.append(f"        </tr>")

    html_parts.extend([
        f"      </tbody>",
        f"    </table>",
        f"  </div>",
        f"</div>"
    ])

    return "\n".join(html_parts)