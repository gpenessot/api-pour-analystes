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
