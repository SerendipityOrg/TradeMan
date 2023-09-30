import re

def format_value(value, format_type="normal"):
            print(f"Formatting value: {value}")  # Debug print
            formatted_value = ""
            if value is None:
                formatted_value = "N/A"
            elif isinstance(value, str):
                if value.startswith('='):
                    formatted_value = "Formula"
                else:
                    try:
                        float_value = float(value.replace('₹', '').replace(',', ''))
                        if float_value < 0:
                            formatted_value = f'<span class="negative-value">₹ {float_value:,.2f}</span>'
                        else:
                            formatted_value = f'<span class="positive-value">₹ {float_value:,.2f}</span>'
                    except ValueError:
                        formatted_value = value
            else:
                if value < 0:
                    formatted_value = f'<span class="negative-value">₹ {value:,.2f}</span>'
                else:
                    formatted_value = f'<span class="positive-value">₹ {value:,.2f}</span>'

            # Apply formatting based on format_type
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

            