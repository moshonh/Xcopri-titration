"""Verified references, ordered exactly as the final manuscript (23 sources).

PAPER_LIST contains seven-element tuples: (authors, year, exact title, journal
or agency, DOI or official regulatory URL, PMID string, evidence summary).
The first two entries are regulatory URLs, not DOIs; the consumer must not
prepend https://doi.org/ to those URLs. The year for EMA is initial approval;
the linked product information is the current, dynamically updated document.
"""

REFERENCES = {'FDA2019': '[1] US Food and Drug Administration. XCOPRI (cenobamate) Prescribing Information [revised '
            'August 2025]. FDA; 2025. Regulatory document, not a DOI: '
            'https://www.accessdata.fda.gov/drugsatfda_docs/label/2025/212839s013lbl.pdf',
 'EMA2021': '[2] European Medicines Agency. Ontozry (cenobamate): Summary of Product Characteristics. EMA; '
            '2021, product information updated 2026. Regulatory document, not a DOI: '
            'https://www.ema.europa.eu/en/documents/product-information/ontozry-epar-product-information_en.pdf',
 'Krauss2020': '[3] Krauss GL et al.. Safety and efficacy of adjunctive cenobamate (YKP3089) in patients '
               'with uncontrolled focal seizures: a multicentre, double-blind, randomised, '
               'placebo-controlled, dose-response trial. Lancet Neurol. 2020;19:38-48. DOI: '
               '10.1016/s1474-4422(19)30399-0. PMID: 31734103',
 'Roberti2021': '[4] Roberti R et al.. Pharmacology of Cenobamate: Mechanism of Action, Pharmacokinetics, '
                'Drug-Drug Interactions and Tolerability. CNS Drugs. 2021;35:609-618. DOI: '
                '10.1007/s40263-021-00819-8. PMID: 33993416',
 'Greene2022': '[5] Greene SA et al.. Effect of cenobamate on the single-dose pharmacokinetics of multiple '
               'cytochrome P450 probes using a cocktail approach in healthy subjects. Clin Transl Sci. '
               '2022;15:899-911. DOI: 10.1111/cts.13204. PMID: 34877801',
 'Smith2022': '[6] Smith MC et al.. Dose Adjustment of Concomitant Antiseizure Medications During Cenobamate '
              'Treatment: Expert Opinion Consensus Recommendations. Neurol Ther. 2022;11:1705-1720. DOI: '
              '10.1007/s40120-022-00400-5. PMID: 36057761',
 'Steinhoff2024': '[7] Steinhoff BJ et al.. Therapeutic strategies during cenobamate treatment initiation: '
                  'Delphi panel recommendations. Ther Adv Neurol Disord. 2024;17:17562864241256733. DOI: '
                  '10.1177/17562864241256733. PMID: 38883228',
 'Landmark2026': '[8] Johannessen Landmark C et al.. Pharmacokinetic variability and complex two-way '
                 'interactions with cenobamate in patients with refractory epilepsy. Epilepsia. '
                 '2026;67:2820-2835. DOI: 10.1002/epi.70184. PMID: 41874535',
 'Charlier2026': '[9] Charlier B et al.. Do Cenobamate Pharmacokinetics Change with Co-Administered '
                 'Antiseizure Medications? An Exploratory Analysis of Responder Patients with Focal '
                 'Drug-Resistant Epilepsy. Pharmaceutics. 2026;18:92. DOI: 10.3390/pharmaceutics18010092. '
                 'PMID: 41599199',
 'Karazniewicz2021': '[10] Karaźniewicz-Łada M et al.. Pharmacokinetic Drug-Drug Interactions among '
                     'Antiepileptic Drugs, Including CBD, Drugs Used to Treat COVID-19 and Nutrients. Int J '
                     'Mol Sci. 2021;22:9582. DOI: 10.3390/ijms22179582. PMID: 34502487',
 'Cohen2026': '[11] Cohen H et al.. Induction of cytochrome P450 2C9 and P-glycoprotein activity by '
              'antiseizure medications: A systematic review and network meta-analysis. Epileptic Disord. '
              '2026;28:855-867. DOI: 10.1002/epd2.70232. PMID: 41948839',
 'Osborn2023': '[12] Osborn M, Abou-Khalil B. The cenobamate-clobazam interaction- evidence of synergy in '
               'addition to pharmacokinetic interaction. Epilepsy Behav. 2023;142:109156. DOI: '
               '10.1016/j.yebeh.2023.109156. PMID: 37037060',
 'Ciullo2026': '[13] Ciullo I et al.. Effectiveness of adjunctive low-dose clobazam in adults with focal '
               'drug-resistant epilepsy and incomplete response to cenobamate: A real-world study. Epilepsia '
               'Open. 2026;11:962-972. DOI: 10.1002/epi4.70261. PMID: 41919359',
 'Operto2025': '[14] Operto FF et al.. Clinical predictors and concomitant antiseizure medications effects '
               'on seizure control in relation to plasma cenobamate concentration: a multicenter '
               'retrospective study. Front Pharmacol. 2025;16:1668382. DOI: 10.3389/fphar.2025.1668382. '
               'PMID: 41059206',
 'Sperling2020': '[15] Sperling MR et al.. Cenobamate (YKP3089) as adjunctive treatment for uncontrolled '
                 'focal seizures in a large, phase 3, multicenter, open-label safety study. Epilepsia. '
                 '2020;61:1099-1108. DOI: 10.1111/epi.16525. PMID: 32396252',
 'Villani2022': '[16] Villani F et al.. Use of cenobamate for the treatment of focal epilepsy: an Italian '
                'expert opinion paper. Expert Rev Neurother. 2022;22:935-940. DOI: '
                '10.1080/14737175.2023.2171291. PMID: 36662573',
 'Zaccara2021': '[17] Zaccara G et al.. Critical Appraisal of Cenobamate as Adjunctive Treatment of Focal '
                'Seizures in Adults. Neuropsychiatr Dis Treat. 2021;17:3447-3457. DOI: 10.2147/ndt.s281490. '
                'PMID: 34876814',
 'Samanta2025': '[18] Samanta D. Cenobamate in pediatric epilepsy and developmental and epileptic '
                'encephalopathies: Efficacy, safety, and syndrome-specific considerations. Epilepsy Behav. '
                '2025;173:110787. DOI: 10.1016/j.yebeh.2025.110787. PMID: 41106086',
 'AbouKhalil2022': '[19] Abou-Khalil BW. Update on Antiseizure Medications 2022. Continuum. 2022;28:500-535. '
                   'DOI: 10.1212/con.0000000000001104. PMID: 35393968',
 'Schoretsanitis2022': '[20] Schoretsanitis G et al.. Drug-drug interactions between psychotropic '
                       'medications and oral contraceptives. Expert Opin Drug Metab Toxicol. '
                       '2022;18:395-411. DOI: 10.1080/17425255.2022.2106214. PMID: 35876180',
 'Chung2020': '[21] Chung SS et al.. Randomized phase 2 study of adjunctive cenobamate in patients with '
              'uncontrolled focal seizures. Neurology. 2020;94:e2311-e2322. DOI: '
              '10.1212/wnl.0000000000009530. PMID: 32409485',
 'ODwyer2024': "[22] O'Dwyer R et al.. Safety and Efficacy of Cenobamate for the Treatment of Focal Seizures "
               'in Older Patients: Post Hoc Analysis of a Phase III, Multicenter, Open-Label Study. Drugs '
               'Aging. 2024;41:251-260. DOI: 10.1007/s40266-024-01102-3. PMID: 38446341',
 'Yoon2026': '[23] Yoon YJ, Sarkis R, Lee JW. Cenobamate in older adults with drug-resistant epilepsy: '
             'Real-world tolerability, efficacy, and predictors of discontinuation. Seizure. '
             '2026;141:109-115. DOI: 10.1016/j.seizure.2026.07.012. PMID: 42468323'}

