from typing import Annotated

from fastapi import APIRouter, Query

from src.api.models.schemas import (
    EvolutionMensuelle,
    RegionAnneeQueryParams,
    TopClient,
    TopClientsQueryParams,
    VenteParCategorie,
    VenteParRegion,
    VentesQueryParams,
    VentesResponse,
)
from src.api.services import analyse

router = APIRouter(prefix="/api/v1", tags=["ventes"])


@router.get("/ventes", summary="Ventes filtrées avec résumé")
def get_ventes(
    q: Annotated[VentesQueryParams, Query()],
) -> VentesResponse:
    return analyse.get_ventes(**q.model_dump())


@router.get("/ventes/par-region", summary="CA agrégé par région")
def get_ventes_par_region(
    annee: Annotated[int | None, Query(description="Année (2024 ou 2025)")] = None,
) -> list[VenteParRegion]:
    return analyse.get_ventes_par_region(annee=annee)


@router.get("/ventes/par-categorie", summary="CA agrégé par catégorie")
def get_ventes_par_categorie(
    q: Annotated[RegionAnneeQueryParams, Query()],
) -> list[VenteParCategorie]:
    return analyse.get_ventes_par_categorie(**q.model_dump())


@router.get("/ventes/top-clients", summary="Top clients par CA")
def get_top_clients(
    q: Annotated[TopClientsQueryParams, Query()],
) -> list[TopClient]:
    return analyse.get_top_clients(**q.model_dump())


@router.get("/ventes/evolution", summary="Évolution mensuelle du CA")
def get_evolution_mensuelle(
    q: Annotated[RegionAnneeQueryParams, Query()],
) -> list[EvolutionMensuelle]:
    return analyse.get_evolution_mensuelle(**q.model_dump())
