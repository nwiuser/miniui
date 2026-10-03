import pytest

from app.core.item_types import (
    render_checkbox_item,
    render_date_picker_item,
    render_display_only_item,
    render_hidden_item,
    render_password_item,
    render_radio_item,
    render_select_item,
    render_text_item,
    render_textarea_item,
)


class _Item:
    """Minimal stand-in for a PageItem row.

    The renderers read presentation attributes with getattr(item, ..., default),
    so plain attribute assignment is enough to drive them.
    """

    def __init__(self, **kwargs):
        self.id = kwargs.pop("id", 1)
        self.name = kwargs.pop("name", "P1_FIELD")
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestTextItem:
    def test_renders_text_input(self):
        html = render_text_item(_Item(), "hello")
        assert "<input type='text'" in html
        assert "name='P1_FIELD'" in html
        assert "id='P1_FIELD'" in html
        assert "value='hello'" in html

    def test_escapes_value(self):
        html = render_text_item(_Item(), "<script>alert(1)</script>")
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_renders_placeholder_and_class(self):
        html = render_text_item(_Item(placeholder="Type here"))
        assert "placeholder='Type here'" in html
        assert "class='form-text'" in html

    def test_empty_value_omits_value_attribute_content(self):
        html = render_text_item(_Item(), "")
        assert "value=''" in html

    def test_extra_css_classes_and_style(self):
        html = render_text_item(
            _Item(element_css_classes="a b", element_css_class="c", element_style="color:red")
        )
        assert "class='form-text a b c'" in html
        assert "style='color:red'" in html

    def test_required_readonly_disabled_flags(self):
        html = render_text_item(_Item(is_required=True, readonly=True, disabled=True))
        assert " required" in html
        assert " readonly" in html
        assert " disabled" in html

    def test_post_element_text(self):
        html = render_text_item(_Item(post_element_text="kg"))
        assert "<span class='post-text'> kg</span>" in html

    def test_data_item_id_attribute(self):
        html = render_text_item(_Item(id=42))
        assert "data-item-id='42'" in html


class TestTextareaItem:
    def test_renders_textarea(self):
        html = render_textarea_item(_Item(), "body text")
        assert "<textarea" in html
        assert ">body text</textarea>" in html
        assert "class='form-textarea'" in html

    def test_escapes_value(self):
        html = render_textarea_item(_Item(), "a & b")
        assert "a &amp; b" in html

    def test_placeholder_and_flags(self):
        html = render_textarea_item(_Item(placeholder="Notes", is_required=True, disabled=True))
        assert "placeholder='Notes'" in html
        assert " required" in html
        assert " disabled" in html


class TestHiddenItem:
    def test_renders_hidden_input(self):
        html = render_hidden_item(_Item(), "secret")
        assert "<input type='hidden'" in html
        assert "value='secret'" in html

    def test_escapes_value(self):
        html = render_hidden_item(_Item(), "a\"b")
        assert 'a"b' not in html
        assert "a&quot;b" in html

    def test_no_value_attribute_when_none(self):
        html = render_hidden_item(_Item(), None)
        assert "value=" not in html

    def test_classes_and_style(self):
        html = render_hidden_item(
            _Item(element_css_classes="x", element_css_class="y", element_style="display:none")
        )
        assert "class='x y'" in html
        assert "style='display:none'" in html


class TestPasswordItem:
    def test_renders_password_input(self):
        html = render_password_item(_Item(), "hunter2")
        assert "<input type='password'" in html
        assert "class='form-password'" in html
        assert "value='hunter2'" in html

    def test_placeholder_and_flags(self):
        html = render_password_item(_Item(placeholder="Password", is_required=True, readonly=True))
        assert "placeholder='Password'" in html
        assert " required" in html
        assert " readonly" in html

    def test_escapes_value(self):
        html = render_password_item(_Item(), "a<b")
        assert "a&lt;b" in html


