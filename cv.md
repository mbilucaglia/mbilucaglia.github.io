---
title: CV
---
{% if site.data.profile.links.cv_pdf != "" %}
[Download CV PDF]({{ site.data.profile.links.cv_pdf | relative_url }})
{% endif %}

## Education and Qualifications
- **2026:** Ph.D. in Cominication Markets and Society, Università IULM (expected)
- **2018:** C.Eng. in Information Technology Engineering, Politecnico di Milano
- **2018:** M.Sc. in Electronics Bioengineering, Alama Mater Studiorum - Università di Bologna, 2018
- **2014:** B.Sc. in Electronics Engineering, Politecnico di Milano

## Academic Positions
- **2022 - 2025:** Ph.D. Fellow (supervisor: Prof. V. Russo), Università IULM
- **2019 - 2022:** Research Fellow (supervisor: Prof. V. Russo), Università IULM
- **2019:** Research Assistant (supervisor: Prof. P. Tressoldi), University of Padua

## Professional Affiliations
- **2020 - present:** Chartered Engineer, Engineers Council of Milan
- **2018 - present:** Member, IEEE-EMBS (Engineering in Medicine and Biology Society)
- **2014 - present:** Member, IEEE (Institute of Electrical and Electronics Engineers)

## Academic Services
### Editorial Services

#### Editorial Board Memberships
- **2026 - present:** Community Reviewer (Review Editor) for Frontiers in Human Neuroscience (Cognitive Neuroscience)

#### Ad hoc Reviewer [manuscripts, reviews]
Frontiers in Psychology [8, 8], Frontiers in Public Health [7, 7], Cognitive Neurodynamics [6, 17], Scientific Reports [6, 16], HardwareX [4, 9], PlosOne [4, 9], Frontiers in Psychiatry [3, 3], Frontiers in Human Neuroscience [2, 2], BMC Research Notes [1, 2], Biocibernetics an Biomedical Engineering [1, 2], Annual International Conference of the IEEE Engineering in Medicine and Biology Society (EMBC) [1, 1], Cognitive Computation [1, 1], Frontiers in Child and Adolescent Psychiatry [1, 1], Frontiers in Physiology [1, 1], Scientific Data [1, 1]

#### Ad hoc Handling Editor [manuscripts]
Frontiers in Human Neuroscience [5], Frontiers in Medicine [2], Frontiers in Public Health [1], Frontiers in Social Psychology [1]

#### Guest Editor - Research Topics / Special Issues
- **2026 - 2027:** ["Machine-Learning/Deep-Learning methods in Neuromarketing and Consumer Neuroscience - Volume III"](https://www.frontiersin.org/research-topics/80492/machine-learningdeep-learning-methods-in-neuromarketing-and-consumer-neuroscience-volume-iii) hosted by Frontiers in Human Neuroscience
- **2025 - 2026:** ["Machine-Learning/Deep-Learning methods in Neuromarketing and Consumer Neuroscience - Volume II"](https://www.frontiersin.org/research-topics/65160/machine-learningdeep-learning-methods-in-neuromarketing-and-consumer-neuroscience-volume-ii) hosted by Frontiers in Human Neuroscience
- **2024 - 2025:** ["Machine-Learning/Deep-Learning methods in Neuromarketing and Consumer Neuroscience"](https://www.frontiersin.org/research-topics/49742/machine-learningdeep-learning-methods-in-neuromarketing-and-consumer-neuroscience/magazine) co-hosted by Frontiers in Neuroscience, Frontiers in Human Neuroscience and Frontiers in Psychology

### Conference Services
- **2025:** Event Comitee Member of the [1st International Online Conference on Behavioral Sciences](https://sciforum.net/event/iocbs2026), organised by Behavioural Sciences

## Publications
Co-author of {% bibliography_count %} peer-reviewes publications, including {% bibliography_count --query @article %} [journal articles](/publications/#journal-articles), {% bibliography_count --query @inproceedings[keywords=paper] %} [conference papers](/publications/#conference-proceedings) and {% bibliography_count --query @inproceedings[keywords=presentation] %}  [conference abstracts / presentations](/publications/#conference-presentations). 

{% assign scholar = site.data.scholar %}
{% if scholar.top_cited_bibtex_keys and scholar.top_cited_bibtex_keys.size > 0 %}
### Selected Publications
<small>Source: [Google Scholar](https://scholar.google.it/citations?user=RvAqXUIAAAAJ&hl=en) & [Scopus](https://www.scopus.com/sources.uri) | Last updated: {{ scholar.updated_at | date: "%d %B %Y" }}</small>
{% bibliography --file top_cited --template bib %}

{% endif %}
