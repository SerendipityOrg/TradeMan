import streamlit as st
from login import login_page
from register import register_page
from st_on_hover_tabs import on_hover_tabs
from admin import main as admin_main
import os
import base64

# Function to convert local image file to Base64
def get_base64_of_image(file_path):
    with open(file_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# The first and only call to st.set_page_config() in your entire app
st.set_page_config(layout="wide")

class SessionState:
    def __init__(self, active_user=None):
        self.active_user = active_user

def inject_custom_css():
    # Specify the absolute path to your image file
    image_file_path = os.path.join(os.path.dirname(__file__),'background.png')
    
    # Check if the file exists before trying to open it
    if not os.path.isfile(image_file_path):
        raise FileNotFoundError(f"The specified file does not exist: {image_file_path}")
    
    background_image_base64 = get_base64_of_image(image_file_path)

    css_file_path = os.path.join(os.path.dirname(__file__), 'styles.css')
    with open(css_file_path) as f:
        st.markdown('<style>{}</style>'.format(f.read()),
                    unsafe_allow_html=True)
    
    css_rule = f"""
    .stApp {{
        background-image: url("data:image/png;base64,{background_image_base64}");
        background-size: cover;
        background-position: center;
    }}
    /* Making elements with 'data-testid' attribute of 'stHeader' transparent */
    [data-testid="stHeader"] {{
        background-color: transparent !important;
    }}
    /* Making elements with class 'st-emotion-cache-18ni7ap ezrtsby2' transparent */
    .st-emotion-cache-18ni7ap.ezrtsby2 {{
        background-color: transparent !important;
    }}
    /* Additional custom styles */
    .css-18e3th9 {{
        background-color: #324A5F; /* Dark blue - change as needed */
    }}
    .css-1d391kg {{
        background-color: transparent; /* Making the header transparent */
    }}
    h1 {{
        color: #fff904;
    }}
    .st-emotion-cache-6qob1r.eczjsme3 {{ /* Targeting the specific classes */
        background-color: CadetBlue; /* Replace with your desired color */
    }}
    """
    st.markdown(f'<style>{css_rule}</style>', unsafe_allow_html=True)


def main():
    st.title("Serendipity Trading Firm")
    
    inject_custom_css()
    # Create session state if it doesn't exist
    if 'session' not in st.session_state:
        st.session_state['session'] = SessionState()

    with st.sidebar:
        st.sidebar.header("")
        tabs = on_hover_tabs(tabName=['Register', 'Login', 'Admin Dashboard'],
                             iconName=['R', 'L', 'A'],
                             styles={'navtab': {'background-color': 'CadetBlue',
                                                'color': '#FFFFFF',
                                                'font-size': '18px',
                                                'transition': '.3s',
                                                'white-space': 'nowrap',
                                                'text-transform': 'uppercase'},
                                     'tabOptionsStyle': {':hover :hover': {'color': 'darkblue',
                                                                           'cursor': 'pointer'}},
                                     'iconStyle': {'position': 'fixed',
                                                   'left': '7.5px',
                                                   'text-align': 'left'},
                                     'tabStyle': {'list-style-type': 'none',
                                                  'margin-bottom': '30px',
                                                  'padding-left': '30px'}},
                             key="1")

    if tabs == "Register":
        register_page()

    elif tabs == "Login":
        login_page()

    elif tabs == "Admin Dashboard":
        admin_main()

if __name__ == "__main__":
    main()
