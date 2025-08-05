import sqlite3

# Création de la base de données
conn = sqlite3.connect("recrutement.db")
cur = conn.cursor()

# Création de la table avec la nouvelle colonne "periode_recrutement"
cur.execute("DROP TABLE IF EXISTS kpi_recrutement")
cur.execute("""
    CREATE TABLE kpi_recrutement (
        rh_nom TEXT,
        mois TEXT,
        kpi_nom TEXT,
        valeur INTEGER,
        commentaire TEXT,
        periode_recrutement TEXT
    )
""")

# Données des recruteurs
donnees = []

# Périodes de recrutement
periodes = {
    "Inès": "Q1/2023",
    "Mariéme": "Q2/2024",
    "Pauline": "Q1/2023",
    "Samya": "Q1/2023"
}

# Données pour Inès
ines_data = [
    ("Nb de candidats contactés", 92, 78, 66, ""),
    ("Nb d'entretiens candidats Salariés", 4, 1, 6, ""),
    ("Nb d'entretiens candidats Sous-Traitants", 23, 5, 11, ""),
    ("Nb de candidats recrutés Salariés", 0, 0, 0, ""),
    ("Nb de candidats intégrés Sous Traitants", 1, 0, 0, ""),
    ("Nombre de présentations clients", 1, 0, 0, ""),
    ("Nb de refus CDI Salariés", 0, 0, 0, ""),
    ("Nombre de KO candidat à la suite d'une présentation client", 0, 0, 0, ""),
    ("Nombre de KO client à la suite d'une présentation client", 0, 0, 0, "")
]

for kpi, j, a, s, com in ines_data:
    donnees.append(("Inès", "Juillet", kpi, j, com, periodes["Inès"]))
    donnees.append(("Inès", "Août", kpi, a, com, periodes["Inès"]))
    donnees.append(("Inès", "Septembre", kpi, s, com, periodes["Inès"]))

# Données pour Mariéme
mariéme_data = [
    ("Nb de candidats contactés", 109, 35, 50, ""),
    ("Nb d'entretiens candidats Salariés", 4, 0, 1, ""),
    ("Nb d'entretiens candidats Sous-Traitants", 15, 4, 6, ""),
    ("Nb de candidats recrutés Salariés", 0, 0, 0, ""),
    ("Nb de candidats intégrés Sous Traitants", 0, 0, 0, ""),
    ("Nombre de présentations clients", 1, 0, 0, ""),
    ("Nb de refus CDI Salariés", 0, 0, 0, ""),
    ("Nombre de KO candidat à la suite d'une présentation client", 0, 0, 0, ""),
    ("Nombre de KO client à la suite d'une présentation client", 1, 0, 0, "KO client")
]

for kpi, j, a, s, com in mariéme_data:
    donnees.append(("Mariéme", "Juillet", kpi, j, com, periodes["Mariéme"]))
    donnees.append(("Mariéme", "Août", kpi, a, com, periodes["Mariéme"]))
    donnees.append(("Mariéme", "Septembre", kpi, s, com, periodes["Mariéme"]))

# Données pour Pauline
pauline_data = [
    ("Nb de candidats contactés", 116, 55, 28, ""),
    ("Nb d'entretiens candidats Salariés", 2, 1, 1, ""),
    ("Nb d'entretiens candidats Sous-Traitants", 13, 18, 5, ""),
    ("Nb de candidats recrutés Salariés", 0, 0, 1, "Sarra KIBROUMA- IED Java Fullstack chez Finaxio"),
    ("Nb de candidats intégrés Sous Traitants", 0, 1, 0, "Oussimi EL ROBERTO - IED Java Fullstack à la STAME"),
    ("Nombre de présentations clients", 0, 2, 3, ""),
    ("Nb de refus CDI Salariés", 0, 0, 0, ""),
    ("Nombre de KO candidat à la suite d'une présentation client", 0, 1, 0, "KO candidat Gyz TABLEAU - on avait le GO chez Finaxy, nous a plantés au dernier moment"),
    ("Nombre de KO client à la suite d'une présentation client", 0, 0, 1, "KO client")
]

for kpi, j, a, s, com in pauline_data:
    donnees.append(("Pauline", "Juillet", kpi, j, com, periodes["Pauline"]))
    donnees.append(("Pauline", "Août", kpi, a, com, periodes["Pauline"]))
    donnees.append(("Pauline", "Septembre", kpi, s, com, periodes["Pauline"]))

# Données pour Samya (correction du mois "Juilet" en "Juillet")
samya_data = [
    ("Nb de candidats contactés", 110, 36, 34, ""),
    ("Nb d'entretiens candidats Salariés", 3, 2, 2, ""),
    ("Nb d'entretiens candidats Sous-Traitants", 16, 10, 9, ""),
    ("Nb de candidats recrutés Salariés", 0, 0, 0, ""),
    ("Nb de candidats intégrés Sous Traitants", 0, 0, 0, ""),
    ("Nombre de présentations clients", 0, 0, 1, "Olivier BATEAUX chez CEPB"),
    ("Nb de refus CDI Salariés", 0, 0, 0, ""),
    ("Nombre de KO candidat à la suite d'une présentation client", 0, 0, 0, ""),
    ("Nombre de KO client à la suite d'une présentation client", 0, 0, 0, "")
]

for kpi, j, a, s, com in samya_data:
    donnees.append(("Samya", "Juillet", kpi, j, com, periodes["Samya"]))
    donnees.append(("Samya", "Août", kpi, a, com, periodes["Samya"]))
    donnees.append(("Samya", "Septembre", kpi, s, com, periodes["Samya"]))

# Insertion des données
cur.executemany("""
    INSERT INTO kpi_recrutement (rh_nom, mois, kpi_nom, valeur, commentaire, periode_recrutement)
    VALUES (?, ?, ?, ?, ?, ?)
""", donnees)

conn.commit()

# Vérification
print("✅ Base de données créée avec succès")
print(f"Total d'enregistrements insérés: {len(donnees)}")

print("\nRécapitulatif par recruteur:")
for rh in ["Inès", "Marienne", "Pauline", "Samya"]:
    cur.execute("SELECT COUNT(*) FROM kpi_recrutement WHERE rh_nom = ?", (rh,))
    count = cur.fetchone()[0]
    periode = periodes[rh]
    print(f"- {rh}: {count} indicateurs (Période: {periode})")

print("\nExemple de données pour Pauline en Septembre:")
cur.execute("""
    SELECT kpi_nom, valeur, commentaire 
    FROM kpi_recrutement 
    WHERE rh_nom = 'Pauline' AND mois = 'Septembre'
""")
for row in cur.fetchall():
    print(f"- {row[0]}: {row[1]} ({row[2]})")

conn.close()