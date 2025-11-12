import os
import requests
import pandas as pd
import plotly.express as px

AURORA_URL = "https://services.swpc.noaa.gov/json/ovation_aurora_latest.json"

def fetch_aurora_data():
    resp = requests.get(AURORA_URL)
    resp.raise_for_status()
    data = resp.json()

    # Coordinates: [Longitude, Latitude, Aurora]
    coords = data["coordinates"]
    df = pd.DataFrame(coords, columns=["lon", "lat", "aurora"])

    obs_time = data.get("Observation Time", "")
    fc_time = data.get("Forecast Time", "")

    return df, obs_time, fc_time

def build_figure():
    df, obs_time, fc_time = fetch_aurora_data()

    title = f"Aurora Forecast<br><sub>Observation: {obs_time} | Forecast: {fc_time}</sub>"

    fig = px.scatter_geo(
        df,
        lon="lon",
        lat="lat",
        color="aurora",
        color_continuous_scale="Viridis",
        projection="natural earth",
        hover_name=None,
        hover_data={"lon": True, "lat": True, "aurora": True},
        title=title,
    )

    fig.update_traces(marker=dict(size=2))

    fig.update_layout(
        margin=dict(l=0, r=0, t=60, b=0),
        coloraxis_colorbar=dict(
            title="Aurora<br>Intensity",
        ),
    )

    return fig

def main():
    os.makedirs("docs", exist_ok=True)

    fig = build_figure()

    output_path = os.path.join("docs", "index.html")
    fig.write_html(
        output_path,
        full_html=True,
        include_plotlyjs="cdn",
    )

    print(f"Saved interactive map to {output_path}")

if __name__ == "__main__":
    main()
