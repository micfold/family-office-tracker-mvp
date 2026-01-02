# src/views/components/numeric_input.py
import streamlit as st
import re
from decimal import Decimal, InvalidOperation

def render_numeric_input(label, value=0.0, key=None):
    """
    Renders a text input for numeric values that formats the display
    with thousand separators and uses a comma for the decimal point.
    It internally handles conversion to/from Decimal for precision.
    """
    session_key = f"numeric_input_val_{key}"
    widget_key = f"numeric_input_widget_{key}"

    # Initialize session state if it's not set
    if session_key not in st.session_state:
        st.session_state[session_key] = f"{Decimal(value):,.2f}".replace(",", " ").replace(".", ",")

    def format_and_update():
        """Formats the input string from the widget's state and updates the session state."""
        input_str = st.session_state[widget_key]
        try:
            standardized = input_str.replace(" ", "").replace(",", ".")

            if not standardized:
                st.session_state[session_key] = "0"
                return

            # Handle trailing decimal separator for typing experience
            if standardized.endswith('.'):
                num_part = standardized[:-1] if standardized[:-1] else "0"
                # Prevent crash on non-numeric input before separator
                if not re.match(r'^\d+$', num_part):
                    st.session_state[session_key] = input_str
                    return
                formatted_int = f"{int(num_part):,}".replace(",", " ")
                st.session_state[session_key] = f"{formatted_int},"
                return

            num = Decimal(standardized)

            # Round to max 2 decimal places
            num_rounded = num.quantize(Decimal('0.01'))

            # If the original input had no decimal part, format as integer.
            if '.' not in standardized:
                formatted = f"{int(num_rounded):,}".replace(",", " ")
            else:
                # It has a decimal part. Format with up to 2 decimal places.
                input_decimals = standardized.split('.')[1]

                if len(input_decimals) == 1:
                    # User typed one decimal, show one decimal.
                    s_rounded_one_place = f"{num_rounded:,.1f}".replace(",", " ").replace(".", ",")
                    formatted = s_rounded_one_place
                else: # 2 or more decimals
                    s_rounded_two_places = f"{num_rounded:,.2f}".replace(",", " ").replace(".", ",")
                    formatted = s_rounded_two_places

            st.session_state[session_key] = formatted

        except (InvalidOperation, ValueError):
            st.session_state[session_key] = input_str

    st.text_input(
        label,
        value=st.session_state[session_key],
        on_change=format_and_update,
        key=widget_key
    )

    # Return the parsed Decimal value from the session state
    try:
        return Decimal(st.session_state[session_key].replace(" ", "").replace(",", "."))
    except (InvalidOperation, ValueError):
        st.warning(f"Invalid number format for '{label}'. Please use a valid number.", icon="⚠️")
        return Decimal(value)
