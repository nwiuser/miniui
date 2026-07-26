"""
Static Content Region Renderer
Renders regions of type 'static_content' which contain raw HTML/CSS/JavaScript.
"""
from typing import Optional
from sqlalchemy.orm import Session

from ...db import models


def render_static_content_region(region: models.Region, db: Session) -> str:
    """
    Render a static content region.

    Args:
        region: The region database object
        db: Database session

    Returns:
        HTML string containing the region's content
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
            options = region.template_options if isinstance(region.template_options, dict) else {}
            if isinstance(options, str):
                import json
                options = json.loads(options)

            content = options.get("content", content)
        except (json.JSONDecodeError, TypeError):
            # If template_options is not valid JSON, treat it as raw content
            content = str(region.template_options)

    # Wrap the content in a container div with appropriate classes
    html = f"""
    <div class='static-content-region' data-region-id='{region.id}'>
        {content}
    </div>
    """.strip()

    return html