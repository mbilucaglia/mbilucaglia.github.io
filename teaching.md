---
layout: default
title: Teaching
permalink: /teaching/
---

# Teaching

{% assign academic = site.data.teaching | where: "track", "academic" %}
{% assign executive = site.data.teaching | where: "track", "executive" %}

## Master's Degree Programmes

{% for item in academic %}
<div class="teaching-item">
  <strong class="teaching-course-title">{{ item.title }}</strong>
  <div>{{ item.role }} · {{ item.year }}</div>
  <div>{{ item.program }} · {{ item.institution }}</div>
  <div class="teaching-activity"><em>Activities:</em> {{ item.activities }}{% unless item.activities contains '.' %}.{% endunless %}</div>
  <div><em>Students:</em> Approximately {{ item.students }}.</div>
</div>
{% endfor %}

## Executive Education

{% for item in executive %}
<div class="teaching-item">
  <strong class="teaching-course-title">{{ item.title }}</strong>
  <div>{{ item.role }} · {{ item.year }}</div>
  <div>{{ item.program }} · {{ item.institution }}</div>
  <div class="teaching-activity"><em>Activities:</em> {{ item.activities }}{% unless item.activities contains '.' %}.{% endunless %}</div>
  <div><em>Students:</em> Approximately {{ item.students }}.</div>
</div>
{% endfor %}
