import streamlit as st


def _fmt_int(val):
    return f"{int(round(val)):,}".replace(",", " ")


def _fmt_dec(val, dec=2):
    return f"{val:.{dec}f}".replace(".", ",")


def _to_rtf(text_md):
    lines = text_md.splitlines()
    rtf_lines = [
        r"{\rtf1\ansi\deff0",
        r"{\fonttbl{\f0\fswiss\fcharset0 Calibri;}}",
        r"{\colortbl;\red15\green23\blue42;\red30\green41\blue59;\red180\green83\blue9;\red6\green95\blue70;}",
        r"\paperw11906\paperh16838\margl1134\margr1134\margt1134\margb1134",
        r"\f0\fs22\cf2 "
    ]

    def esc_rtf(s):
        out = []
        for ch in s:
            code = ord(ch)
            if ch == "\\":
                out.append(r"\\")
            elif ch == "{":
                out.append(r"\{")
            elif ch == "}":
                out.append(r"\}")
            elif code > 127:
                out.append(f"\\u{code}?")
            else:
                out.append(ch)
        return "".join(out)

    for raw in lines:
        line = raw.strip()
        if not line:
            rtf_lines.append(r"\par ")
            continue
        clean = line.replace("**", "")
        if clean.startswith("# "):
            title = esc_rtf(clean[2:].strip())
            rtf_lines.append(rf"\pard\sa180\sb120\b\fs32\cf1 {title}\b0\fs22\cf2\par ")
        elif clean.startswith("## "):
            h2 = esc_rtf(clean[3:].strip())
            rtf_lines.append(rf"\pard\sa140\sb220\b\fs26\cf1 {h2}\b0\fs22\cf2\par ")
        elif clean.startswith("### "):
            h3 = esc_rtf(clean[4:].strip())
            rtf_lines.append(rf"\pard\sa100\sb160\b\fs23\cf3 {h3}\b0\fs22\cf2\par ")
        elif clean.startswith("- ") or clean.startswith("* "):
            item = esc_rtf(clean[2:].strip())
            rtf_lines.append(rf"\pard\li360\fi-180\sa80 \bullet  {item}\par ")
        elif clean.startswith("> "):
            quote = esc_rtf(clean[2:].strip())
            rtf_lines.append(rf"\pard\li360\sa120\i\cf4 {quote}\i0\cf2\par ")
        else:
            body = esc_rtf(clean)
            rtf_lines.append(rf"\pard\sa110\qj {body}\par ")

    rtf_lines.append("}")
    return "\n".join(rtf_lines).encode("ascii", errors="ignore")


