---
layout: default
title: Teaching
permalink: /teaching/
---

# Teaching

My teaching at Università IULM spans master's degree programmes and executive education, with a focus on machine learning, neuroscience, and psychophysiological methods.

{% assign academic = site.data.teaching | where: "track", "academic" %}
{% assign executive = site.data.teaching | where: "track", "executive" %}

## Master's Degree Programmes

{% for item in academic %}
<article class="teaching-item">
  <h3>{{ item.title }}</h3>
  <p class="teaching-meta"><strong>{{ item.role }}</strong> · {{ item.level }} · {{ item.institution }} · {{ item.year }}</p>
  <ul class="compact-list teaching-details">
    {% if item.program %}<li><strong>Programme:</strong> {{ item.program }}</li>{% endif %}
    {% if item.instructor %}<li><strong>Instructor:</strong> {{ item.instructor }}</li>{% endif %}
    {% if item.activities %}<li><strong>Activities:</strong> {{ item.activities }}</li>{% endif %}
    {% if item.students %}<li><strong>Approx. class size:</strong> {{ item.students }} students</li>{% endif %}
    {% if item.topics %}<li><strong>Topics:</strong> {{ item.topics }}</li>{% endif %}
  </ul>
</article>
{% endfor %}

## Executive Education

{% for item in executive %}
<article class="teaching-item">
  <h3>{{ item.title }}</h3>
  <p class="teaching-meta"><strong>{{ item.role }}</strong> · {{ item.level }} · {{ item.institution }} · {{ item.year }}</p>
  <ul class="compact-list teaching-details">
    {% if item.program %}<li><strong>Programme:</strong> {{ item.program }}</li>{% endif %}
    {% if item.activities %}<li><strong>Activities:</strong> {{ item.activities }}</li>{% endif %}
    {% if item.students %}<li><strong>Approx. class size:</strong> {{ item.students }} students</li>{% endif %}
    {% if item.topics %}<li><strong>Topics:</strong> {{ item.topics }}</li>{% endif %}
  </ul>
</article>
{% endfor %}
