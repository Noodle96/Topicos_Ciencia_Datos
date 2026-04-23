from __future__ import annotations

from pathlib import Path
from typing import Any
from datetime import datetime

import pandas as pd
from flask import Flask, jsonify, render_template
from meteostat import Daily, Monthly, Point

# Ruta base del proyecto
BASE_DIR: Path = Path(__file__).resolve().parent
print("base_dir: ", BASE_DIR)

# Rutas de datos
DATA_DIR: Path = BASE_DIR / "data"
STATIONS_CSV: Path = DATA_DIR / "hubway_stations.csv"
print("stations_csv: ", STATIONS_CSV)
TRIPS_CSV: Path = DATA_DIR / "hubway_trips.csv"
print("trips_csv: ", TRIPS_CSV)

WEATHER_START: datetime = datetime(2011, 1, 1)
WEATHER_END: datetime = datetime(2013, 12, 31)

# Crear app Flask
app: Flask = Flask(__name__)


def load_stations() -> pd.DataFrame:
    """
    Carga el dataset de estaciones.
    """
    stations_df: pd.DataFrame = pd.read_csv(STATIONS_CSV)
    print("stations_df.shape: ",stations_df.shape)
    return stations_df


def build_municipal_points(stations_df: pd.DataFrame) -> pd.DataFrame:
    """
    Construye un punto geográfico representativo por municipalidad
    usando el promedio de latitud y longitud de sus estaciones.
    """
    municipal_points_df: pd.DataFrame = (
        stations_df.groupby("municipal", as_index=False)
        .agg(
            lat=("lat", "mean"),
            lng=("lng", "mean"),
        )
        .copy()
    )

    return municipal_points_df


def fetch_monthly_weather_for_point(
    latitude: float,
    longitude: float,
    start: datetime,
    end: datetime,
) -> pd.DataFrame:
    """
    Consulta Meteostat para un punto geográfico y devuelve
    datos mensuales históricos.
    """
    point: Point = Point(latitude, longitude)

    weather_df: pd.DataFrame = Monthly(point, start, end).fetch()
    weather_df = weather_df.reset_index()

    return weather_df


def fetch_daily_weather_for_point(
    latitude: float,
    longitude: float,
    start: datetime,
    end: datetime,
) -> pd.DataFrame:
    """
    Consulta Meteostat para un punto geográfico y devuelve
    datos diarios históricos.
    """
    point: Point = Point(latitude, longitude)

    weather_df: pd.DataFrame = Daily(point, start, end).fetch()
    weather_df = weather_df.reset_index()

    return weather_df


def build_monthly_average_series_from_monthly(
    weather_df: pd.DataFrame,
) -> dict[str, list[float | None]]:
    """
    A partir de un DataFrame mensual histórico, calcula promedios
    por mes del año para temperatura y lluvia.
    """
    if weather_df.empty:
        return {
            "temperature": [None] * 12,
            "rain": [None] * 12,
        }

    weather_df["month"] = pd.to_datetime(weather_df["time"]).dt.month

    monthly_avg_df: pd.DataFrame = (
        weather_df.groupby("month", as_index=False)
        .agg(
            temperature=("tavg", "mean"),  # 🔥 CAMBIO AQUÍ
            rain=("prcp", "mean"),
        )
        .copy()
    )

    result: dict[str, list[float | None]] = {
        "temperature": [],
        "rain": [],
    }

    for month in range(1, 13):
        matching_rows: pd.DataFrame = monthly_avg_df[monthly_avg_df["month"] == month]

        if matching_rows.empty:
            result["temperature"].append(None)
            result["rain"].append(None)
        else:
            row: pd.Series = matching_rows.iloc[0]
            result["temperature"].append(
                None
                if pd.isna(row["temperature"])
                else round(float(row["temperature"]), 2)
            )
            result["rain"].append(
                None if pd.isna(row["rain"]) else round(float(row["rain"]), 2)
            )

    return result


def build_monthly_average_wind_from_daily(
    weather_df: pd.DataFrame,
) -> list[float | None]:
    """
    A partir de un DataFrame diario histórico, calcula el promedio
    de velocidad del viento por mes del año.
    """
    if weather_df.empty:
        return [None] * 12

    weather_df["month"] = pd.to_datetime(weather_df["time"]).dt.month

    wind_avg_df: pd.DataFrame = (
        weather_df.groupby("month", as_index=False)
        .agg(
            wind=("wspd", "mean"),
        )
        .copy()
    )

    result: list[float | None] = []

    for month in range(1, 13):
        matching_rows: pd.DataFrame = wind_avg_df[wind_avg_df["month"] == month]

        if matching_rows.empty:
            result.append(None)
        else:
            row: pd.Series = matching_rows.iloc[0]
            result.append(
                None if pd.isna(row["wind"]) else round(float(row["wind"]), 2)
            )

    return result


