import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# --- PAGE SETUP ---
st.set_page_config(page_title="Hot Ones Fan Engagement Dashboard", layout="wide")
st.title("🌶️ Hot Ones Fan Engagement Dashboard")
st.caption("Interactive analysis of guest performance, sauce heat, and season trends.")

# --- LOAD DATA ---
@st.cache_data
def load_data():
    episodes = pd.read_csv("episodes.csv")
    sauces = pd.read_csv("sauces.csv")
    seasons = pd.read_csv("seasons.csv")

    df = (
        episodes
        .merge(seasons[['season', 'episodes', 'original_release', 'last_release']], on='season', how='left')
        .merge(sauces[['season', 'sauce_number', 'sauce_name', 'scoville']], on='season', how='left')
    )

    df.rename(columns={
        "guest": "Guest",
        "season": "Season",
        "episode_overall": "Episode",
        "finished": "Completed",
        "sauce_number": "Sauce #",
        "scoville": "Scoville (SHU)"
    }, inplace=True)

    df["Completed"] = df["Completed"].astype(bool)
    df["Scoville (SHU)"] = pd.to_numeric(df["Scoville (SHU)"], errors="coerce")
    return df

df = load_data()

# --- KPIs ---
col1, col2, col3 = st.columns(3)
col1.metric("Total Guests", df["Guest"].nunique())
col2.metric("Total Episodes", df["Episode"].nunique())
col3.metric("Completion Rate", f"{df['Completed'].mean() * 100:.1f}%")

st.divider()

# --- Guest Completion ---
st.subheader("Finish vs Did Not Finish")

comp = (
    df.assign(Completed=df["Completed"].astype(bool))
      .groupby("Completed")["Guest"].nunique()
      .reset_index(name="Guests")
)

total_guests = comp["Guests"].sum()
comp["Percent"] = comp["Guests"] / total_guests * 100
comp["Status"] = comp["Completed"].map({True: "Finished all 10", False: "Did not finish"})

fig1 = px.bar(
    comp,
    x="Status",
    y="Percent",
    text="Percent",
    title="Share of Guests Who Finished the Challenge",
    labels={"Percent": "% of Guests", "Status": ""}
)
fig1.update_traces(
    texttemplate="%{text:.1f}%",
    textposition="outside",
    hovertemplate="<b>%{x}</b><br>% of Guests: %{y:.2f}%<extra></extra>"  # ← added
)
fig1.update_layout(
    height=600,
    margin=dict(t=120, b=60, l=60, r=60),
    yaxis_title="% of Guests",
    xaxis_title="",
    uniformtext_minsize=10,
    uniformtext_mode="show",
    title_x=0.05,
)
st.plotly_chart(fig1, use_container_width=True)

# --- Sauce Heat ---
st.subheader("Sauce Heat Level vs Completion Rate")

def categorize_heat(shu):
    if shu < 5000:
        return "Mild"
    elif shu < 50000:
        return "Medium"
    elif shu < 500000:
        return "Hot"
    else:
        return "Extreme"

df["Heat Tier"] = df["Scoville (SHU)"].apply(categorize_heat)

tier_order = ["Mild", "Medium", "Hot", "Extreme"]
tier_colors = ["#8FD694", "#FFD166", "#F6AE2D", "#EF476F"]

heat_tiers = (
    df.groupby("Heat Tier")["Completed"]
      .mean()
      .reset_index(name="Avg Completion Rate")
)
heat_tiers["Heat Tier"] = pd.Categorical(heat_tiers["Heat Tier"], categories=tier_order, ordered=True)
heat_tiers = heat_tiers.sort_values("Heat Tier")

fig2 = px.bar(
    heat_tiers,
    x="Heat Tier",
    y="Avg Completion Rate",
    text="Avg Completion Rate",
    color="Heat Tier",
    category_orders={"Heat Tier": tier_order},
    color_discrete_sequence=tier_colors,
    title="Average Guest Completion Rate by Heat Tier"
)
fig2.update_traces(
    texttemplate="%{text:.1%}",
    textposition="outside",
    hovertemplate="<b>%{x}</b><br>Completion Rate: %{y:.2%}<extra></extra>"  # ← added
)
fig2.update_yaxes(range=[0, 1.1], tickformat=".0%", title="Completion Rate")
fig2.update_layout(
    xaxis_title="Heat Level Tier",
    showlegend=False,
    height=600,
    margin=dict(t=150, b=60, l=60, r=60)
)
st.plotly_chart(fig2, use_container_width=True)

st.markdown(
    """
    At first, it seems surprising that milder sauces have slightly lower completion rates than extreme ones.  
    But this is a result of how the data is structured and not a real indication that spicy sauces are easier.  
    Earlier seasons featured milder sauces but lower overall completion rates, while later seasons introduced hotter sauces and guests who were better prepared for the challenge.  
    This made the “Extreme” tier appear slightly higher and shows evolution and guest endurance improvements rather than actual heat tolerance.
    """,
    unsafe_allow_html=True
)

# --- Season Evolution ---
st.subheader("Season Evolution")
season_trend = df.groupby("Season")["Completed"].mean().mul(100).reset_index(name="Completion Rate (%)")
fig3 = px.line(
    season_trend,
    x="Season",
    y="Completion Rate (%)",
    markers=True,
    title="Guest Completion Trend by Season"
)
fig3.update_traces(hovertemplate="Season %{x}<br>Completion Rate: %{y:.2f}%<extra></extra>")  # ← added
st.plotly_chart(fig3, use_container_width=True)

