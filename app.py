import streamlit as st
import numpy as np
import pandas as pd
from bokeh.models import ColumnDataSource, CustomJS, TapTool
from bokeh.plotting import figure
from streamlit_bokeh_events import streamlit_bokeh_events

# スマホの画面幅に合わせる設定
st.set_page_config(layout="centered")

st.title("⚾ 投球コントロール分析")
st.write("タップして直感的にデータ入力ができます。")

if "pitch_data" not in st.session_state:
    st.session_state.pitch_data = []
if "input_step" not in st.session_state:
    st.session_state.input_step = "target"

# 入力フォーム
pitcher = st.text_input("投手名", "田中")
pitch_type = st.selectbox("球種", ["ストレート", "スライダー", "カーブ", "フォーク"])

st.subheader("① 狙いをタップ" if st.session_state.input_step == "target" else "② 実際の着弾点をタップ")

# スマホで見やすいようにサイズを300に固定
p = figure(x_range=(-2, 2), y_range=(-2, 2), width=300, height=300, toolbar_location=None)
tap_tool = TapTool()
p.add_tools(tap_tool)

# ストライクゾーン
p.quad(top=1, bottom=-1, left=-1, right=1, fill_alpha=0, line_color="black", line_dash="dashed")
p.segment(x0=-2, y0=0, x1=2, y1=0, line_color="gray", line_width=0.5)
p.segment(x0=0, y0=-2, x1=0, y1=2, line_color="gray", line_width=0.5)

source = ColumnDataSource(data=dict(x=[], y=[]))
code = """
    const geometry = cb_data['geometry'];
    source.data = {'x': [geometry['x']], 'y': [geometry['y']]};
    source.change.emit();
"""
p.js_on_event("tap", CustomJS(args=dict(source=source), code=code))

result = streamlit_bokeh_events(bokeh_plot=p, events="TAP", key="bokeh_tap", refresh_on_update=True, override_height=310, debounce_time=0)

if result is not None and "TAP" in result:
    x_click = result["TAP"]["x"]
    y_click = result["TAP"]["y"]

    if st.session_state.input_step == "target":
        st.session_state.current_target = (x_click, y_click)
        st.session_state.input_step = "actual"
        st.rerun()

    elif st.session_state.input_step == "actual":
        tx, ty = st.session_state.current_target
        ax, ay = x_click, y_click

        distance = np.sqrt((ax - tx) ** 2 + (ay - ty) ** 2)
        is_missed_side = False
        if (tx * ax < 0 and abs(tx) > 0.2) or (ty * ay < 0 and abs(ty) > 0.2):
            is_missed_side = True

        st.session_state.pitch_data.append({
            "投手": pitcher, "球種": pitch_type,
            "狙い_X": round(tx, 2), "狙い_Y": round(ty, 2),
            "実際_X": round(ax, 2), "実際_Y": round(ay, 2),
            "ズレ": round(distance, 2), "逆球": "❌ 逆球" if is_missed_side else "◯ 狙い通り"
        })
        st.session_state.input_step = "target"
        st.rerun()

if st.session_state.pitch_data:
    df = pd.DataFrame(st.session_state.pitch_data)
    st.subheader("📊 蓄積データ")
    st.dataframe(df)
    
    missed_count = df["逆球"].value_counts().get("❌ 逆球", 0)
    st.write(f"**球数:** {len(df)}球 | **平均誤差:** {df['ズレ'].mean():.2f} | **逆球:** {missed_count}球")
    
    # スマホからCSVでダウンロードできる機能を追加！
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(label="📥 データをCSV保存", data=csv, file_name=f"{pitcher}_pitch_data.csv", mime="text/csv")
    
    if st.button("全リセット"):
        st.session_state.pitch_data = []
        st.rerun()
