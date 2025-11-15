import streamlit as st
import math
from datetime import datetime
import base64

st.set_page_config(page_title="EC2 Sprickkontroll", layout="wide")

# === DATA ===
F_CTM = {"C12/15": 1.6, "C16/20": 1.9, "C20/25": 2.2, "C25/30": 2.6, "C30/37": 2.9, "C35/45": 3.2, "C40/50": 3.5, "C45/55": 3.8, "C50/60": 4.1}
ARMERING = {8: 50.3, 10: 78.5, 12: 113.1, 16: 201.1, 20: 314.2, 25: 490.9, 28: 615.8, 32: 804.2}

# === FUNKTIONER ===
def minimiarmering(betongklass, f_yk, b_t, d):
    f_ctm = F_CTM[betongklass]
    term1 = 0.26 * (f_ctm / f_yk) * b_t * d
    term2 = 0.0013 * b_t * d
    return max(term1, term2)

def sprickbredd(betongklass, f_yk, M, b, h, d, A_s, phi, c, lasttyp, w_grans):
    f_ctm = F_CTM[betongklass]
    M = M * 1e6
    sigma_s = min((M / (A_s * 0.9 * d)) * 1.15, f_yk)
    Ac_eff = b * min(2.5*(h-d), h/2)
    rho_p_ef = min(A_s / Ac_eff, 0.05)
    k1, k2, k3, k4 = 0.8, 0.5 if lasttyp == "böjning" else 1.0, 3.4, 0.425
    s_r_max = k3 * c + k1 * k2 * k4 * phi / rho_p_ef
    kt = 0.4
    delta = sigma_s - kt * (f_ctm / rho_p_ef) * (1 + 35 * rho_p_ef)
    Es = 200000
    epsilon = delta / Es if delta > 0 else 0
    w_k = s_r_max * epsilon
    A_s_min = minimiarmering(betongklass, f_yk, b, d)
    return {"w_k": w_k, "sigma_s": sigma_s, "s_r_max": s_r_max, "epsilon": epsilon, "A_s_min": A_s_min, "ok": w_k <= w_grans and A_s >= A_s_min}

# === PDF GENERATOR ===
def generate_pdf(data):
    html = f"""
    <html>
    <head><meta charset="utf-8"><title>EC2 Sprickkontroll</title></head>
    <body style="font-family: Arial; margin: 40px;">
    <h1>EC2 Sprickkontroll – Rapport</h1>
    <p><strong>Datum:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    <hr>
    <h2>Indata</h2>
    <ul>
        <li>Betongklass: {data['betongklass']}</li>
        <li>Moment M: {data['M']} kNm</li>
        <li>Bredd b: {data['b']} mm | Höjd h: {data['h']} mm | d: {data['d']} mm</li>
        <li>Armering: {data['antal']} st Ø{data['phi']} → {data['A_s']:.0f} mm²</li>
        <li>Täckskikt c: {data['c']} mm</li>
        <li>Lasttyp: {data['lasttyp']}</li>
        <li>Gräns w_k: {data['w_grans']} mm</li>
    </ul>
    <h2>Resultat</h2>
    <ul>
        <li><strong>Sprickbredd w_k:</strong> {data['w_k']:.3f} mm → <span style="color: {'green' if data['ok'] else 'red'};">{'OK' if data['ok'] else 'EJ OK'}</span></li>
        <li><strong>Minimiarm A_s,min:</strong> {data['A_s_min']:.0f} mm² → {data['A_s']:.0f} mm² {'OK' if data['A_s'] >= data['A_s_min'] else 'För lite'}</li>
    </ul>
    <hr>
    <p><small>Genererad med EC2 Sprickkontroll v2.0 | Byggd av kransengangster1000</small></p>
    </body>
    </html>
    """
    return html

# === APP ===
st.title("EC2 Sprickkontroll & Minimiarm")
st.markdown("**Eurocode 2 – 7.3.3 & 7.3.4** | Uppdaterad 2025")

col1, col2 = st.columns(2)
with col1:
    betongklass = st.selectbox("Betongklass", list(F_CTM.keys()), index=4)
    f_yk = st.selectbox("Armering f_yk [MPa]", [400, 500, 550], index=1)
    lasttyp = st.radio("Lasttyp", ["böjning", "drag"])
with col2:
    M = st.number_input("Moment M [kNm]", 0.0, 1000.0, 120.0)
    w_grans = st.selectbox("Gräns w_k [mm]", [0.2, 0.3, 0.4], index=1)

col1, col2, col3 = st.columns(3)
with col1: b = st.number_input("Bredd b [mm]", 100, 1000, 300)
with col2: h = st.number_input("Höjd h [mm]", 100, 2000, 500)
with col3: d = st.number_input("Användbar höjd d [mm]", 50, 2000, 460)

col1, col2 = st.columns(2)
with col1:
    phi = st.selectbox("Diameter Ø [mm]", list(ARMERING.keys()), index=3)
    antal = st.slider("Antal stänger", 1, 12, 4)
    A_s = antal * ARMERING[phi]
with col2:
    c = st.number_input("Täckskikt c [mm]", 15, 100, 35)
    st.metric("Armeringsarea A_s", f"{A_s:.0f} mm²")

if st.button("Beräkna!", type="primary"):
    resultat = sprickbredd(betongklass, f_yk, M, b, h, d, A_s, phi, c, lasttyp, w_grans)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Sprickbredd w_k", f"{resultat['w_k']:.3f} mm")
        color = "🟢" if resultat['ok'] else "🔴"
        st.markdown(f"**Status:** {color} {'OK' if resultat['ok'] else 'EJ OK'}")
    with col2:
        st.metric("Minimiarm A_s,min", f"{resultat['A_s_min']:.0f} mm²")
        st.write(f"A_s: {A_s:.0f} mm² → {'OK' if A_s >= resultat['A_s_min'] else 'För lite'}")
    
    with st.expander("Detaljer"):
        st.write(f"σ_s ≈ {resultat['sigma_s']:.0f} MPa")
        st.write(f"s_r,max ≈ {resultat['s_r_max']:.1f} mm")
        st.write(f"ε ≈ {resultat['epsilon']:.6f}")

    # === PDF EXPORT ===
    data = {
        "betongklass": betongklass, "M": M, "b": b, "h": h, "d": d,
        "phi": phi, "antal": antal, "A_s": A_s, "c": c, "lasttyp": lasttyp,
        "w_grans": w_grans, "w_k": resultat['w_k'], "A_s_min": resultat['A_s_min'],
        "ok": resultat['ok']
    }
    pdf_html = generate_pdf(data)
    st.download_button(
        label="Ladda ner PDF-rapport",
        data=pdf_html,
        file_name=f"EC2_rapport_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
        mime="text/html"
    )
    st.balloons()

st.caption("Byggd av kransengangster1000 | Uppdaterad 2025")
