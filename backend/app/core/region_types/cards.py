"""
Cards Region Renderer
Renders regions of type 'cards' which display KPI/dashboard cards in the
style of an Oracle APEX Cards region: a responsive grid of cards, each with
an optional icon medallion, a title, a large value, an optional subtitle and
an optional change badge.

Two sources feed the cards, in this order:

1. Static cards from ``region.template_options["cards"]`` — a list of
   ``{"title": ..., "value": ..., "subtitle": ..., "icon": ...,
   "change": ..., "change_direction": "up"|"down", "accent": ...}`` mappings.
   These are fixed KPIs authored in the visual builder. ``icon`` is a short
   glyph (emoji or character) shown in a tinted medallion.
2. Page items assigned to this region (``PageItem.region_id``) — each item
   becomes a card showing its label and current session value (or default).
   ``hidden`` items are skipped.

When neither source yields a card, a placeholder is rendered so the region is
still visible on the page.
"""
from html import escape
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ...db import models
from ..session.service import SessionService


_ACCENTS = {"blue", "green", "purple", "amber", "red"}


def _region_options(region: models.Region) -> Dict[str, Any]:
    """Normalise region.template_options into a dict."""
    import json

    if not region.template_options:
        return {}
    options = region.template_options
    if isinstance(options, (str, bytes)):
        try:
            options = json.loads(options)
        except (ValueError, TypeError):
            return {}
    return options if isinstance(options, dict) else {}


def _card_html(
    title: str,
    value: str,
    subtitle: str = "",
    icon: str = "",
    change: str = "",
    change_direction: str = "",
    accent: str = "blue",
) -> str:
    """Render a single KPI card. All inputs are HTML-escaped."""
    accent = accent if accent in _ACCENTS else "blue"
    direction = change_direction if change_direction in ("up", "down") else ""
    parts = [
        f"<div class='kpi-card kpi-accent-{accent}'>",
    ]
    if icon:
        parts.append(
            f"  <div class='kpi-icon kpi-icon-{accent}'>{escape(str(icon))}</div>"
        )
    parts.extend(
        [
            f"  <div class='kpi-title'>{escape(str(title))}</div>",
            f"  <div class='kpi-value'>{escape(str(value))}</div>",
        ]
    )
    if subtitle:
        parts.append(f"  <div class='kpi-subtitle'>{escape(str(subtitle))}</div>")
    if change:
        arrow = "&#9650;" if direction == "up" else "&#9660;" if direction == "down" else ""
        badge_class = f" kpi-{direction}" if direction else ""
        text = f"{arrow} {escape(str(change))}".strip()
        parts.append(f"  <span class='kpi-badge{badge_class}'>{text}</span>")
    parts.append("</div>")
    return "\n".join(parts)


def render_cards_region(
    region: models.Region,
    db: Session,
    session_id: str,
    page_id: int,
    session_service: SessionService = None,
) -> str:
    """
    Render a cards region containing KPI cards.

    Args:
        region: The region database object
        db: Database session
        session_id: The current session ID
        page_id: The current page ID
        session_service: Optional SessionService instance; if None, a new one is created.

    Returns:
        HTML string containing the KPI cards grid
    """
    if session_service is None:
        session_service = SessionService(db)

    cards: List[str] = []

    # 1. Static cards authored in the builder (template_options["cards"]).
    options = _region_options(region)
    configured = options.get("cards") or []
    if isinstance(configured, list):
        for entry in configured:
            if not isinstance(entry, dict):
                continue
            title = entry.get("title", "")
            value = entry.get("value", "")
            if title == "" and value == "":
                continue
            cards.append(
                _card_html(
                    title=title,
                    value=value,
                    subtitle=entry.get("subtitle", ""),
                    icon=entry.get("icon", ""),
                    change=entry.get("change", ""),
                    change_direction=entry.get("change_direction", ""),
                    accent=entry.get("accent", "blue"),
                )
            )

    # 2. Page items assigned to this region become live KPI cards.
    region_items = (
        db.query(models.PageItem)
        .filter(
            models.PageItem.page_id == page_id,
            models.PageItem.region_id == region.id,
            models.PageItem.is_active == True,
        )
        .order_by(models.PageItem.id)
        .all()
    )
    for item in region_items:
        if (item.item_type or "").lower() == "hidden":
            continue
        current = session_service.get_item(session_id, page_id, item.name)
        value = current if current is not None else (item.default_value or "")
        cards.append(_card_html(title=item.label or item.name, value=value))

    body = "\n".join(cards) if cards else (
        "<div class='cards-empty'><p>No KPI cards defined for this region yet.</p></div>"
    )

    # Note: no inner region header here — the page template already wraps every
    # region with its title bar, and a second one just echoes the name.
    return "\n".join(
        [
            f"<div class='cards-region' data-region-id='{region.id}'>",
            f"  <div class='kpi-cards'>",
            body,
            f"  </div>",
            f"</div>",
        ]
    )
