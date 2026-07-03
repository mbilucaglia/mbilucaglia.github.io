---
layout: default
title: Publications
permalink: /publications/
---

# Publications
## Bibliographic Indices
- **Citations:** {{ scholar.citations }}
- **h-index:** {{ scholar.h_index }}
- **i10-index:** {{ scholar.i10_index }}
  <strong></strong> citations.
  My h-index is <strong>{{ scholar.h_index }}</strong>
  and my i10-index is <strong>{{ scholar.i10_index }}</strong>.
</p>

{% if scholar.updated_at %}
<p>
  <small>
    Metrics last updated:
    {{ scholar.updated_at | date: "%d %B %Y" }}.
  </small>
</p>
{% endif %}

## Summary

- **Total:** {% bibliography_count %}
- [**Journal Articles:**](#journal-articles) {% bibliography_count --query @article %}
- [**Conference Proceedings:**](#conference-proceedings) {% bibliography_count --query @inproceedings[keywords=paper] %}
- [**Conference Abstracts / Presentations:**](#conference-presentations) {% bibliography_count --query @inproceedings[keywords=presentation] %}

## Journal Articles {#journal-articles}

{% bibliography --query @article %}

## Conference Proceedings {#conference-proceedings}

{% bibliography --query @inproceedings[keywords=paper] %}

## Conference Abstracts / Presentations {#conference-presentations}

{% bibliography --query @inproceedings[keywords=presentation] %}
