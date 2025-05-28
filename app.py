import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from streamlit_folium import st_folium
from sklearn.cluster import KMeans
from scipy.stats import zscore

st.title("Uber Data Analysis Dashboard")

# Load dataset
dataset = pd.read_csv("UberDataset.csv")

# Data Cleaning
dataset['START_DATE'] = pd.to_datetime(dataset['START_DATE'], errors='coerce')
dataset['END_DATE'] = pd.to_datetime(dataset['END_DATE'], errors='coerce')

# Fill missing categorical values with forward fill, then backward fill
for col in ['START', 'STOP']:
    if col in dataset.columns:
        dataset[col] = dataset[col].fillna(method='ffill').fillna(method='bfill')

# Fill missing numeric values with median
for col in ['MILES']:
    if col in dataset.columns:
        dataset[col] = dataset[col].fillna(dataset[col].median())

# Drop rows where dates are still missing
dataset.dropna(subset=['START_DATE', 'END_DATE'], inplace=True)

# Add time and duration columns
dataset['time'] = dataset['START_DATE'].dt.hour
dataset['DURATION'] = (dataset['END_DATE'] - dataset['START_DATE']).dt.total_seconds() / 60

# Show cleaned data preview
with st.expander("Show Cleaned Data"):
    st.dataframe(dataset.head())

# Sidebar selection
option = st.sidebar.selectbox(
    "Select Analysis",
    (
        "Peak Hour Analysis",
        "Route Mapping",
        "Ride Duration Analysis",
        "Distance vs. Duration",
        "Clustering",
        "Outlier Detection"
    )
)

if option == "Peak Hour Analysis":
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.countplot(x=dataset['time'], color='purple', ax=ax)
    ax.set_xlabel('Hour of the Day')
    ax.set_ylabel('Number of Rides')
    ax.set_title('Peak Hour Analysis')
    st.pyplot(fig)

elif option == "Route Mapping":
    st.info("Showing up to 100 random start and stop locations for visualization.")
    start_locations = dataset[['START', 'MILES']].drop_duplicates().head(100)
    stop_locations = dataset[['STOP', 'MILES']].drop_duplicates().head(100)
    map_ = folium.Map(location=[40.7128, -74.0060], zoom_start=10)
    for _, row in start_locations.iterrows():
        folium.Marker(
            location=[np.random.uniform(40.6, 40.8), np.random.uniform(-74.1, -73.9)],
            popup=f"Start: {row['START']}\nMiles: {row['MILES']}",
            icon=folium.Icon(color='blue', icon='cloud')
        ).add_to(map_)
    for _, row in stop_locations.iterrows():
        folium.Marker(
            location=[np.random.uniform(40.6, 40.8), np.random.uniform(-74.1, -73.9)],
            popup=f"Stop: {row['STOP']}\nMiles: {row['MILES']}",
            icon=folium.Icon(color='red', icon='cloud')
        ).add_to(map_)
    st_folium(map_, width=700, height=500)

elif option == "Ride Duration Analysis":
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.histplot(dataset['DURATION'], bins=50, kde=True, ax=ax)
    ax.set_xlabel('Ride Duration (minutes)')
    ax.set_ylabel('Frequency')
    ax.set_title('Distribution of Ride Duration')
    st.pyplot(fig)

elif option == "Distance vs. Duration":
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.scatterplot(x=dataset['MILES'], y=dataset['DURATION'], alpha=0.5, ax=ax)
    ax.set_xlabel('Distance (Miles)')
    ax.set_ylabel('Duration (Minutes)')
    ax.set_title('Distance vs. Ride Duration')
    st.pyplot(fig)

elif option == "Clustering":
    np.random.seed(42)
    dataset['lat'] = np.random.uniform(40.5, 40.9, dataset.shape[0])
    dataset['lon'] = np.random.uniform(-74.2, -73.7, dataset.shape[0])
    kmeans = KMeans(n_clusters=5, random_state=42)
    dataset['cluster'] = kmeans.fit_predict(dataset[['lat', 'lon']])
    map_clusters = folium.Map(location=[40.7128, -74.0060], zoom_start=11)
    colors = ['red', 'blue', 'green', 'purple', 'orange']
    for i in range(len(dataset)):
        folium.CircleMarker(
            location=[dataset.iloc[i]['lat'], dataset.iloc[i]['lon']],
            radius=4,
            color=colors[dataset.iloc[i]['cluster']],
            fill=True,
            fill_color=colors[dataset.iloc[i]['cluster']],
            fill_opacity=0.7
        ).add_to(map_clusters)
    st_folium(map_clusters, width=700, height=500)

elif option == "Outlier Detection":
    dataset['Z_SCORE_MILES'] = np.abs(zscore(dataset['MILES']))
    dataset['Z_SCORE_DURATION'] = np.abs(zscore(dataset['DURATION']))
    outliers = dataset[(dataset['Z_SCORE_MILES'] > 3) | (dataset['Z_SCORE_DURATION'] > 3)]
    st.write(f"Number of Outliers Detected: {outliers.shape[0]}")
    st.dataframe(outliers)