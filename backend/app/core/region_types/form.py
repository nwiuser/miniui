"""
Form Region Renderer
Renders regions of type 'form' which contain form items for data entry.
"""
from typing import List
from sqlalchemy.orm import Session

from ...db import models
from ..item_types import (
    render_text_item,
    render_textarea_item,
    render_select_item,
    render_checkbox_item,
    render_radio_item,
    render_date_picker_item,
    render_display_only_item,
    render_hidden_item
)


def form_region(region: models.Region, db: Session, session_id: str, page_id: int) -> str:
    """
    Render a form region containing form items.

    Args:
        region: The region database object
        db: Database session
        session_id: The current session ID
        page_id: The current page ID

    Returns:
        HTML string containing the form with all its items
    """
    # Get all items for this region/position
    # In a real APEX, items belong to pages, not regions directly
    # But for simplicity, we'll get all items for the page and let the template
    # determine layout, or we could add a region_id to page items
    # For this MVP, we'll get all page items and render them in the form

    page_items = db.query(models.PageItem).filter(
        models.PageItem.page_id == page_id,
        models.PageItem.is_active == True
    ).order_by(models.PageItem.id).all()  # Order by ID or we could add a display_sequence

    # Group items by type for rendering
    html_parts = [
        f"<div class='form-region' data-region-id='{region.id}'>",
        f"  <div class='form-header'>",
        f"    <h3>{region.name}</h3>",
        f"  </div>",
        f"  <div class='form-body'>",
        f"    <form class='apex-form' method='post' action='/ords/apex/{region.page.application.alias}/{region.page.page_number}'>",
        f"      <input type='hidden' name='p_session_id' value='{session_id}'>",
        f"      <input type='hidden' name='p_request' value='SUBMIT'>",
        f"      <div class='form-fields'>"
    ]

    # Render each item
    for item in page_items:
        item_html = _render_form_item(item, db, session_id, page_id)
        if item_html:
            html_parts.append(f"      <div class='form-item-group' data-item-id='{item.id}'>")
            html_parts.append(f"        {item_html}")
            html_parts.append(f"      </div>")

    html_parts.extend([
        f"      </div>",  # Close form-fields
        f"      <div class='form-buttons'>",
        f"        <button type='submit' class='button'>Submit</button>",
        f"        <button type='button' class='button cancel'>Cancel</button>",
        f"      </div>",
        f"    </form>",
        f"  </div>",
        f"</div>"
    ])

    return "\n".join(html_parts)


def _render_form_item(item: 'PageItem', db: Session, session_id: str, page_id: int) -> str:
    """Render a single form item based on its type."""
    item_type = item.item_type.lower()

    # Get the current value from session state
    from ..session.service import SessionService
    # We need to create a session service to get the value
    # This is not ideal - we should pass the session service in
    from sqlalchemy.orm import Session
    session_service = SessionService(db)
    current_value = session_service.get_item(session_id, page_id, item.name)

    # Use the current value if available, otherwise use the default
    value_to_use = current_value if current_value is not None else (item.default_value or "")

    if item_type == "text":
        return render_text_item(item, value_to_use)
    elif item_type == "textarea":
        return render_textarea_item(item, value_to_use)
    elif item_type == "select":
        return render_select_item(item, value_to_use, db)
    elif item_type == "checkbox":
        return render_checkbox_item(item, value_to_use)
    elif item_type == "radio":
        return render_radio_item(item, value_to_use, db)
    elif item_type == "date_picker":
        return render_date_picker_item(item, value_to_use)
    elif item_type == "display_only":
        return render_display_only_item(item, value_to_use)
    elif item_type == "hidden":
        return render_hidden_item(item, value_to_use)
    else:
        # Unknown item type - render as text input for safety
        return render_text_item(item, value_to_use)