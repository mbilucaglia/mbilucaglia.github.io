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

**{{ item.title }}**  
{{ item.role }} · {{ item.year }}  
{{ item.program }} · {{ item.institution }}  
*Activities:* {{ item.activities }}{% unless item.activities contains '.' %}{% endunless %}  
*Students:* Approximately {{ item.students }}

{% endfor %}

## Executive Education

{% for item in executive %}

**{{ item.title }}**  
{{ item.role }} · {{ item.year }}  
{{ item.program }} · {{ item.institution }}  
*Activities:* {{ item.activities }}{% unless item.activities contains '.' %}{% endunless %}  
*Students:* Approximately {{ item.students }}

{% endfor %}
