import streamlit as st
import math
from datetime import datetime

st.set_page_config(page_title="EC2 Sprickkontroll", layout="wide")

# === DATA ===
F_CTM = {"C12/15": 1.6, "C16/20": 1.9, "C20/25": 2.2, "C25/30": 2.6, "C30/37": 2.9, "C35/45": 3.2, "C40/50": 3.5, "C45/55": 3.8, "C50/60": 4.1}
ARMERING = {8: 50.3, 10: 78.5, 12: 113.1, 16: 201.1, 20: 314.2, 25: 490.9, 28: 615.8, 32: 804.2}

# === FUNKTIONER ===
def minimiarmering(betongklass, f_yk, b_t, d):
    f_ctm = F_CTM[betongklass]
    term1 = 0.26 * (f_ctm / f_yk) * b_t * d
    term2 = 0.0013 * b_t * d
    return max(term1, term2), term1, term2, f_ctm

def sprickbredd(betongklass, f_yk, M, b, h, d, A_s, phi, c, lasttyp, w_grans):
    f_ctm = F_CTM[betongklass]
    M_Nmm = M * 1e6  # kNm → Nmm

    # 1. Spänning i armering
    sigma_s = min((M_Nmm / (A_s * 0.9 * d)) * 1.15, f_yk)

    # 2. h_c,ef
    h_c_ef = min(2.5 * (h - d), h / 2)
    Ac_eff = b * h_c_ef
    rho_p_ef = min(A_s / Ac_eff, 0.05)

    # 3. s_r,max
    k1 = 0.8
    k2 = 0.5 if lasttyp == "böjning" else 1.0
    k3 = 3.4
    k4 = 0.425
    s_r_max = k3 * c + k1 * k2 * k4 * phi / rho_p_ef

    # 4. ε_sm - ε_cm
    kt = 0.4  # långtid
    f_ct_eff = f_ctm
    delta = sigma_s - kt * (f_ct_eff / rho_p_ef) * (1 + 35 * rho_p_ef)
    Es = 200000
    epsilon = max(delta / Es, 0)

    # 5. Sprickbredd
    w_k = s_r_max * epsilon

    # 6. Minimiarm
    A_s_min, term1, term2, f_ctm_used = minimiarmering(betongklass, f_yk, b, d)

    ok = w_k <= w_grans and A_s >= A_s_min

    # === STEG FÖR REDOVISNING ===
    steg = {
        "f_ctm": f_ctm_used,
        "sigma_s": sigma_s,
        "h_c_ef": h_c_ef,
        "Ac_eff": Ac_eff,
        "rho_p_ef": rho_p_ef,
        "s_r_max": s_r_max,
        "delta": delta,
        "epsilon": epsilon,
        "w_k": w_k,
        "A_s_min": A_s_min,
        "term1": term1,
        "term2": term2,
        "ok": ok
    }

    return {
        "w_k": w_k, "A_s_min": A_s_min, "sigma_s": sigma_s, "s_r_max": s_r_max,
        "epsilon": epsilon, "ok": ok, "steg": steg
    }