class TestDisplayOnlyItem:
    def test_renders_span_with_value(self):
        html = render_display_only_item(_Item(), "42")
        assert html.startswith("<span")
        assert ">42</span>" in html
        assert "class='form-display-only'" in html

    def test_always_readonly(self):
        html = render_display_only_item(_Item())
        assert " readonly" in html

    def test_escapes_value(self):
        html = render_display_only_item(_Item(), "<b>")
        assert "<b>" not in html
        assert "&lt;b&gt;" in html


class TestDatePickerItem:
    def test_renders_date_input(self):
        html = render_date_picker_item(_Item(), "2024-01-31")
        assert "<input type='date'" in html
        assert "value='2024-01-31'" in html
        assert "class='form-date-picker'" in html

    def test_default_step_is_one_day(self):
        html = render_date_picker_item(_Item())
        assert "step='1'" in html

    def test_explicit_step_overrides_default(self):
        html = render_date_picker_item(_Item(step=7))
        assert "step='7'" in html

    def test_min_and_max_dates(self):
        html = render_date_picker_item(_Item(min_date="2024-01-01", max_date="2024-12-31"))
        assert "min='2024-01-01'" in html
        assert "max='2024-12-31'" in html

    def test_no_value_attribute_when_empty(self):
        html = render_date_picker_item(_Item(), "")
        assert "value=" not in html


class TestCheckboxItem:
    @pytest.mark.parametrize("value", ["Y", "y", "yes", "YES", "true", "1", "on"])
    def test_truthy_values_render_checked(self, value):
        html = render_checkbox_item(_Item(), value)
        assert " checked" in html

    @pytest.mark.parametrize("value", ["", None, "N", "n", "false", "0", "off"])
    def test_falsy_values_render_unchecked(self, value):
        html = render_checkbox_item(_Item(), value)
        assert " checked" not in html

    def test_default_value_is_y(self):
        html = render_checkbox_item(_Item())
        assert "value='Y'" in html

    def test_custom_checkbox_value_attribute(self):
        html = render_checkbox_item(_Item(checkbox_value="ON"), "ON")
        assert "value='ON'" in html
        assert " checked" in html

    def test_label_is_rendered(self):
        html = render_checkbox_item(_Item(label="I Agree"))
        assert "<label for='P1_FIELD'>I Agree</label>" in html

    def test_label_is_escaped(self):
        html = render_checkbox_item(_Item(label="<b>Yes</b>"))
        assert "<b>Yes</b>" not in html
        assert "&lt;b&gt;Yes&lt;/b&gt;" in html

    def test_wrapper_div_is_emitted_exactly_once(self):
        html = render_checkbox_item(_Item(label="I Agree"))
        assert html.count("<div class='checkbox-item'>") == 1
        assert html.count("</div>") == 1

    def test_input_appears_exactly_once(self):
        html = render_checkbox_item(_Item(label="I Agree"), "Y")
        assert html.count("type='checkbox'") == 1

    def test_css_classes(self):
        html = render_checkbox_item(_Item(element_css_classes="a", element_css_class="b"))
        assert "class='form-checkbox a b'" in html

    def test_flags(self):
        html = render_checkbox_item(_Item(is_required=True, readonly=True, disabled=True))
        assert " required" in html
        assert " readonly" in html
        assert " disabled" in html

    def test_post_element_text(self):
        html = render_checkbox_item(_Item(post_element_text="optional"))
        assert "<span class='post-text'> optional</span>" in html


