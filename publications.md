---
layout: default
title: Publications
permalink: /publications/
---

# Publications
## Bibliographic Indices
{% assign scholar = site.data.scholar %}

{% if scholar.citations %}
<p>
  According to
  <a
    href="{{ scholar.profile_url }}"
    target="_blank"
    rel="noopener noreferrer"
  >
    Google Scholar
  </a>,
  my publications have received
  <strong>{{ scholar.citations }}</strong> citations.
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
