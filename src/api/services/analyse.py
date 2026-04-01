"""
Couche métier : toutes les requêtes Polars sur le dataset de ventes.
Isolée de FastAPI pour être testable indépendamment.
"""

from pathlib import Path

import polars as pl

from src.api.models.schemas import (
    EvolutionMensuelle,
    HealthResponse,
    TopClient,
    VenteDetail,
    VenteParCategorie,
    VenteParRegion,
    VenteResume,
    VentesResponse,
)

_PARQUET_PATH = Path(__file__).parents[3] / "data" / "ventes_2024_2025.parquet"

# Chargement unique au démarrage du module — évite une I/O à chaque requête
_df: pl.DataFrame = pl.read_parquet(_PARQUET_PATH)


def _filtre_annee(df: pl.DataFrame, annee: int | None) -> pl.DataFrame:
    if annee is not None:
        return df.filter(pl.col("date").dt.year() == annee)
    return df


def _filtre_region(df: pl.DataFrame, region: str | None) -> pl.DataFrame:
    if region is not None:
        return df.filter(pl.col("region") == region)
    return df


def get_ventes(
    region: str | None = None,
    categorie: str | None = None,
    annee: int | None = 2025,
    limit: int = 100,
) -> VentesResponse:
    df = _filtre_annee(_df, annee)
    df = _filtre_region(df, region)

    if categorie is not None:
        df = df.filter(pl.col("categorie") == categorie)

    total_ca = df.select(pl.col("montant").sum()).item() or 0.0
    nb_transactions = len(df)
    panier_moyen = total_ca / nb_transactions if nb_transactions > 0 else 0.0
    regions_disponibles = sorted(df.select("region").unique().to_series().to_list())

    resume = VenteResume(
        total_ca=round(total_ca, 2),
        nb_transactions=nb_transactions,
        panier_moyen=round(panier_moyen, 2),
        regions_disponibles=regions_disponibles,
    )

    rows = (
        df.select(["transaction_id", "date", "region", "categorie", "montant"])
        .head(limit)
        .with_columns(pl.col("date").cast(pl.Utf8))
        .to_dicts()
    )
    data = [VenteDetail(**row) for row in rows]

    return VentesResponse(resume=resume, data=data)


def get_ventes_par_region(annee: int | None = None) -> list[VenteParRegion]:
    df = _filtre_annee(_df, annee)

    ca_total_global = df.select(pl.col("montant").sum()).item() or 1.0

    result = (
        df.group_by("region")
        .agg(
            pl.col("montant").sum().alias("ca_total"),
            pl.len().alias("nb_ventes"),
            pl.col("montant").mean().alias("panier_moyen"),
        )
        .with_columns(
            (pl.col("ca_total") / ca_total_global * 100).round(2).alias("part_ca_pct")
        )
        .sort("ca_total", descending=True)
    )

    return [VenteParRegion(**row) for row in result.to_dicts()]


def get_ventes_par_categorie(
    annee: int | None = None,
    region: str | None = None,
) -> list[VenteParCategorie]:
    df = _filtre_annee(_df, annee)
    df = _filtre_region(df, region)

    result = (
        df.group_by("categorie")
        .agg(
            pl.col("montant").sum().alias("ca_total"),
            pl.len().alias("nb_ventes"),
        )
        .sort("ca_total", descending=True)
    )

    return [VenteParCategorie(**row) for row in result.to_dicts()]


def get_top_clients(
    annee: int | None = None,
    region: str | None = None,
    top_n: int = 10,
) -> list[TopClient]:
    df = _filtre_annee(_df, annee)
    df = _filtre_region(df, region)

    result = (
        df.group_by("client_id")
        .agg(
            pl.col("montant").sum().alias("ca_total"),
            pl.len().alias("nb_transactions"),
        )
        .sort("ca_total", descending=True)
        .head(top_n)
    )

    return [TopClient(**row) for row in result.to_dicts()]


def get_evolution_mensuelle(
    annee: int | None = None,
    region: str | None = None,
) -> list[EvolutionMensuelle]:
    df = _filtre_annee(_df, annee)
    df = _filtre_region(df, region)

    result = (
        df.with_columns(
            pl.col("date").dt.strftime("%Y-%m").alias("mois")
        )
        .group_by("mois")
        .agg(
            pl.col("montant").sum().alias("ca_total"),
            pl.len().alias("nb_ventes"),
        )
        .sort("mois")
    )

    return [EvolutionMensuelle(**row) for row in result.to_dicts()]


def get_health() -> HealthResponse:
    derniere_date = _df.select(pl.col("date").max()).item()
    return HealthResponse(
        status="ok",
        dataset_rows=len(_df),
        dataset_columns=len(_df.columns),
        derniere_date=str(derniere_date),
    )