class TestSelectItem:
    def test_renders_select_with_options(self):
        html = render_select_item(_Item(), "")
        assert "<select" in html
        assert "</select>" in html
        assert "class='form-select'" in html
        assert "<option value='1'>Option 1</option>" in html

    def test_placeholder_option_when_no_value(self):
        html = render_select_item(_Item())
        assert "<option value='' class='placeholder'>-- Select --</option>" in html

    def test_placeholder_text_is_configurable(self):
        html = render_select_item(_Item(placeholder="Pick one"))
        assert ">Pick one</option>" in html

    def test_no_placeholder_option_when_value_present(self):
        html = render_select_item(_Item(), "2")
        assert "class='placeholder'" not in html
        assert "<option value='2' selected>Option 2</option>" in html

    def test_static_lov_options_are_used(self, db_session):
        from app.db import models

        lov = models.Lov(
            lov_name="COLORS",
            is_static=True,
            static_values="STATIC2:r;Red,g;Green,b;Blue",
        )
        db_session.add(lov)
        db_session.commit()
        db_session.refresh(lov)

        html = render_select_item(_Item(lov_id=lov.id), "g", db_session)
        assert "<option value='r'>Red</option>" in html
        assert "<option value='g' selected>Green</option>" in html
        assert "<option value='b'>Blue</option>" in html

    def test_static_lov_without_stat2_prefix(self, db_session):
        from app.db import models

        lov = models.Lov(lov_name="PLAIN", is_static=True, static_values="a;Alpha,b;Beta")
        db_session.add(lov)
        db_session.commit()
        db_session.refresh(lov)

        html = render_select_item(_Item(lov_id=lov.id), "", db_session)
        assert "<option value='a'>Alpha</option>" in html
        assert "<option value='b'>Beta</option>" in html

    def test_unknown_lov_falls_back_to_default_options(self, db_session):
        html = render_select_item(_Item(lov_id=9999), "", db_session)
        assert "<option value='1'>Option 1</option>" in html

    def test_flags_and_classes(self):
        html = render_select_item(
            _Item(element_css_classes="a", element_css_class="b", is_required=True, disabled=True)
        )
        assert "class='form-select a b'" in html
        assert " required" in html
        assert " disabled" in html


class TestRadioItem:
    def test_renders_radio_group(self):
        html = render_radio_item(_Item(), "")
        assert "class='form-radio-group'" in html
        assert html.count("type='radio'") == 3

    def test_selected_option_is_checked(self):
        html = render_radio_item(_Item(), "2")
        assert "value='2' checked" in html
        assert html.count(" checked") == 1

    def test_group_label(self):
        html = render_radio_item(_Item(label="Colour"))
        assert ">Colour</label>" in html

    def test_static_lov_options(self, db_session):
        from app.db import models

        lov = models.Lov(lov_name="SIZES", is_static=True, static_values="S;Small,L;Large")
        db_session.add(lov)
        db_session.commit()
        db_session.refresh(lov)

        html = render_radio_item(_Item(lov_id=lov.id), "L", db_session)
        assert "value='S'" in html
        assert "value='L' checked" in html
        assert ">Large</label>" in html

    def test_radio_ids_are_sanitised(self, db_session):
        from app.db import models

        lov = models.Lov(lov_name="ODD", is_static=True, static_values="a b;Spaced,x'y;Quoted")
        db_session.add(lov)
        db_session.commit()
        db_session.refresh(lov)

        html = render_radio_item(_Item(lov_id=lov.id), "", db_session)
        assert "id='P1_FIELD_a_b'" in html
        assert "id='P1_FIELD_x_y'" in html
        assert "id=\"P1_FIELD_x'y\"" not in html

    def test_radio_option_values_are_escaped(self, db_session):
        from app.db import models

        lov = models.Lov(lov_name="XSS", is_static=True, static_values="a<b;Bold")
        db_session.add(lov)
        db_session.commit()
        db_session.refresh(lov)

        html = render_radio_item(_Item(lov_id=lov.id), "", db_session)
        assert "value='a&lt;b'" in html
        assert "value='a<b'" not in html

    def test_flags_propagate_to_inputs(self):
        html = render_radio_item(_Item(is_required=True, disabled=True, readonly=True))
        assert " required" in html
        assert " disabled" in html
        assert " readonly" in html

    def test_fallback_options_when_no_lov(self):
        html = render_radio_item(_Item(), "")
        assert ">Option 1</label>" in html
        assert ">Option 3</label>" in html
