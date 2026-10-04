"""
Static Content Region Renderer
Renders regions of type 'static_content' which contain raw HTML/CSS/JavaScript.
"""
from typing import Optional
from sqlalchemy.orm import Session
import json

from ...db import models
from ..session.service import SessionService
from .form import _render_form_item


def render_static_content_region(
    region: models.Region,
    db: Session,
    session_id: Optional[str] = None,
    page_id: Optional[int] = None,
    session_service: Optional[SessionService] = None,
) -> str:
    """
    Render a static content region.

    Args:
        region: The region database object
        db: Database session
        session_id: Optional session ID used to resolve item values
        page_id: Optional page ID used to resolve item values
        session_service: Optional SessionService instance

    Returns:
        HTML string containing the region's content plus any page items
        assigned to this region.
    """
    # For static content regions, the template_options might contain
    # the actual HTML content or a reference to it
    # In a simple implementation, we might store the content directly
    # in a column, or in template_options as JSON

    # For this MVP, let's assume the content is stored in template_options
    # as a 'content' key, or we could have a separate content column
    # Since we don't have a content column yet, we'll use template_options

    content = "<!-- No content defined for static content region -->"

    if region.template_options:
        try:
            options = region.template_options
            if isinstance(options, (str, bytes)):
                options = json.loads(options)
            if not isinstance(options, dict):
                options = {}

            content = options.get("content", content)
        except (json.JSONDecodeError, TypeError, ValueError):
            # If template_options is not valid JSON, treat it as raw content
            content = str(region.template_options)

    # Wrap the content in a container div with appropriate classes
    html = f"""
    <div class='static-content-region' data-region-id='{region.id}'>
        {content}
    </div>
    """.strip()

    # Render page items assigned to this region beneath the static content,
    # so items dropped into the region in the builder are visible on the page.
    if session_id is not None and page_id is not None:
        if session_service is None:
            session_service = SessionService(db)
        region_items = db.query(models.PageItem).filter(
            models.PageItem.page_id == page_id,
            models.PageItem.region_id == region.id,
            models.PageItem.is_active == True
        ).order_by(models.PageItem.id).all()
        if region_items:
            parts = [html, "<div class='static-region-items'>"]
            for item in region_items:
                item_html = _render_form_item(item, db, session_id, page_id, session_service)
                if item_html:
                    parts.append(f"<div class='form-item-group' data-item-id='{item.id}'>")
                    parts.append(item_html)
                    parts.append("</div>")
            parts.append("</div>")
            html = "\n".join(parts)

    return html