def generer_texte_rob(ctx):
    collectivite = ctx["collectivite"]
    population = ctx["population"]
    normes = ctx["normes_strate"]
    annees_retro = ctx["annees_retro"]
    rrf_hist, drf_hist = ctx["rrf_hist"], ctx["drf_hist"]
    eb_hist, en_hist = ctx["eb_hist"], ctx["en_hist"]
    equip_hist, subv_hist = ctx["equip_hist"], ctx["subv_hist"]
    fctva_hist, emprunt_hist = ctx["fctva_hist"], ctx["emprunt_hist"]

    tcma_rrf, tcma_drf, tcma_ms = ctx["tcma_rrf"], ctx["tcma_drf"], ctx["tcma_ms"]
    poids_ms_rrf, delta_eb_5ans = ctx["poids_ms_rrf"], ctx["delta_eb_5ans"]

    rrf_m, drf_m, ch012_m = ctx["rrf_m"], ctx["drf_m"], ctx["ch012_m"]
    cap16_m, eb_m, taux_eb = ctx["cap16_m"], ctx["eb_m"], ctx["taux_eb"]
    iib, cap_desend = ctx["iib"], ctx["cap_desend"]
    taux_endettement = ctx["taux_endettement"]
    taux_endettement_consolide = ctx["taux_endettement_consolide"]
    dette_m, dette_garantie_m = ctx["dette_m"], ctx["dette_garantie_m"]
    subv_satellites_m = ctx["subv_satellites_m"]
    frng_init_m, jours_treso_init = ctx["frng_init_m"], ctx["jours_treso_init"]

    effectifs_etp, taux_encadrement = ctx["effectifs_etp"], ctx["taux_encadrement"]
    friction_cfc = ctx["friction_cfc"]
    taux_tfpb_actuel, rendement_1pt_tfpb = ctx["taux_tfpb_actuel"], ctx["rendement_1pt_tfpb"]

    r1_val, r2_val, r3_val = ctx["r1_val"], ctx["r2_val"], ctx["r3_val"]
    r4_val, r5_val, r6_val = ctx["r4_val"], ctx["r5_val"], ctx["r6_val"]
    r7_val, r9_val, r11_val = ctx["r7_val"], ctx["r9_val"], ctx["r11_val"]

    sc_court, annees_proj = ctx["sc_court"], ctx["annees_proj"]
    rrf_p, drf_p, eb_p = ctx["rrf_p"], ctx["drf_p"], ctx["eb_p"]
    fctva_p, dette_p, cap_p = ctx["fctva_p"], ctx["dette_p"], ctx["cap_p"]
    frng_p, jours_treso_p = ctx["frng_p"], ctx["jours_treso_p"]
    ppi_decaisse_p, pop_p = ctx["ppi_decaisse_p"], ctx["pop_p"]

    tx_bases_fisc, delta_pts_tfpb = ctx["tx_bases_fisc"], ctx["delta_pts_tfpb"]
    tx_dot_serv, tx_pop_proj = ctx["tx_dot_serv"], ctx["tx_pop_proj"]
    eco_drf_pct, tx_ms_proj, tx_011_proj = ctx["eco_drf_pct"], ctx["tx_ms_proj"], ctx["tx_011_proj"]
    opex_ppi_pct, part_dette_var, choc_taux_pts = ctx["opex_ppi_pct"], ctx["part_dette_var"], ctx["choc_taux_pts"]
    ppi_base_m, tx_realisation_ppi, tx_subv_ppi = ctx["ppi_base_m"], ctx["tx_realisation_ppi"], ctx["tx_subv_ppi"]
    cessions_m, duree_emprunt_ans = ctx["cessions_m"], ctx["duree_emprunt_ans"]
    delai_subv_mois, part_budget_vert = ctx["delai_subv_mois"], ctx["part_budget_vert"]
    reetalement_hist, amort_hist_profil = ctx["reetalement_hist"], ctx["amort_hist_profil"]
    analyse_prosp = ctx["analyse_prosp"]

    deb_retro, fin_retro = annees_retro[0], annees_retro[-1]
    moy_equip = sum(equip_hist) / len(equip_hist) if equip_hist else 0.0
    tx_cofin_hist = ((sum(subv_hist) + sum(fctva_hist)) / sum(equip_hist) * 100) if sum(equip_hist) > 0 else 0.0
    ecart_ciseau = tcma_drf - tcma_rrf

    if population >= 3500:
        cadre_juridique = (
            f"Conformément aux dispositions des articles L. 2312-1 et D. 2312-3 du Code général des collectivités territoriales (CGCT), "
            f"applicables aux communes de 3 500 habitants et plus ({_fmt_int(population)} habitants DGF pour la {collectivite}), "
            f"le présent Rapport d'Orientation Budgétaire (ROB) présente les évolutions rétrospectives des finances communales, "
            f"l'analyse de la structure et de la gestion de la dette, l'évolution des effectifs et de la masse salariale, "
            f"ainsi que les engagements pluriannuels envisagés sur la période 2026-2030."
        )
    else:
        cadre_juridique = (
            f"Bien que la {collectivite} ({_fmt_int(population)} habitants DGF) se situe sous le seuil légal de 3 500 habitants "
            f"rendant obligatoire le Débat d'Orientation Budgétaire prévu à l'article L. 2312-1 du CGCT, l'exécutif municipal "
            f"soumet à l'assemblée délibérante la présente note d'orientation pluriannuelle afin d'éclairer les choix budgétaires et patrimoniaux du mandat."
        )

    if ecart_ciseau > 0.2:
        lecture_ciseau = (
            f"La période {deb_retro}-{fin_retro} se caractérise par un effet de ciseau budgétaire de +{_fmt_dec(ecart_ciseau)} point par an : "
            f"les dépenses réelles de fonctionnement ont progressé au rythme annuel moyen de +{_fmt_dec(tcma_drf)} % (passant de {_fmt_dec(drf_hist[0])} M€ à {_fmt_dec(drf_hist[-1])} M€), "
            f"plus rapidement que les recettes réelles de fonctionnement (+{_fmt_dec(tcma_rrf)} %/an, de {_fmt_dec(rrf_hist[0])} M€ à {_fmt_dec(rrf_hist[-1])} M€)."
        )
    else:
        lecture_ciseau = (
            f"Sur la période {deb_retro}-{fin_retro}, la collectivité a préservé l'équilibre de sa section de fonctionnement : "
            f"les recettes réelles de fonctionnement ont évolué de +{_fmt_dec(tcma_rrf)} %/an (de {_fmt_dec(rrf_hist[0])} M€ à {_fmt_dec(rrf_hist[-1])} M€) "
            f"face à une progression des dépenses réelles de fonctionnement contenue à +{_fmt_dec(tcma_drf)} %/an (de {_fmt_dec(drf_hist[0])} M€ à {_fmt_dec(drf_hist[-1])} M€)."
        )

    if delta_pts_tfpb > 0:
        politique_fiscale = (
            f"activation d'un levier fiscal de +{_fmt_dec(delta_pts_tfpb, 1)} point sur le taux communal de taxe foncière sur les propriétés bâties (TFPB, actuellement fixé à {_fmt_dec(taux_tfpb_actuel)} %), "
            f"générant un produit supplémentaire estimé à +{_fmt_dec(delta_pts_tfpb * rendement_1pt_tfpb)} M€ en année pleine (rendement d'un point : {_fmt_dec(rendement_1pt_tfpb)} M€)"
        )
    elif delta_pts_tfpb < 0:
        politique_fiscale = (
            f"allègement fiscal de {_fmt_dec(delta_pts_tfpb, 1)} point sur le taux communal de TFPB (actuellement {_fmt_dec(taux_tfpb_actuel)} %), "
            f"représentant une restitution de pouvoir d'achat de {_fmt_dec(abs(delta_pts_tfpb) * rendement_1pt_tfpb)} M€/an aux contribuables locaux"
        )
    else:
        politique_fiscale = (
            f"maintien de la stabilité des taux communaux d'imposition directe (TFPB maintenue à {_fmt_dec(taux_tfpb_actuel)} %), "
            f"la dynamique fiscale reposant exclusivement sur la croissance physique des bases (+{_fmt_dec(tx_bases_fisc, 1)} %/an) et le suivi des constructions neuves avec la DDFiP"
        )

    if eco_drf_pct > 0:
        mesure_011 = (
            f"engagement d'un plan d'économies structurelles immédiat de -{_fmt_dec(eco_drf_pct, 1)} % sur les charges à caractère général (Chap. 011) et subventions non obligatoires (Chap. 65), "
            f"suivi d'un plafonnement de leur évolution annuelle à +{_fmt_dec(tx_011_proj, 1)} %/an ;"
        )
    else:
        mesure_011 = (
            f"maîtrise stricte des charges à caractère général (Chap. 011) et de gestion courante (Chap. 65) limitée à +{_fmt_dec(tx_011_proj, 1)} %/an ;"
        )

    if reetalement_hist:
        mode_dette_txt = (
            f"Un réétalement de l'encours de dette existant ({_fmt_dec(dette_m)} M€) est intégré afin de lisser les échéances annuelles "
            f"(moyenne de {_fmt_dec(sum(amort_hist_profil)/5.0)} M€/an avant renégociation), moyennant une marge financière de +0,25 point. "
        )
    else:
        mode_dette_txt = (
            f"L'extinction de la dette existante ({_fmt_dec(dette_m)} M€) suit son échéancier contractuel précis sur la période 2026-2030 "
            f"({', '.join([f'{y} : {_fmt_dec(v)} M€' for y, v in zip(annees_proj, amort_hist_profil)])}). "
        )

    tx_eb_2030 = (eb_p[-1] / rrf_p[-1] * 100) if rrf_p[-1] > 0 else 0.0

    return f"""# RAPPORT D'ORIENTATION BUDGÉTAIRE (ROB) — EXERCICE 2026 ET PROSPECTIVE 2026-2030
**Collectivité :** {collectivite}
**Strate démographique de référence (DGCL) :** {normes['strate_nom']} ({_fmt_int(population)} habitants DGF)
**Scénario d'orientation retenu :** {sc_court}

---

## I. CADRE RÉGLEMENTAIRE ET ANALYSE RÉTROSPECTIVE ({deb_retro}-{fin_retro})

{cadre_juridique}

### 1. Évolution des équilibres de fonctionnement
{lecture_ciseau}

En conséquence, l'épargne brute (capacité d'autofinancement brute) s'établit à **{_fmt_dec(eb_hist[-1])} M€** à la clôture de l'exercice {fin_retro}, contre {_fmt_dec(eb_hist[0])} M€ en {deb_retro} (soit une variation de **{_fmt_dec(delta_eb_5ans)} M€** sur la période). Après remboursement du capital de la dette ({_fmt_dec(cap16_m)} M€ au chapitre 16), l'épargne nette disponible ressort à **{_fmt_dec(en_hist[-1])} M€**.

### 2. Bilan rétrospectif de l'investissement et du mix de financement
Sur la période {deb_retro}-{fin_retro}, la commune a exécuté un volume moyen de dépenses d'équipement brut de **{_fmt_dec(moy_equip, 1)} M€ par an**, correspondant à un effort moyen de **{_fmt_int((moy_equip * 1e6) / population)} € par habitant** (à comparer à la moyenne de strate de {_fmt_int(normes['r4_equip_hab'])} €/hab.).

Le financement de ces investissements a mobilisé :
- Un taux moyen de cofinancement externe (subventions d'équipement au compte 13 et FCTVA au compte 10222) de **{_fmt_dec(tx_cofin_hist, 1)} %** des dépenses réalisées ;
- Un recours complémentaire à l'épargne nette, aux cessions patrimoniales et à l'emprunt pour un montant cumulé d'emprunt d'équilibre estimé à **{_fmt_dec(sum(emprunt_hist), 1)} M€** sur la période.

---

## II. SITUATION FINANCIÈRE DE RÉFÉRENCE ET RATIOS DE STRATE (ART. L. 2313-1 CGCT)

À l'ouverture du cycle budgétaire 2026, la structure financière de la {collectivite} s'établit comme suit :
- **Recettes réelles de fonctionnement (RRF) :** {_fmt_dec(rrf_m)} M€ ({_fmt_int(r3_val)} €/hab., contre {_fmt_int(normes['r3_rrf_hab'])} €/hab. en moyenne dans la strate) ;
- **Dépenses réelles de fonctionnement (DRF) :** {_fmt_dec(drf_m)} M€ ({_fmt_int(r1_val)} €/hab., contre {_fmt_int(normes['r1_drf_hab'])} €/hab. dans la strate) ;
- **Épargne brute (CAF) :** {_fmt_dec(eb_m)} M€, représentant un taux d'épargne brute de **{_fmt_dec(taux_eb, 1)} %** (moyenne de strate : {_fmt_dec(normes['taux_eb'], 1)} % ; seuil prudentiel recommandé : 10,0 %) ;
- **Indice d'inflexibilité budgétaire (IIB) :** **{_fmt_dec(iib, 1)} %** des RRF (moyenne de strate : {_fmt_dec(normes['iib'], 0)} % ; seuil de vigilance : 75,0 %) ;
- **Fonds de roulement net global (FRNG) :** {_fmt_dec(frng_init_m)} M€, assurant une couverture initiale de **{jours_treso_init} jours** de dépenses réelles de fonctionnement.

Conformément à l'article L. 2313-1 du CGCT, les ratios financiers réglementaires de la collectivité se positionnent ainsi face aux moyennes nationales des **{normes['strate_nom'].lower()}** :
- **Dépenses réelles de fonctionnement / population (R1) :** {_fmt_int(r1_val)} €/hab. (strate : {_fmt_int(normes['r1_drf_hab'])} €/hab.) ;
- **Produit des impositions directes / population (R2) :** {_fmt_int(r2_val)} €/hab. (strate : {_fmt_int(normes['r2_fisc_hab'])} €/hab.) ;
- **Recettes réelles de fonctionnement / population (R3) :** {_fmt_int(r3_val)} €/hab. (strate : {_fmt_int(normes['r3_rrf_hab'])} €/hab.) ;
- **Dépenses d'équipement brut / population (R4) :** {_fmt_int(r4_val)} €/hab. (strate : {_fmt_int(normes['r4_equip_hab'])} €/hab.) ;
- **Encours de dette / population (R5) :** {_fmt_int(r5_val)} €/hab. (strate : {_fmt_int(normes['r5_dette_hab'])} €/hab.) ;
- **DGF et dotations / population (R6) :** {_fmt_int(r6_val)} €/hab. (strate : {_fmt_int(normes['r6_dot_hab'])} €/hab.) ;
- **Part des charges de personnel dans les DRF (R7) :** {_fmt_dec(r7_val, 1)} % (strate : {_fmt_dec(normes['r7_012_drf'], 1)} %) ;
- **Coefficient de rigidité fonctionnement + dette (R9) :** {_fmt_dec(r9_val, 1)} % (strate : {_fmt_dec(normes['r9_rigidite'], 1)} %) ;
- **Taux d'endettement — Encours de dette / RRF (R11) :** {_fmt_dec(r11_val, 1)} % (strate : {_fmt_dec(normes['taux_endettement'], 1)} % ; seuil d'alerte : 100,0 %).

---

## III. GESTION DE LA DETTE, TRÉSORERIE ET RESSOURCES HUMAINES (ART. D. 2312-3 CGCT)

### 1. Structure et profil d'extinction de l'endettement
L'encours de dette directe de la commune au 31 décembre s'élève à **{_fmt_dec(dette_m)} M€**, soit **{_fmt_dec(taux_endettement, 1)} %** des recettes réelles de fonctionnement. Rapporté à l'épargne brute actuelle, le ratio de capacité de désendettement atteint **{_fmt_dec(cap_desend, 1)} années** (moyenne de strate : {_fmt_dec(normes['cap_desend'], 1)} ans ; seuil d'alerte prudentiel : 10 ans ; seuil critique : 12 ans).

En intégrant l'encours de dette garantie au bénéfice des organismes satellites et bailleurs ({_fmt_dec(dette_garantie_m)} M€), l'endettement consolidé s'établit à **{_fmt_dec(dette_m + dette_garantie_m)} M€** ({_fmt_dec(taux_endettement_consolide, 1)} % des RRF). Par ailleurs, les subventions d'équilibre versées aux budgets annexes et satellites (CCAS, Caisse des Écoles) représentent **{_fmt_dec(subv_satellites_m)} M€/an**.

{mode_dette_txt}La part de l'encours exposée aux taux variables ({part_dette_var} %) fait l'objet d'un test de sensibilité intégrant un choc de +{_fmt_dec(choc_taux_pts)} point sur la période.

### 2. Évolution des effectifs et de la masse salariale (Chapitre 012)
La masse salariale s'élève à **{_fmt_dec(ch012_m)} M€**, absorbant **{_fmt_dec(poids_ms_rrf, 1)} %** des recettes réelles de fonctionnement (après une évolution historique de +{_fmt_dec(tcma_ms)} %/an). Les effectifs rémunérés représentent **{effectifs_etp} équivalents temps plein (ETP)**, soit un taux d'encadrement de **{_fmt_dec(taux_encadrement, 1)} agents pour 1 000 habitants** (moyenne de strate : {_fmt_dec(normes['encadrement'], 1)} agents/1 000 hab.).

Sur le mandat 2026-2030, la trajectoire budgétaire fixe un plafond de progression de la masse salariale à **+{_fmt_dec(tx_ms_proj, 1)} % par an**, couvrant le glissement vieillesse-technicité (GVT) et les mesures statutaires nationales tout en encadrant strictement l'effet volume (pilotage du remplacement des départs et du régime indemnitaire RIFSEEP).

---

## IV. ORIENTATIONS BUDGÉTAIRES ET TRAJECTOIRE PLURIANNUELLE (2026-2030)

### 1. Hypothèses de construction de la trajectoire ({sc_court})
Face à une croissance démographique projetée de +{_fmt_dec(tx_pop_proj, 1)} % par an (portant la population à **{_fmt_int(pop_p[-1])} habitants** en 2030), les orientations budgétaires reposent sur les leviers suivants :
- **Politique fiscale et recettes propres :** {politique_fiscale}, accompagnée d'une indexation des dotations et produits des services (chapitres 70 et 75) de +{_fmt_dec(tx_dot_serv, 1)} %/an ;
- **Maîtrise des charges de gestion :** {mesure_011}
- **Programmation Pluriannuelle d'Investissement (PPI) :** inscription d'une enveloppe votée de **{_fmt_dec(ppi_base_m, 1)} M€ HT/an** (soit {_fmt_dec(ppi_base_m * friction_cfc, 1)} M€ TTC en intégrant le coefficient de friction BTP de {_fmt_dec(friction_cfc)}), calibrée sur un taux de réalisation annuel de **{tx_realisation_ppi} %** (soit **{_fmt_dec(sum(ppi_decaisse_p), 1)} M€** effectivement décaissés sur cinq ans, dont **{part_budget_vert} %** fléchés vers la transition écologique au titre du Budget Vert) ;
- **Plan de financement de la PPI :** recherche d'un taux moyen de cofinancement externe de **{tx_subv_ppi} %**, mobilisation de **{_fmt_dec(cessions_m, 1)} M€** de cessions patrimoniales (chapitre 024), encaissement de **{_fmt_dec(sum(fctva_p), 1)} M€** de FCTVA, et recours à des emprunts d'équilibre amortis sur **{duree_emprunt_ans} ans** (partenaires institutionnels AFD / Banque des Territoires). Les charges de fonctionnement induites par les équipements neufs (OPEX) sont provisionnées à hauteur de **{_fmt_dec(opex_ppi_pct, 1)} %/an** de leur valeur nette.

### 2. Résultats projetés à l'horizon 2030 et feuille de route opérationnelle
L'application de ces orientations permet d'atteindre les équilibres suivants au terme de l'exercice 2030 :
- **Recettes / Dépenses réelles de fonctionnement 2030 :** {_fmt_dec(rrf_p[-1], 1)} M€ de RRF face à {_fmt_dec(drf_p[-1], 1)} M€ de DRF (incluant les OPEX induits par les nouveaux équipements) ;
- **Épargne brute 2030 :** **{_fmt_dec(eb_p[-1])} M€**, soit un taux d'épargne brute de **{_fmt_dec(tx_eb_2030, 1)} %** des RRF ;
- **Encours de dette et capacité de désendettement 2030 :** encours stabilisé à **{_fmt_dec(dette_p[-1], 1)} M€**, ramenant la capacité de désendettement à **{_fmt_dec(cap_p[-1], 1)} années** ;
- **Liquidité et Fonds de Roulement 2030 :** FRNG maintenu à **{_fmt_dec(frng_p[-1], 1)} M€** et disponibilités nettes de trésorerie (après portage des subventions sur {delai_subv_mois} mois) à **{jours_treso_p[-1]} jours** de DRF (pour une zone d'équilibre comprise entre 15 et 25 jours).

> **Synthèse des quatre piliers d'exécution (statut : {analyse_prosp['badge']}) :**
> - {analyse_prosp['piliers'][0]}
> - {analyse_prosp['piliers'][1]}
> - {analyse_prosp['piliers'][2]}
> - {analyse_prosp['piliers'][3]}
"""


