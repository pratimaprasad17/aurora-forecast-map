import os
from datetime import datetime

import requests
import pandas as pd
import plotly.graph_objects as go

AURORA_URL = "https://services.swpc.noaa.gov/json/ovation_aurora_latest.json"


def fetch_aurora_data():
    """Fetch latest aurora data from NOAA and return DataFrame + times."""
    resp = requests.get(AURORA_URL)
    resp.raise_for_status()
    data = resp.json()

    # Data format: [Longitude, Latitude, Aurora]
    coords = data["coordinates"]
    df = pd.DataFrame(coords, columns=["lon", "lat", "aurora"])

    obs_time = data.get("Observation Time", "")
    fc_time = data.get("Forecast Time", "")

    return df, obs_time, fc_time


def build_figure(df: pd.DataFrame, obs_time: str, fc_time: str) -> go.Figure:
    """
    Build an interactive world map with threshold dropdown.

    Threshold options:
      - Show all points
      - aurora >= 1
      - aurora >= 5
      - aurora >= 10
    """
    thresholds = [0, 1, 5, 10]
    max_aurora = df["aurora"].max()

    traces = []
    for i, thr in enumerate(thresholds):
        subset = df[df["aurora"] >= thr]

        traces.append(
            go.Scattergeo(
                lon=subset["lon"],
                lat=subset["lat"],
                mode="markers",
                marker=dict(
                    size=2,
                    color=subset["aurora"],
                    colorscale="Viridis",
                    cmin=0,
                    cmax=max_aurora,
                    colorbar=dict(
                        title="Aurora<br>Intensity"
                    )
                    if i == 0  # one shared colorbar
                    else None,
                ),
                showlegend=False,
                visible=(i == 0),  # start with "All" visible
                name=f"aurora ≥ {thr}",
            )
        )

    title = (
        "Aurora Forecast"
        f"<br><sub>Observation: {obs_time} | Forecast: {fc_time}</sub>"
    )

    # Dropdown buttons to toggle thresholds
    buttons = []
    for i, thr in enumerate(thresholds):
        visible = [False] * len(thresholds)
        visible[i] = True

        buttons.append(
            dict(
                label=f"Aurora ≥ {thr}",
                method="update",
                args=[
                    {"visible": visible},
                    {"title": title + f"<br><sup>Threshold: aurora ≥ {thr}</sup>"},
                ],
            )
        )

    fig = go.Figure(data=traces)

    fig.update_layout(
        title=title,
        geo=dict(
            projection_type="natural earth",
            showcoastlines=True,
            coastlinecolor="gray",
            showland=True,
            landcolor="rgb(240,240,240)",
            showcountries=True,
        ),
        updatemenus=[
            dict(
                type="dropdown",
                direction="down",
                showactive=True,
                active=0,
                x=0.02,
                y=0.95,
                xanchor="left",
                yanchor="top",
                buttons=buttons,
            )
        ],
        margin=dict(l=0, r=0, t=80, b=0),
    )

    return fig


def format_iso_timestamp(ts: str) -> str | None:
    """
    Convert ISO time like '2025-11-12T21:47:00Z' to '20251112_214700'.
    Return None if parsing fails.
    """
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y%m%d_%H%M%S")
    except Exception:
        return None


def get_timestamp_from_times(obs_time: str, fc_time: str) -> str:
    """
    Build a filename-safe timestamp using BOTH observation and forecast times.
    Example: 'obs_20251112_214700__fc_20251112_223600'
    """
    obs_part = format_iso_timestamp(obs_time) or "unknown"
    fc_part = format_iso_timestamp(fc_time) or "unknown"
    return f"obs_{obs_part}__fc_{fc_part}"


def main():
    # Ensure docs/ and docs/images/ exist so GitHub Pages can serve them
    docs_dir = "docs"
    images_dir = os.path.join(docs_dir, "images")
    os.makedirs(docs_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)

    df, obs_time, fc_time = fetch_aurora_data()
    fig = build_figure(df, obs_time, fc_time)

    # 1) Save interactive HTML for GitHub Pages
    html_path = os.path.join(docs_dir, "index.html")
    fig.write_html(
        html_path,
        full_html=True,
        include_plotlyjs="cdn",
    )

    # 2) Save a JPG snapshot with timestamped filename
    ts_str = get_timestamp_from_times(obs_time, fc_time)
    jpg_filename = f"aurora_{ts_str}.jpg"
    jpg_path = os.path.join(images_dir, jpg_filename)

    # write_image uses kaleido under the hood
    fig.write_image(jpg_path, format="jpg", width=1600, height=900, scale=2)

    print(f"Saved interactive map to {html_path}")
    print(f"Saved JPEG snapshot to {jpg_path}")


if __name__ == "__main__":
    main()
