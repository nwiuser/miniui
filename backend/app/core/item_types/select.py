"""
Select Item Renderer
Renders items of type 'select' as HTML select elements with options.
"""
import html
from sqlalchemy.orm import Session
from ...db import models

def render_select_item(item, value: str = "", db: Session = None) -> str:
    """
    Render a select input item.

    Args:
        item: The page item database object
        value: The current value of the item
        db: Database session (needed for LOV queries)

    Returns:
        HTML string for the select input
    """
    # Build the select element
    html_str = "<select name='" + item.name + "' id='" + item.name + "'"

    # Add CSS classes
    css_classes = ["form-select"]
    element_css_classes = getattr(item, 'element_css_classes', None)
    if element_css_classes:
        css_classes.extend(element_css_classes.split())
    element_css_class = getattr(item, 'element_css_class', None)
    if element_css_class:
        css_classes.append(element_css_class)
    if css_classes:
        html_str += " class='" + ' '.join(css_classes) + "'"

    # Add inline styles
    element_style = getattr(item, 'element_style', None)
    if element_style:
        html_str += " style='" + html.escape(element_style) + "'"

    # Add readonly/disabled attributes
    if getattr(item, 'readonly', False):
        html_str += " readonly"
    if getattr(item, 'disabled', False):
        html_str += " disabled"

    # Add required attribute
    if getattr(item, 'is_required', False):
        html_str += " required"

    # Add data attributes for AJAX etc.
    html_str += " data-item-id='" + str(item.id) + "'"

    # Close the opening tag
    html_str += ">"

    # Add a null option if applicable
    # This would come from LOV settings in a real implementation
    # For now, we'll add a placeholder if no value is selected
    if not value and not getattr(item, 'disabled', False):
        placeholder_text = getattr(item, 'placeholder', None) or '-- Select --'
        escaped_placeholder = html.escape(str(placeholder_text))
        html_str += "<option value='' class='placeholder'>" + escaped_placeholder + "</option>"

    # Get the options
    options = _get_select_options(item, db)

    # Add each option
    for option_label, option_value in options:
        # Escape the label and value for HTML
        escaped_label = html.escape(str(option_label))
        escaped_value = html.escape(str(option_value))

        # Determine if this option should be selected
        selected = " selected" if str(option_value) == str(value) else ""

        html_str += "<option value='" + escaped_value + "'" + selected + ">" + escaped_label + "</option>"

    # Close the select tag
    html_str += "</select>"

    # If there's a post-text element, add it after
    post_element_text = getattr(item, 'post_element_text', None)
    if post_element_text:
        escaped_post = html.escape(str(post_element_text))
        html_str += "<span class='post-text'> " + escaped_post + "</span>"

    return html_str


def _get_select_options(item: 'PageItem', db: Session) -> list:
    """
    Get the list of options for a select item.

    Args:
        item: The page item database object
        db: Database session

    Returns:
        List of tuples (label, value) for each option
    """
    options = []

    # Check if this item has a list of values (LOV) defined
    lov_id = getattr(item, 'lov_id', None)
    if lov_id:
        # Get the LOV definition
        lov = db.query(models.Lov).filter(models.Lov.id == lov_id).first()
        if lov:
            if getattr(lov, 'is_static', False) and getattr(lov, 'static_values', None):
                # Parse static values
                # Format: "STATIC2:Value1;Display1,Value2;Display2"
                static_values = lov.static_values
                if isinstance(static_values, str) and static_values.startswith("STATIC2:"):
                    static_values = static_values[8:]  # Remove the STATIC2: prefix

                # Split by commas to get each option
                pairs = [pair.strip() for pair in static_values.split(",") if pair.strip()]
                for pair in pairs:
                    if ":" in pair:
                        value, label = pair.split(":", 1)
                        options.append((label.strip(), value.strip()))
                    else:
                        # If no colon, use the same value for label and value
                        options.append((pair.strip(), pair.strip()))
            else:
                # It's a dynamic LOV - we need to execute the SQL query
                # For MVP, we'll return an empty list and note that this needs implementation
                # In a full implementation, we'd execute lov.lov_definition as SQL
                pass
    else:
        # Check for lov_definition directly on the item
        lov_definition = getattr(item, 'lov_definition', None)
        if lov_definition:
            # The lov_definition might be directly on the item
            # This would be a SQL query to execute
            # For MVP, we'll return an empty list
            pass

    # If we still have no options, provide a default
    if not options:
        options = [("Option 1", "1"), ("Option 2", "2"), ("Option 3", "3")]

    return options