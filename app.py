import io
import textwrap
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib.backends.backend_pdf import PdfPages
from rob_generator import render_onglet_rob

st.set_page_config(
    page_title="Archétype Cadrage (Démonstration) — Pilotage M57 | Cabinet QUINZE",
    page_icon="⚖️",
    layout="wide"
)

# ==========================================
# RÉFÉRENTIEL DES STRATES DÉMOGRAPHIQUES (DGCL / OFGL)
# ==========================================
def get_normes_strate(population):
    if population < 3500:
        return {
            "strate_nom": "Communes de moins de 3 500 hab.",
            "strate_court": "< 3 500 hab.",
            "r1_drf_hab": 760,
            "r2_fisc_hab": 390,
            "r3_rrf_hab": 910,
            "r4_equip_hab": 290,
            "r5_dette_hab": 540,
            "r6_dot_hab": 175,
            "r7_012_drf": 47.0,
            "r9_rigidite": 88.0,
            "taux_endettement": 59.0,
            "taux_eb": 16.5,
            "cap_desend": 3.6,
            "iib": 55.0,
            "encadrement": 11.5,
        }
    elif population < 10000:
        return {
            "strate_nom": "Communes de 3 500 à 9 999 hab.",
            "strate_court": "3 500 - 10 000 hab.",
            "r1_drf_hab": 940,
            "r2_fisc_hab": 510,
            "r3_rrf_hab": 1090,
            "r4_equip_hab": 310,
            "r5_dette_hab": 760,
            "r6_dot_hab": 195,
            "r7_012_drf": 53.5,
            "r9_rigidite": 91.0,
            "taux_endettement": 70.0,
            "taux_eb": 14.5,
            "cap_desend": 4.8,
            "iib": 61.0,
            "encadrement": 15.0,
        }
    elif population < 20000:
        return {
            "strate_nom": "Communes de 10 000 à 19 999 hab.",
            "strate_court": "10 000 - 20 000 hab.",
            "r1_drf_hab": 1060,
            "r2_fisc_hab": 560,
            "r3_rrf_hab": 1210,
            "r4_equip_hab": 315,
            "r5_dette_hab": 880,
            "r6_dot_hab": 215,
            "r7_012_drf": 57.0,
            "r9_rigidite": 92.0,
            "taux_endettement": 73.0,
            "taux_eb": 13.5,
            "cap_desend": 5.4,
            "iib": 64.0,
            "encadrement": 17.0,
        }
    elif population < 50000:
        return {
            "strate_nom": "Communes de 20 000 à 49 999 hab.",
            "strate_court": "20 000 - 50 000 hab.",
            "r1_drf_hab": 1150,
            "r2_fisc_hab": 590,
            "r3_rrf_hab": 1300,
            "r4_equip_hab": 310,
            "r5_dette_hab": 960,
            "r6_dot_hab": 230,
            "r7_012_drf": 58.5,
            "r9_rigidite": 93.0,
            "taux_endettement": 74.0,
            "taux_eb": 12.5,
            "cap_desend": 6.0,
            "iib": 66.0,
            "encadrement": 18.5,
        }
    elif population < 100000:
        return {
            "strate_nom": "Communes de 50 000 à 99 999 hab.",
            "strate_court": "50 000 - 100 000 hab.",
            "r1_drf_hab": 1260,
            "r2_fisc_hab": 630,
            "r3_rrf_hab": 1420,
            "r4_equip_hab": 320,
            "r5_dette_hab": 1140,
            "r6_dot_hab": 255,
            "r7_012_drf": 60.0,
            "r9_rigidite": 94.0,
            "taux_endettement": 80.0,
            "taux_eb": 11.8,
            "cap_desend": 6.8,
            "iib": 68.0,
            "encadrement": 20.0,
        }
    else:
        return {
            "strate_nom": "Communes de 100 000 hab. et plus",
            "strate_court": "> 100 000 hab.",
            "r1_drf_hab": 1390,
            "r2_fisc_hab": 680,
            "r3_rrf_hab": 1560,
            "r4_equip_hab": 350,
            "r5_dette_hab": 1210,
            "r6_dot_hab": 285,
            "r7_012_drf": 60.5,
            "r9_rigidite": 93.5,
            "taux_endettement": 77.5,
            "taux_eb": 12.0,
            "cap_desend": 6.4,
            "iib": 68.0,
            "encadrement": 21.5,
        }


# ==========================================
# COMPOSANT PÉDAGOGIQUE (INFOBULLES & NORMES)
# ==========================================
def fiche_pedagogique(bouton_label, titre, definition, formule=None, normes=None, conseil_dgs=None):
    with st.popover(bouton_label):
        st.markdown(f"### {titre}")
        st.markdown(f"**En clair :** {definition}")
        if formule:
            st.markdown(f"**Mode de calcul (M57) :** `{formule}`")
        if normes:
            st.markdown("**Normes, moyennes de strate & seuils d'alerte :**")
            for n in normes:
                st.markdown(f"* {n}")
        if conseil_dgs:
            st.info(f"**Lecture DGS / Élus :** {conseil_dgs}")


# ==========================================
# MOTEUR D'ANALYSE & PRÉCONISATIONS DGS / CRC
# ==========================================
def generer_analyse_prospective(
    rrf_m, drf_m, ch012_m, ch011_m, ch65_m, eb_m, dette_m, frng_init_m, population,
    rrf_p, drf_p, eb_p, en_p, fctva_p, dette_p, cap_p, frng_p,
    jours_treso_p, drf_hab_p, rrf_hab_p, rar_p, pop_p,
    tx_ms_proj, tx_011_proj, eco_drf_pct, tx_bases_fisc, delta_pts_tfpb,
    rendement_1pt_tfpb, tx_dot_serv,
    ppi_base_m, friction_cfc, tx_realisation_ppi, tx_subv_ppi, delai_subv_mois,
    duree_emprunt_ans, reetalement_hist, cessions_m,
    part_dette_var, part_budget_vert, subv_satellites_m, pic_dette_info=None
):
    tx_eb_2030 = (eb_p[-1] / rrf_p[-1] * 100) if rrf_p[-1] > 0 else 0.0
    delta_eb = eb_p[-1] - eb_m
    delta_dette = dette_p[-1] - dette_m
    min_treso = min(jours_treso_p)
    delta_hab_net = (rrf_hab_p[-1] - drf_hab_p[-1]) - (rrf_hab_p[0] - drf_hab_p[0])
    gain_pop_str = f"{pop_p[-1] - population:,}".replace(",", " ")

    eco_coupe_011_k = int(round((ch011_m + ch65_m) * (eco_drf_pct / 100.0) * 1000))
    ms_fil_2030 = ch012_m * ((1 + 0.042) ** 5)
    ms_cible_2030 = ch012_m * ((1 + tx_ms_proj / 100.0) ** 5)
    eco_rh_2030_m = max(0.0, ms_fil_2030 - ms_cible_2030)
    gain_tfpb_an = delta_pts_tfpb * rendement_1pt_tfpb
    en_redressement = (eb_m <= 0 or (eb_m / rrf_m < 0.05 if rrf_m > 0 else True) or (dette_m / eb_m > 13.0 if eb_m > 0 else True))

    if cap_p[-1] > 12.0 or eb_p[-1] <= 0 or min_treso < 10:
        niveau = "critique"
        badge = "ALERTE ROUGE — RUPTURE PRUDENTIELLE & RISQUE TUTELLE CRC"
        couleur_hex = "#991b1b"
        fond_hex = "#fef2f2"
        bord_hex = "#fca5a5"
    elif cap_p[-1] > 10.0 or tx_eb_2030 < 8.5 or min_treso < 15:
        niveau = "vigilance"
        badge = "VIGILANCE RENFORCÉE — MARGES DE MANŒUVRE SOUS TENSION"
        couleur_hex = "#92400e"
        fond_hex = "#fffbeb"
        bord_hex = "#fcd34d"
    else:
        niveau = "soutenable"
        badge = (
            "PLAN DE REDRESSEMENT VALIDÉ — SORTIE DE ZONE ROUGE D'ICI 2030"
            if en_redressement
            else "TRAJECTOIRE SOUTENABLE — FEUILLE DE ROUTE COMPLÈTE DES LEVIERS (2026-2030)"
        )
        couleur_hex = "#065f46"
        fond_hex = "#ecfdf5"
        bord_hex = "#6ee7b7"

    pic_txt = f" ({pic_dette_info})" if pic_dette_info else ""
    diag_lignes = [
        f"Solvabilité & Épargne : Épargne brute à {eb_p[-1]:.2f} M€ en 2030 ({tx_eb_2030:.1f} % des RRF, {delta_eb:+.2f} M€ vs N) et désendettement à {cap_p[-1]:.1f} ans (dette {dette_p[-1]:.1f} M€, {delta_dette:+.1f} M€){pic_txt}.",
        f"Démographie & Liquidité : +{gain_pop_str} hab. d'ici 2030 (épargne nette/hab : {delta_hab_net:+d} €/hab) ; point bas disponibilités à {min_treso} j de DRF (RAR 2030 : {rar_p[-1]:.1f} M€)."
    ]

    if niveau == "critique":
        besoin_pts = max(1.5, round((12.0 * max(0.5, eb_p[-1]) - dette_p[-1]) / (-12.0 * max(0.05, rendement_1pt_tfpb)), 1)) if rendement_1pt_tfpb > 0 else 2.0
        besoin_pts = min(4.5, max(1.5, besoin_pts))
        ppi_cible = round(ppi_base_m * 0.68, 1)
        piliers = [
            f"1. Fonctionnement & RH : Appliquer une coupe sèche de -{max(6.0, eco_drf_pct):.1f} % sur le 011/65 (-{max(eco_coupe_011_k, int(round((ch011_m+ch65_m)*60)))} k€/an) et plafonner la MS 012 sous 2,1 %/an (gel des embauches).",
            f"2. Fiscalité & Recettes propres : Activer +{besoin_pts:.1f} pts de TFPB (+{besoin_pts * rendement_1pt_tfpb:.2f} M€/an), optimiser les bases DDFiP (≥ 3,2 %/an) et revaloriser les tarifs publics (≥ 2,0 %/an).",
            f"3. Investissement & Patrimoine : Recentrer la PPI à {ppi_cible:.1f} M€/an (vs {ppi_base_m:.1f} M€), exiger ≥ 55 % de subventions et céder {max(0.5, round(rrf_m * 0.04, 1)):.1f} M€ d'actifs (Chap. 024).",
            f"4. Dette, Trésorerie & Satellites : Négocier un réétalement de la dette historique, ouvrir une ligne de trésorerie de {max(0.5, round(drf_m/16, 1)):.1f} M€ (portage {delai_subv_mois} mois, seuil alerte < 10 j) et geler les concours satellites ({subv_satellites_m:.2f} M€)."
        ]
    elif niveau == "vigilance":
        piliers = [
            f"1. Fonctionnement & RH : Engager -{max(2.0, eco_drf_pct):.1f} % d'économies achats/fluides sur 011/65 (-{max(eco_coupe_011_k, int(round((ch011_m+ch65_m)*20)))} k€/an) et contenir la MS 012 à +{min(tx_ms_proj, 2.4):.1f} %/an (gain RH : {eco_rh_2030_m:.1f} M€/an en 2030).",
            f"2. Fiscalité & Recettes propres : Sécuriser +{tx_bases_fisc:.1f} %/an de bases fiscales (recensement locaux vacants), acter +{max(1.0, delta_pts_tfpb):.1f} pt de TFPB et indexer les tarifs (70/75) à +{max(2.0, tx_dot_serv):.1f} %/an.",
            f"3. Investissement & Patrimoine : Caler la PPI à {round(ppi_base_m * 0.9, 1):.1f} M€/an (exécution {min(tx_realisation_ppi, 80)} %), cibler ≥ 55 % de subventions, mobiliser {max(0.5, cessions_m):.1f} M€ de cessions et {max(45, part_budget_vert)} % de Budget Vert.",
            f"4. Dette, Trésorerie & Satellites : Flécher les nouveaux prêts sur {max(25, duree_emprunt_ans)} ans (AFD/CDC), exiger l'avance de 30 % sur subventions (solde ≤ 10 mois) pour maintenir les disponibilités au-dessus de 15 jours et plafonner les concours satellites ({subv_satellites_m:.2f} M€/an)."
        ]
    else:
        txt_coupe = f"coupe initiale de -{eco_drf_pct:.1f} % (-{eco_coupe_011_k} k€/an) puis " if eco_drf_pct > 0 else ""
        txt_tfpb = f"+{delta_pts_tfpb:.1f} pt de TFPB (+{gain_tfpb_an:.2f} M€/an), " if delta_pts_tfpb > 0 else "stabilité des taux communaux (0 pt TFPB), "
        txt_cess = f", mobiliser {cessions_m:.1f} M€ de cessions (Chap. 024)" if cessions_m > 0 else ""
        if reetalement_hist:
            txt_dette = f"Appliquer le réétalement négocié de la dette historique (+0,25 pt), flécher les nouveaux emprunts sur {duree_emprunt_ans} ans (AFD/CDC)"
        else:
            txt_dette = f"Flécher les nouveaux emprunts sur {duree_emprunt_ans} ans (AFD/CDC)"
        autofin_suppl = round(max(0.2, en_p[-1] * 0.45), 2)

        piliers = [
            f"1. Fonctionnement & RH : Tenir la {txt_coupe}hausse du 011/65 limitée à +{tx_011_proj:.1f} %/an, et contenir la MS 012 à +{tx_ms_proj:.1f} %/an (gain cumulé RH de {eco_rh_2030_m:.1f} M€/an en 2030 vs tendanciel).",
            f"2. Fiscalité & Recettes propres : Appliquer {txt_tfpb}optimiser les bases fiscales à +{tx_bases_fisc:.1f} %/an (suivi DDFiP des constructions neuves) et revaloriser les tarifs publics (70/75) de +{tx_dot_serv:.1f} %/an.",
            f"3. Investissement & Budget Vert : Calibrer la PPI à {ppi_base_m:.1f} M€/an ({ppi_base_m * friction_cfc:.1f} M€ TTC avec CFC, exécution {tx_realisation_ppi} %), sécuriser {tx_subv_ppi} % de subventions{txt_cess} et porter le Budget Vert à {min(80, part_budget_vert + 10)} %.",
            f"4. Dette, Trésorerie & Long Terme : {txt_dette}, avance subventions 30 % (solde {delai_subv_mois} mois, FCTVA {sum(fctva_p):.1f} M€), affecter {autofin_suppl:.2f} M€ d'épargne nette (couverture {part_dette_var} % taux var.) et sanctuariser une réserve foncière sur le FRNG ({frng_p[-1]:.1f} M€) + convention satellites ({subv_satellites_m:.2f} M€)."
        ]

    return {
        "niveau": niveau,
        "badge": badge,
        "couleur_hex": couleur_hex,
        "fond_hex": fond_hex,
        "bord_hex": bord_hex,
        "diag": diag_lignes,
        "piliers": piliers
    }


