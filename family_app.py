import streamlit as st
import datetime
import pandas as pd
import os

# 画面の設定
st.set_page_config(page_title="Family OS", layout="centered")

st.title("👨‍👩‍👧 Family Support System")
st.write("今の状況をタップしてください。")

# ボタンを横に並べる
col1, col2, col3 = st.columns(3)

state = None
if col1.button("🟢 穏やか", use_container_width=True):
    state = "Green"
if col2.button("🟡 注意", use_container_width=True):
    state = "Yellow"
if col3.button("🔴 限界", use_container_width=True):
    state = "Red"

# ログ保存のロジック
if state:
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_data = {"timestamp": [now], "status": [state]}
    df = pd.DataFrame(new_data)
    
    log_file = "family_mood_log.csv"
    if not os.path.isfile(log_file):
        df.to_csv(log_file, index=False)
    else:
        df.to_csv(log_file, mode='a', header=False, index=False)
    
    if state == "Green":
        st.success(f"【{now}】 記録しました。良い時間が続きますように。")
    elif state == "Yellow":
        st.warning(f"【{now}】 記録しました。少し深呼吸してくださいね。")
    elif state == "Red":
        st.error(f"【{now}】 🔴 今すぐ距離を置いてください！")