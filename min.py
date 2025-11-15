# sprickkontroll_app.py
import streamlit as st
import math

st.set_page_config(page_title="EC2 Sprickkontroll", layout="centered")

# === DATA ===
F_CTM = {
    "C12/15": 1.6, "C16/20": 1.9, "C20/25": 2.2, "C25/30": 2.6,
    "C30/37": 2.9, "C35/45": 3.2, "C40/50": 3.5, "C45/55": 3.8, "C50/60": 4.1
}

ARMERING = {
    8: 50.3, 10: 78.5, 12: 113.1, 16: 201.1, 20: 314.2,
    25: 490.9, 28: 615.8, 32: 804.2
}

# === HJÄLPFUNKTIONER ===
def minimiarmering(betongklass, f_yk, b_t, d):
    f_ctm = F_CTM[betongklass]
    term1 = 0.26 * (f_ctm / f_yk) * b_t * d
    term2 = 0.0013 * b_t * d
    return max(term1, term2)

def sprickbredd(betongklass, f_yk, M, b, h, d, A_s, phi, c, lasttyp, w_grans):
    f_ctm = F_CTM[betongklass]
    M = M * 1e6  # kNm → Nmm

    # Spänning i armering (förenklad)
    sigma_s = (M / (A_s * 0.9 * d)) * 1.15
    sigma_s = min(sigma_s, f_yk)

    # h_c,ef
    Ac_eff = b * min(2.5*(h-d), h/2)
    rho_p_ef = min(A_s / Ac_eff, 0.05)

    # s_r,max
    k1 = 0.8
    k2 = 0.5 if lasttyp == "böjning" else 1.0
    k3 = 3.4
    k4 = 0.425
    s_r_max = k3 * c + k1 * k2 * k4 * phi / rho_p_ef

    # ε_sm - ε_cm
    kt = 0.4  # långtid
    f_ct_eff = f_ctm
    delta = sigma_s - kt * (f_ct_eff / rho_p_ef) * (1 + 35 * rho_p_ef)
    Es = 200000
    epsilon = delta / Es if delta > 0 else 0

    w_k = s_r_max * epsilon

    A_s_min = minimiarmering(betongklass, f_yk, b, d)

    return {
        "w_k": w_k,
        "sigma_s": sigma_s,
        "s_r_max": s_r_max,
        "epsilon": epsilon,
        "A_s_min": A_s_min,
        "ok": w_k <= w_grans and A_s >= A_s_min
    }

# === WEBBAPP ===
st.title("EC2 Sprickkontroll & Minimiarm")
st.markdown("**Eurocode 2 – 7.3.3 & 7.3.4** | Svensk version")

col1, col2 = st.columns(2)
with col1:
    betongklass = st.selectbox("Betongklass", list(F_CTM.keys()), index=4)
    f_yk = st.selectbox("Armering", [400, 500, 550], index=1)
    lasttyp = st.radio("Lasttyp", ["böjning", "drag"])
with col2:
    M = st.number_input("Moment M [kNm]", 0.0, 1000.0, 120.0)
    w_grans = st.selectbox("Sprickbreddsgräns [mm]", [0.2, 0.3, 0.4], index=1)

st.markdown("---")
st.subheader("Geometri [mm]")
col1, col2, col3 = st.columns(3)
with col1: b = st.number_input("Bredd b", 100, 1000, 300)
with col2: h = st.number_input("Höjd h", 100, 2000, 500)
with col3: d = st.number_input("Användbar höjd d", 50, 2000, 460)

st.markdown("---")
st.subheader("Armering")
col1, col2 = st.columns(2)
with col1:
    st.write("**Välj stång & antal:**")
    phi = st.selectbox("Diameter Ø [mm]", list(ARMERING.keys()), index=3)
    antal = st.slider("Antal stång", 1, 12, 4)
    A_s = antal * ARMERING[phi]
with col2:
    c = st.number_input("Täckskikt c [mm]", 15, 100, 35)
    st.write(f"**Armeringsarea:** {A_s:.0f} mm²")

# === BERÄKNING ===
if st.button("Beräkna sprickbredd & minimiarm"):
    resultat = sprickbredd(
        betongklass, f_yk, M, b, h, d, A_s, phi, c, lasttyp, w_grans
    )

    st.markdown("---")
    st.subheader("Resultat")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Sprickbredd w_k", f"{resultat['w_k']:.3f} mm")
        status = "OK" if resultat['ok'] else "EJ OK"
        color = "green" if resultat['ok'] else "red"
        st.markdown(f"<h3 style='color:{color};'>Kontroll: {status}</h3>", unsafe_allow_html=True)
    with col2:
        st.metric("Minimiarm A_s,min", f"{resultat['A_s_min']:.0f} mm²")
        st.write(f"**Din area:** {A_s:.0f} mm² → {'OK' if A_s >= resultat['A_s_min'] else 'För lite'}")

    with st.expander("Detaljerad beräkning"):
        st.write(f"Spänning i armering σ_s ≈ {resultat['sigma_s']:.0f} MPa")
        st.write(f"Max sprickavstånd s_r,max ≈ {resultat['s_r_max']:.1f} mm")
        st.write(f"Relativ deformation ε_sm - ε_cm ≈ {resultat['epsilon']:.5f}")

    with st.expander("Rekommenderad armering"):
        st.write("Vanliga kombinationer (Ø16 = 201 mm²/st):")
        komb = []
        for p in [8,10,12,16,20]:
            for n in range(2,9):
                area = n * ARMERING[p]
                if area >= resultat['A_s_min']:
                    komb.append((n, p, area))
                    if len(komb) >= 8: break
            if len(komb) >= 8: break
        for n, p, a in komb:
            st.write(f"• **{n} st Ø{p}** → {a:.0f} mm²")

    st.success("Beräkning klar!")