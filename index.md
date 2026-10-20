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
</section>
