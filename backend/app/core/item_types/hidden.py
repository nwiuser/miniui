"""
Hidden Item Renderer
Renders items of type 'hidden' as HTML hidden inputs.
"""
import html

def render_hidden_item(item, value: str = "") -> str:
    """
    Render a hidden input item.

    Args:
        item: The page item database object
        value: The current value of the item

    Returns:
        HTML string for the hidden input
    """
    # Escape the value for HTML
    escaped_value = html.escape(str(value))

    # Build the hidden input element
    html_str = "<input type='hidden' name='" + item.name + "' id='" + item.name + "'"

    # Add value if present
    if value is not None:
        html_str += " value='" + escaped_value + "'"

    # Add CSS classes (though hidden inputs don't typically need them)
    element_css_classes = getattr(item, 'element_css_classes', None)
    if element_css_classes:
        html_str += " class='" + html.escape(element_css_classes) + "'"
    element_css_class = getattr(item, 'element_css_class', None)
    if element_css_class:
        # Avoid duplicate class attribute
        if element_css_classes:
            combined = element_css_classes + " " + element_css_class
            html_str += " class='" + html.escape(combined) + "'"
        else:
            html_str += " class='" + html.escape(element_css_class) + "'"

    # Add inline styles (though hidden inputs don't typically need them)
    element_style = getattr(item, 'element_style', None)
    if element_style:
        html_str += " style='" + html.escape(element_style) + "'"

    # Add data attributes for AJAX etc.
    html_str += " data-item-id='" + str(item.id) + "'"

    # Close the tag
    html_str += "/>"

    return html_str