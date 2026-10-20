---
layout: default
title: Home
---

<section class="hero">
  <h1>{{ site.data.profile.name }}</h1>
  <p class="lead">{{ site.data.profile.role }}</p>
  <p>{{ site.data.profile.affiliation }}</p>

{% include profile-photo.html %}

  <div class="short-bio">
    {{ site.data.profile.short_bio | markdownify }}
  </div>

  {% assign interests = site.data.profile.research_interests | default: empty %}
  {% if interests.size > 0 %}
  <h2>Research Interests</h2>
  <div class="research-grid">
    {% for item in interests %}
    <article class="research-interest-card">
      <h3>{{ item.name }}</h3>
      {% if item.description %}
      <p>{{ item.description }}</p>
      {% endif %}
    </article>
    {% endfor %}
  </div>
  {% endif %}

  <div class="button-row">
    <a class="button" href="{{ '/publications/' | relative_url }}">View Publications</a>
    <a class="button button-secondary" href="{{ '/teaching/' | relative_url }}">Teaching</a>
    <a class="button button-secondary" href="{{ '/cv/' | relative_url }}">CV</a>
    <a class="button button-secondary" href="{{ '/contact/' | relative_url }}">Contact</a>
  </div>
</section>
