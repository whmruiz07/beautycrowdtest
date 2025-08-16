
import streamlit as st
import numpy as np
import pandas as pd
import random, math
from typing import Dict, List

st.set_page_config(page_title="CrowdTest – Beauty Blogger", layout="wide")
st.title("💄 CrowdTest – Beauty Blogger")
st.caption("主題：美容 Blogger｜Persona：年輕女生（可調）｜A/B 文案測試 + 受眾想法生成")

# ---------- Sidebar: Persona & Weights ----------
with st.sidebar:
    st.header("🧑‍🎤 Persona（受眾輪廓）")
    age = st.select_slider("年齡", options=list(range(16, 31)), value=22)
    focus = st.multiselect("關注主題", ["保養", "底妝", "彩妝流行", "開架好物", "敏感肌", "抗痘", "抗老", "香氛"], default=["保養","底妝","開架好物"])
    budget = st.selectbox("預算取向", ["學生黨/開架為主", "平價＋少量專櫃", "專櫃/高端"])
    platform = st.selectbox("平台", ["Instagram", "TikTok", "YouTube Shorts", "X"])
    region = st.selectbox("地區語系", ["繁中（台港）", "簡中", "英文"])

    st.header("🧪 測試設定")
    n_users = st.slider("模擬受眾人數", 200, 5000, 1200, step=100)
    seed = st.number_input("隨機種子（重現結果）", value=42, step=1)

    st.header("⚙️ 權重（可調）")
    w_len = st.slider("文案長度最佳區間權重", 0.0, 2.0, 0.6, 0.1)
    w_emoji = st.slider("表情符號/情感權重", 0.0, 2.0, 0.5, 0.1)
    w_hashtag = st.slider("Hashtag 規範權重", 0.0, 2.0, 0.4, 0.1)
    w_value = st.slider("優惠/實用性權重", 0.0, 2.0, 0.5, 0.1)
    w_skin = st.slider("膚質/功效對位權重", 0.0, 2.0, 0.7, 0.1)
    w_auth = st.slider("真實/非廣告觀感權重", 0.0, 2.0, 0.6, 0.1)

st.subheader("✍️ 輸入文案（A/B）")
c1, c2 = st.columns(2)
with c1:
    txt_a = st.text_area("版本 A 文案", height=180, placeholder="例：開架粉底完勝？新款柔霧持妝，一整天不暗沉！我的上妝步驟＋持妝小技巧👇")
with c2:
    txt_b = st.text_area("版本 B 文案", height=180, placeholder="例：敏感肌也能用的保濕精華，7天有感透亮。成分＋用法＋注意事項都寫給你！")

run = st.button("🚀 開始 CrowdTest")

# ---------- Heuristics ----------
SKIN_TERMS = {"敏感":"敏感肌","痘":"抗痘","粉刺":"抗痘","毛孔":"控油/毛孔","保濕":"保濕","乾":"乾肌","出油":"油肌","抗老":"抗老","淡斑":"淡斑","防曬":"防曬","提亮":"提亮"}
VALUE_TERMS = ["折扣","優惠","開架","平價","比價","心得","清單","步驟","教學","技巧","實測","前後對比","before","after"]
EMOJIS = ["✨","💖","😍","🥹","🔥","✅","🧴","💄","🪄","👇","📌","⚠️","😅","😭"]
AD_LIKE = ["合作","廣告","折扣碼","sponsored","#ad"]

