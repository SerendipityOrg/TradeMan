import streamlit as st

class _SessionState:
    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)


def get(**kwargs):
    if 'session_state' not in st.session_state:
        st.session_state.session_state = _SessionState(**kwargs)

    return st.session_state.session_state
