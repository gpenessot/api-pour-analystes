"""
Génère un dataset fictif de ventes pour la démo DataGyver #11.
Distribution réaliste : plus de transactions en fin d'année, Île-de-France surreprésentée.
"""

import random
from pathlib import Path

import numpy as np
import polars as pl

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

N_ROWS = 50_000
OUTPUT_PATH = Path(__file__).parent / "ventes_2024_2025.parquet"

REGIONS = ["Nord", "Sud", "Est", "Ouest", "Île-de-France"]
REGION_WEIGHTS = [0.15, 0.25, 0.13, 0.12, 0.35]

CATEGORIES = ["Logiciel", "Formation", "Consulting", "Support", "Licence"]

COMMERCIAUX = [
    "Alice Martin", "Bob Dupont", "Clara Leroy", "David Bernard", "Emma Petit",
    "François Thomas", "Gabrielle Robert", "Hugo Simon", "Inès Michel",
    "Julien Garcia", "Karine Martinez", "Luc Fontaine", "Marie Blanc",
    "Nicolas Moreau", "Océane Girard",
]


def generer_dates(n: int, rng: np.random.Generator) -> list[str]:
    """Distribution saisonnière réaliste : T4 surreprésenté (deals de fin d'année)."""
    # Poids par mois : T4 (oct-déc) capte ~35% des ventes
    poids_mensuels = [0.06, 0.06, 0.07, 0.07, 0.08, 0.08, 0.07, 0.07, 0.08, 0.10, 0.13, 0.13]

    dates = []
    for _ in range(n):
        annee = rng.choice([2024, 2025])
        mois = rng.choice(range(1, 13), p=poids_mensuels)
        # Nombre de jours selon le mois
        jours_par_mois = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        jour = rng.integers(1, jours_par_mois[mois - 1] + 1)
        dates.append(f"{annee}-{mois:02d}-{jour:02d}")
    return dates


def main() -> None:
    rng = np.random.default_rng(SEED)

    transaction_ids = [
        "".join(random.choices("0123456789abcdef", k=8)) for _ in range(N_ROWS)
    ]

    dates = generer_dates(N_ROWS, rng)

    regions = rng.choice(REGIONS, size=N_ROWS, p=REGION_WEIGHTS).tolist()
    categories = rng.choice(CATEGORIES, size=N_ROWS).tolist()

    # ~2000 clients uniques au format CLT-XXXX
    client_pool = [f"CLT-{i:04d}" for i in range(1, 2001)]
    clients = rng.choice(client_pool, size=N_ROWS).tolist()

    commerciaux = rng.choice(COMMERCIAUX, size=N_ROWS).tolist()

    # Distribution log-normale : médiane ~800€, quelques gros deals jusqu'à ~15k€
    montants_raw = np.exp(rng.normal(loc=np.log(800), scale=0.9, size=N_ROWS))
    montants = np.clip(montants_raw, 50, 15_000).round(2).tolist()

    df = pl.DataFrame({
        "transaction_id": transaction_ids,
        "date": dates,
        "region": regions,
        "categorie": categories,
        "client_id": clients,
        "montant": montants,
        "commercial": commerciaux,
    }).with_columns(pl.col("date").cast(pl.Date))

    df.write_parquet(OUTPUT_PATH, compression="snappy")

    taille_mb = OUTPUT_PATH.stat().st_size / 1024 / 1024
    print(f"Dataset genere : {OUTPUT_PATH}")
    print(f"   Lignes        : {len(df):,}")
    print(f"   Colonnes      : {df.columns}")
    print(f"   Taille fichier: {taille_mb:.2f} MB")
    stats = df.select("montant").describe()
    print("\nStats montant (EUR) :")
    # encode pour eviter les erreurs sur les terminaux Windows (cp1252)
    print(stats.to_pandas().to_string().encode("ascii", errors="replace").decode("ascii"))


if __name__ == "__main__":
    main()
