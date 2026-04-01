# Prompt Claude Code : Démo FastAPI + Streamlit pour Newsletter DataGyver

## Contexte

Tu vas créer le repo compagnon de la newsletter DataGyver #11 "De 'je t'envoie un Excel' à 'voici un endpoint'". Ce repo sert de démo pédagogique pour des data analysts juniors/reconvertis qui n'ont jamais créé d'API. Il doit être clonable et fonctionnel en moins de 5 minutes.

## Stack obligatoire

- **Python 3.12+**
- **uv** comme gestionnaire de dépendances et d'environnement (pas pip, pas poetry)
- **FastAPI** avec `fastapi[standard]` (inclut uvicorn)
- **Polars** pour le traitement de données
- **Pydantic v2** pour les schémas (installé avec FastAPI)
- **Streamlit** pour le dashboard
- **httpx** pour les tests API
- **pytest** pour les tests

## Structure du projet

```
fastapi-data-analyst/
├── pyproject.toml
├── Makefile
├── README.md
├── data/
│   └── generate_data.py        # Script de génération du dataset fictif
├── src/
│   ├── api/
│   │   ├── main.py             # Point d'entrée FastAPI
│   │   ├── routes/
│   │   │   └── ventes.py       # Endpoints ventes
│   │   ├── services/
│   │   │   └── analyse.py      # Logique métier Polars
│   │   └── models/
│   │       └── schemas.py      # Modèles Pydantic v2
│   └── dashboard/
│       └── app.py              # App Streamlit
├── tests/
│   ├── conftest.py
│   └── test_api.py
└── assets/
    └── powerquery_example.m    # Requête Power Query pour Power BI
```

## 1. Dataset fictif (`data/generate_data.py`)

Génère un fichier `data/ventes_2024_2025.parquet` avec Polars :