# ==========================================
# GÉNÉRATEURS DE LIVRABLES PDF (FILIGRANE DÉMO)
# ==========================================
def _draw_box(ax, x, y, w, h, facecolor="#ffffff", edgecolor="#cbd5e1", lw=1.0, radius=0.012):
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=facecolor, edgecolor=edgecolor, linewidth=lw,
        transform=ax.transAxes
    )
    ax.add_patch(box)


def _draw_demo_stamp(ax):
    ax.text(
        0.5, 0.5, "SPÉCIMEN DE DÉMONSTRATION\nDOCUMENT NON OPPOSABLE",
        ha="center", va="center", fontsize=26, fontweight="bold",
        color="#d97706", alpha=0.14, rotation=32, transform=ax.transAxes
    )


def build_tbif_pdf(
    collectivite, population, normes_strate, rrf_m, ch012_m, ch011_m, ch65_m, ch661_m,
    cap16_m, dette_m, dette_garantie_m, frng_init_m, friction_cfc, ppi_base_m,
    opex_ppi_pct, rendement_1pt_tfpb, jours_treso_init, eb_2030
):
    charges_gestion_m = ch012_m + ch011_m + ch65_m
    ebg_m = rrf_m - charges_gestion_m
    eb_m = ebg_m - ch661_m
    en_m = eb_m - cap16_m
    taux_eb = (eb_m / rrf_m * 100) if rrf_m > 0 else 0.0
    iib = ((ch012_m + ch65_m + ch661_m + cap16_m) / rrf_m * 100) if rrf_m > 0 else 0.0
    cap_desend = (dette_m / eb_m) if eb_m > 0 else 99.9
    taux_endett = (dette_m / rrf_m * 100) if rrf_m > 0 else 0.0
    dette_consolidee_m = dette_m + dette_garantie_m
    taux_endett_consol = (dette_consolidee_m / rrf_m * 100) if rrf_m > 0 else 0.0
    ppi_soutenable = round(max(0.5, max(eb_m, rrf_m * 0.06) * 2.1), 1)
    opex_induits_k = int(round((ppi_soutenable * 0.5) * (opex_ppi_pct / 100.0) * 1000))
    fctva_annuel_m = round(ppi_soutenable * friction_cfc * 0.85 * 0.16404, 2)

    score_eb = min(40, max(0, int(round((taux_eb / 12.0) * 40))))
    score_desend = min(35, max(0, int(round(((15.0 - min(15.0, cap_desend)) / 10.0) * 35))))
    score_iib = min(25, max(0, int(round(((90.0 - min(90.0, iib)) / 25.0) * 25))))
    health_score = max(12, min(98, score_eb + score_desend + score_iib))

    pop_fmt = f"{population:,}".replace(",", " ")

    buf = io.BytesIO()
    fig = plt.figure(figsize=(8.27, 11.69), dpi=150)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.add_patch(Rectangle((0, 0.915), 1, 0.085, facecolor="#0f172a", transform=ax.transAxes))
    ax.add_patch(Rectangle((0, 0.911), 1, 0.004, facecolor="#d97706", transform=ax.transAxes))
    ax.text(0.04, 0.962, "ARCHÉTYPE CADRAGE [DÉMONSTRATION]  |  ARBITRAGE M57 & PROSPECTIVE",
            color="white", fontsize=11.0, fontweight="bold")
    ax.text(0.04, 0.932, f"CAS FICTIF : {collectivite.upper()} ({pop_fmt} hab. — {normes_strate['strate_nom']})",
            color="#cbd5e1", fontsize=8.3)

    _draw_box(ax, 0.04, 0.805, 0.23, 0.09, facecolor="#f8fafc", edgecolor="#94a3b8", lw=1.2)
    ax.text(0.155, 0.872, "HEALTH SCORE M57", ha="center", fontsize=8, fontweight="bold", color="#475569")
    score_color = "#dc2626" if health_score < 50 else ("#d97706" if health_score < 70 else "#059669")
    ax.text(0.155, 0.822, f"{health_score}/100", ha="center", fontsize=21, fontweight="bold", color=score_color)

    en_tension = (taux_eb < 8.0 or cap_desend > 10.0 or taux_endett > 100.0)
    alert_bg = "#fef2f2" if en_tension else "#ecfdf5"
    alert_bd = "#fca5a5" if en_tension else "#6ee7b7"
    alert_fg = "#991b1b" if en_tension else "#065f46"
    alert_title = "RUPTURE D'ÉPARGNE BRUTE OU TENSION D'ENDETTEMENT IDENTIFIÉE" if en_tension else "ÉQUILIBRE FINANCIER SOUS CONTRÔLE PRUDENTIEL"
    _draw_box(ax, 0.29, 0.805, 0.67, 0.09, facecolor=alert_bg, edgecolor=alert_bd, lw=1.2)
    ax.text(0.31, 0.872, alert_title, fontsize=8.7, fontweight="bold", color=alert_fg)
    ax.text(0.31, 0.844, f"• Épargne brute : {taux_eb:.1f}% (Strate : {normes_strate['taux_eb']:.1f}%) | Taux endettement : {taux_endett:.1f}% (Strate : {normes_strate['taux_endettement']:.0f}%).",
            fontsize=7.8, color="#1e293b")
    ax.text(0.31, 0.820, f"• IIB : {iib:.1f}% (Strate : {normes_strate['iib']:.0f}%) | Désendettement : {cap_desend:.1f} ans (Strate : {normes_strate['cap_desend']:.1f} ans) | FRNG : {jours_treso_init} j.",
            fontsize=7.8, color="#1e293b")

    _draw_box(ax, 0.04, 0.335, 0.48, 0.450, facecolor="#ffffff", edgecolor="#cbd5e1", lw=1.1)
    ax.add_patch(Rectangle((0.04, 0.745), 0.48, 0.04, facecolor="#1e293b", transform=ax.transAxes))
    ax.text(0.055, 0.758, "1. CASCADE DES SIG M57 & ÉPARGNE", color="white", fontsize=9, fontweight="bold")

    sig_rows = [
        ("Recettes Réelles de Fonct. (RRF)", f"{rrf_m:.2f} M€", False, "#0f172a"),
        ("- Charges de gestion (012+011+65)", f"-{charges_gestion_m:.2f} M€", False, "#475569"),
        ("= Excédent Brut de Gestion (EBG)", f"{ebg_m:.2f} M€", True, "#0f172a"),
        ("- Intérêts de la dette (Chap. 661)", f"-{ch661_m:.2f} M€", False, "#475569"),
        ("= Épargne Brute (CAF)", f"{eb_m:.2f} M€ ({taux_eb:.1f}%)", True, "#b45309"),
        ("- Capital dette amorti (Chap. 16)", f"-{cap16_m:.2f} M€", False, "#475569"),
        ("= Épargne Nette disponible", f"{en_m:.2f} M€", True, "#059669" if en_m >= 0 else "#dc2626"),
    ]
    y_pos = 0.705
    for label, val, is_bold, col in sig_rows:
        if is_bold:
            ax.add_patch(Rectangle((0.048, y_pos - 0.012), 0.464, 0.038, facecolor="#f1f5f9", transform=ax.transAxes))
        ax.text(0.058, y_pos, label, fontsize=8.3, fontweight="bold" if is_bold else "normal", color="#1e293b")
        ax.text(0.505, y_pos, val, ha="right", fontsize=8.5, fontweight="bold" if is_bold else "normal", color=col)
        y_pos -= 0.054

    _draw_box(ax, 0.54, 0.653, 0.42, 0.132, facecolor="#ffffff", edgecolor="#cbd5e1", lw=1.1)
    ax.add_patch(Rectangle((0.54, 0.747), 0.42, 0.038, facecolor="#1e293b", transform=ax.transAxes))
    ax.text(0.555, 0.760, "2. INVESTISSEMENT, FCTVA & OPEX", color="white", fontsize=8.8, fontweight="bold")
    ppi_items = [
        ("Friction Contextuelle (CFC) :", f"{friction_cfc:.2f}"),
        ("PPI Soutenable / FCTVA :", f"{ppi_soutenable:.1f} / {fctva_annuel_m:.2f} M€"),
        ("Impact Opex Induits PPI :", f"+{opex_induits_k} k€/an"),
    ]
    yp = 0.720
    for k, v in ppi_items:
        ax.text(0.555, yp, k, fontsize=7.9, color="#334155")
        ax.text(0.945, yp, v, ha="right", fontsize=8.1, fontweight="bold", color="#0f172a")
        yp -= 0.027

    _draw_box(ax, 0.54, 0.478, 0.42, 0.162, facecolor="#ffffff", edgecolor="#cbd5e1", lw=1.1)
    ax.add_patch(Rectangle((0.54, 0.602), 0.42, 0.038, facecolor="#1e293b", transform=ax.transAxes))
    ax.text(0.555, 0.615, "3. ENDETTEMENT & TRÉSORERIE", color="white", fontsize=8.8, fontweight="bold")
    dette_items = [
        ("Capacité Désendettement :", f"{cap_desend:.1f} ans (Str. {normes_strate['cap_desend']:.1f}a)"),
        ("Taux Endettement (R11) :", f"{taux_endett:.1f}% (Str. {normes_strate['taux_endettement']:.0f}%)"),
        ("Dette Directe / Consol. :", f"{dette_m:.1f} / {dette_consolidee_m:.1f} M€ ({taux_endett_consol:.0f}%)"),
        ("FRNG (Fonds Roulement) :", f"{frng_init_m:.1f} M€ ({jours_treso_init} j)"),
    ]
    yd = 0.575
    for k, v in dette_items:
        ax.text(0.555, yd, k, fontsize=7.8, color="#334155")
        is_alert_line = ("Désendettement" in k and cap_desend > 10) or ("Endettement" in k and taux_endett > 100)
        ax.text(0.945, yd, v, ha="right", fontsize=7.9, fontweight="bold",
                color="#dc2626" if is_alert_line else "#0f172a")
        yd -= 0.027

    _draw_box(ax, 0.54, 0.335, 0.42, 0.130, facecolor="#ffffff", edgecolor="#cbd5e1", lw=1.1)
    ax.add_patch(Rectangle((0.54, 0.427), 0.42, 0.038, facecolor="#1e293b", transform=ax.transAxes))
    ax.text(0.555, 0.440, "4. ARBITRAGE DES SCÉNARIOS DOB", color="white", fontsize=8.8, fontweight="bold")
    ax.text(0.555, 0.400, "1. Fil de l'eau : Ciseau non résorbé", fontsize=8.0, color="#dc2626", fontweight="bold")
    ax.text(0.555, 0.374, f"2. PPI Intégrale ({ppi_base_m:.1f} M€) : Alerte bancaire", fontsize=8.0, color="#d97706", fontweight="bold")
    ax.text(0.555, 0.348, f"3. Cible Optimisée : SOUTENABLE (Ép. +{eb_2030:.1f} M€)", fontsize=8.0, color="#059669", fontweight="bold")

    ax.text(0.04, 0.302, f"RÉFÉRENTIEL M57 & NORMES DE STRATE ({normes_strate['strate_nom'].upper()})",
            fontsize=9.0, fontweight="bold", color="#0f172a")
    cards = [
        ("INFLEXIBILITÉ (IIB)", "Salaires + Dette + Fluides\nrapportés aux RRF",
         [f"Moy. Strate : {normes_strate['iib']:.0f} %", "Vigilance : > 75 %", "Critique : > 85 %"]),
        ("TAUX ENDETTEMENT (R11)", "Encours de dette directe\nrapporté aux RRF",
         [f"Moy. Strate : {normes_strate['taux_endettement']:.0f} %", "Vigilance : > 90 %", "Alerte : > 100 %"]),
        ("DÉSENDETTEMENT", "Encours de dette divisé\npar l'Épargne Brute",
         [f"Moy. Strate : {normes_strate['cap_desend']:.1f} ans", "Alerte : > 10 ans", "Refus Prêt : > 12 ans"]),
        ("ÉPARGNE & LIQUIDITÉ", "Épargne brute et disponibilités\n(lissage par douzièmes)",
         [f"Ép. Str. {normes_strate['taux_eb']:.1f}% | Disp. 15-25j", "Vigilance tréso : 10-15 j", "Alerte tréso : < 10 j"]),
    ]
    for idx, (ctitle, cdesc, clines) in enumerate(cards):
        cx = 0.04 + idx * 0.234
        _draw_box(ax, cx, 0.080, 0.218, 0.208, facecolor="#f8fafc", edgecolor="#cbd5e1", lw=1.0)
        ax.text(cx + 0.011, 0.266, ctitle, fontsize=7.5, fontweight="bold", color="#0f172a")
        ax.text(cx + 0.011, 0.224, cdesc, fontsize=7.0, color="#475569")
        for li, line in enumerate(clines):
            lcol = "#059669" if li == 0 else ("#d97706" if li == 1 else "#dc2626")
            ax.text(cx + 0.011, 0.175 - li * 0.033, f"• {line}", fontsize=7.3, fontweight="bold", color=lcol)

    _draw_demo_stamp(ax)
    ax.plot([0.04, 0.96], [0.052, 0.052], color="#cbd5e1", lw=0.8)
    ax.text(0.04, 0.032, "Spécimen de démonstration non opposable  •  Cabinet QUINZE", fontsize=7.8, color="#b45309", fontweight="bold")
    ax.text(0.96, 0.032, "Page 1/1", ha="right", fontsize=7.8, fontweight="bold", color="#475569")

    fig.savefig(buf, format="pdf")
    plt.close(fig)
    return buf.getvalue()