def render_onglet_rob(ctx):
    st.subheader("📝 Générateur Automatique du Rapport d'Orientation Budgétaire (Art. L. 2312-1 & D. 2312-3 CGCT)")
    st.caption(
        "Ce module rédige automatiquement la note réglementaire complète à partir de vos balances M57, "
        "des moyennes de votre strate DGCL et du scénario prospectif sélectionné dans l'onglet 3."
    )

    texte_rob_genere = generer_texte_rob(ctx)
    collectivite_slug = ctx["collectivite"].replace(" ", "_")

    c_top1, c_top2, c_top3 = st.columns([2.1, 1.0, 1.0])
    with c_top1:
        st.info(
            f"**Document prêt pour le Conseil Municipal :** Calibré sur **{ctx['collectivite']}** "
            f"({_fmt_int(ctx['population'])} hab. — **{ctx['normes_strate']['strate_court']}**) • Scénario : **{ctx['sc_court']}**."
        )
    with c_top2:
        st.download_button(
            "📘 Télécharger Word / Pages (.rtf)",
            data=_to_rtf(texte_rob_genere),
            file_name=f"ROB_2026_2030_{collectivite_slug}.rtf",
            mime="application/rtf",
            type="primary",
            use_container_width=True
        )
    with c_top3:
        st.download_button(
            "📄 Télécharger Texte (.md)",
            data=texte_rob_genere.encode("utf-8"),
            file_name=f"ROB_2026_2030_{collectivite_slug}.md",
            mime="text/markdown",
            use_container_width=True
        )

    tab_apercu, tab_edition = st.tabs(["👁️ Aperçu mis en page (Prêt à lire)", "✏️ Éditer ou Copier le texte brut"])

    with tab_apercu:
        with st.container(border=True):
            st.markdown(texte_rob_genere)

    with tab_edition:
        st.caption("Vous pouvez modifier directement les paragraphes ci-dessous avant d'exporter le document final.")
        texte_modifie = st.text_area(
            "Contenu modifiable du ROB :",
            value=texte_rob_genere,
            height=520,
            label_visibility="collapsed"
        )
        if texte_modifie != texte_rob_genere:
            st.download_button(
                "💾 Télécharger la version modifiée (.rtf)",
                data=_to_rtf(texte_modifie),
                file_name=f"ROB_Personnalise_{collectivite_slug}.rtf",
                mime="application/rtf"
            )
