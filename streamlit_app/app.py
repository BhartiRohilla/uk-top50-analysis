import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Page config
st.set_page_config(page_title="UK Top 50 Analytics", layout="wide")

# Title
st.title("🇬🇧 UK Top 50 Playlist Market Structure Dashboard")
st.markdown("*Market Structure, Artist Diversity & Content Localization Analysis for Atlantic Recording Corporation*")

# Load data - with correct path for deployment
@st.cache_data
def load_data():
    # Try different possible paths
    paths_to_try = [
        'data/Atlantic_United_Kingdom.csv'
    ]
    
    for path in paths_to_try:
        if os.path.exists(path):
            df = pd.read_csv(path)
            df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y', errors='coerce')
            df['is_collaboration'] = df['artist'].str.contains('&|,', na=False)
            return df
    
    st.error("Dataset not found. Checked paths: " + ", ".join(paths_to_try))
    st.stop()

df = load_data()

# Rest of your code continues here...

# Define UK artists
uk_artists = ['Central Cee', 'RAYE', 'Dua Lipa', 'Ed Sheeran', 'Dave', 'Stormzy', 
              'Sam Smith', 'Adele', 'Harry Styles', 'Calvin Harris', 'Ellie Goulding',
              'Arctic Monkeys', 'Sam Fender', 'Becky Hill', 'Charli XCX']

# Sidebar filters
st.sidebar.header("🔍 Filters")

# Date range
min_date = df['date'].min()
max_date = df['date'].max()
date_range = st.sidebar.date_input("Date Range", 
                                    value=[min_date, max_date],
                                    min_value=min_date,
                                    max_value=max_date)

# Apply date filter
filtered_df = df.copy()
if len(date_range) == 2:
    filtered_df = filtered_df[(filtered_df['date'] >= pd.to_datetime(date_range[0])) & 
                              (filtered_df['date'] <= pd.to_datetime(date_range[1]))]

# ========== KPIs at Top ==========
st.subheader("📊 Key Performance Indicators")

# Calculate artist counts (need to split for unique artist count)
artist_series = filtered_df['artist'].str.replace(',', ' &').str.split(' & ').explode()
unique_artists = artist_series.nunique()

collab_pct = (filtered_df['is_collaboration'].sum() / len(filtered_df)) * 100
explicit_pct = (filtered_df['is_explicit'].sum() / len(filtered_df)) * 100

# UK artist share (using original artist field)
uk_mask = filtered_df['artist'].apply(lambda x: any(artist in str(x) for artist in uk_artists))
uk_pct = (uk_mask.sum() / len(filtered_df)) * 100

single_pct = (filtered_df[filtered_df['album_type'] == 'single'].shape[0] / len(filtered_df)) * 100

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Unique Artists", unique_artists)

with col2:
    st.metric("Collaboration Ratio", f"{collab_pct:.1f}%")

with col3:
    st.metric("Explicit Content", f"{explicit_pct:.1f}%")

with col4:
    st.metric("UK Artist Share", f"{uk_pct:.1f}%")

with col5:
    st.metric("Singles Ratio", f"{single_pct:.1f}%")

# ========== Artist Dominance Chart ==========
st.subheader("📈 Artist Dominance")

# Split artists for counting
artist_counts = artist_series.value_counts().head(15).reset_index()
artist_counts.columns = ['artist', 'count']

fig1 = px.bar(artist_counts, x='count', y='artist', orientation='h',
              title="Top 15 Artists by Appearance Count",
              labels={'count': 'Number of Appearances', 'artist': ''},
              color='count', color_continuous_scale='Blues')
fig1.update_layout(height=500)
st.plotly_chart(fig1, use_container_width=True)

# Two columns
col1, col2 = st.columns(2)

with col1:
    st.subheader("🔞 Explicit vs Clean Content")
    explicit_counts = filtered_df['is_explicit'].value_counts().reset_index()
    explicit_counts.columns = ['is_explicit', 'count']
    explicit_counts['type'] = explicit_counts['is_explicit'].map({True: 'Explicit', False: 'Clean'})
    fig2 = px.pie(explicit_counts, values='count', names='type', 
                  title="Content Type Distribution")
    st.plotly_chart(fig2, use_container_width=True)

with col2:
    st.subheader("🤝 Collaboration vs Solo")
    collab_counts = filtered_df['is_collaboration'].value_counts().reset_index()
    collab_counts.columns = ['is_collaboration', 'count']
    collab_counts['type'] = collab_counts['is_collaboration'].map({True: 'Collaboration', False: 'Solo'})
    fig3 = px.pie(collab_counts, values='count', names='type',
                  title="Track Type Distribution")
    st.plotly_chart(fig3, use_container_width=True)

# Album type
st.subheader("💿 Album Type Distribution")
album_counts = filtered_df['album_type'].value_counts().reset_index()
album_counts.columns = ['album_type', 'count']
fig4 = px.bar(album_counts, x='album_type', y='count',
              title="Tracks by Album Type",
              color='album_type')
st.plotly_chart(fig4, use_container_width=True)

# Duration
st.subheader("⏱️ Track Duration Analysis")
filtered_df['duration_sec'] = filtered_df['duration_ms'] / 1000
fig5 = px.histogram(filtered_df, x='duration_sec', nbins=50,
                    title="Distribution of Track Durations",
                    labels={'duration_sec': 'Duration (seconds)'})
st.plotly_chart(fig5, use_container_width=True)

import networkx as nx
# ========== Collaboration Network ==========
st.subheader("🕸️ Artist Collaboration Network")

# Build network for top collaborators
import networkx as nx

# Get top 30 most frequent artists for cleaner visualization
top_artists_list = artist_counts.head(30)['artist'].tolist()

# Find collaborations among top artists
collab_pairs = []
for _, row in filtered_df[filtered_df['is_collaboration'] == True].iterrows():
    artists_in_song = row['artist'].replace(',', ' &').split(' & ')
    artists_in_song = [a.strip() for a in artists_in_song]
    # Only keep if both artists are in top 30
    if len(artists_in_song) >= 2:
        for i in range(len(artists_in_song)):
            for j in range(i+1, len(artists_in_song)):
                if artists_in_song[i] in top_artists_list and artists_in_song[j] in top_artists_list:
                    collab_pairs.append((artists_in_song[i], artists_in_song[j]))

# Create network graph
if collab_pairs:
    G = nx.Graph()
    G.add_edges_from(collab_pairs)
    
    # Get positions
    pos = nx.spring_layout(G, k=2, iterations=50)
    
    # Create edge trace
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    
    edge_trace = go.Scatter(x=edge_x, y=edge_y, mode='lines', line=dict(width=1, color='#888'), hoverinfo='none')
    
    # Create node trace
    node_x = []
    node_y = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
    
    node_trace = go.Scatter(x=node_x, y=node_y, mode='markers+text', 
                            text=list(G.nodes()), textposition="top center",
                            marker=dict(size=20, color='lightblue', line=dict(width=2, color='darkblue')),
                            hoverinfo='text')
    
    fig6 = go.Figure(data=[edge_trace, node_trace],
                     layout=go.Layout(title="Collaboration Network (Top 30 Artists)",
                                      showlegend=False, hovermode='closest',
                                      xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                      yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                      height=600))
    st.plotly_chart(fig6, use_container_width=True)
else:
    st.info("Not enough collaboration data for network visualization with current filters.")
st.success("✅ Dashboard ready! Use date filter in sidebar to explore.")