def build_prospective_pdf(
    collectivite, scenario_nom, ppi_base_m, tx_realisation_ppi, tx_subv_ppi, friction_cfc,
    annees_proj, rrf_p, drf_p, eb_p, fctva_p, dette_p, cap_p, frng_p,
    jours_treso_p, drf_hab_p, rar_fin_m, dette_init, analyse_dict
):
    tx_eb_p = [round((eb / rrf * 100) if rrf > 0 else 0.0, 1) for eb, rrf in zip(eb_p, rrf_p)]

    buf = io.BytesIO()
    fig = plt.figure(figsize=(8.27, 11.69), dpi=150)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.add_patch(Rectangle((0, 0.915), 1, 0.085, facecolor="#0f172a", transform=ax.transAxes))
    ax.add_patch(Rectangle((0, 0.911), 1, 0.004, facecolor="#d97706", transform=ax.transAxes))
    ax.text(0.04, 0.962, "ARCHÉTYPE CADRAGE [DÉMONSTRATION]  |  PROSPECTIVE & ARBITRAGE DGS (2026-2030)",
            color="white", fontsize=10.5, fontweight="bold")
    ax.text(0.04, 0.932, f"CAS FICTIF : {collectivite.upper()}  •  SCÉNARIO : {scenario_nom.upper()}  •  PPI : {ppi_base_m:.1f} M€/an",
            color="#cbd5e1", fontsize=8.0)

    treso_col = "#1d4ed8" if jours_treso_p[-1] >= 15 else ("#d97706" if jours_treso_p[-1] >= 10 else "#dc2626")
    kpis = [
        ("ÉPARGNE BRUTE 2030", f"{eb_p[-1]:+.1f} M€", f"Taux d'épargne : {tx_eb_p[-1]:.1f} %", "#059669" if eb_p[-1] > 0 else "#dc2626"),
        ("CAPACITÉ DÉSEND. 2030", f"{cap_p[-1]:.1f} ans", "Seuil alerte : 12 ans", "#059669" if cap_p[-1] <= 12 else "#dc2626"),
        ("ENCOURS DETTE 2030", f"{dette_p[-1]:.1f} M€", f"Variation : {dette_p[-1] - dette_init:+.1f} M€", "#0f172a"),
        ("DISPONIBILITÉS 2030", f"{jours_treso_p[-1]} jours", f"FRNG : {frng_p[-1]:.1f} M€ | RAR : {rar_fin_m:.1f} M€", treso_col),
    ]
    for i, (kt, kv, ks, kc) in enumerate(kpis):
        kx = 0.04 + i * 0.233
        _draw_box(ax, kx, 0.815, 0.218, 0.084, facecolor="#f8fafc", edgecolor="#cbd5e1", lw=1.0)
        ax.text(kx + 0.012, 0.880, kt, fontsize=7.2, fontweight="bold", color="#475569")
        ax.text(kx + 0.012, 0.845, kv, fontsize=13.0, fontweight="bold", color=kc)
        ax.text(kx + 0.012, 0.823, ks, fontsize=6.9, color="#64748b")

    ax.text(0.04, 0.792, "1. PROJECTION RRF VS DRF (INCLUANT OPEX INDUITS PPI)", fontsize=8.1, fontweight="bold", color="#0f172a")
    ax.text(0.52, 0.792, "2. SOLDE D'ÉPARGNE & TRÉSORERIE (FRNG)", fontsize=8.1, fontweight="bold", color="#0f172a")

    ax1 = fig.add_axes([0.075, 0.595, 0.39, 0.185])
    ax1.plot(annees_proj, rrf_p, marker="o", color="#2563eb", lw=2, label="Recettes (RRF)")
    ax1.plot(annees_proj, drf_p, marker="s", color="#dc2626", lw=2, label="Dépenses (DRF+OPEX)")
    ax1.set_xticks(annees_proj)
    ax1.tick_params(labelsize=7.2)
    ax1.grid(True, linestyle="--", alpha=0.4)
    ax1.legend(loc="upper left", fontsize=6.7, frameon=True)

    ax2 = fig.add_axes([0.555, 0.595, 0.39, 0.185])
    ax2.plot(annees_proj, eb_p, marker="^", color="#16a34a", lw=2, label="Épargne Brute")
    ax2.plot(annees_proj, frng_p, marker="s", linestyle=":", color="#2563eb", lw=2, label="Fonds Roulement")
    ax2.axhline(0, color="black", linestyle="--", lw=0.8)
    ax2.set_xticks(annees_proj)
    ax2.tick_params(labelsize=7.2)
    ax2.grid(True, linestyle="--", alpha=0.4)
    ax2.legend(loc="upper left", fontsize=6.7, frameon=True)

    ax.text(0.04, 0.558, "TABLEAU PLURIANNUEL DES TRAJECTOIRES BUDGÉTAIRES & DÉMOGRAPHIQUES M57",
            fontsize=8.2, fontweight="bold", color="#0f172a")
    col_labels = ["Indicateurs M57"] + [str(a) for a in annees_proj]
    table_data = [
        ["Recettes réelles de fonctionnement (M€)"] + [f"{v:.1f}" for v in rrf_p],
        ["Dépenses réelles de fonct. + OPEX induits (M€)"] + [f"{v:.1f}" for v in drf_p],
        ["Épargne Brute dégagée (M€)"] + [f"{v:.1f}" for v in eb_p],
        ["FCTVA encaissé sur décaissements PPI (M€)"] + [f"{v:.2f}" for v in fctva_p],
        ["Encours de la dette au 31/12 (M€)"] + [f"{v:.1f}" for v in dette_p],
        ["Capacité de désendettement (années)"] + [f"{v:.1f}" for v in cap_p],
        ["Disponibilités nettes (Jours DRF) / DRF par hab."] + [f"{j} j ({d}€)" for j, d in zip(jours_treso_p, drf_hab_p)],
    ]
    tbl_ax = fig.add_axes([0.04, 0.355, 0.92, 0.195])
    tbl_ax.axis("off")
    table = tbl_ax.table(
        cellText=table_data,
        colLabels=col_labels,
        loc="center",
        cellLoc="center",
        colWidths=[0.42] + [0.116] * 5
    )
    table.auto_set_font_size(False)
    table.set_fontsize(7.2)
    table.scale(1, 1.28)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#cbd5e1")
        if row == 0:
            cell.set_facecolor("#1e293b")
            cell.get_text().set_color("white")
            cell.get_text().set_weight("bold")
        else:
            if col == 0:
                cell.get_text().set_ha("left")
            if row in (3, 6):
                cell.set_facecolor("#f1f5f9")
                cell.get_text().set_weight("bold")

    _draw_box(ax, 0.04, 0.056, 0.92, 0.285,
              facecolor=analyse_dict["fond_hex"], edgecolor=analyse_dict["bord_hex"], lw=1.1)
    ax.text(0.055, 0.323, f"FEUILLE DE ROUTE EXHAUSTIVE DGS : {analyse_dict['badge']}",
            fontsize=8.0, fontweight="bold", color=analyse_dict["couleur_hex"])

    all_lines = [f"• {d}" for d in analyse_dict["diag"]] + analyse_dict["piliers"]
    y_curr = 0.303
    for idx_l, raw_line in enumerate(all_lines):
        is_reco = idx_l >= 2
        for w_line in textwrap.wrap(raw_line, width=128):
            ax.text(0.055, y_curr, w_line, fontsize=6.85,
                    fontweight="bold" if is_reco else "normal",
                    color=analyse_dict["couleur_hex"] if is_reco else "#1e293b")
            y_curr -= 0.0145
        y_curr -= 0.0025

    _draw_demo_stamp(ax)
    ax.plot([0.04, 0.96], [0.044, 0.044], color="#cbd5e1", lw=0.8)
    ax.text(0.04, 0.027, "Spécimen de démonstration non opposable  •  Cabinet QUINZE", fontsize=7.8, color="#b45309", fontweight="bold")
    ax.text(0.96, 0.027, "Page 1/1", ha="right", fontsize=7.8, fontweight="bold", color="#475569")

    fig.savefig(buf, format="pdf")
    plt.close(fig)
    return buf.getvalue()


