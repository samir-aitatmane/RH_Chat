import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os
import re
from dotenv import load_dotenv
from groq import Groq

# --- Configurations ---
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=API_KEY)

conn = sqlite3.connect('recrutement.db', check_same_thread=False)

KPI_LIST = [
    "Nb de candidats contactés",
    "Nb entretiens candidats Salariés",
    "Nb entretiens candidats Sous-Traitants",
    "Nb de candidats recrutés Salariés",
    "Nb de candidats intégrés Sous Traitants",
    "Nombre de présentations clients",
    "Nb de refus CDI Salariés",
    "Nombre de KO candidat à la suite d'une présentation client",
    "Nombre de KO client à la suite d'une présentation client"
]

# --- Fonctions ---

def get_schema():
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(kpi_recrutement)")
    schema = cursor.fetchall()
    return "\n".join([f"- {col[1]} ({col[2]})" for col in schema])

def ask_llm(user_input):
    system_prompt = f"""
Tu es un assistant RH intelligent. Tu as accès à une base de données SQLite avec la table `kpi_recrutement`.
Voici son schéma :
{get_schema()}

Liste des KPI disponibles :
{', '.join(KPI_LIST)}

Si la question de l'utilisateur est une salutation, une question générale ou un remerciement, réponds simplement de manière naturelle sans SQL.

Si c’est une question demandant une analyse de données RH, génère une réponse claire en langage naturel **et** ajoute à la fin une requête SQL encadrée par ```sql et ``` (pour qu'on puisse l'exécuter).

Réponds toujours en français.
Si tu ne connais pas la réponse, ne génère pas de réponses aléatoires ou fausses.
"""

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        temperature=0.5,
        max_tokens=800
    )
    return response.choices[0].message.content.strip()

def extract_sql(response_text):
    if "```sql" in response_text:
        start = response_text.find("```sql") + 6
        end = response_text.find("```", start)
        return response_text[start:end].strip()
    return None

def escape_apostrophes_in_sql(sql: str) -> str:
    # Double les apostrophes à l’intérieur des chaînes SQL pour éviter les erreurs
    def replacer(match):
        content = match.group(1)
        escaped = content.replace("'", "''")
        return f"'{escaped}'"
    
    pattern = r"'([^']*)'"
    return re.sub(pattern, replacer, sql)

def execute_sql(sql):
    try:
        sql = escape_apostrophes_in_sql(sql)
        return pd.read_sql_query(sql, conn)
    except Exception as e:
        st.error(f"Erreur SQL : {e}")
        return pd.DataFrame()

def visualize(df, kpi_name):
    if df.empty or not all(c in df.columns for c in ['mois', 'rh_nom', 'valeur']):
        return None
    pivot = df.pivot_table(index='mois', columns='rh_nom', values='valeur', aggfunc='sum').fillna(0)
    fig, ax = plt.subplots(figsize=(10, 5))
    pivot.plot(kind='line', ax=ax, marker='o')
    ax.set_title(f"Évolution de {kpi_name} par recruteur")
    ax.set_xlabel("Mois")
    ax.set_ylabel("Valeur")
    plt.xticks(rotation=45)
    return fig


st.title("🤖 Assistant RH intelligent")

question = st.text_input("Pose ta question RH :", "")

if st.button("Envoyer"):
    if question.strip() == "":
        st.warning("Merci d'entrer une question avant d'envoyer.")
    else:
        with st.spinner("Réflexion en cours..."):
            llm_response = ask_llm(question)

        st.markdown("### 🤖 Réponse de l'assistant :")
        st.markdown(llm_response)

        sql_query = extract_sql(llm_response)

        if sql_query:
            st.markdown("### 🧠 Requête SQL générée :")
            st.code(sql_query, language="sql")

            df = execute_sql(sql_query)
            if not df.empty:
                st.markdown("### Résultats :")
                st.dataframe(df)

                for kpi in KPI_LIST:
                    if kpi.lower() in question.lower():
                        fig = visualize(df, kpi)
                        if fig:
                            st.pyplot(fig)
                        break
