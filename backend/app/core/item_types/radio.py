"""
Radio Item Renderer
Renders items of type 'radio' as HTML radio button groups.
"""
import html
from typing import List, Tuple
from sqlalchemy.orm import Session

def render_radio_item(item, value: str = "", db: Session = None) -> str:
    """
    Render a radio button group item.

    Args:
        item: The page item database object
        value: The current value of the item
        db: Database session (needed for LOV queries)

    Returns:
        HTML string for the radio button group
    """
    # Get the options (radio button choices)
    options = _get_radio_options(item, db)

    # Start building the container for the radio group
    css_classes = ["form-radio-group"]
    element_css_classes = getattr(item, 'element_css_classes', None)
    if element_css_classes:
        css_classes.extend(element_css_classes.split())
    element_css_class = getattr(item, 'element_css_class', None)
    if element_css_class:
        css_classes.append(element_css_class)
    class_attr = " ".join(css_classes)

    style_attr = ""
    element_style = getattr(item, 'element_style', None)
    if element_style:
        style_attr = " style='" + html.escape(element_style) + "'"

    readonly_attr = " readonly" if getattr(item, 'readonly', False) else ""
    disabled_attr = " disabled" if getattr(item, 'disabled', False) else ""
    required_attr = " required" if getattr(item, 'is_required', False) else ""

    html_str = "<div class='" + class_attr + "'" + style_attr + readonly_attr + disabled_attr + required_attr + " data-item-id='" + str(item.id) + "'>"

    # Add the label if present
    label = getattr(item, 'label', None)
    if label:
        escaped_label = html.escape(str(label))
        html_str += "<label for='" + item.name + "_label' class='radio-label'>" + escaped_label + "</label>"

    # Create each radio button
    for option_label, option_value in options:
        # Escape the label and value for HTML
        escaped_label = html.escape(str(option_label))
        escaped_value = html.escape(str(option_value))

        # Determine if this radio button should be checked
        checked = " checked" if str(option_value) == str(value) else ""

        # Build the radio button input
        # Create a safe ID by replacing quotes and spaces
        raw_id = item.name + "_" + str(option_value)
        safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in raw_id)
        radio_html = ("<input type='radio' name='" + item.name +
                      "' id='" + safe_id +
                      "' value='" + escaped_value + "'" +
                      checked + readonly_attr + disabled_attr + ">")

        # Add the label for this radio button
        html_str += ("<label for='" + safe_id + "' class='radio-option-label'>" +
                     escaped_label + "</label>")

        html_str += "<div class='radio-option'>" + radio_html + "</div>"

    # Close the container
    html_str += "</div>"

    # If there's a post-text element, add it after
    post_element_text = getattr(item, 'post_element_text', None)
    if post_element_text:
        escaped_post = html.escape(str(post_element_text))
        html_str += "<span class='post-text'> " + escaped_post + "</span>"

    return html_str


def _get_radio_options(item: 'PageItem', db: Session) -> List[Tuple[str, str]]:
    """
    Get the list of options for a radio item.

    Args:
        item: The page item database object
        db: Database session

    Returns:
        List of tuples (label, value) for each option
    """
    options = []

    # Check if this item has a list of values (LOV) defined
    if getattr(item, 'lov_id', None):
        # Get the LOV definition
        from ... import models
        lov = db.query(models.Lov).filter(models.Lov.id == item.lov_id).first()
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