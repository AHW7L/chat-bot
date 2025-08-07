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
As a professional cryptocurrency data analyst, analyze this image concisely and academically.

CRITICAL: Limit your response to exactly 5 key points, each point should be ONE sentence only.

For different chart types, focus on:

**Sentiment Analysis Heatmap**: 1) Dominant sentiment zones, 2) Intensity distribution patterns, 3) Temporal sentiment shifts, 4) Correlation with market events, 5) Investment implications.

**Confusion Matrix**: 1) Overall classification accuracy, 2) Precision/recall for each class, 3) Most common misclassification patterns, 4) Model performance strengths, 5) Recommended improvements.

**Gauge Dashboard**: 1) Current indicator reading and position, 2) Risk zone assessment, 3) Threshold breach probability, 4) Historical context comparison, 5) Action recommendations.

**Histogram Groups**: 1) Distribution shape and skewness, 2) Central tendency measures, 3) Outlier identification, 4) Statistical significance, 5) Market behavior insights.

**Time Series**: 1) Primary trend direction, 2) Volatility patterns, 3) Seasonal/cyclical components, 4) Anomaly detection, 5) Forecast implications.

User question: {prompt}

Provide exactly 5 bullet points, each containing ONE precise academic sentence.
"""
    
    message_placeholder = st.empty()
    message_placeholder.markdown("Analyzing image...")
    full_response = ""
    
    try:
        # Try streaming first
        response_iterator = model.generate_content([enhanced_prompt, image], stream=True, safety_settings=SAFETY_SETTTINGS)
        
        for chunk in response_iterator:
            if hasattr(chunk, 'text') and chunk.text:
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
    
    except (StopIteration, Exception) as e:
        # If streaming fails, try non-streaming approach
        if "StopIteration" in str(type(e)) or isinstance(e, StopIteration):
            message_placeholder.markdown("Switching to non-streaming mode...")
            try:
                response = model.generate_content([enhanced_prompt, image], stream=False, safety_settings=SAFETY_SETTTINGS)
                if hasattr(response, 'text') and response.text:
                    full_response = response.text
                else:
                    st.error("❌ No response generated. The image might not be processable or the prompt was blocked.")
                    return None
            except Exception as non_stream_error:
                st.error("❌ Both streaming and non-streaming failed.")
                st.exception(non_stream_error)
                return None
        
        elif "models/" in str(e) and "is not found" in str(e):
            st.error("❌ Model not available. Please check the Google AI documentation for current model names.")
            st.info("💡 Try updating your google-generativeai package: `pip install --upgrade google-generativeai`")
            return None
        
        elif hasattr(e, '__class__') and 'BlockedPromptException' in str(e.__class__):
            st.error("❌ Content was blocked by safety filters. Try rephrasing your prompt.")
            return None
        
        else:
            st.error("❌ An unexpected error occurred:")
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
    
    # Use session state to track if analysis should run
    if "run_analysis" not in st.session_state:
        st.session_state.run_analysis = False
    
    with col1:
        if st.button("📊 Comprehensive Analysis", help="Perform comprehensive professional analysis of the chart"):
            if image is not None:
                prompt = "Please provide a comprehensive professional analysis of this cryptocurrency data chart"
                st.session_state.current_prompt = prompt
                st.session_state.run_analysis = True
            
    with col2:
        if st.button("📈 Trend Analysis", help="Focus on analyzing data trends and patterns"):
            if image is not None:
                prompt = "Please focus on analyzing trends, patterns and key change points in the chart"
                st.session_state.current_prompt = prompt
                st.session_state.run_analysis = True
    
    with col3:
        if st.button("⚠️ Risk Assessment", help="Analyze from risk management perspective"):
            if image is not None:
                prompt = "Please analyze this chart from risk management and investment decision perspective"
                st.session_state.current_prompt = prompt
                st.session_state.run_analysis = True
    
    # Manual analysis button
    if st.button("🔍 Start Analysis", type="primary", disabled=(image is None)):
        if image is None:
            st.warning("Please upload a chart image first", icon="⚠️")
        elif not prompt.strip():
            st.warning("Please enter an analysis question or select a quick analysis option", icon="⚠️")
        else:
            st.session_state.current_prompt = prompt
            st.session_state.run_analysis = True
    
    # Run analysis if triggered
    if st.session_state.run_analysis and image is not None:
        current_prompt = st.session_state.get("current_prompt", prompt)
        if current_prompt and current_prompt.strip():
            with st.container():
                st.write("**Analysis Question:**")
                st.write(current_prompt)
                st.divider()
                st.write("**AI Professional Analysis:**")
                
                # Run the analysis
                result = analyze_image(current_prompt, resized_img)
                
                # Reset the flag after analysis
                st.session_state.run_analysis = False
                
                # Store the result in session state to prevent disappearing
                if result:
                    st.session_state.last_analysis = {
                        "question": current_prompt,
                        "result": result
                    }
        else:
            st.session_state.run_analysis = False
    
    # Display last analysis if no new analysis is running
    elif "last_analysis" in st.session_state and not st.session_state.run_analysis:
        with st.expander("📋 Last Analysis Result", expanded=True):
            st.write("**Question:**")
            st.write(st.session_state.last_analysis["question"])
            st.divider()
            st.write("**Analysis:**")
            st.markdown(st.session_state.last_analysis["result"])