def build_retro_pdf(
    collectivite, annees_retro, rrf_hist, drf_hist, ms_hist, eb_hist, en_hist,
    tcma_rrf, tcma_drf, tcma_ms, poids_ms_rrf, delta_eb_5ans,
    equip_hist, subv_hist, fctva_hist, cess_hist, pop, normes_strate
):
    buf = io.BytesIO()
    with PdfPages(buf) as pdf:
        fig1 = plt.figure(figsize=(8.27, 11.69), dpi=150)
        ax = fig1.add_axes([0, 0, 1, 1])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")

        ax.add_patch(Rectangle((0, 0.915), 1, 0.085, facecolor="#0f172a", transform=ax.transAxes))
        ax.add_patch(Rectangle((0, 0.911), 1, 0.004, facecolor="#d97706", transform=ax.transAxes))
        ax.text(0.04, 0.962, f"ARCHÉTYPE CADRAGE [DÉMONSTRATION]  |  AUDIT RÉTROSPECTIF M57 ({annees_retro[0]}-{annees_retro[-1]})",
                color="white", fontsize=10.5, fontweight="bold")
        ax.text(0.04, 0.932, f"CAS FICTIF : {collectivite.upper()}  •  JEU DE DONNÉES PRÉREMPLI",
                color="#cbd5e1", fontsize=8.3)

        rkpis = [
            ("TCMA RECETTES (RRF)", f"+{tcma_rrf:.2f} % / an", "Dynamique des ressources", "#059669"),
            ("TCMA DÉPENSES (DRF)", f"+{tcma_drf:.2f} % / an", f"Écart : {tcma_drf - tcma_rrf:+.2f} pts vs RRF", "#dc2626"),
            ("TCMA MASSE SALARIALE", f"+{tcma_ms:.2f} % / an", f"Poids : {poids_ms_rrf:.1f} % des RRF", "#d97706"),
            ("ÉVOLUTION ÉPARGNE BRUTE", f"{eb_hist[-1]:.1f} M€", f"Variation période : {delta_eb_5ans:+.1f} M€", "#dc2626" if delta_eb_5ans < 0 else "#059669"),
        ]
        for i, (kt, kv, ks, kc) in enumerate(rkpis):
            kx = 0.04 + i * 0.233
            _draw_box(ax, kx, 0.805, 0.218, 0.092, facecolor="#f8fafc", edgecolor="#cbd5e1", lw=1.0)
            ax.text(kx + 0.012, 0.875, kt, fontsize=7.1, fontweight="bold", color="#475569")
            ax.text(kx + 0.012, 0.838, kv, fontsize=12.5, fontweight="bold", color=kc)
            ax.text(kx + 0.012, 0.814, ks, fontsize=7.1, color="#64748b")

        ax.text(0.04, 0.775, "1. EFFET DE CISEAU HISTORIQUE (RRF VS DRF)", fontsize=8.5, fontweight="bold", color="#0f172a")
        ax.text(0.52, 0.775, "2. ÉROSION DE L'ÉPARGNE BRUTE & NETTE", fontsize=8.5, fontweight="bold", color="#0f172a")

        g1 = fig1.add_axes([0.075, 0.615, 0.39, 0.145])
        g1.plot(annees_retro, rrf_hist, marker="o", color="#2563eb", lw=2, label="Recettes (RRF)")
        g1.plot(annees_retro, drf_hist, marker="s", color="#dc2626", lw=2, label="Dépenses (DRF)")
        g1.tick_params(labelsize=7.5)
        g1.grid(True, linestyle="--", alpha=0.4)
        g1.legend(loc="upper left", fontsize=7.2)

        g2 = fig1.add_axes([0.555, 0.615, 0.39, 0.145])
        g2.plot(annees_retro, eb_hist, marker="^", color="#16a34a", lw=2, label="Épargne Brute")
        g2.plot(annees_retro, en_hist, marker="s", color="#d97706", lw=2, label="Épargne Nette")
        g2.tick_params(labelsize=7.5)
        g2.grid(True, linestyle="--", alpha=0.4)
        g2.legend(loc="upper right", fontsize=7.2)

        emprunt_hist = [max(0.0, e - en - s - f - c) for e, en, s, f, c in zip(equip_hist, en_hist, subv_hist, fctva_hist, cess_hist)]
        moy_equip = sum(equip_hist) / len(equip_hist) if equip_hist else 0
        moy_subv = (sum(subv_hist) + sum(fctva_hist)) / sum(equip_hist) * 100 if sum(equip_hist) > 0 else 0
        ratio_equip_hab = int(round((moy_equip * 1e6) / pop))

        ax.text(0.04, 0.565, "3. RÉTROSPECTIVE DE L'INVESTISSEMENT & MIX DE FINANCEMENT", fontsize=8.5, fontweight="bold", color="#0f172a")

        _draw_box(ax, 0.04, 0.420, 0.44, 0.130, facecolor="#f8fafc", edgecolor="#cbd5e1", lw=1.0)
        ax.text(0.055, 0.525, "DIAGNOSTIC DE L'EFFORT D'ÉQUIPEMENT", fontsize=8.0, fontweight="bold", color="#0f172a")
        ax.text(0.055, 0.495, f"• Enveloppe moyenne exécutée : {moy_equip:.1f} M€ / an.", fontsize=7.5, color="#1e293b")
        ax.text(0.055, 0.472, f"• Effort par habitant : {ratio_equip_hab} € / hab (Strate : {normes_strate['r4_equip_hab']} €).", fontsize=7.5, color="#1e293b")
        ax.text(0.055, 0.449, f"• Taux de cofinancement (Subv. + FCTVA) : {moy_subv:.1f} %.", fontsize=7.5, color="#1e293b")
        ax.text(0.055, 0.426, f"• Recours à l'emprunt / tréso : {sum(emprunt_hist):.1f} M€ sur la période.", fontsize=7.5, color="#1e293b")

        g3 = fig1.add_axes([0.555, 0.420, 0.39, 0.130])
        width = 0.5
        bottom = np.zeros(len(annees_retro))
        g3.bar(annees_retro, en_hist, width, label='Épargne Nette', color='#059669', bottom=bottom)
        bottom += np.array(en_hist)
        g3.bar(annees_retro, subv_hist, width, label='Subventions', color='#2563eb', bottom=bottom)
        bottom += np.array(subv_hist)
        g3.bar(annees_retro, fctva_hist, width, label='FCTVA', color='#3b82f6', bottom=bottom)
        bottom += np.array(fctva_hist)
        g3.bar(annees_retro, cess_hist, width, label='Cessions', color='#d97706', bottom=bottom)
        bottom += np.array(cess_hist)
        g3.bar(annees_retro, emprunt_hist, width, label='Emprunt / Tréso', color='#dc2626', bottom=bottom)
        g3.plot(annees_retro, equip_hist, marker='o', color='black', lw=1.5, label='Total Équipement')
        g3.tick_params(labelsize=6.5)
        g3.grid(True, axis="y", linestyle="--", alpha=0.4)
        g3.legend(loc="upper left", bbox_to_anchor=(1.02, 1), fontsize=6.0, frameon=False)
        g3.spines['top'].set_visible(False)
        g3.spines['right'].set_visible(False)

        ax.text(0.04, 0.380, f"TABLEAU RÉTROSPECTIF DES SOLDES M57 ({annees_retro[0]}-{annees_retro[-1]})", fontsize=8.8, fontweight="bold", color="#0f172a")
        tx_eb_h = [round((e / r * 100) if r > 0 else 0.0, 1) for e, r in zip(eb_hist, rrf_hist)]
        t_data = [
            ["Recettes Réelles de Fonctionnement (M€)"] + [f"{v:.2f}" for v in rrf_hist],
            ["Dépenses Réelles de Fonctionnement (M€)"] + [f"{v:.2f}" for v in drf_hist],
            ["Masse Salariale — Chapitre 012 (M€)"] + [f"{v:.2f}" for v in ms_hist],
            ["Épargne Brute / CAF (M€)"] + [f"{v:.2f}" for v in eb_hist],
            ["Épargne Nette disponible (M€)"] + [f"{v:.2f}" for v in en_hist],
            ["Taux d'Épargne Brute (%)"] + [f"{v:.1f} %" for v in tx_eb_h],
        ]
        n_cols = len(annees_retro)
        col_w = [0.42] + [round(0.58 / max(1, n_cols), 3)] * n_cols
        tax = fig1.add_axes([0.04, 0.165, 0.92, 0.200])
        tax.axis("off")
        tbl = tax.table(cellText=t_data, colLabels=["Soldes M57"] + annees_retro, loc="center", cellLoc="center", colWidths=col_w)
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(7.5)
        tbl.scale(1, 1.35)
        for (r, c), cell in tbl.get_celld().items():
            cell.set_edgecolor("#cbd5e1")
            if r == 0:
                cell.set_facecolor("#1e293b")
                cell.get_text().set_color("white")
                cell.get_text().set_weight("bold")
            else:
                if c == 0:
                    cell.get_text().set_ha("left")
                if r in (4, 6):
                    cell.set_facecolor("#f1f5f9")
                    cell.get_text().set_weight("bold")

        _draw_box(ax, 0.04, 0.055, 0.92, 0.095, facecolor="#fef2f2", edgecolor="#fca5a5", lw=1.0)
        ax.text(0.055, 0.128, "DIAGNOSTIC DE L'EFFET DE CISEAU BUDGÉTAIRE", fontsize=8.8, fontweight="bold", color="#991b1b")
        ax.text(0.055, 0.102, f"• Les dépenses de fonctionnement (+{tcma_drf:.2f} %/an) progressent plus vite que les recettes (+{tcma_rrf:.2f} %/an).", fontsize=8, color="#1e293b")
        ax.text(0.055, 0.076, f"• L'épargne brute passe de {eb_hist[0]:.2f} M€ en {annees_retro[0]} à {eb_hist[-1]:.2f} M€ en {annees_retro[-1]} ({delta_eb_5ans:+.2f} M€).", fontsize=8, color="#1e293b")

        _draw_demo_stamp(ax)
        ax.plot([0.04, 0.96], [0.035, 0.035], color="#cbd5e1", lw=0.8)
        ax.text(0.04, 0.020, "Spécimen de démonstration non opposable  •  Cabinet QUINZE", fontsize=7.8, color="#b45309", fontweight="bold")
        ax.text(0.96, 0.020, "Page 1/2", ha="right", fontsize=7.8, fontweight="bold", color="#475569")
        pdf.savefig(fig1)
        plt.close(fig1)

        fig2 = plt.figure(figsize=(8.27, 11.69), dpi=150)
        ax = fig2.add_axes([0, 0, 1, 1])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")

        ax.add_patch(Rectangle((0, 0.915), 1, 0.085, facecolor="#0f172a", transform=ax.transAxes))
        ax.add_patch(Rectangle((0, 0.911), 1, 0.004, facecolor="#d97706", transform=ax.transAxes))
        ax.text(0.04, 0.962, "ARCHÉTYPE CADRAGE [DÉMONSTRATION]  |  DÉCOMPOSITION RH & ARBITRAGES",
                color="white", fontsize=10.5, fontweight="bold")
        ax.text(0.04, 0.932, f"CAS FICTIF : {collectivite.upper()}  •  LEVIERS MANAGÉRIAUX & PISTES D'AUDIT",
                color="#cbd5e1", fontsize=8.5)

        ax.text(0.04, 0.875, "1. DÉCOMPOSITION DE LA PROGRESSION DE LA MASSE SALARIALE (CHAPITRE 012)", fontsize=9.2, fontweight="bold", color="#0f172a")
        gvt_pts = 1.2
        etat_pts = 0.6
        vol_pts = max(0.0, round(tcma_ms - (gvt_pts + etat_pts), 2))
        grh = fig2.add_axes([0.34, 0.65, 0.60, 0.20])
        labels_rh = ["Effet Volume\n(Levier local)", "Mesures d'État\n(Indice / Ségur)", "GVT Mécanique\n(Ancienneté)"]
        vals_rh = [vol_pts, etat_pts, gvt_pts]
        colors_rh = ["#059669", "#d97706", "#64748b"]
        grh.barh(labels_rh, vals_rh, color=colors_rh, height=0.55)
        grh.set_xlabel("Contribution annuelle (% / an)", fontsize=7.5)
        grh.tick_params(labelsize=7.8)
        grh.grid(True, axis="x", linestyle="--", alpha=0.4)

        _draw_box(ax, 0.04, 0.49, 0.92, 0.125, facecolor="#fffbeb", edgecolor="#fcd34d", lw=1.0)
        ax.text(0.055, 0.59, "LECTURE MANAGÉRIALE : FACTEURS SUBIS VS LEVIER INTERNE", fontsize=8.8, fontweight="bold", color="#92400e")
        ax.text(0.055, 0.56, f"• Sur +{tcma_ms:.2f} % / an d'évolution salariale, {gvt_pts + etat_pts:.1f} points sont structurels (GVT + revalorisations nationales).", fontsize=8, color="#1e293b")
        ax.text(0.055, 0.532, f"• {vol_pts:.2f} points relèvent directement des décisions locales (créations de postes, remplacements, heures supplémentaires).", fontsize=8, color="#1e293b")
        ax.text(0.055, 0.504, "• Cible pacte RH : Piloter le taux de remplacement des départs et encadrer l'enveloppe indemnitaire (RIFSEEP).", fontsize=8, fontweight="bold", color="#92400e")

        ax.text(0.04, 0.445, "2. BILAN STRATÉGIQUE : ATOUTS & PISTES D'INVESTIGATION", fontsize=9.2, fontweight="bold", color="#0f172a")
        _draw_box(ax, 0.04, 0.12, 0.44, 0.30, facecolor="#ecfdf5", edgecolor="#6ee7b7", lw=1.0)
        ax.text(0.055, 0.392, "ATOUTS & MARGES DE MANŒUVRE", fontsize=8.8, fontweight="bold", color="#065f46")
        ax.text(0.055, 0.352, f"• Dynamisme des recettes (+{tcma_rrf:.1f} % / an) porté\n  par la croissance démographique et fiscale.", fontsize=8, color="#1e293b")
        ax.text(0.055, 0.285, f"• Capacité d'autofinancement brute maintenue à\n  {eb_hist[-1]:.2f} M€ sur le dernier exercice clos.", fontsize=8, color="#1e293b")
        ax.text(0.055, 0.218, "• Potentiel élevé de cofinancements externes\n  (État, Fonds Européens, AFD) et FCTVA.", fontsize=8, color="#1e293b")

        _draw_box(ax, 0.52, 0.12, 0.44, 0.30, facecolor="#fef2f2", edgecolor="#fca5a5", lw=1.0)
        ax.text(0.535, 0.392, "POINTS DE VIGILANCE & PISTES D'AUDIT", fontsize=8.8, fontweight="bold", color="#991b1b")
        ax.text(0.535, 0.352, "• Résorber l'effet de ciseau : contenir la hausse\n  des charges générales (Chap. 011) sous 1,5 %.", fontsize=8, color="#1e293b")
        ax.text(0.535, 0.285, f"• Rigidité salariale ({poids_ms_rrf:.1f} % des RRF) :\n  auditer le régime indemnitaire et l'absentéisme.", fontsize=8, color="#1e293b")
        ax.text(0.535, 0.218, "• Intégrer systématiquement le coefficient CFC\n  et les OPEX induits dans le chiffrage PPI.", fontsize=8, color="#1e293b")

        _draw_demo_stamp(ax)
        ax.plot([0.04, 0.96], [0.055, 0.055], color="#cbd5e1", lw=0.8)
        ax.text(0.04, 0.035, "Spécimen de démonstration non opposable  •  Cabinet QUINZE", fontsize=8, color="#b45309", fontweight="bold")
        ax.text(0.96, 0.035, "Page 2/2", ha="right", fontsize=8, fontweight="bold", color="#475569")
        pdf.savefig(fig2)
        plt.close(fig2)

    return buf.getvalue()


# ==========================================
# BANDEAU MODE DÉMONSTRATION
# ==========================================
st.warning(
    "**MODE DÉMONSTRATION INTERACTIF** — Cet environnement de test fonctionne sur un jeu de données prérempli et verrouillé. "
    "Vous pouvez manipuler librement les curseurs de simulation prospective 2026-2030, les scénarios DOB et les fiches pédagogiques. "
    "L'import de balances comptables M57 réelles et la sauvegarde dans le Cloud sont désactivés."
)

# ==========================================
# 1. BARRE LATÉRALE : DONNÉES PRÉREMPLIES VERROUILLÉES
# ==========================================
st.sidebar.markdown("## ⚖️ Archétype Cadrage")
st.sidebar.info("🔒 **Mode Démonstration** : les données comptables de base sont préremplies et verrouillées.")

collectivite = st.sidebar.text_input(
    "Collectivité étudiée (verrouillé)",
    "Collectivité de Démonstration (Strate 50 000 hab.)",
    disabled=True
)

balances_parsees = []
source_reelle = False

def_fisc = 26000000.00
def_dot = 28000000.00
def_serv = 7800000.00
def_012 = 38400000.00
def_011 = 13200000.00
def_65 = 4520000.00
def_661 = 1600000.00
def_16 = 3200000.00
def_dette = 48513000.00
def_equip = 14000000.00
def_dette_gar = 18500000.00
def_subv_sat = 2800000.00
def_frng = 5500000.00
def_rar = 4200000.00
def_pop = 50017
def_etp = 850

st.sidebar.markdown("### 1. Fonctionnement & Fiscalité (Prérempli)")
fisc_eur = st.sidebar.number_input("Impôts & Taxes (Chap. 73)", min_value=0.0, value=float(def_fisc), format="%.2f", disabled=True)
taux_tfpb_actuel = st.sidebar.number_input("Taux communal Taxe Foncière TFPB (%)", min_value=1.0, max_value=80.0, value=38.50, format="%.2f", disabled=True)
dot_eur = st.sidebar.number_input("Dotations & DGF (Chap. 74)", min_value=0.0, value=float(def_dot), format="%.2f", disabled=True)
serv_eur = st.sidebar.number_input("Produits des services & autres (70/75)", min_value=0.0, value=float(def_serv), format="%.2f", disabled=True)
rrf_eur = fisc_eur + dot_eur + serv_eur
rendement_1pt_tfpb = ((fisc_eur * 0.65) / taux_tfpb_actuel) / 1e6 if taux_tfpb_actuel > 0 else 0.0
st.sidebar.caption(f"RRF : **{rrf_eur / 1e6:.2f} M€** • +1 pt TFPB = **+{rendement_1pt_tfpb:.2f} M€/an**")

ch012_eur = st.sidebar.number_input("Masse Salariale (Chap. 012)", min_value=0.0, value=float(def_012), format="%.2f", disabled=True)
ch011_eur = st.sidebar.number_input("Charges générales (Chap. 011)", min_value=0.0, value=float(def_011), format="%.2f", disabled=True)
ch65_eur = st.sidebar.number_input("Gestion & Subventions (Chap. 65)", min_value=0.0, value=float(def_65), format="%.2f", disabled=True)
ch661_eur = st.sidebar.number_input("Intérêts de la dette (Chap. 661)", min_value=0.0, value=float(def_661), format="%.2f", disabled=True)

st.sidebar.markdown("### 2. Dette, Trésorerie & Satellites (Prérempli)")
cap16_eur = st.sidebar.number_input("Remboursement capital dette (Chap. 16)", min_value=0.0, value=float(def_16), format="%.2f", disabled=True)
dette_eur = st.sidebar.number_input("Encours de dette directe au 31/12 (€)", min_value=0.0, value=float(def_dette), format="%.2f", disabled=True)

cap16_def_m = round(cap16_eur / 1e6, 2)
amort_hist_profil = [cap16_def_m] * 5

dette_garantie_eur = st.sidebar.number_input("Encours de dette garantie satellites (€)", min_value=0.0, value=float(def_dette_gar), format="%.2f", disabled=True)
subv_satellites_eur = st.sidebar.number_input("Subventions CCAS / Satellites (dont Chap. 65)", min_value=0.0, value=float(def_subv_sat), format="%.2f", disabled=True)
frng_init_eur = st.sidebar.number_input("Fonds de Roulement initial — FRNG (€)", min_value=0.0, value=float(def_frng), format="%.2f", disabled=True)
rar_init_eur = st.sidebar.number_input("Restes à Réaliser d'investissement — RAR (€)", min_value=0.0, value=float(def_rar), format="%.2f", disabled=True)
equip_brut_eur = st.sidebar.number_input("Dépenses d'équipement brut N (€)", min_value=0.0, value=float(def_equip), format="%.2f", disabled=True)

st.sidebar.markdown("### 3. Démographie, RH & Contexte (Prérempli)")
population = st.sidebar.number_input("Population DGF actuelle (habitants)", min_value=1, value=int(def_pop), disabled=True)
normes_strate = get_normes_strate(population)
st.sidebar.caption(f"Strate DGCL : **{normes_strate['strate_nom']}**")
effectifs_etp = st.sidebar.number_input("Effectifs rémunérés (ETP)", min_value=1, value=int(def_etp), disabled=True)
friction_cfc = st.sidebar.number_input("Coefficient de friction CFC (BTP)", min_value=1.00, max_value=2.00, value=1.28, format="%.2f", disabled=True)

# Conversions en € et M€
drf_eur = ch012_eur + ch011_eur + ch65_eur + ch661_eur
rrf_m = rrf_eur / 1e6
ch012_m = ch012_eur / 1e6
ch011_m = ch011_eur / 1e6
ch65_m = ch65_eur / 1e6
ch661_m = ch661_eur / 1e6
drf_m = ch012_m + ch011_m + ch65_m + ch661_m
cap16_m = cap16_eur / 1e6
dette_m = dette_eur / 1e6
dette_garantie_m = dette_garantie_eur / 1e6
subv_satellites_m = subv_satellites_eur / 1e6
frng_init_m = frng_init_eur / 1e6
rar_init_m = rar_init_eur / 1e6

eb_m = rrf_m - drf_m
en_m = eb_m - cap16_m
taux_eb = (eb_m / rrf_m * 100) if rrf_m > 0 else 0.0
taux_en = (en_m / rrf_m * 100) if rrf_m > 0 else 0.0
iib = ((ch012_m + ch65_m + ch661_m + cap16_m) / rrf_m * 100) if rrf_m > 0 else 0.0
cap_desend = (dette_m / eb_m) if eb_m > 0 else 99.9
taux_endettement = (dette_m / rrf_m * 100) if rrf_m > 0 else 0.0
taux_endettement_consolide = ((dette_m + dette_garantie_m) / rrf_m * 100) if rrf_m > 0 else 0.0
jours_treso_init = int(round((frng_init_m / drf_m) * 365)) if drf_m > 0 else 0
taux_encadrement = (effectifs_etp / population) * 1000.0
duree_res_hist = round(min(20.0, max(8.0, (dette_m / cap16_m) if cap16_m > 0 else 14.0)), 1)
pic_dette_info = None

