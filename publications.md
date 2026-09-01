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

Co-author of {% bibliography_count %} peer-reviewes publications, including {% bibliography_count --query @article %} [journal articles](/publications/#journal-articles), {% bibliography_count --query @inproceedings[keywords=paper] %} [conference papers](/publications/#conference-proceedings) and {% bibliography_count --query @inproceedings[keywords=presentation] %}  [conference abstracts / presentations](/publications/#conference-presentations). 

## Summary
- **Journal Articles:** {% bibliography_count --query @article %}
- **Conference Proceedings:** {% bibliography_count --query @inproceedings[keywords=paper] %}
- **Conference Abstracts / Presentations:**  {% bibliography_count --query @inproceedings[keywords=presentation] %} 

## List of Publications
{% assign scholar = site.data.scholar %}
<small>Source: [Google Scholar](https://scholar.google.it/citations?user=RvAqXUIAAAAJ&hl=en) & [Scopus](https://www.scopus.com/sources.uri) | Last updated: {{ scholar.updated_at | date: "%d %B %Y" }}</small>

### Journal Articles {#journal-articles}

{% bibliography --query @article %}

### Conference Proceedings {#conference-proceedings}

{% bibliography --query @inproceedings[keywords=paper] %}

### Conference Abstracts / Presentations {#conference-presentations}

{% bibliography --query @inproceedings[keywords=presentation] %}
