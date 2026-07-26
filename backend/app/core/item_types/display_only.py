"""
Display Only Item Renderer
Renders items of type 'display_only' as plain text (non-editable).
"""
import html

def render_display_only_item(item, value: str = "") -> str:
    """
    Render a display only item.

    Args:
        item: The page item database object
        value: The current value of the item

    Returns:
        HTML string for the display only value
    """
    # Escape the value for HTML
    escaped_value = html.escape(str(value))

    # Build the display element (usually a span)
    html_str = "<span name='" + item.name + "' id='" + item.name + "'"

    # Add CSS classes
    css_classes = ["form-display-only"]
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

    # Add readonly attribute (display only items are always readonly)
    html_str += " readonly"

    # Add data attributes for AJAX etc.
    html_str += " data-item-id='" + str(item.id) + "'"

    # Close the opening tag and add the content
    html_str += ">" + escaped_value + "</span>"

    # If there's a post-text element, add it after
    post_element_text = getattr(item, 'post_element_text', None)
    if post_element_text:
        escaped_post = html.escape(str(post_element_text))
        html_str += "<span class='post-text'> " + escaped_post + "</span>"

    return html_str