# Données rétrospectives préremplies
annees_retro = ["2021", "2022", "2023", "2024", "2025"]
rrf_hist = [round(rrf_m * 0.87, 2), round(rrf_m * 0.91, 2), round(rrf_m * 0.94, 2), round(rrf_m * 0.97, 2), round(rrf_m, 2)]
drf_hist = [round(drf_m * 0.80, 2), round(drf_m * 0.84, 2), round(drf_m * 0.90, 2), round(drf_m * 0.95, 2), round(drf_m, 2)]
ms_hist = [round(ch012_m * 0.81, 2), round(ch012_m * 0.85, 2), round(ch012_m * 0.91, 2), round(ch012_m * 0.96, 2), round(ch012_m, 2)]
eb_hist = [round(r - d, 2) for r, d in zip(rrf_hist, drf_hist)]
en_hist = [round(e - cap16_m, 2) for e in eb_hist]
equip_m = equip_brut_eur / 1e6
equip_hist = [round(equip_m * 0.70, 2), round(equip_m * 0.85, 2), round(equip_m * 0.92, 2), round(equip_m * 0.98, 2), round(equip_m, 2)]
subv_hist = [round(e * 0.35, 2) for e in equip_hist]
fctva_hist = [round(e * 0.14, 2) for e in equip_hist]
cess_hist = [0.0, 0.5, 0.0, 1.2, 0.0]

emprunt_hist = [max(0.0, e - en - s - f - c) for e, en, s, f, c in zip(equip_hist, en_hist, subv_hist, fctva_hist, cess_hist)]
n_intervalles = max(1, len(annees_retro) - 1)
tcma_rrf = ((rrf_hist[-1] / rrf_hist[0]) ** (1 / n_intervalles) - 1) * 100 if rrf_hist[0] > 0 else 0.0
tcma_drf = ((drf_hist[-1] / drf_hist[0]) ** (1 / n_intervalles) - 1) * 100 if drf_hist[0] > 0 else 0.0
tcma_ms = ((ms_hist[-1] / ms_hist[0]) ** (1 / n_intervalles) - 1) * 100 if ms_hist[0] > 0 else 0.0
poids_ms_rrf = (ch012_m / rrf_m * 100) if rrf_m > 0 else 0.0
delta_eb_5ans = eb_hist[-1] - eb_hist[0]

# ==========================================
# 2. EN-TÊTE EXÉCUTIF, LEXIQUE & LIVRABLES PDF
# ==========================================
col_titre, col_lex, col_btn1, col_btn2, col_btn3 = st.columns([2.7, 1.0, 1.05, 1.05, 1.15])

with col_titre:
    st.title("Archétype Cadrage — Démonstration")
    st.caption(f"Cas fictif : {collectivite} ({normes_strate['strate_nom']}) • Cliquez sur ℹ️ pour les normes.")

with col_lex:
    st.write("")
    with st.popover("📖 Lexique M57", use_container_width=True):
        st.markdown(f"## 📖 Guide Pédagogique & Normes ({normes_strate['strate_court']})")
        st.caption(f"Référentiel calibré sur la strate DGCL : **{normes_strate['strate_nom']}**.")
        st.markdown("---")
        st.markdown("### 1. Les grands soldes (Le compte de résultat)")
        st.markdown(f"""
- **RRF (Recettes Réelles de Fonctionnement) :** L'argent qui rentre chaque année pour faire tourner la mairie (impôts locaux, dotations de l'État, cantine, périscolaire). Moyenne de strate : **{normes_strate['r3_rrf_hab']} €/hab**.
- **DRF (Dépenses Réelles de Fonctionnement) :** Les dépenses courantes obligatoires (salaires des agents, électricité, entretien, subventions aux associations, intérêts des emprunts). Moyenne de strate : **{normes_strate['r1_drf_hab']} €/hab**.
- **Épargne Brute (ou CAF) :** `RRF - DRF`. C'est l'excédent dégagé par la gestion courante. Moyenne de strate : **{normes_strate['taux_eb']:.1f} % des RRF** | **Norme de sécurité : > 10 %** (alerte sous 7 %).
- **Épargne Nette :** `Épargne Brute - Remboursement du capital de la dette (Chap. 16)`. C'est la vraie cagnotte disponible pour payer les nouveaux investissements sans emprunter.
        """)
        st.markdown("### 2. Les 4 ratios surveillés par le Préfet et les banques")
        st.markdown(f"""
- **Taux d'endettement (Ratio R11) :** `Encours de dette / RRF`. Mesure le poids de la dette par rapport aux recettes annuelles. **Moyenne de votre strate : {normes_strate['taux_endettement']:.0f} % | Vigilance : > 90 % | Alerte : > 100 %**.
- **Capacité de désendettement :** `Encours de dette / Épargne Brute`. Nombre d'années théoriques pour rembourser toute la dette. **Moyenne de votre strate : {normes_strate['cap_desend']:.1f} ans | Alerte : 10 ans | Seuil critique CRC / Refus de prêt : > 12 ans.**
- **Indice d'Inflexibilité Budgétaire (IIB) :** Part des dépenses impossibles à couper à court terme (salaires + subventions + dette). **Moyenne de votre strate : {normes_strate['iib']:.0f} % | Vigilance : 75 % | Critique : > 85 %.**
- **Disponibilités de trésorerie (Compte 515) :** Nombre de jours de DRF couverts par la trésorerie nette disponible. **Équilibre normal : 15 à 25 jours | Vigilance : 10 à 15 jours | Alerte liquidité : < 10 jours**.
        """)

pdf_retro_bytes = build_retro_pdf(
    collectivite, annees_retro, rrf_hist, drf_hist, ms_hist, eb_hist, en_hist,
    tcma_rrf, tcma_drf, tcma_ms, poids_ms_rrf, delta_eb_5ans,
    equip_hist, subv_hist, fctva_hist, cess_hist, population, normes_strate
)

with col_btn1:
    st.write("")
    st.download_button(
        "📄 Spécimen Rétro (2 p.)",
        data=pdf_retro_bytes,
        file_name="Specimen_Demo_Dossier_Retro.pdf",
        mime="application/pdf",
        use_container_width=True
    )

# ==========================================
# 3. ONGLETS PRINCIPAUX DE L'APPLICATION
# ==========================================
st.markdown("""
<style>
div[data-baseweb="tab-list"] {
    flex-wrap: wrap !important;
    gap: 4px 14px !important;
}
</style>
""", unsafe_allow_html=True)

onglets = st.tabs([
    "📊 Rétrospective",
    "⚖️ TBI-F Exécutif",
    "🔮 Prospective 2026-2030",
    "🏛️ Pilotage DGS",
    "📝 Rédaction ROB"
])

# ------------------------------------------
# ONGLET 1 : RÉTROSPECTIVE (2021-2025)
# ------------------------------------------
with onglets[0]:
    h_r1, h_r2 = st.columns([0.92, 0.08])
    with h_r1:
        st.subheader("Indicateurs clés de la trajectoire passée")
    with h_r2:
        fiche_pedagogique(
            "ℹ️",
            "TCMA & Effet de Ciseau",
            "Le TCMA (Taux de Croissance Annuel Moyen) mesure la vitesse moyenne à laquelle augmentent les recettes et les dépenses chaque année.",
            "Effet de ciseau = TCMA Dépenses (DRF) - TCMA Recettes (RRF)",
            [
                "Trajectoire saine : Recettes ≥ Dépenses (écart nul ou positif).",
                "Alerte ciseau : Lorsque les dépenses augmentent plus vite que les recettes pendant plus de 2 ans, l'épargne fond mécaniquement."
            ],
            "Si le ciseau n'est pas refermé, la ville devra soit augmenter les impôts, soit réduire ses projets d'investissement."
        )

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("TCMA Recettes (RRF)", f"+{tcma_rrf:.2f} % / an")
    k2.metric(
        "TCMA Dépenses (DRF)",
        f"+{tcma_drf:.2f} % / an",
        f"{tcma_drf - tcma_rrf:+.2f} pts vs RRF",
        delta_color="inverse"
    )
    k3.metric(
        "TCMA Masse Salariale",
        f"+{tcma_ms:.2f} % / an",
        f"Poids final : {poids_ms_rrf:.1f}% des RRF",
        delta_color="inverse"
    )
    k4.metric(
        "Évolution Épargne Brute",
        f"{eb_m:.1f} M€",
        f"{delta_eb_5ans:+.1f} M€",
        delta_color="normal" if delta_eb_5ans >= 0 else "inverse"
    )

    st.divider()

    g1, g2 = st.columns(2)
    with g1:
        st.subheader("1. Effet de ciseau historique")
        df_ciseau_hist = pd.DataFrame({
            "Exercice": annees_retro,
            "Recettes (RRF)": rrf_hist,
            "Dépenses (DRF)": drf_hist
        }).set_index("Exercice")
        st.line_chart(df_ciseau_hist)

    with g2:
        st.subheader("2. Érosion de l'Épargne Brute & Nette")
        df_erosion = pd.DataFrame({
            "Exercice": annees_retro,
            "Épargne Brute (M€)": eb_hist,
            "Épargne Nette (M€)": en_hist
        }).set_index("Exercice")
        st.line_chart(df_erosion)

    st.divider()
    inv_t1, inv_t2 = st.columns([0.92, 0.08])
    with inv_t1:
        st.subheader("3. Rétrospective de l'Investissement & Mix de Financement")
    with inv_t2:
        fiche_pedagogique(
            "ℹ️",
            "Bouclage financier de l'investissement",
            "Ce graphique détaille comment la collectivité a payé ses travaux (équipements bruts) au fil des années.",
            "Recours à l'emprunt = Équipements bruts - (Épargne Nette + Subventions + FCTVA + Cessions)",
            [
                "Taux de cofinancement : part des travaux couverte par des aides externes (subventions + FCTVA). L'objectif est d'atteindre 50 à 60 %.",
                f"Effort d'équipement : en moyenne {normes_strate['r4_equip_hab']} € par an et par habitant pour la strate de votre commune."
            ],
            "Une barre rouge (Emprunt/Trésorerie) importante signifie que la commune n'a pas dégagé assez d'épargne nette et/ou n'a pas obtenu assez de subventions pour financer ses projets."
        )

    inv_c1, inv_c2 = st.columns([1, 1.6])
    moy_equip = sum(equip_hist) / len(equip_hist) if equip_hist else 0
    moy_subv = (sum(subv_hist) + sum(fctva_hist)) / sum(equip_hist) * 100 if sum(equip_hist) > 0 else 0
    ratio_equip_hab = int(round((moy_equip * 1e6) / population))

    with inv_c1:
        st.markdown("#### 🏗️ Diagnostic de l'effort d'équipement")
        st.info(
            f"* **Enveloppe moyenne exécutée :** **{moy_equip:.1f} M€ / an** sur la période.\n"
            f"* **Effort par habitant :** **{ratio_equip_hab} € / hab.** (Moyenne strate : {normes_strate['r4_equip_hab']} €).\n"
            f"* **Taux de cofinancement (Subventions + FCTVA) :** **{moy_subv:.1f} %** en moyenne.\n"
            f"* **Recours résiduel à l'emprunt / Trésorerie :** **{sum(emprunt_hist):.1f} M€** au total sur 5 ans."
        )
    with inv_c2:
        df_mix = pd.DataFrame({
            "Exercice": annees_retro,
            "Épargne Nette": en_hist,
            "Subventions": subv_hist,
            "FCTVA": fctva_hist,
            "Cessions": cess_hist,
            "Emprunt / Trésorerie": emprunt_hist
        }).set_index("Exercice")
        st.bar_chart(df_mix, color=["#059669", "#2563eb", "#3b82f6", "#d97706", "#dc2626"])

    st.divider()
    rh_t1, rh_t2 = st.columns([0.92, 0.08])
    with rh_t1:
        st.subheader("4. Décomposition de la dérive RH & Levier Managérial")
    with rh_t2:
        fiche_pedagogique(
            "ℹ️",
            "Comprendre l'évolution de la Masse Salariale (Chap. 012)",
            "La masse salariale augmente pour trois raisons distinctes : deux sont imposées de l'extérieur, une seule dépend des décisions de la mairie.",
            "Évolution 012 = GVT + Mesures d'État + Effet Volume",
            [
                "1. GVT (Glissement Vieillesse Technicité) : ~1,2 %/an automatique lié à l'ancienneté et aux avancements d'échelon.",
                "2. Mesures d'État : revalorisation nationale du point d'indice, Ségur, hausses des cotisations.",
                "3. Effet Volume (Levier local) : créations de postes, remplacement des départs, heures supplémentaires et primes (RIFSEEP).",
                f"Norme de votre strate ({normes_strate['strate_court']}) : la masse salariale représente en moyenne {normes_strate['r7_012_drf']:.1f} % des dépenses de fonctionnement."
            ],
            "On ne peut pas agir sur le GVT ni sur les décisions de l'État : tout l'enjeu du pacte RH consiste à piloter l'effet volume."
        )

    rh_col1, rh_col2 = st.columns([1, 1.35])
    with rh_col1:
        gvt_pts = 1.2
        etat_pts = 0.6
        volume_pts = max(0.0, round(tcma_ms - (gvt_pts + etat_pts), 1))
        df_rh_decomp = pd.DataFrame({
            "Facteur": [
                "1. GVT (Ancienneté / Technicité)",
                "2. Mesures d'État (Point d'indice / Ségur)",
                "3. Effet Volume (Recrutements / Primes)"
            ],
            "Points (% / an)": [gvt_pts, etat_pts, volume_pts]
        }).set_index("Facteur")
        st.bar_chart(df_rh_decomp, horizontal=True, color="#d97706")

    with rh_col2:
        st.markdown("#### 📌 Levier Managérial vs Facteurs Subis")
        st.info(
            f"**Sur les +{tcma_ms:.1f} % / an de dérive de la masse salariale constatée :**\n\n"
            f"* **{gvt_pts + etat_pts:.1f} points sont incompressibles et subis** (GVT mécanique + hausses statutaires décidées par l'État).\n"
            f"* **{volume_pts:.1f} points seulement relèvent du levier managérial local** (créations nettes de postes, vacataires et heures supplémentaires).\n\n"
            "**↳ Recommandation pour l'arbitrage :** Le pacte RH doit cibler cet effet volume (non-remplacement partiel des départs à la retraite et encadrement des compléments indemnitaires)."
        )

    st.divider()
    st.subheader("⚖️ Bilan Stratégique : Atouts & Pistes d'Investigation Chiffrées")

    eco_1pct_011 = int(round(ch011_m * 10))
    eco_05pt_012 = int(round(ch012_m * 5))
    b1, b2 = st.columns(2)
    with b1:
        st.markdown("#### 🟢 Atouts & Marges de Manœuvre")
        st.success(f"**Dynamisme des ressources :** Recettes en croissance de **+{tcma_rrf:.1f} % / an** (+{(rrf_hist[-1]-rrf_hist[0]):.1f} M€ sur la période), offrant une assiette fiscale porteuse.")
        if eb_m > 0:
            st.success(f"**Autofinancement maintenu :** **{eb_m:.2f} M€** d'épargne brute dégagée sur le dernier exercice clos, permettant d'amorcer la PPI sans rupture immédiate.")
        else:
            st.warning(f"**Alerte structurelle :** L'épargne brute est négative (**{eb_m:.2f} M€**) ; un plan de redressement immédiat est indispensable.")

    with b2:
        st.markdown("#### 🔴 Points de Vigilance & Gains d'Audit Potentiels")
        st.warning(
            f"**Ciseau budgétaire ({tcma_drf - tcma_rrf:+.2f} pts/an) :** Dépenses (+{tcma_drf:.1f}%/an) > Recettes (+{tcma_rrf:.1f}%/an).\n\n"
            f"**↳ Action chiffrée :** Chaque **1 % d'économie** sur les achats et fluides (Chap. 011) dégage **{eco_1pct_011} k€/an** d'épargne nette supplémentaire."
        )
        st.warning(
            f"**Rigidité salariale ({poids_ms_rrf:.1f} % des RRF) :** La masse salariale atteint **{ch012_m:.2f} M€**.\n\n"
            f"**↳ Action chiffrée :** Freiner de **0,5 point** le glissement volume (RIFSEEP / remplacements) économise **{eco_05pt_012} k€/an** dès la première année."
        )

