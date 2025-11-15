import numpy as np

def calculate_f_ctm(f_ck):
    """Beräknar medeldraghållfasthet f_ctm enligt EC2 tabell 3.1."""
    if f_ck <= 50:
        return 0.3 * f_ck**(2/3)
    else:
        return 2.12 * np.log(1 + 0.1 * (f_ck + 8))

def calculate_E_cm(f_ck):
    """Beräknar E-modul för betong enligt EC2 ekv. 3.5."""
    f_cm = f_ck + 8
    return 22 * (f_cm / 10)**0.3 * 1000  # i MPa

def calculate_crack_width(A_s, b, h, d, c, phi, f_ck, f_yk, sigma_s, k_c=0.4, k=1.0, load_type='böjning', k_t=0.4):
    """Beräknar sprickbredd w_k enligt EC2 §7.3.4."""
    f_ct_eff = calculate_f_ctm(f_ck)
    E_s = 200000  # MPa
    alpha_e = E_s / calculate_E_cm(f_ck)
    
    if load_type == 'böjning':
        h_c_eff = min(2.5 * (h - d), h/2)
    else:  # drag
        h_c_eff = h/2
    
    A_c_eff = b * h_c_eff
    rho_p_eff = A_s / A_c_eff
    
    if rho_p_eff == 0:
        return np.inf
    
    k1 = 0.8  # högvidhäftande stavar
    k2 = 0.5 if load_type == 'böjning' else 1.0
    k3 = 3.4
    k4 = 0.425
    s_r_max = k3 * c + k1 * k2 * k4 * phi / rho_p_eff  # mm
    
    eps_sm_minus_cm = (sigma_s - k_t * (f_ct_eff / rho_p_eff) * (1 + alpha_e * rho_p_eff)) / E_s
    eps_sm_minus_cm = max(eps_sm_minus_cm, 0.6 * sigma_s / E_s)
    
    w_k = s_r_max * eps_sm_minus_cm  # mm
    return w_k

def min_reinforcement_for_crack_width(b, h, d, c, phi, f_ck, f_yk, w_k_lim, sigma_s, load_type='böjning', max_iter=100, tol=0.01, k_t=0.4):
    """Itererar för att hitta min A_s så att w_k <= w_k_lim."""
    f_ctm = calculate_f_ctm(f_ck)
    
    # Absolut minimum enligt §9.2.1.1
    A_s_abs_min = max(0.26 * (f_ctm / f_yk) * b * d, 0.0013 * b * d)
    
    # Initialgissning från ekv. 7.1
    k = max(0.65, 1 - (h - 300)/1000) if h > 300 else 1.0  # approximation för k (geometri)
    k_c = 0.4 if load_type == 'böjning' else 1.0
    A_ct = b * h / 2 if load_type == 'böjning' else b * h
    f_ct_eff = f_ctm
    A_s_initial = k_c * k * f_ct_eff * A_ct / sigma_s
    A_s = max(A_s_initial, A_s_abs_min)
    
    step = A_s * 0.05  # ökning per iteration
    for i in range(max_iter):
        w_k = calculate_crack_width(A_s, b, h, d, c, phi, f_ck, f_yk, sigma_s, k_c, k, load_type, k_t)
        if w_k <= w_k_lim + tol:
            return A_s
        A_s += step
    
    print("Konvergerade inte inom max iterationer.")
    return A_s

# Interaktiv del
if __name__ == "__main__":
    print("Program för beräkning av minimiarmering enligt Eurocode 2 (EN 1992-1-1).")
    print("Notera: För prEN 1992-1-1 (2023) utesluts krympning; lägg till ytarmering för stora φ.")
    
    b = float(input("Bredd b [mm]: "))
    h = float(input("Höjd h [mm]: "))
    d = float(input("Effektiv höjd d [mm]: "))
    c = float(input("Överbetong c [mm]: "))
    phi = float(input("Stavdiameter φ [mm]: "))
    f_ck = float(input("Betonghållfasthet f_ck [MPa]: "))
    f_yk = float(input("Armeringsflytgräns f_yk [MPa]: "))
    w_k_lim = float(input("Tillåten sprickbredd w_k [mm]: "))
    sigma_s = float(input("Armeringsspänning σ_s vid SLS [MPa]: "))
    load_type = input("Lasttyp (böjning/drag): ").lower()
    
    A_s_min = min_reinforcement_for_crack_width(b, h, d, c, phi, f_ck, f_yk, w_k_lim, sigma_s, load_type)
    print(f"\nMinimiarmering A_{{s,min}}: {A_s_min:.2f} mm²")
    print(f"Armeringskvot ρ_min: {A_s_min / (b * d):.4f}")
