import re
from babel.numbers import format_currency


def format_value(value, format_type="normal"):
    print(f"Formatting value: {value}")  # Debug print
    formatted_value = ""

    if value is None:
        formatted_value = "N/A"
    else:
        try:
            # Ensure value is a float for formatting
            float_value = float(str(value).replace('₹', '').replace(',', '').strip())
            # Use custom_format to format the numerical part
            formatted_value = custom_format(float_value)

            # Apply additional HTML styling for negative values
            if float_value < 0:
                formatted_value = f'<span class="negative-value">{formatted_value}</span>'
            else:
                formatted_value = f'<span class="positive-value">{formatted_value}</span>'
        except ValueError:
            # Handle the case where conversion to float fails
            formatted_value = value

    # Apply additional formatting based on format_type
    if format_type == "bold":
        return f"<b>{formatted_value}</b>"
    elif format_type == "italic":
        return f"<i>{formatted_value}</i>"
    else:
        return formatted_value


def format_stat_value(value):
    if value is None:
        return "N/A"
    elif isinstance(value, str):
        if "₹" in value and "-" in value:
            return f'<span class="negative-value">{value}</span>'
        elif "₹" in value:
            return f'<span class="positive-value">{value}</span>'
        elif "%" in value and "-" in value:
            return f'<span class="negative-value">{value}</span>'
        elif "%" in value:
            return f'<span class="positive-value">{value}</span>'
        else:
            return value
    elif value < 0:
        return f'<span class="negative-value">₹ {value:,.2f}</span>'
    else:
        return f'<span class="positive-value">₹ {value:,.2f}</span>'


def indian_format(num):
    """Format number in Indian style"""
    x = round(num)
    if x < 1e5:
        return str(x)
    x = round(x / 1e5)
    if x < 100:
        return '{} Lakh'.format(x)
    x = round(x / 100)
    return '{} Crore'.format(x)


# Custom format function for currency

def custom_format(amount):
    if isinstance(amount, (int, float)):
        formatted = format_currency(amount, 'INR', locale='en_IN')
        return formatted.replace('₹', '₹ ')
    elif isinstance(amount, str):
        # Handle the case where 'amount' is already a formatted string
        return amount
    else:
        # Return the value as is (not formatted)
        return amount