# ------------------------------------------
# ONGLET 2 : TBI-F EXÉCUTIF
# ------------------------------------------
with onglets[1]:
    sig_t1, sig_t2 = st.columns([0.92, 0.08])
    with sig_t1:
        st.subheader("1. Formation de l'Épargne — Soldes Intermédiaires de Gestion (M57)")
    with sig_t2:
        fiche_pedagogique(
            "ℹ️",
            "La cascade de l'Épargne (SIG M57)",
            "Ce tableau montre comment se forme la capacité d'autofinancement de la collectivité, étape par étape, comme un compte de résultat.",
            "RRF - DRF = Épargne Brute (CAF)  |  Épargne Brute - Capital Dette (Chap. 16) = Épargne Nette",
            [
                f"Taux d'Épargne Brute (Épargne Brute / RRF) : Moyenne de votre strate ({normes_strate['strate_court']}) = {normes_strate['taux_eb']:.1f} % | Norme de sécurité > 10 % | Vulnérabilité < 7 %.",
                "Épargne Nette : doit impérativement rester positive (> 0 M€). Si elle devient négative, la mairie emprunte pour rembourser ses anciens emprunts (situation de rupture)."
            ],
            "L'Épargne Nette est le premier euro disponible pour financer les nouveaux projets d'investissement."
        )

    df_sig = pd.DataFrame([
        {
            "Soldes Intermédiaires de Gestion (SIG M57)": "+ Recettes Réelles de Fonctionnement (RRF)",
            "Montant": f"{rrf_m:.2f} M€",
            "% des RRF": "100.0 %",
            "Lecture Stratégique & Prudentielle": f"Fiscalité ({fisc_eur/1e6:.1f} M€), Dotations ({dot_eur/1e6:.1f} M€), Services ({serv_eur/1e6:.1f} M€)"
        },
        {
            "Soldes Intermédiaires de Gestion (SIG M57)": "- Dépenses Réelles de Fonctionnement (DRF)",
            "Montant": f"- {drf_m:.2f} M€",
            "% des RRF": f"{(drf_m / rrf_m * 100):.1f} %",
            "Lecture Stratégique & Prudentielle": "Charges courantes de gestion, masse salariale et intérêts de la dette"
        },
        {
            "Soldes Intermédiaires de Gestion (SIG M57)": "= Épargne de Gestion / Épargne Brute (CAF)",
            "Montant": f"{eb_m:.2f} M€",
            "% des RRF": f"{taux_eb:.1f} %",
            "Lecture Stratégique & Prudentielle": f"Moyenne strate ({normes_strate['strate_court']}) : {normes_strate['taux_eb']:.1f} % | Seuil prudentiel : > 10,0 %"
        },
        {
            "Soldes Intermédiaires de Gestion (SIG M57)": "- Remboursement du capital de la dette (Chapitre 16)",
            "Montant": f"- {cap16_m:.2f} M€",
            "% des RRF": f"{(cap16_m / rrf_m * 100):.1f} %",
            "Lecture Stratégique & Prudentielle": f"Amortissement annuel (durée résiduelle estimée du stock : {duree_res_hist:.1f} ans)"
        },
        {
            "Soldes Intermédiaires de Gestion (SIG M57)": "= Épargne Nette (Autofinancement disponible pour la PPI)",
            "Montant": f"{en_m:.2f} M€",
            "% des RRF": f"{taux_en:.1f} %",
            "Lecture Stratégique & Prudentielle": "Autofinancement net résiduel avant FCTVA, subventions et cessions"
        }
    ])
    st.dataframe(df_sig, hide_index=True, use_container_width=True)

    st.divider()

    col_drf, col_rat = st.columns([1.05, 1.15])

    with col_drf:
        drf_h1, drf_h2 = st.columns([0.85, 0.15])
        with drf_h1:
            st.subheader("2. Structure des Dépenses (DRF)")
        with drf_h2:
            fiche_pedagogique(
                "ℹ️",
                "Les 4 chapitres des dépenses courantes (M57)",
                "Chaque dépense de fonctionnement est classée dans un chapitre normalisé au niveau national.",
                "DRF = Chap. 011 + Chap. 012 + Chap. 65 + Chap. 661",
                [
                    "Chap. 011 (Charges générales) : eau, électricité, carburant, fournitures, entretien (~22 % des DRF en moyenne).",
                    f"Chap. 012 (Personnel) : salaires et charges sociales (moyenne de votre strate : {normes_strate['r7_012_drf']:.1f} % des DRF).",
                    "Chap. 65 (Gestion courante) : subventions aux associations, au CCAS, indemnités des élus (~15 %).",
                    "Chap. 661 (Frais financiers) : intérêts payés aux banques sur la dette (~3 %)."
                ],
                "Les économies rapides à court terme se cherchent d'abord sur le Chapitre 011 (renégociation de contrats, sobriété énergétique)."
            )

        df_struct = pd.DataFrame({
            "Chapitre M57": [
                "Chap. 011 — Charges à caractère général",
                "Chap. 012 — Personnel et frais assimilés",
                "Chap. 65 — Gestion courante & subventions",
                "Chap. 661 — Intérêts de la dette"
            ],
            "Part DRF (%)": [
                round(ch011_m / drf_m * 100, 1) if drf_m > 0 else 0.0,
                round(ch012_m / drf_m * 100, 1) if drf_m > 0 else 0.0,
                round(ch65_m / drf_m * 100, 1) if drf_m > 0 else 0.0,
                round(ch661_m / drf_m * 100, 1) if drf_m > 0 else 0.0
            ]
        }).set_index("Chapitre M57")
        st.bar_chart(df_struct, horizontal=True)

    with col_rat:
        rat_h1, rat_h2 = st.columns([0.85, 0.15])
        with rat_h1:
            st.subheader(f"3. Ratios & Normes ({normes_strate['strate_court']})")
        with rat_h2:
            fiche_pedagogique(
                "ℹ️",
                f"Les seuils d'alerte & moyennes de votre strate ({normes_strate['strate_nom']})",
                "Ces 4 indicateurs mesurent la rigidité budgétaire et la solvabilité de la commune comparée aux collectivités françaises de même taille.",
                "Taux d'endettement (R11) = Dette / RRF  |  Désendettement = Dette / Épargne Brute",
                [
                    f"Indice d'Inflexibilité (IIB) : Moyenne strate {normes_strate['iib']:.0f} % | Vigilance > 75 % | Critique > 85 %.",
                    f"Taux d'endettement (R11) : Moyenne strate {normes_strate['taux_endettement']:.0f} % | Vigilance > 90 % | Alerte > 100 %.",
                    f"Capacité de désendettement : Moyenne strate {normes_strate['cap_desend']:.1f} ans | Alerte > 10 ans | Seuil critique CRC > 12 ans.",
                    "FRNG & Disponibilités : un FRNG sain couvre > 30 jours de DRF ; les disponibilités nettes courantes se situent entre 15 et 25 jours."
                ],
                "Grâce au versement mensuel par douzièmes de la fiscalité et de la DGF, une commune n'a pas besoin de conserver plus de 15 à 25 jours de cash dormant."
            )

        with st.container(border=True):
            r_top1, r_top2 = st.columns(2)
            r_top1.metric(
                "Indice Inflexibilité (IIB)",
                f"{iib:.1f} %",
                f"Strate : {normes_strate['iib']:.0f}% | Critique > 85%",
                delta_color="normal" if iib <= 85 else "inverse"
            )
            r_top2.metric(
                "Capacité Désendettement",
                f"{cap_desend:.1f} ans",
                f"Strate : {normes_strate['cap_desend']:.1f}a | Alerte > 10a",
                delta_color="inverse" if cap_desend > 10 else "normal"
            )

            st.progress(min(1.0, max(0.0, iib / 100.0)))

            r_bot1, r_bot2 = st.columns(2)
            r_bot1.metric(
                "Taux d'Endettement (Direct / Consol.)",
                f"{taux_endettement:.1f}% / {taux_endettement_consolide:.1f}%",
                f"Strate : {normes_strate['taux_endettement']:.0f}% | Alerte > 100%",
                delta_color="inverse" if taux_endettement > 100 else "normal"
            )
            r_bot2.metric(
                "FRNG & Couverture DRF",
                f"{frng_init_m:.2f} M€ ({jours_treso_init} j)",
                f"FRNG cible > 30 j | Disp. tréso : 15-25 j"
            )

    st.divider()
    cgct_h1, cgct_h2 = st.columns([0.92, 0.08])
    with cgct_h1:
        st.subheader(f"4. Ratios Réglementaires M57 (Art. L. 2313-1 CGCT) — Strate : {normes_strate['strate_nom']}")
    with cgct_h2:
        fiche_pedagogique(
            "ℹ️",
            "Les 9 ratios obligatoires du Code Général des Collectivités (CGCT)",
            "La loi oblige les communes de plus de 3 500 habitants à publier ces ratios dans leur budget et compte administratif pour se comparer aux villes de même strate démographique.",
            "Comparaison automatique aux moyennes DGCL de votre strate",
            [
                f"Strate appliquée automatiquement ({population:,} hab.) : {normes_strate['strate_nom']}.".replace(",", " "),
                "Ratio R11 (Taux d'endettement) : rapporte l'encours de dette au 31/12 aux recettes réelles de fonctionnement (RRF).",
                "Ratio R9 (< 93-94 % en moyenne) : mesure la part des recettes absorbée par le fonctionnement et le remboursement de la dette."
            ],
            "Ces écarts permettent d'objectiver les marges de manœuvre fiscales ou les surcoûts structurels devant l'assemblée délibérante."
        )

    r1_val = int(round(drf_eur / population))
    r2_val = int(round(fisc_eur / population))
    r3_val = int(round(rrf_eur / population))
    r4_val = int(round(equip_brut_eur / population))
    r5_val = int(round(dette_eur / population))
    r6_val = int(round(dot_eur / population))
    r7_val = round((ch012_m / drf_m * 100) if drf_m > 0 else 0.0, 1)
    r9_val = round(((drf_m + cap16_m) / rrf_m * 100) if rrf_m > 0 else 0.0, 1)
    r11_val = round(taux_endettement, 1)

    df_cgct = pd.DataFrame([
        {
            "Code": "R1",
            "Libellé Officiel M57": "Dépenses réelles de fonctionnement / Population",
            "Valeur Commune": f"{r1_val:,} € / hab".replace(",", " "),
            f"Moyenne Strate ({normes_strate['strate_court']})": f"{normes_strate['r1_drf_hab']:,} € / hab".replace(",", " "),
            "Écart vs Strate": f"{r1_val - normes_strate['r1_drf_hab']:+d} € / hab"
        },
        {
            "Code": "R2",
            "Libellé Officiel M57": "Produit des impositions directes / Population",
            "Valeur Commune": f"{r2_val:,} € / hab".replace(",", " "),
            f"Moyenne Strate ({normes_strate['strate_court']})": f"{normes_strate['r2_fisc_hab']:,} € / hab".replace(",", " "),
            "Écart vs Strate": f"{r2_val - normes_strate['r2_fisc_hab']:+d} € / hab"
        },
        {
            "Code": "R3",
            "Libellé Officiel M57": "Recettes réelles de fonctionnement / Population",
            "Valeur Commune": f"{r3_val:,} € / hab".replace(",", " "),
            f"Moyenne Strate ({normes_strate['strate_court']})": f"{normes_strate['r3_rrf_hab']:,} € / hab".replace(",", " "),
            "Écart vs Strate": f"{r3_val - normes_strate['r3_rrf_hab']:+d} € / hab"
        },
        {
            "Code": "R4",
            "Libellé Officiel M57": "Dépenses d'équipement brut / Population",
            "Valeur Commune": f"{r4_val:,} € / hab".replace(",", " "),
            f"Moyenne Strate ({normes_strate['strate_court']})": f"{normes_strate['r4_equip_hab']:,} € / hab".replace(",", " "),
            "Écart vs Strate": f"{r4_val - normes_strate['r4_equip_hab']:+d} € / hab"
        },
        {
            "Code": "R5",
            "Libellé Officiel M57": "Encours de dette / Population",
            "Valeur Commune": f"{r5_val:,} € / hab".replace(",", " "),
            f"Moyenne Strate ({normes_strate['strate_court']})": f"{normes_strate['r5_dette_hab']:,} € / hab".replace(",", " "),
            "Écart vs Strate": f"{r5_val - normes_strate['r5_dette_hab']:+d} € / hab"
        },
        {
            "Code": "R6",
            "Libellé Officiel M57": "Dotation Globale de Fonctionnement & Dotations / Population",
            "Valeur Commune": f"{r6_val:,} € / hab".replace(",", " "),
            f"Moyenne Strate ({normes_strate['strate_court']})": f"{normes_strate['r6_dot_hab']:,} € / hab".replace(",", " "),
            "Écart vs Strate": f"{r6_val - normes_strate['r6_dot_hab']:+d} € / hab"
        },
        {
            "Code": "R7",
            "Libellé Officiel M57": "Dépenses de personnel / Dépenses réelles de fonctionnement",
            "Valeur Commune": f"{r7_val:.1f} %",
            f"Moyenne Strate ({normes_strate['strate_court']})": f"{normes_strate['r7_012_drf']:.1f} %",
            "Écart vs Strate": f"{r7_val - normes_strate['r7_012_drf']:+.1f} pts"
        },
        {
            "Code": "R9",
            "Libellé Officiel M57": "DRF + remboursement annuel de la dette / RRF",
            "Valeur Commune": f"{r9_val:.1f} %",
            f"Moyenne Strate ({normes_strate['strate_court']})": f"{normes_strate['r9_rigidite']:.1f} %",
            "Écart vs Strate": f"{r9_val - normes_strate['r9_rigidite']:+.1f} pts"
        },
        {
            "Code": "R11",
            "Libellé Officiel M57": "Taux d'endettement (Encours de dette / RRF)",
            "Valeur Commune": f"{r11_val:.1f} %",
            f"Moyenne Strate ({normes_strate['strate_court']})": f"{normes_strate['taux_endettement']:.1f} % (Alerte > 100%)",
            "Écart vs Strate": f"{r11_val - normes_strate['taux_endettement']:+.1f} pts"
        }
    ])
    st.dataframe(df_cgct, hide_index=True, use_container_width=True)

    st.markdown("#### 🎯 Préconisations Immédiates sur l'Exercice en Cours")
    if taux_eb < 8.0 or cap_desend > 10.0 or taux_endettement > 100.0:
        st.warning(
            f"**Reconstitution prioritaire de l'épargne brute (actuellement {taux_eb:.1f} % vs moyenne strate {normes_strate['taux_eb']:.1f} % et norme de sécurité > 10 %) :**\n\n"
            f"* **Cible budgétaire :** Il manque **{max(0.0, (0.10 * rrf_m) - eb_m):.2f} M€** d'épargne brute annuelle pour atteindre le standard prudentiel de 10 %.\n"
            f"* **Action n°1 (Recettes) :** Réviser les grilles tarifaires des services publics (périscolaire, restauration, occupation du domaine public) et sécuriser les bases fiscales (+1 pt TFPB = **+{rendement_1pt_tfpb:.2f} M€/an**).\n"
            f"* **Action n°2 (Dépenses) :** Geler 3 % des crédits non engagés du Chapitre 011 (**{int(round(ch011_m * 30))} k€**) en réserve de précaution jusqu'au Budget Supplémentaire."
        )
    else:
        st.success(
            f"**Consolidation d'un socle financier sain (Épargne brute à {taux_eb:.1f} %, Taux d'endettement à {taux_endettement:.1f} % vs strate {normes_strate['taux_endettement']:.0f} %, Désendettement à {cap_desend:.1f} ans) :**\n\n"
            f"* **Action n°1 (Optimisation) :** Affecter en priorité l'épargne nette disponible (**{en_m:.2f} M€**) au financement des opérations d'investissement non subventionnées afin de limiter le recours à l'emprunt.\n"
            f"* **Action n°2 (Prévention) :** Auditer les contrats pluriannuels du Chapitre 011 et plafonner l'évolution de la masse salariale (Chap. 012) au rythme de croissance des recettes."
        )