def text_features(t: str, platform: str) -> Dict[str, float]:
    t_low = t.lower()
    length = len(t)
    n_hash = t.count("#")
    n_emoji = sum(ch in t for ch in EMOJIS)
    has_value = any(k in t for k in VALUE_TERMS)
    has_ad = any(k.lower() in t_low for k in AD_LIKE)
    skin_hits = sum(k in t for k in SKIN_TERMS.keys())
    if platform in ["Instagram","TikTok","YouTube Shorts"]:
        len_score = 1.0 - abs(length-120)/200
    else:
        len_score = 1.0 - abs(length-80)/180
    len_score = max(0.0, min(1.0, len_score))
    emoji_score = min(1.0, n_emoji/6)
    hash_score = 1.0 if 2 <= n_hash <= 5 else (0.7 if n_hash in (1,6) else 0.4 if n_hash==0 else 0.5)
    value_score = 1.0 if has_value else 0.5
    skin_score = min(1.0, 0.3 + 0.15*skin_hits)
    auth_score = 0.6 if has_ad else 1.0
    return {"len_score":len_score,"emoji_score":emoji_score,"hash_score":hash_score,"value_score":value_score,"skin_score":skin_score,"auth_score":auth_score,
            "length":length,"n_hash":n_hash,"n_emoji":n_emoji,"skin_hits":skin_hits,"has_ad":float(has_ad)}

def engagement_prob(features: Dict[str,float], weights) -> Dict[str,float]:
    base_like, base_comment, base_share, base_save = 0.18, 0.035, 0.02, 0.06
    adj = (weights["len"]*features["len_score"] + weights["emoji"]*features["emoji_score"] + weights["hash"]*features["hash_score"]
           + weights["value"]*features["value_score"] + weights["skin"]*features["skin_score"] + weights["auth"]*features["auth_score"]) / (sum(weights.values())+1e-6)
    mult = 0.7 + 0.9*adj
    return {"like":min(0.9, base_like*mult),"comment":min(0.5, base_comment*mult),"share":min(0.4, base_share*mult),"save":min(0.6, base_save*mult)}

def simulate_engagement(n, probs, rng):
    return (sum(rng.random()<probs["like"] for _ in range(n)),
            sum(rng.random()<probs["comment"] for _ in range(n)),
            sum(rng.random()<probs["share"] for _ in range(n)),
            sum(rng.random()<probs["save"] for _ in range(n)))

def se(p, n): return (max(p*(1-p), 1e-9)/max(n,1))**0.5
def ci95(p, n):
    s = se(p,n); return max(0.0, p-1.96*s), min(1.0, p+1.96*s)

POS_BANK = ["看起來很真實、不是硬廣。","步驟清楚，懶人也能跟。","有 before/after 對比更有說服力！","關鍵成分有講明白，讚。","適合學生黨價格友好。","妝感自然、不假面。","對敏感肌很友善，想試！","拍攝光線跟膚況坦誠，信任度 up。","願意收藏再看一次。"]
NEG_BANK = ["資訊有點散，看不出重點。","像在賣東西，缺少個人使用感。","步驟太快/太長，跟不上。","沒有講到可能的副作用或注意事項。","照片修得太過頭，不真實。","Hashtag 太多/太少，像是機器發文。"]
HINTS_BY_TERM = {"敏感":"提一下致敏風險與避雷成分。","痘":"增加實際痘痘期間的使用心得。","保濕":"補上吸收時間與後續疊擦感受。","抗老":"說明見效時間與耐受度安排。","防曬":"補充室內/戶外/補擦建議。","開架":"可以給替代清單或比價。","提亮":"用自然光拍未開濾鏡照片。"}

def gen_thoughts(txt, feats, rng):
    bank = []; bank += rng.sample(POS_BANK, k=3); bank += rng.sample(NEG_BANK, k=2)
    for k, note in HINTS_BY_TERM.items():
        if k in txt: bank.append(note)
    if feats["n_emoji"] >= 3: bank.append("整體氛圍可愛有活力，蠻像姐妹聊天。")
    if feats["n_hash"] == 0: bank.append("加上 2–5 個精準 hashtag 會更好被找到。")
    elif feats["n_hash"] > 8: bank.append("Hashtag 稍多，可精簡成主題＋品牌＋功效。")
    out = []
    for s in bank:
        if s not in out: out.append(s)
        if len(out) >= 5: break
    return out

# ---- Heat color without matplotlib ----
def heat_css(v: float) -> str:
    if pd.isna(v): return ""
    if v >= 0.85: return "background-color:#1e7e34;color:white;"   # strong green
    if v >= 0.7:  return "background-color:#4CAF50;color:white;"   # green
    if v >= 0.55: return "background-color:#C8E6C9;color:#222;"    # light green
    if v >= 0.4:  return "background-color:#FFF59D;color:#222;"    # yellow
    if v >= 0.25: return "background-color:#FFCCBC;color:#222;"    # light orange
    return "background-color:#F44336;color:white;"                 # red