- **~50 000 lignes** de transactions de ventes
- Colonnes :
  - `transaction_id` : identifiant unique (UUID court, 8 caractères hex)
  - `date` : dates entre 2024-01-01 et 2025-12-31, distribution réaliste (plus de ventes en fin d'année)
  - `region` : parmi ["Nord", "Sud", "Est", "Ouest", "Île-de-France"] avec distribution non uniforme (IdF = 35%, Sud = 25%, Nord = 15%, Est = 13%, Ouest = 12%)
  - `categorie` : parmi ["Logiciel", "Formation", "Consulting", "Support", "Licence"]
  - `client_id` : ~2000 clients uniques (format "CLT-XXXX")
  - `montant` : entre 50€ et 15000€, distribution log-normale réaliste (médiane ~800€, quelques gros deals)
  - `commercial` : 15 noms de commerciaux fictifs
- Le script doit être reproductible (`random.seed(42)` ou équivalent Polars/numpy)
- Sauvegarde en Parquet avec compression snappy
- Affiche un résumé après génération (nb lignes, colonnes, taille fichier, stats descriptives montant)

## 2. API FastAPI

### `src/api/models/schemas.py`

Modèles Pydantic v2 pour les réponses :

```python
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
    part_ca_pct: float  # pourcentage du CA total

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

class HealthResponse(BaseModel):
    status: str
    dataset_rows: int
    dataset_columns: int
    derniere_date: str
```

### `src/api/services/analyse.py`

Logique métier en Polars pur (aucune dépendance à FastAPI ici) :

- Charger le Parquet une seule fois au démarrage (variable de module)
- Fonctions :
  - `get_ventes(region, categorie, annee, limit)` → filtre le dataset, retourne résumé + données
  - `get_ventes_par_region(annee)` → agrégation par région avec % du CA
  - `get_ventes_par_categorie(annee, region)` → agrégation par catégorie
  - `get_top_clients(annee, region, top_n)` → top N clients par CA
  - `get_evolution_mensuelle(annee, region)` → CA par mois
  - `get_health()` → infos sur le dataset chargé

### `src/api/routes/ventes.py`

Endpoints (tous en GET) :

| Endpoint | Params query | Description |
|---|---|---|
| `GET /api/v1/ventes` | `region?`, `categorie?`, `annee?` (défaut: 2025), `limit?` (défaut: 100, max: 1000) | Ventes filtrées avec résumé |
| `GET /api/v1/ventes/par-region` | `annee?` | CA agrégé par région |
| `GET /api/v1/ventes/par-categorie` | `annee?`, `region?` | CA agrégé par catégorie |
| `GET /api/v1/ventes/top-clients` | `annee?`, `region?`, `top_n?` (défaut: 10) | Top clients par CA |
| `GET /api/v1/ventes/evolution` | `annee?`, `region?` | CA mensuel |
| `GET /health` | aucun | Santé de l'API + infos dataset |

Utiliser `APIRouter` avec prefix `/api/v1` et tags pour une doc Swagger propre.

### `src/api/main.py`

- Titre : "API Ventes - DataGyver Demo"
- Description : mentionner que c'est la démo de la newsletter DataGyver #11
- Version : "1.0.0"
- Inclure le router ventes
- Ajouter un middleware CORS permissif (pour que Streamlit puisse appeler l'API en dev)

## 3. Dashboard Streamlit (`src/dashboard/app.py`)

### Design

Dashboard propre et professionnel avec :

- **Titre** : "📊 Dashboard Ventes"
- **Sidebar** avec les filtres :
  - Sélection de l'année (2024 / 2025)
  - Sélection de la région (multiselect avec "Toutes" par défaut)
  - L'URL de l'API (préremplie `http://localhost:8000`, modifiable)
  - Un indicateur de statut de connexion à l'API (vert/rouge)

- **Section KPIs** (st.metric en colonnes) :
  - CA Total
  - Nombre de transactions
  - Panier moyen
  - Nombre de régions

- **Section graphiques** (2 colonnes) :
  - Graphique bar : CA par région (Plotly ou st.bar_chart natif)
  - Graphique bar : CA par catégorie

- **Section évolution** :
  - Line chart : évolution mensuelle du CA

- **Section Top Clients** :
  - Tableau des top 10 clients

- **Footer** : lien vers la newsletter DataGyver et le repo GitHub

### Implémentation

- Toutes les données viennent de l'API via `requests.get()` (jamais de lecture directe du Parquet)
- Gérer proprement le cas où l'API n'est pas accessible (message d'erreur clair, pas de crash)
- Utiliser `@st.cache_data(ttl=60)` pour les appels API
- Formater les montants en euros avec séparateur de milliers
- Le dashboard doit être fonctionnel et visuellement propre sans CSS custom

## 4. Tests (`tests/`)

### `tests/conftest.py`
- Fixture `client` qui crée un `TestClient` FastAPI

### `tests/test_api.py`
Tests à implémenter :
- `test_health` : vérifie status 200 et présence des champs
- `test_get_ventes_sans_filtre` : vérifie structure de réponse
- `test_get_ventes_filtre_region` : vérifie que le filtre fonctionne
- `test_get_ventes_region_inexistante` : vérifie réponse vide (pas d'erreur)
- `test_get_ventes_par_region` : vérifie toutes les régions présentes
- `test_get_ventes_par_categorie` : vérifie structure
- `test_get_top_clients` : vérifie que top_n est respecté
- `test_get_evolution` : vérifie 12 mois pour une année complète
- `test_limit_parameter` : vérifie que limit cap les résultats

## 5. Fichiers de support

### `Makefile`

```makefile
.PHONY: setup data api dashboard test all

setup:
	uv sync

data:
	uv run python data/generate_data.py

api:
	uv run fastapi dev src/api/main.py

dashboard:
	uv run streamlit run src/dashboard/app.py

test:
	uv run pytest tests/ -v

all: setup data
	@echo "✅ Setup terminé. Lancez 'make api' puis 'make dashboard' dans deux terminaux."
```

### `assets/powerquery_example.m`

Requête Power Query fonctionnelle montrant comment connecter Power BI à l'API :

```m
let
    // Configuration - Modifiez ces paramètres selon vos besoins
    ApiBase = "http://localhost:8000",
    Annee = "2025",
    
    // Appel API - CA par région
    Url = ApiBase & "/api/v1/ventes/par-region?annee=" & Annee,
    Source = Json.Document(Web.Contents(Url)),
    Table = Table.FromRecords(Source),
    
    // Typage des colonnes
    TypedTable = Table.TransformColumnTypes(Table, {
        {"region", type text},
        {"ca_total", type number},
        {"nb_ventes", Int64.Type},
        {"panier_moyen", type number},
        {"part_ca_pct", type number}
    })
in
    TypedTable
```

### `README.md`

README complet avec :
- Badge "Made for DataGyver Newsletter"
- Description du projet (1 paragraphe)
- Screenshot ou GIF du dashboard Streamlit (placeholder pour l'instant)
- Prérequis : Python 3.12+, uv
- Quick start en 4 commandes (`git clone`, `make setup`, `make data`, puis `make api` + `make dashboard`)
- Architecture du projet (arbre + explication 1 ligne par dossier)
- Section "Connecter Power BI" avec les étapes (Get Data → Web → coller URL)
- Section "Endpoints disponibles" (tableau des endpoints avec exemples d'URL)
- Lien vers la newsletter DataGyver
- Licence MIT

### `pyproject.toml`

- `name = "fastapi-data-analyst"`
- `version = "1.0.0"`
- `description = "Démo API pour data analysts - Newsletter DataGyver #11"`
- `requires-python = ">=3.12"`
- Dependencies : fastapi[standard], polars, pydantic, streamlit, requests, plotly
- Dev dependencies : pytest, httpx

## Contraintes importantes

1. **Tout doit fonctionner avec `uv`** : pas de `pip install`, pas de `requirements.txt`
2. **Pas de commentaires évidents** : ne pas commenter `# importer polars` au-dessus de `import polars`. Les commentaires doivent apporter de la valeur (le "pourquoi", pas le "quoi")
3. **Code idiomatique Polars** : utiliser les expressions Polars, pas de `.apply()`, pas de boucles Python sur les données
4. **Pydantic v2** : utiliser `model_config = ConfigDict(...)` pas `class Config`, utiliser `model_dump()` pas `.dict()`
5. **Le dashboard Streamlit ne doit JAMAIS lire le Parquet directement** : il consomme exclusivement l'API
6. **Gestion d'erreurs propre** : l'API retourne des réponses cohérentes même avec des paramètres invalides, le dashboard affiche un message clair si l'API est down
7. **Le code doit être prêt à être montré** : c'est du code pédagogique destiné à des analystes juniors, il doit être lisible et exemplaire
8. **Formater avec Ruff** avant de finaliser

## Comment exécuter

Après génération, vérifie que tout fonctionne :

```bash
# 1. Setup
uv sync

# 2. Générer les données
uv run python data/generate_data.py

# 3. Lancer l'API (terminal 1)
uv run fastapi dev src/api/main.py

# 4. Lancer le dashboard (terminal 2)
uv run streamlit run src/dashboard/app.py

# 5. Tests
uv run pytest tests/ -v
```

Vérifie que :
- `http://localhost:8000/docs` affiche la doc Swagger
- `http://localhost:8000/api/v1/ventes/par-region` retourne du JSON valide
- Le dashboard Streamlit affiche les KPIs et graphiques
- Tous les tests passent
