---
layout: default
title: Publications
permalink: /publications/
---

# Publications
{% assign scholar = site.data.scholar %}

{% if scholar.citations %}
## Bibliographic Indices [Source: Google Scholar, {{ scholar.updated_at | date: "%d %B %Y" }}]

- **Citations:** {{ scholar.citations }}
- **h-index:** {{ scholar.h_index }}
- **i10-index:** {{ scholar.i10_index }}

{% if scholar.updated_at %}
<small>
  Metrics last updated:
  {{ scholar.updated_at | date: "%d %B %Y" }}.
</small>
{% endif %}
{% endif %}

## Journal Articles {#journal-articles}

{% bibliography --query @article %}

## Conference Proceedings {#conference-proceedings}

{% bibliography --query @inproceedings[keywords=paper] %}

## Conference Abstracts / Presentations {#conference-presentations}

{% bibliography --query @inproceedings[keywords=presentation] %}
