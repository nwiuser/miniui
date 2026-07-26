"""
Date Picker Item Renderer
Renders items of type 'date_picker' as HTML date input elements.
"""
import html

def render_date_picker_item(item, value: str = "") -> str:
    """
    Render a date picker input item.

    Args:
        item: The page item database object
        value: The current value of the item (expected in YYYY-MM-DD format)

    Returns:
        HTML string for the date input
    """
    # Start building the input element
    html_str = "<input type='date' name='" + item.name + "' id='" + item.name + "'"

    # Add value if present (should be in YYYY-MM-DD format for date input)
    if value:
        # For MVP, we'll assume it's already in the correct format or empty
        html_str += " value='" + html.escape(str(value)) + "'"

    # Add placeholder if present
    placeholder = getattr(item, 'placeholder', None)
    if placeholder:
        escaped_placeholder = html.escape(str(placeholder))
        html_str += " placeholder='" + escaped_placeholder + "'"

    # Add CSS classes
    css_classes = ["form-date-picker"]
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

    # Add min/max attributes if specified
    min_date = getattr(item, 'min_date', None)
    if min_date:
        html_str += " min='" + html.escape(str(min_date)) + "'"
    max_date = getattr(item, 'max_date', None)
    if max_date:
        html_str += " max='" + html.escape(str(max_date)) + "'"

    # Add step attribute (for time components) - default to 1 day
    step = getattr(item, 'step', None)
    if not step:
        html_str += " step='1'"  # 1 day
    else:
        html_str += " step='" + html.escape(str(step)) + "'"

    # Add data attributes for AJAX etc.
    html_str += " data-item-id='" + str(item.id) + "'"

    # Close the tag
    html_str += "/>"

    # If there's a post-text element, add it after
    post_element_text = getattr(item, 'post_element_text', None)
    if post_element_text:
        escaped_post = html.escape(str(post_element_text))
        html_str += "<span class='post-text'> " + escaped_post + "</span>"

    return html_str