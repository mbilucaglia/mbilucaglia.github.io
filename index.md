---
layout: default
title: Home
---

<section class="hero">
  <h1>{{ site.data.profile.name }}</h1>
  <p class="lead">{{ site.data.profile.role }}</p>
  <p>{{ site.data.profile.affiliation }}</p>
  <p>{{ site.data.profile.short_bio }}</p>

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

<section class="callout">
  <h2>Publications workflow</h2>
  <p>This site reads publications directly from <code>_bibliography/publications.bib</code>. Add, remove, or edit entries in that file, then commit and push to GitHub.</p>
  <p>If you upload PDFs to <code>assets/files/papers/</code> and name each file with its BibTeX key, the publications page will show a PDF link automatically.</p>
</section>

{% assign links = site.data.profile.links %}
{% if links %}
<section>
  <h2>Links</h2>
  <ul class="profile-links">
    {% if links.google_scholar != "" %}<li><a href="{{ links.google_scholar }}">Google Scholar</a></li>{% endif %}
    {% if links.orcid != "" %}<li><a href="{{ links.orcid }}">ORCID</a></li>{% endif %}
    {% if links.github != "" %}<li><a href="{{ links.github }}">GitHub</a></li>{% endif %}
    {% if links.linkedin != "" %}<li><a href="{{ links.linkedin }}">LinkedIn</a></li>{% endif %}
    {% if links.website != "" %}<li><a href="{{ links.website }}">Personal website</a></li>{% endif %}
  </ul>
</section>
{% endif %}
