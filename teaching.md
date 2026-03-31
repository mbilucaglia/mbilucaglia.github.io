---
title: Teaching
---

Edit <code>_data/teaching.yml</code> to update this page.

{% assign courses = site.data.teaching | default: empty %}
{% if courses.size == 0 %}
No teaching entries added yet.
{% endif %}
{% for course in courses %}
<div class="teaching-item">
  <h2>{{ course.course }}</h2>
  <p><strong>{{ course.term }}</strong> — {{ course.role }}</p>
  <p>{{ course.institution }}</p>
  <p>{{ course.notes }}</p>
</div>
{% endfor %}