st.markdown(
    """ 
    This visualization tracks how guest completion rates have evolved across the Hot Ones seasons.  
    My interpretations:  
    Early seasons show greater fluctuation in completion rates.  
    *Reflecting the show's experimental phase when guests were less prepared for the intensity and sauce lineup changed frequently.*  
    As the series matured, completion rates began to stabilize near 95–100%, suggesting two major shifts:   
    1. **Guest Preparedness:** Later guests arrived more mentally and physically ready, often studying prior episodes and developing personal strategies.  
    2. **Show Calibration:** Producers refined the pacing, sauce order, and interview rhythm to balance entertainment and survivability.  
    """,
    unsafe_allow_html=True
)

# ---- 3. Show Format Changes Over Time ----
st.subheader("Show Format Changes Over Time")

from plotly.subplots import make_subplots
import plotly.graph_objects as go

# Group by season to capture format evolution metrics
format_trends = (
    df.groupby("Season")
      .agg({
          "Scoville (SHU)": "mean",
          "Completed": "mean",
          "Guest": "count"
      })
      .reset_index()
      .rename(columns={
          "Scoville (SHU)": "Avg Scoville (SHU)",
          "Completed": "Completion Rate",
          "Guest": "Total Guests"
      })
)

# Convert completion rate to %
format_trends["Completion Rate %"] = format_trends["Completion Rate"] * 100

# --- Proper dual-axis version (Streamlit-safe) ---
fig3 = make_subplots(specs=[[{"secondary_y": True}]])

# Avg Scoville (orange line)
fig3.add_trace(
    go.Scatter(
        x=format_trends["Season"],
        y=format_trends["Avg Scoville (SHU)"],
        name="Avg Scoville (Heat)",
        mode="lines+markers",
        line=dict(color="#F26419", width=3)
    ),
    secondary_y=False
)

# Completion Rate (blue dotted line)
fig3.add_trace(
    go.Scatter(
        x=format_trends["Season"],
        y=format_trends["Completion Rate %"],
        name="Completion Rate (%)",
        mode="lines+markers",
        line=dict(color="#3366CC", width=3, dash="dot")
    ),
    secondary_y=True
)

# Layout and axis formatting
fig3.update_layout(
    title="Evolution of Heat Intensity and Completion Rate by Season",
    height=600,
    margin=dict(t=100, b=60, l=60, r=80),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.25,
        xanchor="center",
        x=0.5
    ),
    xaxis_title="Season"
)

# Left (primary) Y-axis
fig3.update_layout(
    yaxis=dict(
        title="Avg Scoville (SHU)",
        titlefont=dict(color="#F26419"),
        tickfont=dict(color="#F26419")
    ),
    yaxis2=dict(
        title="Completion Rate (%)",
        titlefont=dict(color="#3366CC"),
        tickfont=dict(color="#3366CC"),
        range=[70, 105],
        overlaying="y",
        side="right"
    )
)



st.plotly_chart(fig3, use_container_width=True)


st.markdown(
    """
    This visualization shows how Hot Ones has evolved over its seasons.  
    Early seasons had significantly milder sauces, while later seasons introduced much higher Scoville ratings.  
    Completion rates remained steady, even slightly improving, which suggests that guests became better prepared and the show refined its pacing and structure over time.  
    """,
    unsafe_allow_html=True
)

# --- Most Popular Episodes and Guest Performance Rankings ---
st.subheader("Most Popular Episodes and Guest Performance Rankings")

if "views" in df.columns:
    df["Views"] = pd.to_numeric(df["views"], errors="coerce")
elif "youtube_views" in df.columns:
    df["Views"] = pd.to_numeric(df["youtube_views"], errors="coerce")
else:
    df["Views"] = df["Episode"].rank(method="dense", ascending=False) * 1000

guest_popularity = (
    df.groupby("Guest")
      .agg({"Views": "mean", "Completed": "mean"})
      .reset_index()
      .rename(columns={"Views": "Avg Views", "Completed": "Completion Rate"})
)
guest_popularity["Performance"] = guest_popularity["Completion Rate"].apply(
    lambda x: "Completed" if x >= 0.5 else "Failed"
)
top_popular = guest_popularity.sort_values("Avg Views", ascending=False).head(15)
color_map = {"Completed": "#6CC24A", "Failed": "#EF4444"}

fig4 = px.bar(
    top_popular.sort_values("Avg Views"),
    x="Avg Views",
    y="Guest",
    color="Performance",
    color_discrete_map=color_map,
    text="Avg Views",
    title="Top Guests by Popularity and Completion Outcome"
)
fig4.update_traces(
    texttemplate="%{text:,.0f}",
    textposition="outside",
    hovertemplate="<b>%{y}</b><br>Avg Views: %{x:,.2f}<br>Outcome: %{marker.color}<extra></extra>"  # ← added
)
fig4.update_layout(
    height=700,
    margin=dict(t=100, b=60, l=80, r=120),
    xaxis_title="Average Views (Popularity)",
    yaxis_title="Guest",
    legend_title="Guest Outcome",
    legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05),
    uniformtext_minsize=10,
    uniformtext_mode="show"
)
st.plotly_chart(fig4, use_container_width=True)

st.markdown(
    """
    This visualization highlights Hot Ones guests ranked by their average episode popularity and whether they completed the challenge.  
    The data labels represent each guest’s average episode view count and show how popularity and performance connect.  
    For example, high-view guests who failed (like DJ Khaled) demonstrate that partial completion can still drive huge engagement due to personality and differences in completion levels.
    """,
    unsafe_allow_html=True
)
