from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.models.schemas import HealthResponse
from src.api.routes.ventes import router as ventes_router
from src.api.services import analyse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fail fast : vérifie que le dataset est accessible avant d'accepter des requêtes.
    # Sans ça, les erreurs de fichier manquant n'apparaissent qu'au premier appel.
    health = analyse.get_health()
    print(f"Dataset prêt : {health.dataset_rows:,} lignes / {health.dataset_columns} colonnes")
    yield
    # Pas de ressources à libérer — le DataFrame vit dans le module analyse.


app = FastAPI(
    title="API Ventes - DataGyver Demo",
    description=(
        "API de démonstration pour la newsletter **DataGyver #11** : "
        "\"De 'je t'envoie un Excel' à 'voici un endpoint'\". "
        "Explore les endpoints ci-dessous ou connecte Power BI via le bouton *Try it out*."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS permissif pour le dev local — à restreindre en production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(ventes_router)


@app.get("/health", tags=["monitoring"])
def health() -> HealthResponse:
    return analyse.get_health()
