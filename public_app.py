from __future__ import annotations
from pathlib import Path
import json
import sys
import pandas as pd
import streamlit as st

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from alpha_trader.io_utils import safe_read_csv

PUB=ROOT/'public_data'
st.set_page_config(page_title='台股 Alpha Trader',page_icon='📈',layout='wide')
st.markdown('''
<style>
.block-container{padding-top:1.2rem;max-width:1500px}
div[data-testid="stMetric"]{background:#f5f6f8;padding:12px 16px;border-radius:12px}
.notice{padding:12px 16px;border:1px solid #e7e9ee;border-radius:12px;background:#fafbfc}
</style>
''',unsafe_allow_html=True)

@st.cache_data(ttl=300)
def load_meta():
    p=PUB/'metadata.json'
    if not p.exists(): return {}
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return {}

meta=load_meta()
cands=safe_read_csv(PUB/'latest_candidates.csv',dtype={'stock_id':str})
lb=safe_read_csv(PUB/'alpha_tournament_leaderboard.csv')
tc=safe_read_csv(PUB/'alpha_tournament_candidates.csv',dtype={'stock_id':str})
health=safe_read_csv(PUB/'alpha_health.csv')
report=safe_read_csv(PUB/'walkforward_report.csv')
reg=safe_read_csv(PUB/'market_regime.csv')

latest_date=meta.get('latest_signal_date') or (str(reg['date'].max())[:10] if (not reg.empty and 'date' in reg) else 'N/A')
latest_regime=(str(reg.iloc[-1]['regime']) if (not reg.empty and 'regime' in reg) else 'N/A')
base_exposure=(float(reg.iloc[-1]['base_exposure']) if (not reg.empty and 'base_exposure' in reg and pd.notna(reg.iloc[-1]['base_exposure'])) else 0.0)
active=int((health['health'].astype(str)=='ACTIVE').sum()) if (not health.empty and 'health' in health) else 0
champion=int(meta.get('champion_count') or 0)
branch_cov=meta.get('branch_coverage')
branch_cov=float(branch_cov) if branch_cov is not None else 0.0

st.title('台股 Alpha Trader')
st.caption('主力資金代理 × 動能交易 × Alpha Tournament × Walk-Forward 驗證')
st.markdown('<div class="notice"><b>公開研究看板：</b>僅顯示衍生訊號與彙總研究結果，不提供原始市場資料。內容僅供研究與教育用途，不構成投資建議；模型機率與歷史績效不保證未來結果。</div>',unsafe_allow_html=True)

m1,m2,m3,m4,m5,m6=st.columns(6)
m1.metric('資料日期',latest_date)
m2.metric('市場 Regime',latest_regime)
m3.metric('研究曝險上限',f'{base_exposure:.0%}')
m4.metric('嚴格候選',len(cands))
m5.metric('Champion',champion)
m6.metric('分點樣本覆蓋',f'{branch_cov:.1%}')

if champion==0:
    st.warning('目前沒有 Alpha 通過 Champion 風控門檻；系統允許不交易，不會為了產生訊號而硬選。')
if branch_cov < 0.12:
    st.info('券商分點歷史覆蓋仍偏低；分點型 Alpha 會被限制參賽，直到歷史樣本足夠。')

st.divider()
t1,t2,t3,t4=st.tabs(['今日研究候選','Alpha Tournament','Alpha Health','Walk-Forward'])

with t1:
    st.subheader('今日研究候選')
    if cands.empty:
        st.info('本期沒有通過嚴格門檻的候選；系統允許不交易。')
    else:
        x=cands.copy()
        pct=['p_win_5','p_win_10','p_win_20','consensus_prob','alpha_percentile','momentum_score','smart_money_score','accumulation_score','final_score']
        for c in pct:
            if c in x: x[c]=(pd.to_numeric(x[c],errors='coerce')*100).round(1)
        st.dataframe(x,width='stretch',hide_index=True)
        st.caption('「主力資金代理」為法人、分點集中/持續性與價量行為等可觀測資訊組合，不代表辨識到特定市場參與者。')

with t2:
    st.subheader('Alpha Tournament')
    if lb.empty:
        st.info('目前沒有足夠樣本產生 Tournament 排名。')
    else:
        x=lb.copy()
        for c in ['recent_win_rate','recent_win_rate_lcb','recent_avg_return','recent_cohort_avg_return','recent_cohort_max_drawdown','all_win_rate','branch_coverage']:
            if c in x: x[c]=(pd.to_numeric(x[c],errors='coerce')*100).round(2)
        st.dataframe(x,width='stretch',hide_index=True)
        champs=x[x['status'].astype(str).eq('CHAMPION')] if 'status' in x else pd.DataFrame()
        if not champs.empty:
            st.success(f"目前 Champion：{champs.iloc[0].get('label','')} / {champs.iloc[0].get('recipe','')}")
        else:
            st.warning('目前沒有 Alpha 通過 Champion 門檻。')
        st.caption('Tournament 的「同日組合回撤」先將同一訊號日候選等權平均，再計算回撤；它仍是研究診斷，不等同真實資金部位回測。')
    if not tc.empty:
        st.markdown('#### Tournament 最新候選')
        st.dataframe(tc,width='stretch',hide_index=True)

with t3:
    st.subheader('Alpha 健康度')
    if health.empty:
        st.info('目前尚無足夠 OOS 樣本。')
    else:
        x=health.copy()
        for c in ['win_rate','win_rate_lcb','avg_return','median_return','max_drawdown']:
            if c in x: x[c]=(pd.to_numeric(x[c],errors='coerce')*100).round(2)
        st.dataframe(x,width='stretch',hide_index=True)

with t4:
    st.subheader('Walk-Forward 未見資料驗證')
    if report.empty:
        st.info('目前尚無 Walk-Forward 報告。')
    else:
        x=report.copy()
        for c in ['win_rate','win_rate_lcb','avg_return','median_return','max_drawdown']:
            if c in x: x[c]=(pd.to_numeric(x[c],errors='coerce')*100).round(2)
        st.dataframe(x,width='stretch',hide_index=True)

st.divider()
st.caption('資料更新時間以頁面「資料日期」為準。公開版刻意不載入 API Token、SQLite 資料庫、原始 OHLCV 或原始券商分點資料。')
