---
layout: default
title: Publications
permalink: /publications/
---

# Publications

## Summary

- **Total:** {% bibliography_count %}
- **Journal Articles:** {% bibliography_count --query @article %}
- **Conference Proceedings:** {% bibliography_count --query @inproceedings[keywords=paper] %}
- **Conference Abstracts / Presentations:** {% bibliography_count --query @inproceedings[keywords=presentation] %}
- **Working Manuscripts:** {% bibliography_count --query @unpublished %}

## Journal Articles

{% bibliography --query @article %}

## Conference Proceedings

{% bibliography --query @inproceedings[keywords=paper] %}

## Conference Abstracts / Presentations

{% bibliography --query @inproceedings[keywords=presentation] %}

## Working Manuscripts

{% bibliography --query @unpublished %}
