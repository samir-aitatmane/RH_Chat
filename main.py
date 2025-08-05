import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from groq import Groq
from dotenv import load_dotenv
import os
import re

# Chargement de la clé API Groq
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Connexion à la base SQLite
conn = sqlite3.connect('recrutement.db')

# Liste exacte des noms de KPI
KPI_LIST = [
    "Nb de candidats contactés",
    "Nb d'entretiens candidats Salariés",
    "Nb d'entretiens candidats Sous-Traitants",
    "Nb de candidats recrutés Salariés",
    "Nb de candidats intégrés Sous Traitants",
    "Nombre de présentations clients",
    "Nb de refus CDI Salariés",
    "Nombre de KO candidat à la suite d'une présentation client",
    "Nombre de KO client à la suite d'une présentation client"
]

def clean_sql_query(sql_query):
    """Nettoie la requête SQL en supprimant les backticks et les marqueurs de code"""
    cleaned = re.sub(r'```sql|```', '', sql_query, flags=re.IGNORECASE)
    cleaned = cleaned.replace('`', '')
    return cleaned.strip()

def get_table_schema():
    """Récupère le schéma de la table kpi_recrutement"""
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(kpi_recrutement)")
    schema = cursor.fetchall()
    return "\n".join([f"- {col[1]} ({col[2]})" for col in schema])

def execute_sql_query(query):
    """Exécute une requête SQL et retourne un DataFrame"""
    try:
        print(f"Requête nettoyée:\n{query}")
        return pd.read_sql_query(query, conn)
    except Exception as e:
        print(f"Erreur SQL: {e}")
        return pd.DataFrame()

def groq_to_sql(natural_language_query):
    """Convertit une question en langage naturel en requête SQL avec Groq"""
    kpi_examples = "\n".join([f"- '{kpi}'" for kpi in KPI_LIST])
    
    system_prompt = f"""
    Tu es un expert SQLite spécialisé en RH. Voici le schéma de la table 'kpi_recrutement':
    {get_table_schema()}
    
    Règles importantes :
    1. Les noms des KPI doivent être exactement comme dans cette liste (respecter la casse et les accents) :
    {kpi_examples}
    2. Les mois en français : 'juillet', 'août', 'septembre'
    3. Les recruteurs : 'Inès', 'Marienne', 'Pauline', 'Samya'
    4. Utilise toujours des alias explicites pour les colonnes
    5. Pour les calculs mensuels, regrouper par 'rh_nom' et 'mois'
    6. Ne renvoie QUE du code SQL, sans commentaires ni explications
    """
    
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": natural_language_query}
        ],
        temperature=0.1,
        max_tokens=500
    )
    raw_sql = response.choices[0].message.content.strip()
    return clean_sql_query(raw_sql)

def extract_kpi_name(query):
    """Extrait le nom du KPI de la question de l'utilisateur"""
    for kpi in KPI_LIST:
        if kpi.lower() in query.lower():
            return kpi
    return "Indicateur RH"

def visualize_trends(df, kpi_name):
    """Génère un graphique d'évolution mensuelle par recruteur"""
    if df.empty or 'rh_nom' not in df.columns or 'mois' not in df.columns or 'valeur' not in df.columns:
        return None
        
    try:
        # Préparer les données pour le graphique
        pivot_df = df.pivot_table(index='mois', columns='rh_nom', values='valeur', aggfunc='sum').fillna(0)
        
        # Ordonner les mois chronologiquement
        mois_order = ['juillet', 'août', 'septembre']
        pivot_df = pivot_df.reindex(mois_order)
        
        # Créer le graphique
        plt.figure(figsize=(12, 6))
        pivot_df.plot(kind='bar', width=0.8)
        
        # Personnalisation
        plt.title(f"Évolution du {kpi_name} par Mois (T3 2024)")
        plt.xlabel("Mois")
        plt.ylabel("Valeur")
        plt.xticks(rotation=0)
        plt.legend(title="Recruteur")
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        # Sauvegarder et afficher
        filename = f"evolution_{kpi_name.replace(' ', '_').replace('/', '_')}.png"
        plt.savefig(filename)
        plt.close()
        return filename
    except Exception as e:
        print(f"Erreur de visualisation: {e}")
        return None

# Interface principale
print("🤖 Assistant RH - Analyse du 3ème Trimestre 2024")
print("Exemples de questions :")
print("- Quel est le total des 'Nb de candidats contactés' par Inès en septembre ?")
print("- Compare les 'Nb d'entretiens candidats Salariés' de Marienne et Samya sur le trimestre")
print("- Qui a le plus de 'Nb de candidats recrutés Salariés' en août ?")
print("- Affiche l'évolution des 'Nb de candidats contactés' par mois pour chaque recruteur")
print("- Quitter avec 'exit'")

while True:
    try:
        user_input = input("\nQuestion : ")
        if user_input.lower() in ['exit', 'quit']:
            break

        # Génération de la requête SQL
        sql_query = groq_to_sql(user_input)
        print(f"\nRequête générée :\n{sql_query}")
        
        # Exécution de la requête
        result_df = execute_sql_query(sql_query)
        
        # Vérification et affichage des résultats
        if not result_df.empty:
            print("\n🔍 Résultats :")
            print(result_df.to_markdown(index=False))
            
            # Détection automatique des besoins de visualisation
            if "évolution" in user_input.lower() or "graphique" in user_input.lower():
                kpi_name = extract_kpi_name(user_input)
                chart_file = visualize_trends(result_df, kpi_name)
                if chart_file:
                    print(f"\n📈 Graphique généré : {chart_file}")
                    try:
                        # Afficher le graphique dans une nouvelle fenêtre
                        img = plt.imread(chart_file)
                        plt.imshow(img)
                        plt.axis('off')
                        plt.show()
                    except:
                        print("(Le graphique a été sauvegardé sur le disque)")
        else:
            print("\nAucun résultat trouvé.")
            
    except Exception as e:
        print(f"\n❌ Erreur : {str(e)}")

conn.close()