def build_municipal_weather_payload(
    stations_df: pd.DataFrame,
    start: datetime,
    end: datetime,
) -> list[dict[str, Any]]:
    """
    Construye el payload climático mensual promedio por municipalidad.
    """
    municipal_points_df: pd.DataFrame = build_municipal_points(stations_df)

    payload: list[dict[str, Any]] = []

    for _, row in municipal_points_df.iterrows():
        municipal_name: str = str(row["municipal"])
        latitude: float = float(row["lat"])
        longitude: float = float(row["lng"])

        monthly_weather_df: pd.DataFrame = fetch_monthly_weather_for_point(
            latitude=latitude,
            longitude=longitude,
            start=start,
            end=end,
        )

        daily_weather_df: pd.DataFrame = fetch_daily_weather_for_point(
            latitude=latitude,
            longitude=longitude,
            start=start,
            end=end,
        )

        print("Russell debug:")
        print("MONTHLY COLUMNS:", monthly_weather_df.columns.tolist())
        print("DAILY COLUMNS:", daily_weather_df.columns.tolist())

        monthly_series: dict[str, list[float | None]] = (
            build_monthly_average_series_from_monthly(monthly_weather_df)
        )

        wind_series: list[float | None] = build_monthly_average_wind_from_daily(
            daily_weather_df
        )

        payload.append(
            {
                "municipal": municipal_name,
                "temperature": monthly_series["temperature"],
                "rain": monthly_series["rain"],
                "wind": wind_series,
            }
        )

    return payload


def load_trips() -> pd.DataFrame:
    """
    Carga el dataset de viajes y realiza una limpieza mínima
    usando solo las columnas necesarias para esta fase.
    """
    trips_df: pd.DataFrame = pd.read_csv(TRIPS_CSV)

    # Conservar únicamente columnas relevantes para esta fase
    trips_df = trips_df[["start_date", "strt_statn"]].copy()
    print("trips_df.shape after selecting columns: ", trips_df.shape)

    # Eliminar nulls solo en columnas necesarias
    trips_df = trips_df.dropna(subset=["start_date", "strt_statn"])

    # Convertir fecha
    trips_df["start_date"] = pd.to_datetime(trips_df["start_date"], errors="coerce")

    # Eliminar filas donde la fecha no pudo convertirse
    trips_df = trips_df.dropna(subset=["start_date"])

    # Convertir estación a entero
    trips_df["strt_statn"] = trips_df["strt_statn"].astype(int)

    # Extraer mes numérico
    trips_df["month"] = trips_df["start_date"].dt.month
    print("trips final: ")
    print(trips_df.head())
    print(trips_df.shape)
    return trips_df


def build_municipal_month_counts(
    stations_df: pd.DataFrame,
    trips_df: pd.DataFrame,
) -> list[dict[str, Any]]:
    """
    Construye una lista con la frecuencia mensual de uso para cada municipalidad.
    """
    # Nos quedamos solo con columnas necesarias del dataset de estaciones
    stations_subset_df: pd.DataFrame = stations_df[["id", "municipal"]].copy()

    # Asegurar tipos compatibles para el merge
    stations_subset_df["id"] = stations_subset_df["id"].astype(int)

    # Unir viajes con estaciones para obtener municipalidad
    merged_df: pd.DataFrame = trips_df.merge(
        stations_subset_df,
        left_on="strt_statn",
        right_on="id",
        how="inner",
    )

    # Agrupar por municipalidad y mes
    grouped_df: pd.DataFrame = (
        merged_df.groupby(["municipal", "month"]).size().reset_index(name="count")
    )

    municipals: list[str] = sorted(merged_df["municipal"].dropna().unique().tolist())

    result: list[dict[str, Any]] = []

    for municipal_name in municipals:
        monthly_counts: list[int] = []

        for month in range(1, 13):
            matching_rows: pd.DataFrame = grouped_df[
                (grouped_df["municipal"] == municipal_name)
                & (grouped_df["month"] == month)
            ]

            if matching_rows.empty:
                monthly_counts.append(0)
            else:
                monthly_counts.append(int(matching_rows["count"].iloc[0]))

        result.append(
            {
                "municipal": municipal_name,
                "monthly_counts": monthly_counts,
            }
        )

    return result


@app.route("/")
def index() -> str:
    """
    Renderiza la página principal.
    """
    return render_template("index.html")


@app.route("/api/stations")
def api_stations() -> Any:
    """
    Devuelve las municipalidades disponibles.
    """
    stations_df: pd.DataFrame = load_stations()

    municipals: list[str] = sorted(stations_df["municipal"].dropna().unique().tolist())

    municipals_payload: list[dict[str, str]] = [
        {"municipal": municipal_name} for municipal_name in municipals
    ]

    return jsonify(municipals_payload)


@app.route("/api/station-monthly-usage")
def api_station_monthly_usage() -> Any:
    """
    Devuelve, para cada municipalidad, la frecuencia mensual de uso.
    """
    stations_df: pd.DataFrame = load_stations()
    trips_df: pd.DataFrame = load_trips()

    payload: list[dict[str, Any]] = build_municipal_month_counts(stations_df, trips_df)

    return jsonify(payload)


@app.route("/api/weather-monthly-averages")
def api_weather_monthly_averages() -> Any:
    """
    Devuelve promedios mensuales de temperatura, lluvia y viento
    para cada municipalidad.
    """
    stations_df: pd.DataFrame = load_stations()

    payload: list[dict[str, Any]] = build_municipal_weather_payload(
        stations_df=stations_df,
        start=WEATHER_START,
        end=WEATHER_END,
    )

    return jsonify(payload)


if __name__ == "__main__":
    app.run(debug=True)
