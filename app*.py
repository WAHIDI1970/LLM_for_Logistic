import streamlit as st
import pandas as pd
import numpy as np
import base64
import os
from langchain_groq import ChatGroq
import streamlit.components.v1 as components

# --- 1. CONFIGURATION & ASSETS ---
logo_path = "assets/image.png"
bg_path = "assets/logo.jpg"
st.set_page_config(page_title="SG ATS - ORM Risk Auditor", layout="wide")

# --- 2. STYLE CSS AVANCÉ & JAVASCRIPT ---
accent = "#d31b1b"  # Rouge SG
bg_dark = "#0a0a0a"

st.markdown(f"""
<style>
    :root {{ --accent: {accent}; }}
    html, body, .stApp {{ background-color: {bg_dark}; color: white; }}
    
    /* Effet Glassmorphism pour les cartes */
    .stMetric, .stDataFrame, div[data-testid="stChatMessage"] {{
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        transition: all 0.3s ease;
    }}
    
    /* Animation au survol via CSS */
    .stMetric:hover {{
        transform: translateY(-5px);
        border-color: {accent} !important;
        box-shadow: 0 10px 20px rgba(211, 27, 27, 0.2);
    }}

    /* Boutons stylisés */
    .stButton>button {{
        background: {accent} !important;
        border: none !important;
        font-weight: bold !important;
        transition: transform 0.2s !important;
    }}
    .stButton>button:active {{ transform: scale(0.95); }}

    /* Sidebar Gradient */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #050505 0%, #111111 100%) !important;
        border-right: 1px solid {accent};
    }}
</style>

<script>
    // Petit script JS pour feedback console et animation légère
    const buttons = window.parent.document.querySelectorAll('button');
    buttons.forEach(btn => {{
        btn.addEventListener('mouseover', () => {{
            btn.style.filter = 'brightness(1.2)';
        }});
        btn.addEventListener('mouseleave', () => {{
            btn.style.filter = 'brightness(1.0)';
        }});
    }});
</script>
""", unsafe_allow_html=True)

# --- 3. LOGIQUE MÉTIER ---
def present_risk_database(df):
    return {
        "nb_lignes": df.shape[0],
        "nb_colonnes": df.shape[1],
        "taux_completude": round((1 - df.isna().sum().sum() / df.size) * 100, 2),
        "missing_by_col": df.isna().sum()
    }

def check_risk_semantic_integrity(df, column_name):
    unique_values = df[column_name].dropna().unique()
    cleaned = [str(v).strip().upper().replace(".", "").replace("-", " ") for v in unique_values]
    conflicts = []
    seen = {}
    for original, clean in zip(unique_values, cleaned):
        if clean in seen:
            conflicts.append({"original": original, "doublon_probable": seen[clean]})
        seen[clean] = original
    return conflicts

# --- 4. GESTION DU BACKGROUND ---
if os.path.exists(bg_path):
    with open(bg_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{b64}");
            background-size: cover;
            background-attachment: fixed;
        }}
        .stApp::before {{
            content: ""; position: fixed; inset: 0;
            background: rgba(0, 0, 0, 0.85); z-index: -1;
        }}
        </style>
        """, unsafe_allow_html=True)

# --- 5. SIDEBAR & NAVIGATION ---
if "messages" not in st.session_state: st.session_state.messages = []

with st.sidebar:
    if os.path.exists(logo_path): st.image(logo_path, width=180)
    st.title("🛡️ Risk Audit Panel")
    api_key = st.text_input("🔑 Groq API Key", type="password")
    uploaded_file = st.file_uploader("📂 Charger KRI Data", type="csv")
    
    if uploaded_file:
        st.session_state.df = pd.read_csv(uploaded_file)
        st.success("✅ Données prêtes")
        
        st.markdown("---")
        st.subheader("🛠️ Outils Quick Audit")
        db_info = present_risk_database(st.session_state.df)
        cols = list(st.session_state.df.columns)
        target_col = st.selectbox("Sélectionner Colonne", cols)
        if st.button("Lancer l'Audit Sémantique"):
            st.session_state.audit_res = check_risk_semantic_integrity(st.session_state.df, target_col)
            st.session_state.target = target_col

# --- 6. INTERFACE DASHBOARD ---
st.markdown(f"<h1 style='color:white; margin-bottom:0;'>SG ATS — Département ORM</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='color:{accent}; font-weight:bold;'>Dashboard d'Intégrité des Risques Opérationnels</p>", unsafe_allow_html=True)

if st.session_state.get('df') is not None:
    df = st.session_state.df
    info = present_risk_database(df)
    
    # KPIs en haut
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total KRIs", info['nb_lignes'])
    k2.metric("Dimensions", info['nb_colonnes'])
    k3.metric("Qualité Data", f"{info['taux_completude']}%")
    k4.metric("Alertes Sémantiques", len(st.session_state.get('audit_res', [])))

    st.markdown("---")
    
    left, right = st.columns([1.8, 1.2])
    
    with left:
        tab1, tab2 = st.tabs(["📊 Visualisation Qualité", "🔍 Résultats d'Audit"])
        
        with tab1:
            st.subheader("Analyse des Manquants par Colonne")
            missing_df = info['missing_by_col'][info['missing_by_col'] > 0]
            if not missing_df.empty:
                st.bar_chart(missing_df)
            else:
                st.success("Félicitations : Aucune valeur manquante détectée.")
                
            st.subheader("Aperçu des Données Critiques")
            st.dataframe(df.head(10), use_container_width=True)
            
        with tab2:
            if "audit_res" in st.session_state:
                st.write(f"Analyse de la colonne : **{st.session_state.target}**")
                if st.session_state.audit_res:
                    for c in st.session_state.audit_res:
                        st.warning(f"🚩 Conflit détecté : `{c['original']}` pourrait être `{c['doublon_probable']}`")
                else:
                    st.success("Aucun conflit sémantique trouvé sur cette dimension.")
            else:
                st.info("Utilisez la barre latérale pour lancer un audit sémantique.")

    with right:
        st.subheader("💬 Assistant IA ORM")
        
        # Zone de Chat
        chat_container = st.container()
        with chat_container:
            for m in st.session_state.messages:
                with st.chat_message(m["role"]): st.write(m["content"])

        if prompt := st.chat_input("Posez une question sur l'exposition au risque..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.write(prompt)
            
            if api_key:
                try:
                    llm = ChatGroq(groq_api_key=api_key, model_name="llama-3.3-70b-versatile")
                    context = f"Colonnes: {list(df.columns)}. Aperçu: {df.head(3).to_json()}"
                    full_prompt = f"Tu es l'expert Risque de SG ATS. Contexte: {context}. Réponds à: {prompt}"
                    response = llm.invoke(full_prompt).content
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur API: {e}")
            else:
                st.warning("Clé API requise.")

else:
    st.info("👋 Bienvenue. Veuillez charger un fichier KRI pour activer le dashboard d'audit.")

# --- FOOTER ---
st.markdown(f"<br><hr><center><p style='color:#fff;'>SG ATS - Internal Use Only - 2026</p></center>", unsafe_allow_html=True)
