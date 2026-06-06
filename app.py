import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# スマホの画面幅に合わせる設定
st.set_page_config(layout="centered")

st.title("⚾ 投球コントロール分析")
st.write("9分割のストライクゾーンをタップして入力してください。")

# データを保持するためのセッション状態の初期化
if "pitch_data" not in st.session_state:
    st.session_state.pitch_data = []
if "input_step" not in st.session_state:
    st.session_state.input_step = "target"

# 入力フォーム
pitcher = st.text_input("投手名", "田中")
pitch_type = st.selectbox("球種", ["ストレート", "スライダー", "カーブ", "フォーク"])

st.subheader("① 狙いをタップ" if st.session_state.input_step == "target" else "② 実際の着弾点をタップ")

# --- Matplotlibで9分割ストライクゾーンの画像を作成 ---
# これにより、スマホの画面サイズに左右されない正確な座標ベースの画像を作ります
fig, ax = plt.subplots(figsize=(4, 4))

# 外枠（ボールゾーンを含めた全体）の設定
ax.set_xlim(-2, 2)
ax.set_ylim(-2, 2)

# 縦長の9分割ストライクゾーンの箱を描画 (横幅は-1〜1、縦幅は-1.2〜1.2で実戦的な縦長に設定)
x_edges = [-1.0, -0.33, 0.33, 1.0]
y_edges = [-1.2, -0.4, 0.4, 1.2]

# 縦線を描く
for x in x_edges:
    ax.plot([x, x], [-1.2, 1.2], color="black", linewidth=1.5)
# 横線を描く
for y in y_edges:
    ax.plot([-1.0, 1.0], [y, y], color="black", linewidth=1.5)

# 中心線（十字のガイド線、うっすら表示）
ax.axhline(0, color="gray", linewidth=0.5, linestyle="--")
ax.axvline(0, color="gray", linewidth=0.5, linestyle="--")

# 背景や目盛りを消してスッキリさせる
ax.axis('off')
fig.patch.set_facecolor('#f0f2f6') # Streamlitの背景色に合わせる
ax.set_facecolor('#ffffff')

# すでに今選んだ「狙い」がある場合は、②のステップで緑色の点を表示する
if st.session_state.input_step == "actual" and "current_target" in st.session_state:
    tx, ty = st.session_state.current_target
    ax.scatter(tx, ty, color="green", s=150, zorder=5, label="Target")
    ax.text(tx, ty + 0.15, "狙い", color="green", fontsize=10, ha='center', weight='bold')

# 一時的な画像ファイルとして保存
fig.savefig("zone.png", bbox_inches='tight', pad_inches=0, facecolor=fig.get_facecolor(), edgecolor='none')
plt.close(fig)

# --- タップイベント用のコンポーネント ---
# 作成した9分割画像をStreamlit上でクリック可能にする
value = st.image(
    "zone.png",
    caption="キャッチャー目線（枠外はボールゾーン）",
    use_container_width=True
)

# クリック（タップ）された時の座標変換ロジック
if value is not None and "click" in value and value["click"] is not None:
    click_raw = value["click"]
    raw_x = click_raw.get("x", 0)
    raw_y = click_raw.get("y", 0)
    
    # st.imageの仕様変更に対応した、解像度から-2.0〜2.0への絶対座標マッピング
    # ※画像の中心を(0,0)とする
    x_click = ((raw_x / 300) * 4) - 2
    y_click = -(((raw_y / 300) * 4) - 2)

    x_click = max(-2.0, min(2.0, x_click))
    y_click = max(-2.0, min(2.0, y_click))

    if st.session_state.input_step == "target":
        st.session_state.current_target = (x_click, y_click)
        st.session_state.input_step = "actual"
        st.toast("🎯 狙いを登録しました！", icon="✅")
        st.rerun()
