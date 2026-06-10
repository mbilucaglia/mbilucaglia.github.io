---
layout: default
title: Home
---

<section class="hero">
  <h1>{{ site.data.profile.name }}</h1>
  <p class="lead">{{ site.data.profile.role }}</p>
  <p>{{ site.data.profile.affiliation }}</p>

{% if site.data.profile.photo %}
<figure class="profile-photo-frame">
  <img
    src="{{ site.data.profile.photo | relative_url }}"
    alt="{{ site.data.profile.name | escape }}">
</figure>
{% endif %}

  <div class="short-bio">
    {{ site.data.profile.short_bio | markdownify }}
  </div>

  {% assign interests = site.data.profile.research_interests | default: empty %}
  {% if interests.size > 0 %}
  <h2>Research Interests</h2>
  <ul class="interests-list">
    {% for item in interests %}
    <li>{{ item }}</li>
    {% endfor %}
  </ul>
  {% endif %}

  <div class="button-row">
    <a class="button" href="{{ '/publications/' | relative_url }}">View Publications</a>
    <a class="button button-secondary" href="{{ '/contact/' | relative_url }}">Contact</a>
  </div>
</section>
