---
layout: default
title: Publications
permalink: /publications/
---

# Publications
{% assign scholar = site.data.scholar %}

{% if scholar.citations %}
## Bibliographic Indices 
[source: [Google Scholar](https://scholar.google.it/citations?user=RvAqXUIAAAAJ&hl), updated: {{ scholar.updated_at | date: "%d %B %Y" }}]

- **Citations:** {{ scholar.citations }}
- **h-index:** {{ scholar.h_index }}
- **i10-index:** {{ scholar.i10_index }}

## Journal Articles {#journal-articles}

{% bibliography --query @article %}

## Conference Proceedings {#conference-proceedings}

{% bibliography --query @inproceedings[keywords=paper] %}

## Conference Abstracts / Presentations {#conference-presentations}

{% bibliography --query @inproceedings[keywords=presentation] %}
