import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import re
import os
from dotenv import load_dotenv
from groq import Groq  # Assure-toi que ce package est installé

# --- Initialisation ---
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=API_KEY)
conn = sqlite3.connect('recrutement.db', check_same_thread=False)

# Liste des KPI disponibles dans la base
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
    """Nettoie le SQL généré pour éviter les backticks ou balises markdown"""
    cleaned = re.sub(r'```sql|```', '', sql_query, flags=re.IGNORECASE)
    cleaned = cleaned.replace('`', '')
    return cleaned.strip()

def get_table_schema():
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(kpi_recrutement)")
    schema = cursor.fetchall()
    return "\n".join([f"- {col[1]} ({col[2]})" for col in schema])

def groq_to_sql(natural_language_query):
    """Appelle Groq pour générer une requête SQL à partir d’une question en langage naturel"""
    prompt = f"""
    Tu es un expert SQL SQLite spécialisé en ressources humaines. Voici le schéma de la table kpi_recrutement :
    {get_table_schema()}

    Liste des KPI disponibles (à utiliser strictement comme noms de colonnes) :
    {', '.join(KPI_LIST)}

    Règles importantes :
    - Toujours renvoyer du SQL valide SQLite sans commentaires ni texte,
    - Toujours sélectionner 'rh_nom', 'mois' et 'valeur' pour les analyses,
    - Regrouper les résultats par 'rh_nom' et 'mois' si nécessaire,
    - Ne pas utiliser de commandes dangereuses (DROP, DELETE, UPDATE, INSERT).

    Question utilisateur : {natural_language_query}
    """

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": natural_language_query}
        ],
        temperature=0.1,
        max_tokens=512
    )

    raw_sql = response.choices[0].message.content.strip()
    return clean_sql_query(raw_sql)

def execute_sql_query(query):
    try:
        return pd.read_sql_query(query, conn)
    except Exception as e:
        st.error(f"Erreur SQL : {e}")
        return pd.DataFrame()

def visualize_trends(df, kpi_name):
    if df.empty or 'mois' not in df.columns or 'rh_nom' not in df.columns or 'valeur' not in df.columns or 'kpi_nom' not in df.columns:
        st.warning("Les colonnes nécessaires pour le graphique ne sont pas présentes.")
        return None
    try:
        st.write("Valeurs de mois dans le DataFrame:", df['mois'].unique())
        pivot = df.pivot_table(index='mois', columns='rh_nom', values='valeur', aggfunc='sum').fillna(0)
        
        # Adapter l'ordre si possible selon les mois présents
        order = list(df['mois'].unique())
        pivot = pivot.reindex(order)

        fig, ax = plt.subplots(figsize=(10, 5))
        pivot.plot(kind='line', marker='o', ax=ax)
        ax.set_title(f"Évolution de {kpi_name} par recruteur")
        ax.set_xlabel("Mois")
        ax.set_ylabel("Valeur")
        ax.grid(True)
        plt.xticks(rotation=0)
        return fig
    except Exception as e:
        st.error(f"Erreur visualisation : {e}")
        return None


def main():
    st.title("🤖 Agent conversationnel RH - Reporting KPI")

    user_question = st.text_input("Pose ta question sur les KPIs RH", "")

    if user_question:
        with st.spinner("Génération de la requête SQL..."):
            sql_query = groq_to_sql(user_question)
        st.code(sql_query, language="sql")

        df = execute_sql_query(sql_query)

        if df.empty:
            st.warning("Aucun résultat trouvé. Essaie une autre question.")
            return

        st.dataframe(df)

        # Essayer de deviner le KPI à partir de la question
        kpi_guess = next((kpi for kpi in KPI_LIST if kpi.lower() in user_question.lower()), "Indicateur RH")

        fig = visualize_trends(df, kpi_guess)
        if fig:
            st.pyplot(fig)

        # Analyse simple
        if 'mois' in df.columns and 'rh_nom' in df.columns and 'valeur' in df.columns:
            grouped = df.groupby(['mois', 'rh_nom'])['valeur'].sum().reset_index()
            mois_max = grouped.groupby('mois')['valeur'].sum().idxmax()
            mois_min = grouped.groupby('mois')['valeur'].sum().idxmin()
            st.markdown(f"Le mois le plus actif pour **{kpi_guess}** est **{mois_max}** ; le moins actif est **{mois_min}**.")

            total_par_rh = grouped.groupby('rh_nom')['valeur'].sum()
            max_rh = total_par_rh.idxmax()
            min_rh = total_par_rh.idxmin()
            st.markdown(f"Le recruteur le plus performant est **{max_rh}** ; le moins performant est **{min_rh}**.")

if __name__ == "__main__":
    main()
