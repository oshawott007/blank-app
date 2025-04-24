import streamlit as st

# Set page config
st.set_page_config(
    page_title="My Simple Website yoyo Nigga",
    page_icon="🌐",
    layout="wide"
)

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "About", "Contact", "Calculator"])

# Home page
if page == "Home":
    st.title("Welcome to My Website! 👋")
    st.write("""
    This is a simple website built with Streamlit.
    Use the sidebar to navigate between different pages.
    """)
    
    # st.image("https://streamlit.io/images/brand/streamlit-logo-secondary-colormark-darktext.png", 
    #          width=300)
    
    st.subheader("Features")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write("✅ Easy to use")
    with col2:
        st.write("🚀 Fast deployment")
    with col3:
        st.write("💻 Python-powered")

# About page
elif page == "About":
    st.title("About This Website")
    st.write("""
    This website demonstrates how to create a multi-page app using Streamlit.
    Streamlit is an open-source Python library that makes it easy to create 
    and share beautiful, custom web apps for machine learning and data science.
    """)
    
    st.subheader("Technologies Used")
    st.markdown("""
    - Python
    - Streamlit
    - Pandas
    - Matplotlib
    """)

# Contact page
elif page == "Contact":
    st.title("Contact Us")
    
    with st.form("contact_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        message = st.text_area("Message")
        submitted = st.form_submit_button("Submit")
        
        if submitted:
            st.success(f"Thank you {name}! We'll get back to you soon.")

# Calculator page
elif page == "Calculator":
    st.title("Simple Calculator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        num1 = st.number_input("Enter first number", value=0)
    
    with col2:
        num2 = st.number_input("Enter second number", value=0)
    
    operation = st.selectbox("Select operation", 
                            ["Add", "Subtract", "Multiply", "Divide"])
    
    if st.button("Calculate"):
        if operation == "Add":
            result = num1 + num2
        elif operation == "Subtract":
            result = num1 - num2
        elif operation == "Multiply":
            result = num1 * num2
        elif operation == "Divide":
            result = num1 / num2 if num2 != 0 else "Cannot divide by zero"
        
        st.success(f"Result: {result}")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("Built with ❤️ using Streamlit")
