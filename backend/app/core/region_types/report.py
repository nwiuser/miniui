"""
Report Region Renderer
Renders regions of type 'report' which display data from SQL queries.
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
import json
import math

from ...db import models
from ..session.service import SessionService


def render_report_region(
    region: models.Region,
    db: Session,
    session_id: str,
    page_id: int,
    session_service: SessionService = None,
    rendering_service = None  # We'll import inside the function to avoid circular import
) -> str:
    """
    Render a report region.

    Args:
        region: The region database object
        db: Database session
        session_id: The current session ID
        page_id: The current page ID
        session_service: Optional SessionService instance; if None, a new one is created.
        rendering_service: Optional RenderingService instance; if None, a new one is created.

    Returns:
        HTML string containing the report table
    """
    if session_service is None:
        session_service = SessionService(db)
    if rendering_service is None:
        # Import inside function to avoid circular import
        from ..rendering.service import RenderingService
        rendering_service = RenderingService(db)

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

    # Get pagination and sort settings from session state or region options
    # Get items per page (default to 15 if not specified)
    items_per_page = 15
    items_per_page_item = None

    # Check if items per page is specified in region options
    if region.template_options:
        try:
            opts = region.template_options if isinstance(region.template_options, dict) else {}
            if isinstance(opts, str):
                opts = json.loads(opts)

            items_per_page_item = opts.get("items_per_page_item")
            if items_per_page_item:
                # Get the value from session state
                ipp_value = session_service.get_item(session_id, page_id, items_per_page_item)
                if ipp_value and ipp_value.isdigit():
                    items_per_page = int(ipp_value)
            else:
                # Direct value in options
                items_per_page = int(opts.get("items_per_page", items_per_page))
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

    # Get current page from session state (default to 1)
    page_item = None
    if region.template_options:
        try:
            opts = region.template_options if isinstance(region.template_options, dict) else {}
            if isinstance(opts, str):
                opts = json.loads(opts)

            page_item = opts.get("page_item")
            if page_item:
                # Get the value from session state
                page_value = session_service.get_item(session_id, page_id, page_item)
                if page_value and page_value.isdigit():
                    current_page = int(page_value)
                else:
                    current_page = 1
            else:
                # Default page from options
                current_page = int(opts.get("page", 1))
        except (json.JSONDecodeError, TypeError, ValueError):
            current_page = 1
    else:
        current_page = 1

    # Get sort settings
    sort_column = None
    sort_direction = "ASC"  # Default to ascending
    sort_column_item = None
    sort_direction_item = None

    if region.template_options:
        try:
            opts = region.template_options if isinstance(region.template_options, dict) else {}
            if isinstance(opts, str):
                opts = json.loads(opts)

            sort_column_item = opts.get("sort_column_item")
            if sort_column_item:
                # Get the value from session state
                sort_column = session_service.get_item(session_id, page_id, sort_column_item)
                # If not set in session, check for direct value
                if not sort_column:
                    sort_column = opts.get("sort_column")
            else:
                # Direct value in options
                sort_column = opts.get("sort_column")

            sort_direction_item = opts.get("sort_direction_item")
            if sort_direction_item:
                # Get the value from session state
                sort_direction = session_service.get_item(session_id, page_id, sort_direction_item)
                # If not set in session, check for direct value
                if not sort_direction:
                    sort_direction = opts.get("sort_direction", "ASC").upper()
            else:
                # Direct value in options
                sort_direction = opts.get("sort_direction", "ASC").upper()

            # Validate sort direction
            if sort_direction not in ["ASC", "DESC"]:
                sort_direction = "ASC"
        except (json.JSONDecodeError, TypeError):
            pass

    # Ensure minimum values
    items_per_page = max(1, items_per_page)
    current_page = max(1, current_page)

    # Calculate offset
    offset = (current_page - 1) * items_per_page

    # Store pagination and sort info in session state for potential reset process
    # We'll store it with a standard naming convention
    pagination_prefix = f"RP_{region.id}"
    session_service.set_item(session_id, page_id, f"{pagination_prefix}_ROW_OFFSET", offset)
    session_service.set_item(session_id, page_id, f"{pagination_prefix}_SORT_COLUMN", sort_column or "")
    session_service.set_item(session_id, page_id, f"{pagination_prefix}_SORT_DIRECTION", sort_direction)
    # Note: We'll update the row count after executing the query

    # Substitute session items in the SQL query
    substituted_sql = rendering_service._substitute_strings(sql_query, session_id, page_id)

    try:
        # Add ORDER BY if sort column is specified
        ordered_sql = substituted_sql.strip()
        if sort_column:
            # Basic validation to prevent SQL injection - in production, use whitelist
            # For now, we'll just check that it doesn't contain dangerous characters
            if ";" not in sort_column and "--" not in sort_column and "/*" not in sort_column:
                ordered_sql = f"{ordered_sql} ORDER BY {sort_column} {sort_direction}"

        # Add LIMIT and OFFSET for pagination
        paginated_sql = f"{ordered_sql} LIMIT {items_per_page} OFFSET {offset}"

        # Execute the query
        result = db.execute(paginated_sql)

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

        # Update the row count in session state
        session_service.set_item(session_id, page_id, f"{pagination_prefix}_ROW_COUNT", len(rows))

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

    # Get total row count for pagination controls (without LIMIT/OFFSET)
    total_rows = 0
    try:
        # Create a count query - this is simplified and might not work for all SQL
        # A production implementation would need to be more sophisticated
        count_sql = f"SELECT COUNT(*) FROM ({substituted_sql}) count_table"
        # Remove ORDER BY if present for count query (can cause issues in some databases)
        # This is a simple approach - a real implementation would parse the SQL properly
        if " ORDER BY " in count_sql.upper():
            # Find the ORDER BY clause and remove it for the count query
            # This is simplified - a real implementation would be more robust
            parts = count_sql.split(" ORDER BY ")
            select_part = parts[0]
            # Reconstruct without ORDER BY
            count_sql = f"SELECT COUNT(*) FROM ({select_part}) count_table"

        count_result = db.execute(count_sql)
        total_rows = list(count_result)[0][0] if list(count_result) else 0
    except Exception:
        # If we can't get the count, we'll hide the pagination controls
        total_rows = 0

    # Build the HTML table
    html_parts = [
        f"<div class='report-region' data-region-id='{region.id}'>",
        f"  <div class='report-header'>",
        f"    <h3>{region.name}</h3>",
        f"  </div>",
        f"  <div class='report-body'>",
    ]

    # Add pagination controls if we have data
    if total_rows > 0:
        total_pages = max(1, math.ceil(total_rows / items_per_page))
        has_previous = current_page > 1
        has_next = current_page < total_pages

        html_parts.append(f"    <div class='report-pagination'>")
        html_parts.append(f"      <span class='pagination-info'>")
        start_row = offset + 1 if rows else 0
        end_row = offset + len(rows)
        html_parts.append(f"        Showing {start_row}-{end_row} of {total_rows} rows")
        html_parts.append(f"      </span>")

        if has_previous or has_next:
            html_parts.append(f"      <div class='pagination-controls'>")
            if has_previous:
                # Link to previous page
                prev_page_item = page_item or f"{pagination_prefix}_PAGE"
                # In a real implementation, this would generate a URL or trigger a submit
                # For now, we'll just show the text with a data attribute for JS handling
                html_parts.append(f"        <button type='button' class='pagination-prev' data-page='{current_page - 1}' data-sort-column='{sort_column}' data-sort-direction='{sort_direction}'>« Previous</button>")
            if has_next:
                # Link to next page
                next_page_item = page_item or f"{pagination_prefix}_PAGE"
                html_parts.append(f"        <button type='button' class='pagination-next' data-page='{current_page + 1}' data-sort-column='{sort_column}' data-sort-direction='{sort_direction}'>Next »</button>")
            # Add page selector if there are many pages
            if total_pages > 1:
                html_parts.append(f"      </div>")
                html_parts.append(f"      <div class='page-selector'>")
                html_parts.append(f"        <select class='page-select' data-page-item='{page_item or ''}' data-sort-column='{sort_column}' data-sort-direction='{sort_direction}'>")
                for p in range(1, min(total_pages + 1, 11)):  # Show first 10 pages
                    selected = ' selected' if p == current_page else ''
                    html_parts.append(f"          <option value='{p}'{selected}>{p}</option>")
                if total_pages > 10:
                    html_parts.append(f"          <option value='...'>...</option>")
                    # Add last page
                    html_parts.append(f"          <option value='{total_pages}'>{total_pages}</option>")
                html_parts.append(f"        </select>")
                html_parts.append(f"      </div>")
            html_parts.append(f"    </div>")

    html_parts.extend([
        f"    <table class='report-table'>",
        f"      <thead>",
        f"        <tr>"
    ])

    # Add header cells with sorting capability
    for i, column in enumerate(columns):
        # Determine if this column is currently being sorted
        is_sorted = (sort_column and
                    (sort_column == column or
                     (sort_column.isdigit() and int(sort_column) == i + 1)))

        # Determine sort direction for this column (toggle if clicking same column)
        if is_sorted:
            next_direction = "DESC" if sort_direction == "ASC" else "ASC"
        else:
            # Default to ASC for new sort columns
            next_direction = "ASC"

        # Create sort indicator
        sort_indicator = ""
        if is_sorted:
            sort_indicator = " ▲" if sort_direction == "ASC" else " ▼"

        # Make headers clickable for sorting (in a real implementation, this would trigger a form submit or AJAX call)
        # For now, we'll add data attributes that JavaScript could use
        html_parts.append(f"          <th class='sortable' data-column-index='{i}' data-column-name='{column}' data-sort-direction='{next_direction}'>{column}{sort_indicator}</th>")

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