# ------------------------------------------
# ONGLET 3 : PROSPECTIVE 2026-2030 (INTERACTIF)
# ------------------------------------------
with onglets[2]:
    pr_h1, pr_h2 = st.columns([0.92, 0.08])
    with pr_h1:
        st.subheader("Modélisation Prospective 2026-2030 — Arbitrage DOB, Plan de Redressement & Dette")
    with pr_h2:
        fiche_pedagogique(
            "ℹ️",
            "Simulateur interactif DOB 2026-2030",
            "Testez librement l'impact des leviers fiscaux, RH, PPI et de dette sur la trajectoire quinquennale de la collectivité fictive.",
            "Annuité Cap. = Amortissement Dette Historique + (Nouveaux emprunts / Maturité AFD-CDC)",
            [
                "Plan d'économies structurelles (%) : applique une coupe nette dès l'exercice 1 sur les charges générales et subventions non obligatoires (Chap. 011 + 65).",
                "Réétalement dette historique : lisse et allonge l'échéancier de la dette existante sur +7 ans (plafonné à 22 ans), avec prise en compte d'un surcoût de taux de +0,25 pt.",
                "Cessions patrimoniales (Chap. 024) : ventes de terrains ou immeubles injectant du cash direct en investissement sans recourir à l'emprunt."
            ],
            "Basculez entre les 3 scénarios préconfigurés ou ajustez manuellement les curseurs ci-dessous."
        )

    scenario_choisi = st.radio(
        "Sélecteur rapide de scénario pour le Débat d'Orientation Budgétaire (DOB) :",
        [
            "Scénario 3 : Cible Optimisée / Plan de Redressement (Trajectoire verte calibrée)",
            "Scénario 1 : Fil de l'eau (Tendanciel sans mesure correctrice)",
            "Scénario 2 : PPI Intégrale (Sur-investissement sans pacte de gestion)"
        ],
        horizontal=True
    )

    en_crise_grave = (eb_m <= 0 or taux_eb < 4.5 or cap_desend > 13.0)
    en_tension_init = (taux_eb < 8.0 or cap_desend > 10.0)

    ppi_sc1 = round(max(0.5, rrf_m * 0.195), 1)
    ppi_sc2 = round(max(1.0, rrf_m * 0.295), 1)

    if en_crise_grave:
        ppi_sc3 = round(max(0.3, rrf_m * 0.11), 1)
        tfpb_sc3 = 3.0
        ms_sc3, ch011_sc3, eco_sc3 = 1.8, 0.8, 8.0
        reetal_sc3 = True
        cessions_sc3 = round(max(0.2, rrf_m * 0.05), 1)
        subv_sc3, dur_sc3 = 60, 25
    elif en_tension_init:
        ppi_sc3 = round(max(0.5, min(rrf_m * 0.20, max(eb_m, rrf_m * 0.065) * 2.55)), 1)
        tfpb_sc3 = 1.5 if taux_eb >= 5.0 else 2.2
        ms_sc3, ch011_sc3, eco_sc3 = 2.1, 0.9, 2.0
        reetal_sc3 = False
        cessions_sc3 = round(max(0.1, rrf_m * 0.02), 1)
        subv_sc3, dur_sc3 = 55, 25
    else:
        ppi_sc3 = round(max(0.5, min(rrf_m * 0.23, eb_m * 2.05)), 1)
        tfpb_sc3 = 0.0
        ms_sc3, ch011_sc3, eco_sc3 = 2.4, 1.2, 0.0
        reetal_sc3 = False
        cessions_sc3 = 0.0
        subv_sc3, dur_sc3 = 55, 22

    if "Scénario 1" in scenario_choisi:
        p_bases, p_tfpb, p_dot, p_ms, p_011, p_eco, p_ppi, p_exec, p_subv, p_delai, p_dur, p_reetal, p_cess, p_vert = (
            2.8, 0.0, 1.5, 4.2, 2.8, 0.0, ppi_sc1, 75, 35, 16, 15, False, 0.0, 25
        )
        sc_court = "Fil de l'eau"
    elif "Scénario 2" in scenario_choisi:
        p_bases, p_tfpb, p_dot, p_ms, p_011, p_eco, p_ppi, p_exec, p_subv, p_delai, p_dur, p_reetal, p_cess, p_vert = (
            3.0, 0.5, 1.8, 3.8, 2.2, 0.0, ppi_sc2, 80, 40, 15, 18, False, 0.0, 35
        )
        sc_court = "PPI Intégrale"
    else:
        p_bases, p_tfpb, p_dot, p_ms, p_011, p_eco, p_ppi, p_exec, p_subv, p_delai, p_dur, p_reetal, p_cess, p_vert = (
            3.3, tfpb_sc3, 2.2, ms_sc3, ch011_sc3, eco_sc3, ppi_sc3, 80, subv_sc3, 10, dur_sc3, reetal_sc3, cessions_sc3, 45
        )
        sc_court = "Plan Redressement CRC" if en_crise_grave else "Cible Optimisée"

    ppi_min_slider = float(min(0.2, round(rrf_m * 0.03, 1)))
    ppi_max_slider = float(max(30.0, round(rrf_m * 0.50, 0)))
    ppi_step_slider = 0.1 if rrf_m < 15.0 else 0.5
    cess_max_slider = float(max(10.0, round(rrf_m * 0.20, 0)))

    c_sim1, c_sim2, c_sim3 = st.columns(3)
    with c_sim1:
        st.markdown("**1. Fiscalité, Recettes & Démographie**")
        tx_bases_fisc = st.slider("Dynamique naturelle des bases (%)", 0.5, 6.0, float(p_bases), 0.1)
        delta_pts_tfpb = st.slider("Variation taux TFPB mandat (points)", -2.0, 5.0, float(p_tfpb), 0.25,
                                   help=f"1 point de TFPB = {rendement_1pt_tfpb:.2f} M€/an de recettes fiscales supplémentaires.")
        tx_dot_serv = st.slider("Évolution Dotations & Tarifs (%)", 0.0, 5.0, float(p_dot), 0.1)
        tx_pop_proj = st.slider("Croissance démographique annuelle (%)", 0.0, 5.0, 2.5, 0.1)

    with c_sim2:
        st.markdown("**2. Dépenses & Plan d'Économies Structurelles**")
        eco_drf_pct = st.slider("Coupe sèche immédiate 011 & 65 dès N+1 (%)", 0.0, 15.0, float(p_eco), 0.5,
                                help="Baisse structurelle immédiate sur les charges à caractère général et subventions non obligatoires.")
        tx_ms_proj = st.slider("Évolution Masse Salariale 012 (%/an)", 1.0, 6.0, float(p_ms), 0.1)
        tx_011_proj = st.slider("Évolution tendancielle 011 & 65 (%/an)", 0.0, 5.0, float(p_011), 0.1)
        opex_ppi_pct = st.slider("OPEX induits équipements neufs (%/an)", 0.0, 10.0, 3.5, 0.5)
        part_dette_var = st.slider("Part dette à taux variable (%)", 0, 100, 25, 5)
        choc_taux_pts = st.slider("Stress-test hausse des taux (+pts)", 0.0, 3.0, 0.5, 0.25)

    with c_sim3:
        st.markdown("**3. PPI, Cessions & Restructuration Dette**")
        ppi_base_m = st.slider("Enveloppe PPI votée (M€/an)", ppi_min_slider, ppi_max_slider, float(p_ppi), ppi_step_slider)
        tx_realisation_ppi = st.slider("Taux de réalisation annuel PPI (%)", 50, 100, int(p_exec), 5)
        tx_subv_ppi = st.slider("Cofinancements / Subventions (%)", 10, 75, int(p_subv), 5)
        cessions_m = st.slider("Cessions patrimoniales Chap. 024 (M€ sur 5 ans)", 0.0, cess_max_slider, float(p_cess), ppi_step_slider,
                               help="Ventes de terrains ou bâtiments communaux finançant directement la PPI hors emprunt.")
        duree_emprunt_ans = st.slider("Maturité nouveaux prêts AFD/CDC (ans)", 15, 30, int(p_dur), 1)
        delai_subv_mois = st.slider("Délai solde subventions (mois)", 6, 24, int(p_delai), 1)
        part_budget_vert = st.slider("Part Budget Vert / Éco-conditionnalité (%)", 0, 100, int(p_vert), 5)
        reetalement_hist = st.checkbox(
            f"Réétaler la dette historique (durée {duree_res_hist:.0f}a → {min(22.0, duree_res_hist+7.0):.0f}a, +0,25 pt)",
            value=bool(p_reetal),
            help="Lisse et allonge l'échéancier de la dette existante sur +7 ans avec pénalité financière."
        )

    annees_proj = [2026, 2027, 2028, 2029, 2030]
    ppi_reelle_cfc = ppi_base_m * friction_cfc
    plancher_frng = round(drf_m / 12.0, 2)

    rrf_p, drf_p, eb_p, en_p, fctva_p, dette_p, cap_p, frng_p = [], [], [], [], [], [], [], []
    opex_cum_p, ppi_decaisse_p, rar_p, pop_p, drf_hab_p, rrf_hab_p, jours_treso_p = [], [], [], [], [], [], []

    cur_fisc = fisc_eur / 1e6
    cur_dot_serv = (dot_eur + serv_eur) / 1e6
    cur_012 = ch012_m
    cur_autres = (ch011_m + ch65_m) * (1.0 - eco_drf_pct / 100.0)
    cur_dette_hist = dette_m
    cur_dette_nouv = 0.0
    cur_frng = frng_init_m
    cur_rar = rar_init_m
    cur_pop = float(population)
    decaissement_n_moins_1 = equip_brut_eur / 1e6
    cumul_ppi_nouvelle = 0.0
    gain_taux_tfpb_annuel = delta_pts_tfpb * rendement_1pt_tfpb
    cession_annuelle = cessions_m / 5.0

    duree_hist_eff = min(22.0, duree_res_hist + 7.0)
    penalite_reetal = 0.0025 if reetalement_hist else 0.0

    for idx_yr, yr in enumerate(annees_proj):
        cur_pop = cur_pop * (1 + tx_pop_proj / 100.0)
        coeff_taux = 0.5 if idx_yr == 0 else 1.0
        cur_fisc = cur_fisc * (1 + tx_bases_fisc / 100.0) + (gain_taux_tfpb_annuel * coeff_taux * 0.45 if idx_yr > 0 else gain_taux_tfpb_annuel * 0.55)
        cur_dot_serv = cur_dot_serv * (1 + tx_dot_serv / 100.0)
        cur_rrf = cur_fisc + cur_dot_serv

        cur_012 = cur_012 * (1 + tx_ms_proj / 100.0)
        if idx_yr > 0:
            cur_autres = cur_autres * (1 + tx_011_proj / 100.0)
        opex_induits_an = cumul_ppi_nouvelle * (opex_ppi_pct / 100.0)

        taux_hist = 0.032 + penalite_reetal
        taux_nouv = 0.034 + (part_dette_var / 100.0) * (choc_taux_pts / 100.0)
        interets = cur_dette_hist * taux_hist + cur_dette_nouv * taux_nouv
        cur_drf = cur_012 + cur_autres + interets + opex_induits_an
        cur_eb = cur_rrf - cur_drf

        if reetalement_hist:
            amort_hist = min(cur_dette_hist, dette_m / duree_hist_eff)
        else:
            amort_hist = min(cur_dette_hist, amort_hist_profil[idx_yr])
        amort_nouv = cur_dette_nouv / float(duree_emprunt_ans)
        amort_cap = amort_hist + amort_nouv
        cur_en = cur_eb - amort_cap

        enveloppe_totale_disp = ppi_reelle_cfc + cur_rar
        ppi_decaisse_an = enveloppe_totale_disp * (tx_realisation_ppi / 100.0)
        cur_rar = max(0.0, enveloppe_totale_disp - ppi_decaisse_an)

        fctva_an = decaissement_n_moins_1 * 0.85 * 0.16404
        subv_acquises = ppi_decaisse_an * (tx_subv_ppi / 100.0)

        ressources_inv = max(0.0, cur_en) + subv_acquises + fctva_an + cession_annuelle
        reste_a_financer = max(0.0, ppi_decaisse_an - ressources_inv)
        marge_frng_mobilisable = max(0.0, cur_frng - plancher_frng)
        prelevement_frng = min(reste_a_financer, marge_frng_mobilisable * 0.35)
        besoin_emprunt = max(0.0, reste_a_financer - prelevement_frng)

        excedent_ressources = max(0.0, ressources_inv - ppi_decaisse_an)
        cur_frng = cur_frng - prelevement_frng + (excedent_ressources * 0.5)

        cur_dette_hist = max(0.0, cur_dette_hist - amort_hist)
        cur_dette_nouv = max(0.0, cur_dette_nouv - amort_nouv + besoin_emprunt)
        cur_dette_tot = cur_dette_hist + cur_dette_nouv
        cur_cap = (cur_dette_tot / cur_eb) if cur_eb > 0 else 99.9

        portage_subv = subv_acquises * 0.70 * (delai_subv_mois / 12.0) * 0.30
        treso_nette = max(0.0, cur_frng - portage_subv)
        jours_treso = int(round((treso_nette / cur_drf) * 365)) if cur_drf > 0 else 0

        decaissement_n_moins_1 = ppi_decaisse_an
        cumul_ppi_nouvelle += (ppi_decaisse_an / friction_cfc) * 0.50

        rrf_p.append(round(cur_rrf, 2))
        drf_p.append(round(cur_drf, 2))
        eb_p.append(round(cur_eb, 2))
        en_p.append(round(cur_en, 2))
        fctva_p.append(round(fctva_an, 2))
        dette_p.append(round(cur_dette_tot, 2))
        cap_p.append(round(cur_cap, 1))
        frng_p.append(round(cur_frng, 2))
        opex_cum_p.append(round(opex_induits_an, 2))
        ppi_decaisse_p.append(round(ppi_decaisse_an, 2))
        rar_p.append(round(cur_rar, 2))
        pop_p.append(int(round(cur_pop)))
        drf_hab_p.append(int(round((cur_drf * 1e6) / cur_pop)))
        rrf_hab_p.append(int(round((cur_rrf * 1e6) / cur_pop)))
        jours_treso_p.append(jours_treso)

    analyse_prosp = generer_analyse_prospective(
        rrf_m, drf_m, ch012_m, ch011_m, ch65_m, eb_m, dette_m, frng_init_m, population,
        rrf_p, drf_p, eb_p, en_p, fctva_p, dette_p, cap_p, frng_p,
        jours_treso_p, drf_hab_p, rrf_hab_p, rar_p, pop_p,
        tx_ms_proj, tx_011_proj, eco_drf_pct, tx_bases_fisc, delta_pts_tfpb,
        rendement_1pt_tfpb, tx_dot_serv,
        ppi_base_m, friction_cfc, tx_realisation_ppi, tx_subv_ppi, delai_subv_mois,
        duree_emprunt_ans, reetalement_hist, cessions_m,
        part_dette_var, part_budget_vert, subv_satellites_m, pic_dette_info=pic_dette_info
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Épargne Brute 2030", f"{eb_p[-1]:.2f} M€", f"Dont -{opex_cum_p[-1]:.2f} M€ OPEX PPI")
    m2.metric(
        "Capacité Désendettement 2030",
        f"{cap_p[-1]:.1f} ans",
        "Trajectoire soutenable" if cap_p[-1] <= 12 else "Alerte tutelle CRC (> 12 ans)",
        delta_color="normal" if cap_p[-1] <= 12 else "inverse"
    )
    m3.metric(
        "Disponibilités Tréso 2030",
        f"{jours_treso_p[-1]} jours",
        f"FRNG : {frng_p[-1]:.2f} M€ (Alerte < 10 j)",
        delta_color="normal" if jours_treso_p[-1] >= 15 else ("off" if jours_treso_p[-1] >= 10 else "inverse")
    )
    m4.metric(
        "PPI Décaissée & Cessions",
        f"{sum(ppi_decaisse_p):.1f} M€",
        f"Cessions : {cessions_m:.1f} M€ | Vert : {(sum(ppi_decaisse_p) * part_budget_vert / 100):.1f} M€"
    )

    st.divider()

    gp1, gp2 = st.columns(2)
    with gp1:
        st.subheader("Trajectoire Recettes vs Dépenses (incl. OPEX PPI)")
        st.line_chart(pd.DataFrame({
            "Année": [str(a) for a in annees_proj],
            "Recettes (RRF)": rrf_p,
            "Dépenses (DRF + OPEX)": drf_p
        }).set_index("Année"))

    with gp2:
        st.subheader("Encours de Dette, Épargne Brute & FRNG (M€)")
        st.bar_chart(pd.DataFrame({
            "Année": [str(a) for a in annees_proj],
            "Encours Dette (M€)": dette_p,
            "Épargne Brute (M€)": eb_p,
            "FRNG (M€)": frng_p
        }).set_index("Année"))

    df_prosp = pd.DataFrame({
        "Exercice": [str(a) for a in annees_proj],
        "RRF (M€)": rrf_p,
        "DRF + OPEX (M€)": drf_p,
        "Épargne Brute (M€)": eb_p,
        "PPI Décaissée (M€)": ppi_decaisse_p,
        "RAR Reportés (M€)": rar_p,
        "FCTVA (M€)": fctva_p,
        "Dette (M€)": dette_p,
        "Désend. (ans)": cap_p,
        "Disp. (j)": jours_treso_p
    })
    st.dataframe(df_prosp, hide_index=True, use_container_width=True)

    st.divider()
    st.subheader(f"🧭 Feuille de Route Exhaustive DGS — {analyse_prosp['badge']}")
    texte_complet_ui = (
        f"**Analyse de la trajectoire :**\n"
        f"* {analyse_prosp['diag'][0]}\n"
        f"* {analyse_prosp['diag'][1]}\n\n"
        f"**Les 4 piliers de gestion mobilisés pour le Rapport d'Orientation Budgétaire (ROB) :**\n"
        f"* {analyse_prosp['piliers'][0]}\n"
        f"* {analyse_prosp['piliers'][1]}\n"
        f"* {analyse_prosp['piliers'][2]}\n"
        f"* {analyse_prosp['piliers'][3]}"
    )
    if analyse_prosp["niveau"] == "critique":
        st.error(texte_complet_ui)
    elif analyse_prosp["niveau"] == "vigilance":
        st.warning(texte_complet_ui)
    else:
        st.success(texte_complet_ui)

# ------------------------------------------
# ONGLET 4 : PILOTAGE DGS
# ------------------------------------------
with onglets[3]:
    dgs_h1, dgs_h2 = st.columns([0.92, 0.08])
    with dgs_h1:
        st.subheader("Pilotage Stratégique DGS — Démographie, Liquidité & Risque Consolidé")
    with dgs_h2:
        fiche_pedagogique(
            "ℹ️",
            f"Les 4 angles de contrôle de la Direction Générale ({normes_strate['strate_court']})",
            "Au-delà de l'équilibre comptable du budget principal, un DGS surveille la pression démographique, la trésorerie au quotidien et les risques portés par les organismes satellites.",
            "Taux d'encadrement = (ETP / Population) × 1 000  |  Disponibilités = (Trésorerie nette / DRF) × 365",
            [
                f"Taux d'encadrement : moyenne de votre strate ({normes_strate['strate_court']}) = {normes_strate['encadrement']:.1f} agents pour 1 000 habitants.",
                "Disponibilités de trésorerie : grâce au versement mensuel par douzièmes, une couverture de 15 à 25 jours est saine.",
                f"Taux d'endettement : moyenne de votre strate = {normes_strate['taux_endettement']:.0f} % (alerte > 100 %)."
            ],
            "Ce tableau de bord permet d'anticiper les besoins de lignes de trésorerie et d'encadrer les subventions d'équilibre versées au CCAS ou à la Caisse des Écoles."
        )

    d1, d2, d3, d4 = st.columns(4)
    d1.metric(
        "Population Projetée 2030",
        f"{pop_p[-1]:,} hab".replace(",", " "),
        f"+{pop_p[-1] - population:,} hab (+{((pop_p[-1]/population - 1)*100):.1f}%)".replace(",", " ")
    )
    d2.metric(
        "Taux d'Encadrement RH",
        f"{taux_encadrement:.1f} agents / 1 000 hab",
        f"Moy. strate ({normes_strate['strate_court']}) : {normes_strate['encadrement']:.1f} | {effectifs_etp} ETP"
    )
    d3.metric(
        "Disponibilités Tréso (FRNG → 2030)",
        f"{jours_treso_init} j → {jours_treso_p[-1]} j",
        "Équilibre : 15-25 j | Alerte < 10 j",
        delta_color="normal" if jours_treso_p[-1] >= 15 else ("off" if jours_treso_p[-1] >= 10 else "inverse")
    )
    d4.metric(
        "Endettement Consolidé (incl. Satellites)",
        f"{(dette_m + dette_garantie_m):.1f} M€",
        f"{taux_endettement_consolide:.1f} % des RRF (Strate : {normes_strate['taux_endettement']:.0f}%)"
    )

    st.divider()

    col_dem1, col_dem2 = st.columns(2)
    with col_dem1:
        st.subheader("1. Effet Démographique : Évolution par Habitant (€ / hab)")
        df_hab = pd.DataFrame({
            "Exercice": [str(a) for a in annees_proj],
            "Recettes / hab (€)": rrf_hab_p,
            "Dépenses / hab (€)": drf_hab_p
        }).set_index("Exercice")
        st.line_chart(df_hab)
        ecart_hab = (rrf_hab_p[-1] - drf_hab_p[-1]) - (rrf_hab_p[0] - drf_hab_p[0])
        if ecart_hab >= 0:
            st.success(f"**Résilience par habitant :** L'épargne dégagée par habitant progresse de **+{ecart_hab} €/hab** sur le mandat malgré la croissance démographique.")
        else:
            st.warning(f"**Érosion silencieuse par habitant :** L'épargne par habitant recule de **{ecart_hab} €/hab** sous l'effet de la poussée démographique.")

    with col_dem2:
        st.subheader("2. Tension de Trésorerie & Portage des Subventions")
        df_treso = pd.DataFrame({
            "Exercice": [str(a) for a in annees_proj],
            "Disponibilités Trésorerie (jours de DRF)": jours_treso_p
        }).set_index("Exercice")
        st.bar_chart(df_treso, color="#2563eb")
        min_j = min(jours_treso_p)
        if min_j < 10:
            st.error(f"**Alerte Liquidité (< 10 j) :** Point bas à **{min_j} jours** de fonctionnement. Ouvrir une ligne de trésorerie ou accélérer les acomptes de subventions.")
        elif min_j < 15:
            st.warning(f"**Vigilance Trésorerie (10-15 j) :** Point bas à **{min_j} jours** de fonctionnement (marge étroite lors des pics de mandatement PPI).")
        else:
            st.success(f"**Trésorerie à l'équilibre (15-25 j+) :** Les disponibilités restent au-dessus de **{min_j} jours** sur tout le mandat malgré un délai de versement du solde des subventions de **{delai_subv_mois} mois**.")

    st.divider()
    st.subheader("3. Consolidation Budgets Annexes, Satellites & Sensibilité Taux")

    s1, s2 = st.columns(2)
    with s1:
        poids_sat_drf = (subv_satellites_m / drf_m * 100) if drf_m > 0 else 0.0
        st.markdown("#### 🏢 Exposition aux Satellites (CCAS, Caisse des Écoles, SPL)")
        st.info(
            f"* **Subventions d'équilibre versées :** **{subv_satellites_m:.2f} M€/an** (soit **{poids_sat_drf:.1f} %** des dépenses réelles de fonctionnement).\n"
            f"* **Encours de dette garantie :** **{dette_garantie_m:.2f} M€**, portant le ratio d'endettement consolidé à **{taux_endettement_consolide:.1f} %** des RRF (moyenne strate dette directe : **{normes_strate['taux_endettement']:.0f} %**).\n"
            "* **Recommandation DGS :** Instaurer un pacte financier annuel avec chaque satellite pour plafonner les subventions d'équilibre."
        )

    with s2:
        surcout_stress_m = dette_m * (part_dette_var / 100.0) * (choc_taux_pts / 100.0)
        rendement_total_tfpb = delta_pts_tfpb * rendement_1pt_tfpb
        st.markdown("#### 🎛️ Sensibilité Fiscale (TFPB) & Stress-Test Taux")
        st.info(
            f"* **Levier Taxe Foncière (TFPB actuelle {taux_tfpb_actuel:.2f} %) :** Chaque point supplémentaire rapporte **{rendement_1pt_tfpb:.2f} M€/an** (impact scénario : **{rendement_total_tfpb:+.2f} M€/an**).\n"
            f"* **Stress-test taux (+{choc_taux_pts:.2f} pts sur {part_dette_var}% de dette variable) :** Surcoût financier annuel estimé à **{surcout_stress_m:.2f} M€/an**.\n"
            f"* **Effet maturité ({duree_emprunt_ans} ans) :** L'allongement sur prêts AFD/CDC réduit l'annuité en capital et protège l'épargne nette."
        )

with onglets[4]:
    render_onglet_rob(locals())

pdf_tbif_bytes = build_tbif_pdf(
    collectivite, population, normes_strate, rrf_m, ch012_m, ch011_m, ch65_m, ch661_m,
    cap16_m, dette_m, dette_garantie_m, frng_init_m, friction_cfc, ppi_base_m,
    opex_ppi_pct, rendement_1pt_tfpb, jours_treso_init, eb_p[-1]
)
pdf_prosp_bytes = build_prospective_pdf(
    collectivite, sc_court, ppi_base_m, tx_realisation_ppi, tx_subv_ppi, friction_cfc,
    annees_proj, rrf_p, drf_p, eb_p, fctva_p, dette_p, cap_p, frng_p,
    jours_treso_p, drf_hab_p, rar_p[-1], dette_m, analyse_prosp
)

with col_btn2:
    st.write("")
    st.download_button(
        "📑 Spécimen TBI (1 p.)",
        data=pdf_tbif_bytes,
        file_name="Specimen_Demo_TBI_M57.pdf",
        mime="application/pdf",
        use_container_width=True
    )

with col_btn3:
    st.write("")
    st.download_button(
        "🔮 Spécimen Prosp. (1 p.)",
        data=pdf_prosp_bytes,
        file_name="Specimen_Demo_Prospective.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True
    )

st.sidebar.markdown("---")
st.sidebar.caption("🔒 Sauvegarde Cloud & import de balances comptables réservés à la version sous licence.")