PAPER_LIST = [('US Food and Drug Administration',
  '2025',
  'XCOPRI (cenobamate) Prescribing Information [revised August 2025]',
  'FDA regulatory document — not a DOI',
  'https://www.accessdata.fda.gov/drugsatfda_docs/label/2025/212839s013lbl.pdf',
  '',
  'FDA regulatory prescribing information (not a DOI): dosing, interactions, contraindications and safety '
  'warnings, including liver injury.'),
 ('European Medicines Agency',
  '2021',
  'Ontozry (cenobamate): Summary of Product Characteristics',
  'EMA regulatory document — not a DOI',
  'https://www.ema.europa.eu/en/documents/product-information/ontozry-epar-product-information_en.pdf',
  '',
  'EMA regulatory product information (not a DOI): the EU summary of product characteristics, dosing and '
  'safety information.'),
 ('Krauss GL et al.',
  '2020',
  'Safety and efficacy of adjunctive cenobamate (YKP3089) in patients with uncontrolled focal seizures: a '
  'multicentre, double-blind, randomised, placebo-controlled, dose-response trial',
  'Lancet Neurol',
  '10.1016/s1474-4422(19)30399-0',
  'PMID:31734103',
  'Phase 2 randomized, double-blind, placebo-controlled dose-response trial of adjunctive cenobamate for '
  'uncontrolled focal seizures.'),
 ('Roberti R et al.',
  '2021',
  'Pharmacology of Cenobamate: Mechanism of Action, Pharmacokinetics, Drug-Drug Interactions and '
  'Tolerability',
  'CNS Drugs',
  '10.1007/s40263-021-00819-8',
  'PMID:33993416',
  'Review of cenobamate pharmacology, pharmacokinetics, drug interactions and tolerability, including '
  'CYP2C19 inhibition and CYP3A4/2B6 induction.'),
 ('Greene SA et al.',
  '2022',
  'Effect of cenobamate on the single-dose pharmacokinetics of multiple cytochrome P450 probes using a '
  'cocktail approach in healthy subjects',
  'Clin Transl Sci',
  '10.1111/cts.13204',
  'PMID:34877801',
  'Healthy-volunteer CYP probe study evaluated cenobamate up to 200 mg/day and its effects on CYP3A4/5, '
  'CYP2B6, CYP2C19 and CYP2C9 substrates.'),
 ('Smith MC et al.',
  '2022',
  'Dose Adjustment of Concomitant Antiseizure Medications During Cenobamate Treatment: Expert Opinion '
  'Consensus Recommendations',
  'Neurol Ther',
  '10.1007/s40120-022-00400-5',
  'PMID:36057761',
  'Expert consensus on proactive and reactive dose adjustment of concomitant antiseizure medications during '
  'cenobamate initiation.'),
 ('Steinhoff BJ et al.',
  '2024',
  'Therapeutic strategies during cenobamate treatment initiation: Delphi panel recommendations',
  'Ther Adv Neurol Disord',
  '10.1177/17562864241256733',
  'PMID:38883228',
  'International Delphi recommendations on cenobamate titration and management of concomitant antiseizure '
  'medications, including sodium channel blockers.'),
 ('Johannessen Landmark C et al.',
  '2026',
  'Pharmacokinetic variability and complex two-way interactions with cenobamate in patients with refractory '
  'epilepsy',
  'Epilepsia',
  '10.1002/epi.70184',
  'PMID:41874535',
  'Observational therapeutic drug monitoring study describing substantial cenobamate pharmacokinetic '
  'variability and complex two-way interactions.'),
 ('Charlier B et al.',
  '2026',
  'Do Cenobamate Pharmacokinetics Change with Co-Administered Antiseizure Medications? An Exploratory '
  'Analysis of Responder Patients with Focal Drug-Resistant Epilepsy',
  'Pharmaceutics',
  '10.3390/pharmaceutics18010092',
  'PMID:41599199',
  'Exploratory single-center study of 17 responders examining variable cenobamate concentrations and '
  'associations with concomitant drugs.'),
 ('Karaźniewicz-Łada M et al.',
  '2021',
  'Pharmacokinetic Drug-Drug Interactions among Antiepileptic Drugs, Including CBD, Drugs Used to Treat '
  'COVID-19 and Nutrients',
  'Int J Mol Sci',
  '10.3390/ijms22179582',
  'PMID:34502487',
  'Review of pharmacokinetic interactions among antiseizure drugs, including cannabidiol, and selected other '
  'drugs and nutrients.'),
 ('Cohen H et al.',
  '2026',
  'Induction of cytochrome P450 2C9 and P-glycoprotein activity by antiseizure medications: A systematic '
  'review and network meta-analysis',
  'Epileptic Disord',
  '10.1002/epd2.70232',
  'PMID:41948839',
  'Systematic review and network meta-analysis comparing the effects of antiseizure medications on CYP2C9 '
  'and P-glycoprotein substrates.'),
 ('Osborn M, Abou-Khalil B',
  '2023',
  'The cenobamate-clobazam interaction- evidence of synergy in addition to pharmacokinetic interaction',
  'Epilepsy Behav',
  '10.1016/j.yebeh.2023.109156',
  'PMID:37037060',
  'Small observational report of sedation and altered N-desmethylclobazam-to-clobazam ratios during '
  'co-treatment; pharmacodynamic synergy was proposed, not established.'),
 ('Ciullo I et al.',
  '2026',
  'Effectiveness of adjunctive low-dose clobazam in adults with focal drug-resistant epilepsy and incomplete '
  'response to cenobamate: A real-world study',
  'Epilepsia Open',
  '10.1002/epi4.70261',
  'PMID:41919359',
  'Retrospective single-center study of 85 adults with incomplete cenobamate response; low-dose adjunctive '
  'clobazam was associated with seizure reduction and was generally well tolerated.'),
 ('Operto FF et al.',
  '2025',
  'Clinical predictors and concomitant antiseizure medications effects on seizure control in relation to '
  'plasma cenobamate concentration: a multicenter retrospective study',
  'Front Pharmacol',
  '10.3389/fphar.2025.1668382',
  'PMID:41059206',
  'Multicenter retrospective study examining cenobamate plasma concentrations, clinical response and '
  'concomitant antiseizure medications.'),
 ('Sperling MR et al.',
  '2020',
  'Cenobamate (YKP3089) as adjunctive treatment for uncontrolled focal seizures in a large, phase 3, '
  'multicenter, open-label safety study',
  'Epilepsia',
  '10.1111/epi.16525',
  'PMID:32396252',
  'Large phase 3 open-label titration safety study. No DRESS cases were observed, which does not establish '
  'prevention of DRESS.'),
 ('Villani F et al.',
  '2022',
  'Use of cenobamate for the treatment of focal epilepsy: an Italian expert opinion paper',
  'Expert Rev Neurother',
  '10.1080/14737175.2023.2171291',
  'PMID:36662573',
  'Italian expert opinion on patient selection, treatment goals, cenobamate dosing and slow titration to '
  'improve tolerability.'),
 ('Zaccara G et al.',
  '2021',
  'Critical Appraisal of Cenobamate as Adjunctive Treatment of Focal Seizures in Adults',
  'Neuropsychiatr Dis Treat',
  '10.2147/ndt.s281490',
  'PMID:34876814',
  'Review of cenobamate efficacy, pharmacology, drug interactions and safety, including QT shortening.'),
 ('Samanta D',
  '2025',
  'Cenobamate in pediatric epilepsy and developmental and epileptic encephalopathies: Efficacy, safety, and '
  'syndrome-specific considerations',
  'Epilepsy Behav',
  '10.1016/j.yebeh.2025.110787',
  'PMID:41106086',
  'Narrative review of limited pediatric and developmental and epileptic encephalopathy evidence, including '
  'syndrome-specific safety considerations.'),
 ('Abou-Khalil BW',
  '2022',
  'Update on Antiseizure Medications 2022',
  'Continuum',
  '10.1212/con.0000000000001104',
  'PMID:35393968',
  'Broad clinical update on antiseizure medications, including cenobamate.'),
 ('Schoretsanitis G et al.',
  '2022',
  'Drug-drug interactions between psychotropic medications and oral contraceptives',
  'Expert Opin Drug Metab Toxicol',
  '10.1080/17425255.2022.2106214',
  'PMID:35876180',
  'Review of pharmacokinetic interactions between oral contraceptives and psychotropic or antiseizure '
  'medications.'),
 ('Chung SS et al.',
  '2020',
  'Randomized phase 2 study of adjunctive cenobamate in patients with uncontrolled focal seizures',
  'Neurology',
  '10.1212/wnl.0000000000009530',
  'PMID:32409485',
  'Randomized phase 2 placebo-controlled trial of adjunctive cenobamate 200 mg/day in adults with '
  'uncontrolled focal seizures.'),
 ("O'Dwyer R et al.",
  '2024',
  'Safety and Efficacy of Cenobamate for the Treatment of Focal Seizures in Older Patients: Post Hoc '
  'Analysis of a Phase III, Multicenter, Open-Label Study',
  'Drugs Aging',
  '10.1007/s40266-024-01102-3',
  'PMID:38446341',
  'Post hoc analysis of adults aged 65–70 years in a phase 3 open-label study, examining efficacy, adverse '
  'effects and concomitant medication burden.'),
 ('Yoon YJ, Sarkis R, Lee JW',
  '2026',
  'Cenobamate in older adults with drug-resistant epilepsy: Real-world tolerability, efficacy, and '
  'predictors of discontinuation',
  'Seizure',
  '10.1016/j.seizure.2026.07.012',
  'PMID:42468323',
  'Retrospective cohort of 75 adults aged 60 years or older examining cenobamate tolerability, efficacy, '
  'dose and discontinuation.')]
