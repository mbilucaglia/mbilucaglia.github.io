---
layout: default
title: Publications
---

- **Total:** {% bibliography_count %}
- **Journal Articles:** {% bibliography_count --query @article %}
- **Conference Proceedings:** {% bibliography_count --query @inproceedings[keywords=paper] %}
- **Conference Abstracts:** {% bibliography_count --query @inproceedings[keywords=presentation] %}
- **Working Manuscripts:** {% bibliography_count --query @unpublished %}

## Journal Articles
{% bibliography --query @article %}

## Conference Proceedings
{% bibliography --query @inproceedings[keywords=paper] %}

## Conference Abstracts
{% bibliography --query @inproceedings[keywords=presentation] %}

## Working Manuscripts
{% bibliography --query @unpublished %}
