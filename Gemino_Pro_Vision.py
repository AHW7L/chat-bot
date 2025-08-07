from PIL import Image
import google.generativeai as genai
import streamlit as st
import time
import random
from utils import SAFETY_SETTTINGS

st.set_page_config(
    page_title="Chat To Master",
    page_icon="🔥",
    menu_items={
        'About': ""
    }
)

st.title('Cryptocurrency Data Visualization Analyst')

# Try to get API key from secrets first, then from user input
if "app_key" not in st.session_state:
    try:
        # Try to get API key from Streamlit secrets
        app_key = st.secrets["GEMINI_API_KEY"]
        st.session_state.app_key = app_key
        st.success("API Key loaded from secrets successfully!")
    except (KeyError, FileNotFoundError):
        # If not found in secrets, ask user to input
        app_key = st.text_input("Your Gemini App Key", type='password', 
                               help="Enter your Gemini API key or configure it in .streamlit/secrets.toml")
        if app_key:
            st.session_state.app_key = app_key

try:
    genai.configure(api_key = st.session_state.app_key)
    # Try different available models for vision tasks
    try:
        model = genai.GenerativeModel('gemini-2.5-pro')
        st.info("Using Gemini 2.5 Pro model")
    except:
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            st.info("Using Gemini 2.5 Flash model")
        except:
            model = genai.GenerativeModel('gemini-pro')
            st.warning("Using Gemini Pro model (may have limited vision capabilities)")
except AttributeError as e:
    st.warning("Please Put Your Gemini App Key First.")


def analyze_image(prompt, image):
    # Add professional prompts for cryptocurrency data analysis charts
    enhanced_prompt = f"""
As a professional cryptocurrency data analyst and data visualization expert, please analyze this image.

If the image contains any of the following chart types, please provide detailed professional analysis:

1. **Sentiment Analysis Heatmap**: Analyze market sentiment distribution, hotspot areas, sentiment intensity changes
2. **Confusion Matrix**: Interpret classification accuracy, precision, recall, F1-score and other metrics
3. **Gauge Dashboard**: Analyze current indicator values, threshold settings, risk levels
4. **Histogram Groups**: Analyze data distribution, frequency, statistical characteristics, outliers
5. **Line Chart (Time Series)**: Analyze trends, seasonality, volatility, key time points

Please analyze from the following perspectives:
- Chart type identification and data structure
- Key numerical values and statistical indicators
- Trend and pattern recognition
- Outliers or important observations
- Significance and recommendations for cryptocurrency markets

User question: {prompt}

Please provide a professional and detailed analysis report.
"""
    
    message_placeholder = st.empty()
    message_placeholder.markdown("Analyzing image...")
    full_response = ""
    try:
        for chunk in model.generate_content([enhanced_prompt, image], stream = True, safety_settings = SAFETY_SETTTINGS):                   
            word_count = 0
            random_int = random.randint(5, 10)
            for word in chunk.text:
                full_response += word
                word_count += 1
                if word_count == random_int:
                    time.sleep(0.05)
                    message_placeholder.markdown(full_response + "_")
                    word_count = 0
                    random_int = random.randint(5, 10)
    except genai.types.generation_types.BlockedPromptException as e:
        st.exception(e)
        return None
    except Exception as e:
        # Handle model not found or other API errors
        if "models/" in str(e) and "is not found" in str(e):
            st.error("❌ Model not available. The Gemini vision model may have been updated. Please check the Google AI documentation for current model names.")
            st.info("💡 Try updating your google-generativeai package: `pip install --upgrade google-generativeai`")
        else:
            st.exception(e)
        return None
    message_placeholder.markdown(full_response)
    return full_response


image = None
if "app_key" in st.session_state:
    uploaded_file = st.file_uploader("Upload cryptocurrency data chart...", type=["jpg", "png", "jpeg", "gif"], label_visibility='collapsed')
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        
        # Convert image to RGB mode to remove transparency channel
        if image.mode in ('RGBA', 'LA', 'P'):
            # Create white background
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        width, height = image.size
        resized_img = image.resize((128, int(height/(width/128))), Image.LANCZOS)
        st.image(image)

if "app_key" in st.session_state:
    prompt = st.text_input(
        "Please describe what you want to analyze:", 
        placeholder="e.g.: Analyze sentiment distribution in this heatmap, interpret confusion matrix performance, analyze time series trends, etc."
    )
    
    # Add quick analysis options
    st.write("**Quick Analysis Options:**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Comprehensive Analysis", help="Perform comprehensive professional analysis of the chart"):
            if image is not None:
                prompt = "Please provide a comprehensive professional analysis of this cryptocurrency data chart"
            
    with col2:
        if st.button("📈 Trend Analysis", help="Focus on analyzing data trends and patterns"):
            if image is not None:
                prompt = "Please focus on analyzing trends, patterns and key change points in the chart"
    
    with col3:
        if st.button("⚠️ Risk Assessment", help="Analyze from risk management perspective"):
            if image is not None:
                prompt = "Please analyze this chart from risk management and investment decision perspective"
    
    if st.button("🔍 Start Analysis", type="primary", disabled=(image is None)) or prompt:
        if image is None:
            st.warning("Please upload a chart image first", icon="⚠️")
        elif not prompt.strip():
            st.warning("Please enter an analysis question or select a quick analysis option", icon="⚠️")
        else:
            with st.container():
                st.write("**Analysis Question:**")
                st.write(prompt)
                st.divider()
                st.write("**AI Professional Analysis:**")
                analyze_image(prompt, resized_img)