# === PDF GENERATOR ===
def generate_pdf(data, steg):
    html = f"""
    <html><head><meta charset="utf-8"><title>EC2 Sprickkontroll</title></head>
    <body style="font-family: Arial; margin: 40px;">
    <h1>EC2 Sprickkontroll – Rapport</h1>
    <p><strong>Datum:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    <hr>
    <h2>Indata</h2>
    <ul>
        <li>Betongklass: {data['betongklass']}</li>
        <li>Moment M: {data['M']} kNm</li>
        <li>Geometri: b = {data['b']} mm, h = {data['h']} mm, d = {data['d']} mm</li>
        <li>Armering: {data['antal']} st Ø{data['phi']} → {data['A_s']:.0f} mm²</li>
        <li>Täckskikt c: {data['c']} mm | Lasttyp: {data['lasttyp']}</li>
        <li>Gräns w_k: {data['w_grans']} mm</li>
    </ul>
    <h2>Resultat</h2>
    <ul>
        <li><strong>Sprickbredd w_k:</strong> {steg['w_k']:.3f} mm → <span style="color: {'green' if steg['ok'] else 'red'};">{'OK' if steg['ok'] else 'EJ OK'}</span></li>
        <li><strong>Minimiarm A_s,min:</strong> {steg['A_s_min']:.0f} mm² → {data['A_s']:.0f} mm² {'OK' if data['A_s'] >= steg['A_s_min'] else 'För lite'}</li>
    </ul>
    <h2>Beräkningssteg (EC2 7.3.3 & 7.3.4)</h2>
    <ol>
        <li><strong>f_ctm</strong> = {steg['f_ctm']:.1f} MPa (Tabell 7.1N)</li>
        <li><strong>σ_s</strong> ≈ {steg['sigma_s']:.0f} MPa (1.15 × M / (A_s × 0.9d))</li>
        <li><strong>h_c,ef</strong> = min(2.5×(h−d), h/2) = {steg['h_c_ef']:.0f} mm</li>
        <li><strong>A_c,eff</strong> = b × h_c,ef = {steg['Ac_eff']:.0f} mm²</li>
        <li><strong>ρ_p,ef</strong> = A_s / A_c,eff = {steg['rho_p_ef']:.4f}</li>
        <li><strong>s_r,max</strong> = 3.4c + 0.8×{0.5 if data['lasttyp']=='böjning' else 1.0}×0.425×Ø/ρ_p,ef = {steg['s_r_max']:.1f} mm</li>
        <li><strong>Δσ_s</strong> = σ_s − 0.4 × (f_ctm / ρ_p,ef) × (1 + 35ρ_p,ef) = {steg['delta']:.1f} MPa</li>
        <li><strong>ε_sm − ε_cm</strong> = Δσ_s / E_s = {steg['epsilon']:.6f}</li>
        <li><strong>w_k</strong> = s_r,max × (ε_sm − ε_cm) = {steg['w_k']:.3f} mm</li>
        <li><strong>A_s,min</strong> = max(0.26×f_ctm/f_yk×b×d, 0.0013×b×d) = max({steg['term1']:.0f}, {steg['term2']:.0f}) = {steg['A_s_min']:.0f} mm²</li>
    </ol>
    <hr>
    <p><small>EC2 Sprickkontroll v3.0 | Byggd av kransengangster1000</small></p>
    </body></html>
    """
    return html

# === APP ===
st.title("EC2 Sprickkontroll & Minimiarm")
st.markdown("**Eurocode 2 – 7.3.3 & 7.3.4** | Fullständig beräkning")

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
    steg = resultat["steg"]

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Sprickbredd w_k", f"{resultat['w_k']:.3f} mm")
        color = "success" if resultat['ok'] else "error"
        st.markdown(f"**Status:** :{color}[{'OK' if resultat['ok'] else 'EJ OK'}]")
    with col2:
        st.metric("Minimiarm A_s,min", f"{resultat['A_s_min']:.0f} mm²")
        st.write(f"A_s: {A_s:.0f} mm² → {'OK' if A_s >= resultat['A_s_min'] else 'För lite'}")

    # === BERÄKNINGSSTEG ===
    with st.expander("Visa beräkningssteg (EC2 7.3.3 & 7.3.4)", expanded=False):
        st.markdown(f"**1. f_ctm** = {steg['f_ctm']:.1f} MPa *(Tabell 7.1N)*")
        st.markdown(f"**2. σ_s** ≈ {steg['sigma_s']:.0f} MPa *(1.15 × M / (A_s × 0.9d))*")
        st.markdown(f"**3. h_c,ef** = min(2.5×(h−d), h/2) = {steg['h_c_ef']:.0f} mm")
        st.markdown(f"**4. A_c,eff** = b × h_c,ef = {steg['Ac_eff']:.0f} mm²")
        st.markdown(f"**5. ρ_p,ef** = A_s / A_c,eff = {steg['rho_p_ef']:.4f}")
        st.markdown(f"**6. s_r,max** = 3.4c + 0.8×{0.5 if lasttyp=='böjning' else 1.0}×0.425×Ø/ρ_p,ef = {steg['s_r_max']:.1f} mm")
        st.markdown(f"**7. Δσ_s** = σ_s − 0.4 × (f_ctm / ρ_p,ef) × (1 + 35ρ_p,ef) = {steg['delta']:.1f} MPa")
        st.markdown(f"**8. ε_sm − ε_cm** = Δσ_s / 200000 = {steg['epsilon']:.6f}")
        st.markdown(f"**9. w_k** = s_r,max × (ε_sm − ε_cm) = **{steg['w_k']:.3f} mm**")
        st.markdown(f"**10. A_s,min** = max(0.26×f_ctm/f_yk×b×d, 0.0013×b×d) = max({steg['term1']:.0f}, {steg['term2']:.0f}) = **{steg['A_s_min']:.0f} mm²**")

    # === PDF ===
    data = {**locals(), "A_s": A_s}
    pdf_html = generate_pdf(data, steg)
    st.download_button(
        label="Ladda ner PDF-rapport (med steg)",
        data=pdf_html,
        file_name=f"EC2_rapport_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
        mime="text/html"
    )
    st.balloons()

st.caption("Byggd av kransengangster1000 | Version 3.0 – Fullständiga beräkningar")
