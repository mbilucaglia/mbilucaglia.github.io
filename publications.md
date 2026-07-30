---
layout: default
title: Publications
permalink: /publications/
---

# Publications
{% assign scholar = site.data.scholar %}

## Bibliographic Indices 
<small>Source: [Google Scholar](https://scholar.google.it/citations?user=RvAqXUIAAAAJ&hl=en) | Last updated: {{ scholar.updated_at | date: "%d %B %Y" }}</small>

- **Citations:** {{ scholar.citations }}
- **h-index:** {{ scholar.h_index }}
- **i10-index:** {{ scholar.i10_index }}

## Summary
- **Journal Articles:** ,
- **Conference Proceedings:**
- **Conference Abstracts / Presentations:**

## List of Publications
{% assign scholar = site.data.scholar %}
<small>Source: [Google Scholar](https://scholar.google.it/citations?user=RvAqXUIAAAAJ&hl=en) & [Scopus](https://www.scopus.com/sources.uri) | Last updated: {{ scholar.updated_at | date: "%d %B %Y" }}</small>

### Journal Articles {#journal-articles}

{% bibliography --query @article %}

### Conference Proceedings {#conference-proceedings}

{% bibliography --query @inproceedings[keywords=paper] %}

### Conference Abstracts / Presentations {#conference-presentations}

{% bibliography --query @inproceedings[keywords=presentation] %}
