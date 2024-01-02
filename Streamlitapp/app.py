import streamlit as st
from login import login_page
from register import register_page
from st_on_hover_tabs import on_hover_tabs
from admin import main as admin_main
import os


# The first and only call to st.set_page_config() in your entire app
st.set_page_config(layout="wide")


class SessionState:
    def __init__(self, active_user=None):
        self.active_user = active_user


def inject_custom_css():
    css_file_path = os.path.join(os.path.dirname(__file__), 'styles.css')
    with open(css_file_path) as f:
        st.markdown('<style>{}</style>'.format(f.read()),
                    unsafe_allow_html=True)
        
    css_rule = """
    h1 {
        color: darkblue;
    }
      .st-emotion-cache-6qob1r.eczjsme3 { /* Targeting the specific classes */
        background-color: #708090; /* Replace with your desired color */
    }
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
                             styles={'navtab': {'background-color': '#708090',
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
