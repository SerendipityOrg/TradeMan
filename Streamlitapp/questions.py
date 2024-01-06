import streamlit as st

# Set page config to widen the app and set a title and icon
st.set_page_config(page_title='Serendipity Trading Firm', layout='centered')

st.write('''
We are dedicated to providing you with a tailored trading strategy that aligns with your specific financial goals and risk tolerance. 
To better understand your preferences and requirements, please respond to the following inquiries. 
Your detailed answers will enable us to recommend an optimal strategy for your investments. 
You can request strategy adjustments at any time via Telegram.
''')

with st.form("investment_form"):
    st.subheader('Determination of Investment Horizon')
    investment_horizon = st.radio(
        "Please specify your anticipated investment duration:",
        ('Short-Term (upto 1 year)', 'Long-Term(above 1 year)'))

    st.subheader('Allocation of Investment Capital')
    st.write('How would you prefer to apportion your investment among the following categories? Ensure the total allocation sums to 100%.')
    col1, col2, col3 = st.columns(3)
    with col1:
        debt = st.number_input('Debt (%)', min_value=0.0, max_value=100.0, value=0.0, step=0.1)
    with col2:
        equity = st.number_input('Equity (%)', min_value=0.0, max_value=100.0, value=0.0, step=0.1)
    with col3:
        fno = st.number_input('Futures and Options (FnO) (%)', min_value=0.0, max_value=100.0, value=0.0, step=0.1)

    st.subheader('Acceptable Drawdown Threshold')
    drawdown_threshold = st.slider(
        'What is your tolerance for potential declines in your investment value? Indicate the maximum percentage of the drawdown you are comfortable with.',
        0, 100, 50)

    st.subheader('Frequency of Capital Withdrawal')
    withdrawal_frequency = st.selectbox(
        "Please indicate your preferred frequency for withdrawing funds from your investments.",
        ('Weekly', 'As needed'))

    st.subheader('Commission Preferences')
    commission_preference = st.selectbox(
        "Select the commission structure that aligns with your investment approach.",
        ('50%-50% (Loss sharing model)', '75%-25% (Exclusive of loss sharing)'))

    # Submit button
    submitted = st.form_submit_button("Submit")
    if submitted:
        st.success("You've submitted the form successfully!")
        st.subheader("Your Responses:")
        st.write(f"Investment Horizon: {investment_horizon}")
        st.write(f"Investment Allocation: Debt: {debt}%, Equity: {equity}%, FnO: {fno}%")
        st.write(f"Drawdown Threshold: {drawdown_threshold}%")
        st.write(f"Withdrawal Frequency: {withdrawal_frequency}")
        st.write(f"Commission Preference: {commission_preference}")
