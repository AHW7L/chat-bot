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

st.title('加密货币数据可视化分析师')

if "app_key" not in st.session_state:
    app_key = st.text_input("Your Gemini App Key", type='password')
    if app_key:
        st.session_state.app_key = app_key

try:
    genai.configure(api_key = st.session_state.app_key)
    model = genai.GenerativeModel('gemini-pro-vision')
except AttributeError as e:
    st.warning("Please Put Your Gemini App Key First.")


def analyze_image(prompt, image):
    # 为加密货币数据分析图表添加专业提示词
    enhanced_prompt = f"""
作为一位专业的加密货币数据分析师和数据可视化专家，请分析这张图片。

如果图片包含以下任何类型的图表，请提供详细的专业分析：

1. **情感分析热力图**: 分析市场情感分布、热点区域、情感强度变化
2. **混淆矩阵**: 解读分类准确率、精确率、召回率、F1分数等指标
3. **仪表盘(Gauge)**: 分析当前指标值、阈值设置、风险等级
4. **直方图组**: 分析数据分布、频率、统计特征、异常值
5. **折线图(时间序列)**: 分析趋势、季节性、波动性、关键时间点

请从以下角度进行分析：
- 图表类型识别和数据结构
- 关键数值和统计指标
- 趋势和模式识别
- 异常值或重要观察点
- 对加密货币市场的意义和建议

用户问题: {prompt}

请提供专业、详细的分析报告。
"""
    
    message_placeholder = st.empty()
    message_placeholder.markdown("正在分析图片...")
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
        st.exception(e)
        return None
    message_placeholder.markdown(full_response)
    return full_response


image = None
if "app_key" in st.session_state:
    uploaded_file = st.file_uploader("上传加密货币数据图表...", type=["jpg", "png", "jpeg", "gif"], label_visibility='collapsed')
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        width, height = image.size
        resized_img = image.resize((128, int(height/(width/128))), Image.LANCZOS)
        st.image(image)

if "app_key" in st.session_state:
    prompt = st.text_input(
        "请描述您想分析的内容:", 
        placeholder="例如：分析这个热力图的情感分布、解读混淆矩阵的分类性能、分析时间序列的趋势变化等"
    )
    
    # 添加快速分析选项
    st.write("**快速分析选项：**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 全面分析", help="对图表进行全面的专业分析"):
            if image is not None:
                prompt = "请对这张加密货币数据图表进行全面的专业分析"
            
    with col2:
        if st.button("📈 趋势分析", help="重点分析数据趋势和模式"):
            if image is not None:
                prompt = "请重点分析图表中的趋势、模式和关键变化点"
    
    with col3:
        if st.button("⚠️ 风险评估", help="从风险管理角度分析"):
            if image is not None:
                prompt = "请从风险管理和投资决策角度分析这张图表"
    
    if st.button("🔍 开始分析", type="primary", disabled=(image is None)) or prompt:
        if image is None:
            st.warning("请先上传图表图片", icon="⚠️")
        elif not prompt.strip():
            st.warning("请输入分析问题或选择快速分析选项", icon="⚠️")
        else:
            with st.container():
                st.write("**分析问题：**")
                st.write(prompt)
                st.divider()
                st.write("**AI专业分析：**")
                analyze_image(prompt, resized_img)