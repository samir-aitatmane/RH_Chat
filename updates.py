import sqlite3

# Connexion à la base de données
conn = sqlite3.connect("recrutement.db")
cursor = conn.cursor()

# Requête de mise à jour
cursor.execute("""
    UPDATE kpi_recrutement
    SET rh_nom = 'Marieme'
    WHERE rh_nom = 'Merienne'
""")

# Valider et fermer
conn.commit()
conn.close()

print("Nom du recruteur mis à jour avec succès.")
