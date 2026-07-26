"""
Checkbox Item Renderer
Renders items of type 'checkbox' as HTML checkbox inputs.
"""
import html

def render_checkbox_item(item, value: str = "") -> str:
    """
    Render a checkbox input item.

    Args:
        item: The page item database object
        value: The current value of the item (typically 'Y' for checked, 'N' or empty for unchecked)

    Returns:
        HTML string for the checkbox input
    """
    # Determine if the checkbox should be checked
    # In APEX, checkboxes typically use 'Y' for checked and 'N' for unchecked
    # But we'll handle common truthy values
    checked = False
    if value:
        value_lower = value.lower()
        if value_lower in ('y', 'yes', 'true', '1', 'on'):
            checked = True
        # Also check if the value matches the checkbox's value attribute
        elif hasattr(item, 'checkbox_value') and item.checkbox_value:
            if value == item.checkbox_value:
                checked = True

    # Build the input element
    html_str = "<input type='checkbox' name='" + item.name + "' id='" + item.name + "'"

    # Add CSS classes
    css_classes = ["form-checkbox"]
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

    # Add checked attribute
    if checked:
        html_str += " checked"

    # Add required attribute (though checkboxes are rarely required in the traditional sense)
    if getattr(item, 'is_required', False):
        html_str += " required"

    # Add data attributes for AJAX etc.
    html_str += " data-item-id='" + str(item.id) + "'"

    # Add the value attribute (what gets submitted when checked)
    checkbox_value = getattr(item, 'checkbox_value', None)
    if checkbox_value:
        html_str += " value='" + html.escape(str(checkbox_value)) + "'"
    else:
        # Default value for checkboxes
        html_str += " value='Y'"

    # Close the input tag
    html_str += "/>"

    # Wrap with label for better accessibility
    label_html = ""
    label = getattr(item, 'label', None)
    if label:
        escaped_label = html.escape(str(label))
        label_html = "<label for='" + item.name + "'>" + escaped_label + "</label>"

    # For checkboxes, the label usually comes after the input
    html_str = "<div class='checkbox-item'>"
    if label_html:
        html_str += label_html + " "
    html_str += html_str
    html_str += "</div>"

    # If there's a post-text element, add it after
    post_element_text = getattr(item, 'post_element_text', None)
    if post_element_text:
        escaped_post = html.escape(str(post_element_text))
        html_str += "<span class='post-text'> " + escaped_post + "</span>"

    return html_str