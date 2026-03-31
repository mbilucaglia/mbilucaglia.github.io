---
layout: default
title: Teaching
permalink: /teaching/
---

# Teaching

{% assign academic = site.data.teaching | where: "track", "academic" %}
{% assign professional = site.data.teaching | where: "track", "postgrad_professional" %}
{% assign phd = site.data.teaching | where: "track", "phd" %}

## Academic Courses

{% if academic and academic.size > 0 %}
  {% for item in academic %}
  - **{{ item.title }}**  
    {{ item.level }}, {{ item.role }}  
    {{ item.institution }}, {{ item.year }}  
    **Length:** {{ item.hours }} hours{% if item.sessions %} ({{ item.sessions }} sessions){% endif %}{% if item.notes %}  
    *{{ item.notes }}*{% endif %}
  {% endfor %}
{% else %}
No academic courses listed yet.
{% endif %}

## Postgraduate / Professional Courses

{% if professional and professional.size > 0 %}
  {% for item in professional %}
  - **{{ item.title }}**  
    {{ item.level }}, {{ item.role }}  
    {{ item.institution }}, {{ item.year }}  
    **Length:** {{ item.hours }} hours{% if item.sessions %} ({{ item.sessions }} sessions){% endif %}{% if item.notes %}  
    *{{ item.notes }}*{% endif %}
  {% endfor %}
{% else %}
No postgraduate or professional courses listed yet.
{% endif %}

## Ph.D. Courses

{% if phd and phd.size > 0 %}
  {% for item in phd %}
  - **{{ item.title }}**  
    {{ item.level }}, {{ item.role }}  
    {{ item.institution }}, {{ item.year }}  
    **Length:** {{ item.hours }} hours{% if item.sessions %} ({{ item.sessions }} sessions){% endif %}{% if item.notes %}  
    *{{ item.notes }}*{% endif %}
  {% endfor %}
{% else %}
No Ph.D. courses listed yet.
{% endif %}
