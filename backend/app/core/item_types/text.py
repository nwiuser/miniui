"""
Text Item Renderer
Renders items of type 'text' as HTML input elements.
"""
import html

def render_text_item(item, value: str = "") -> str:
    """
    Render a text input item.

    Args:
        item: The page item database object
        value: The current value of the item

    Returns:
        HTML string for the text input
    """
    # Escape the value for HTML
    escaped_value = html.escape(str(value))

    # Build the input element
    html_str = "<input type='text' name='" + item.name + "' id='" + item.name + "'"

    # Add value if present
    if value is not None:
        html_str += " value='" + escaped_value + "'"

    # Add placeholder if present
    placeholder = getattr(item, 'placeholder', None)
    if placeholder:
        escaped_placeholder = html.escape(str(placeholder))
        html_str += " placeholder='" + escaped_placeholder + "'"

    # Add CSS classes
    css_classes = ["form-text"]
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

    # Close the tag
    html_str += " >"

    # If there's a post-text element, add it after
    post_element_text = getattr(item, 'post_element_text', None)
    if post_element_text:
        escaped_post = html.escape(str(post_element_text))
        html_str += "<span class='post-text'> " + escaped_post + "</span>"

    return html_str