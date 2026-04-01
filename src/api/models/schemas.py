from pydantic import BaseModel, ConfigDict, Field


# ── Modèles de réponse ────────────────────────────────────────────────────────
# Pas de frozen=True : ces objets sont créés, sérialisés, puis jetés.
# frozen ajoute __hash__ et des checks inutiles pour des modèles éphémères.

class VenteResume(BaseModel):
    total_ca: float
    nb_transactions: int
    panier_moyen: float
    regions_disponibles: list[str]


class VenteParRegion(BaseModel):
    region: str
    ca_total: float
    nb_ventes: int
    panier_moyen: float
    part_ca_pct: float


class VenteParCategorie(BaseModel):
    categorie: str
    ca_total: float
    nb_ventes: int


class VenteDetail(BaseModel):
    transaction_id: str
    date: str
    region: str
    categorie: str
    montant: float


class VentesResponse(BaseModel):
    resume: VenteResume
    data: list[VenteDetail]


class TopClient(BaseModel):
    client_id: str
    ca_total: float
    nb_transactions: int


class EvolutionMensuelle(BaseModel):
    mois: str
    ca_total: float
    nb_ventes: int


class HealthResponse(BaseModel):
    status: str
    dataset_rows: int
    dataset_columns: int
    derniere_date: str


# ── Modèles de paramètres de requête (FastAPI 0.115+) ─────────────────────────
# Regrouper les query params dans un modèle Pydantic évite la répétition
# d'Annotated[..., Query(...)] sur chaque endpoint.

class VentesQueryParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    region: str | None = Field(None, description="Filtrer par région")
    categorie: str | None = Field(None, description="Filtrer par catégorie")
    annee: int | None = Field(2025, description="Année (2024 ou 2025)")
    limit: int = Field(100, ge=1, le=1000, description="Nombre de lignes retournées")


class RegionAnneeQueryParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    annee: int | None = Field(None, description="Année (2024 ou 2025)")
    region: str | None = Field(None, description="Filtrer par région")


class TopClientsQueryParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    annee: int | None = Field(None, description="Année (2024 ou 2025)")
    region: str | None = Field(None, description="Filtrer par région")
    top_n: int = Field(10, ge=1, le=100, description="Nombre de clients à retourner")