# ---------- Run ----------
if run:
    rng = random.Random(int(seed))
    weights = {"len":w_len,"emoji":w_emoji,"hash":w_hashtag,"value":w_value,"skin":w_skin,"auth":w_auth}

    feats_a = text_features(txt_a, platform)
    feats_b = text_features(txt_b, platform)
    probs_a = engagement_prob(feats_a, weights)
    probs_b = engagement_prob(feats_b, weights)

    la, ca, sa, sva = simulate_engagement(n_users, probs_a, rng)
    lb, cb, sb, svb = simulate_engagement(n_users, probs_b, rng)

    pa = {k: v/n_users for k,v in zip(["like","comment","share","save"], [la,ca,sa,sva])}
    pb = {k: v/n_users for k,v in zip(["like","comment","share","save"], [lb,cb,sb,svb])}
    ci_a = {k: ci95(pa[k], n_users) for k in pa}
    ci_b = {k: ci95(pb[k], n_users) for k in pb}

    score_a = 1.0*pa["like"] + 2.0*pa["comment"] + 2.0*pa["save"] + 1.5*pa["share"]
    score_b = 1.0*pb["like"] + 2.0*pb["comment"] + 2.0*pb["save"] + 1.5*pb["share"]

    def row(label, p, ci, score):
        return {"版本":label,
                "👍 Like": f"{p['like']*100:.1f}% ({ci['like'][0]*100:.0f}–{ci['like'][1]*100:.0f})",
                "💬 Comment": f"{p['comment']*100:.1f}% ({ci['comment'][0]*100:.0f}–{ci['comment'][1]*100:.0f})",
                "🔁 Share": f"{p['share']*100:.1f}% ({ci['share'][0]*100:.0f}–{ci['share'][1]*100:.0f})",
                "📌 Save": f"{p['save']*100:.1f}% ({ci['save'][0]*100:.0f}–{ci['save'][1]*100:.0f})",
                "綜合分數": score}
    df = pd.DataFrame([row("A", pa, ci_a, score_a), row("B", pb, ci_b, score_b)]).set_index("版本")

    def color_score(v, best):
        return "background-color: #4CAF50; color:white;" if v >= best*0.98 else "background-color: #F44336; color:white;"
    best_score = max(score_a, score_b)
    styled = df.style.applymap(lambda v: color_score(v, best_score), subset=["綜合分數"])
    st.subheader("📈 模擬結果（比例% 與 95%信賴區間）")
    st.dataframe(styled, use_container_width=True)

    st.markdown("### 🧪 文案要點評分（0~1 越高越佳）")
    diag = pd.DataFrame({
        "項目": ["長度匹配","表情符號","Hashtag 規範","價值/實用","膚質/功效對位","真實度"],
        "A": [feats_a["len_score"], feats_a["emoji_score"], feats_a["hash_score"], feats_a["value_score"], feats_a["skin_score"], feats_a["auth_score"]],
        "B": [feats_b["len_score"], feats_b["emoji_score"], feats_b["hash_score"], feats_b["value_score"], feats_b["skin_score"], feats_b["auth_score"]],
    }).set_index("項目")
    diag_styled = diag.style.applymap(heat_css)  # no matplotlib needed
    st.dataframe(diag_styled, use_container_width=True)

    st.markdown("### 💭 受眾的想法（質性摘要）")
    thoughts_a = gen_thoughts(txt_a, feats_a, rng)
    thoughts_b = gen_thoughts(txt_b, feats_b, rng)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**版本 A – 受眾想法**")
        for t in thoughts_a: st.write(f"• {t}")
    with c2:
        st.markdown("**版本 B – 受眾想法**")
        for t in thoughts_b: st.write(f"• {t}")

else:
    st.info("在左側設定 Persona 與測試參數，填入 A/B 文案後點擊「開始 CrowdTest」。")
