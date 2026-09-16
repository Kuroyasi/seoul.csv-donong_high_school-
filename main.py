import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# ------------------------------------------------------------
# 기본 설정
# ------------------------------------------------------------
st.set_page_config(
    page_title="서울 100년 기온 변화",
    page_icon="🌡️",
    layout="wide",
)

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"


@st.cache_data
def load_data(url: str) -> pd.DataFrame:
    """서울 기온 CSV 데이터를 불러와 전처리합니다."""
    df = pd.read_csv(url, encoding="utf-8-sig")
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    df = df.dropna(subset=["날짜"])
    df["연도"] = df["날짜"].dt.year
    return df


@st.cache_data
def get_yearly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """연도별 평균/최저/최고 기온 평균값을 계산합니다."""
    yearly = (
        df.groupby("연도")[["평균기온", "최저기온", "최고기온"]]
        .mean()
        .reset_index()
        .round(2)
    )
    return yearly


# ------------------------------------------------------------
# 데이터 로드
# ------------------------------------------------------------
with st.spinner("데이터를 불러오는 중입니다..."):
    raw_df = load_data(DATA_URL)
    yearly_df = get_yearly_summary(raw_df)

min_year = int(yearly_df["연도"].min())
max_year = int(yearly_df["연도"].max())

# ------------------------------------------------------------
# 헤더
# ------------------------------------------------------------
st.title("🌡️ 서울 100년 기온 변화")
st.markdown(
    f"기상청 서울(지점 108) 일별 기온 데이터를 바탕으로, "
    f"**{min_year}년부터 {max_year}년까지** 연평균 기온의 변화를 한눈에 살펴봅니다."
)

# ------------------------------------------------------------
# 사이드바 옵션
# ------------------------------------------------------------
st.sidebar.header("⚙️ 옵션")

year_range = st.sidebar.slider(
    "살펴볼 연도 범위를 선택하세요",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
)

show_minmax = st.sidebar.checkbox("최저·최고 기온도 함께 보기", value=False)
show_trend = st.sidebar.checkbox("추세선(이동평균) 표시", value=True)
window = st.sidebar.slider("이동평균 기간(년)", min_value=3, max_value=20, value=10, step=1)

filtered = yearly_df[
    (yearly_df["연도"] >= year_range[0]) & (yearly_df["연도"] <= year_range[1])
].copy()

if show_trend:
    filtered["이동평균"] = filtered["평균기온"].rolling(window=window, min_periods=1, center=True).mean()

# ------------------------------------------------------------
# 핵심 지표
# ------------------------------------------------------------
col1, col2, col3 = st.columns(3)

first_val = filtered["평균기온"].iloc[0]
last_val = filtered["평균기온"].iloc[-1]
change = last_val - first_val

with col1:
    st.metric(f"{year_range[0]}년 연평균 기온", f"{first_val:.1f} ℃")
with col2:
    st.metric(f"{year_range[1]}년 연평균 기온", f"{last_val:.1f} ℃")
with col3:
    st.metric("변화량", f"{change:+.1f} ℃")

st.divider()

# ------------------------------------------------------------
# 메인 그래프
# ------------------------------------------------------------
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=filtered["연도"],
        y=filtered["평균기온"],
        mode="lines+markers",
        name="연평균 기온",
        line=dict(color="#e76f51", width=2),
        marker=dict(size=4),
    )
)

if show_trend:
    fig.add_trace(
        go.Scatter(
            x=filtered["연도"],
            y=filtered["이동평균"],
            mode="lines",
            name=f"{window}년 이동평균(추세)",
            line=dict(color="#264653", width=3, dash="dash"),
        )
    )

if show_minmax:
    fig.add_trace(
        go.Scatter(
            x=filtered["연도"],
            y=filtered["최고기온"],
            mode="lines",
            name="연평균 최고기온",
            line=dict(color="#f4a261", width=1.5),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=filtered["연도"],
            y=filtered["최저기온"],
            mode="lines",
            name="연평균 최저기온",
            line=dict(color="#2a9d8f", width=1.5),
        )
    )

fig.update_layout(
    title="연도별 평균 기온 변화",
    xaxis_title="연도",
    yaxis_title="기온 (℃)",
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=550,
)

st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------
# 데이터 표
# ------------------------------------------------------------
with st.expander("📋 연도별 데이터 표 보기"):
    st.dataframe(
        filtered.rename(
            columns={
                "연도": "연도",
                "평균기온": "연평균 기온(℃)",
                "최저기온": "연평균 최저기온(℃)",
                "최고기온": "연평균 최고기온(℃)",
                "이동평균": f"{window}년 이동평균(℃)",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

st.caption("데이터 출처: 기상청 서울(지점 108) 관측 자료")
