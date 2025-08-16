import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="CrowdTest - 美容 Blogger", layout="wide")
st.title("💄 CrowdTest – 美容 Blogger")

# ---- Persona ----
st.sidebar.header("Persona 設定")
age = st.sidebar.slider("年齡", 18, 35, 24)
skin_type = st.sidebar.selectbox("膚質", ["乾性", "油性", "混合", "敏感"])
budget = st.sidebar.radio("預算偏好", ["開架", "專櫃"])
platform = st.sidebar.selectbox("主要平台", ["Instagram", "YouTube", "小紅書", "TikTok"])
language = st.sidebar.radio("語系", ["中文", "英文"])
n_audience = st.sidebar.slider("模擬受眾數", 50, 500, 200, 50)

# ---- 文案 ----
st.subheader("文案測試")
col1, col2 = st.columns(2)
with col1:
    text_a = st.text_area("版本 A", "夏日必備防曬霜，清爽不油膩！")
with col2:
    text_b = st.text_area("版本 B", "炎炎夏日，給你水潤防護，素顏也發光✨")

# ---- 模擬 ----
if st.button("開始 CrowdTest"):
    np.random.seed(42)
    df = pd.DataFrame({
        "Audience": range(1, n_audience+1),
        "Like_A": np.random.binomial(1, 0.6, n_audience),
        "Like_B": np.random.binomial(1, 0.7, n_audience),
        "Comment_A": np.random.binomial(1, 0.2, n_audience),
        "Comment_B": np.random.binomial(1, 0.25, n_audience),
        "Save_A": np.random.binomial(1, 0.3, n_audience),
        "Save_B": np.random.binomial(1, 0.4, n_audience),
    })

    # 統計
    stats = {
        "A": {
            "Like": df["Like_A"].mean(),
            "Comment": df["Comment_A"].mean(),
            "Save": df["Save_A"].mean(),
        },
        "B": {
            "Like": df["Like_B"].mean(),
            "Comment": df["Comment_B"].mean(),
            "Save": df["Save_B"].mean(),
        }
    }
    st.write("### 📊 測試結果")
    result_df = pd.DataFrame(stats).T * 100
    st.bar_chart(result_df)

    # ---- 顏色熱力表 ----
    styled = result_df.style.background_gradient(cmap="RdYlGn")
    st.dataframe(styled, use_container_width=True)

    # ---- 受眾想法 ----
    st.write("### 💬 受眾的想法")
    thoughts = []
    if "防曬" in text_a + text_b:
        thoughts.append("不少受眾提到「防曬」是夏天必備，關心是否會黏膩。")
    if "水潤" in text_a + text_b or "保濕" in text_a + text_b:
        thoughts.append("部分受眾希望產品能兼顧保濕，尤其是乾肌或長時間上班族。")
    if budget == "開架":
        thoughts.append("學生族群認為開架產品 CP 值高，更願意嘗試。")
    if budget == "專櫃":
        thoughts.append("專櫃產品被認為更值得信賴，適合敏感肌。")

    if thoughts:
        for t in thoughts:
            st.markdown(f"- {t}")
    else:
        st.info("受眾回饋尚不足，建議再加入更多細節。")
