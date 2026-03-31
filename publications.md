---
layout: default
title: Publications
---

- **Total:** {% bibliography_count %}
- **Journal Articles:** {% bibliography_count --query @article %}
- **Conference Proceedings:** {% bibliography_count --query @inproceedings[subtype=paper] %}
- **Conference Abstracts:** {% bibliography_count --query @inproceedings[subtype=presentation] %}
- **Working Manuscripts:** {% bibliography_count --query @unpublished %}

## Journal Articles
{% bibliography --query @article %}

## Conference Proceedings
{% bibliography --query @inproceedings[subtype=paper] %}

## Conference Abstracts
{% bibliography --query @inproceedings[subtype=presentation] %}

## Working Manuscripts
{% bibliography --query @unpublished %}
