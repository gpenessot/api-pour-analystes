from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "dataset_rows" in data
    assert "dataset_columns" in data
    assert "derniere_date" in data
    assert data["dataset_rows"] > 0


def test_get_ventes_sans_filtre(client: TestClient) -> None:
    response = client.get("/api/v1/ventes")
    assert response.status_code == 200
    data = response.json()
    assert "resume" in data
    assert "data" in data
    resume = data["resume"]
    assert "total_ca" in resume
    assert "nb_transactions" in resume
    assert "panier_moyen" in resume
    assert "regions_disponibles" in resume
    assert len(data["data"]) <= 100


def test_get_ventes_filtre_region(client: TestClient) -> None:
    response = client.get("/api/v1/ventes", params={"region": "Nord", "annee": 2024})
    assert response.status_code == 200
    data = response.json()
    # Toutes les lignes retournées doivent être de la région Nord
    for vente in data["data"]:
        assert vente["region"] == "Nord"


def test_get_ventes_region_inexistante(client: TestClient) -> None:
    response = client.get("/api/v1/ventes", params={"region": "Atlantide"})
    assert response.status_code == 200
    data = response.json()
    assert data["resume"]["nb_transactions"] == 0
    assert data["data"] == []


def test_get_ventes_par_region(client: TestClient) -> None:
    response = client.get("/api/v1/ventes/par-region", params={"annee": 2024})
    assert response.status_code == 200
    data = response.json()
    regions = {r["region"] for r in data}
    expected = {"Nord", "Sud", "Est", "Ouest", "Île-de-France"}
    assert regions == expected
    # La somme des parts doit être ~100%
    total_pct = sum(r["part_ca_pct"] for r in data)
    assert abs(total_pct - 100.0) < 0.5


def test_get_ventes_par_categorie(client: TestClient) -> None:
    response = client.get("/api/v1/ventes/par-categorie", params={"annee": 2025})
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for item in data:
        assert "categorie" in item
        assert "ca_total" in item
        assert "nb_ventes" in item
        assert item["ca_total"] > 0


def test_get_top_clients(client: TestClient) -> None:
    top_n = 5
    response = client.get("/api/v1/ventes/top-clients", params={"top_n": top_n})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == top_n
    # Vérification de l'ordre décroissant
    cas = [c["ca_total"] for c in data]
    assert cas == sorted(cas, reverse=True)


def test_get_evolution(client: TestClient) -> None:
    response = client.get("/api/v1/ventes/evolution", params={"annee": 2024})
    assert response.status_code == 200
    data = response.json()
    # 2024 est une année complète dans le dataset — on attend 12 mois
    assert len(data) == 12
    mois = [e["mois"] for e in data]
    assert mois == sorted(mois)


def test_limit_parameter(client: TestClient) -> None:
    response = client.get("/api/v1/ventes", params={"limit": 10, "annee": 2024})
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) <= 10

    # Vérification que limit > 1000 est rejeté
    response_too_large = client.get("/api/v1/ventes", params={"limit": 9999})
    assert response_too_large.status_code == 422
