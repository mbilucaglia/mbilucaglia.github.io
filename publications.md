---
layout: default
title: Publications
permalink: /publications/
---

# Publications
## Summary

- **Total:** {% bibliography_count %}
- **Journal Articles(#journal-articles):** {% bibliography_count --query @article %}
- **Conference Proceedings(#conference-proceedings):** {% bibliography_count --query @inproceedings[keywords=paper] %}
- **Conference Abstracts / Presentations(#conference-presentations):** {% bibliography_count --query @inproceedings[keywords=presentation] %}

## Journal Articles {#journal-articles}

{% bibliography --query @article %}

## Conference Proceedings {#conference-proceedings}

{% bibliography --query @inproceedings[keywords=paper] %}

## Conference Abstracts / Presentations {#conference-presentations}

{% bibliography --query @inproceedings[keywords=presentation] %}
