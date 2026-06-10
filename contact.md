---
layout: default
title: Contact
permalink: /contact/
---

# Contact

- **Email:** [{{ site.data.profile.email }}](mailto:{{ site.data.profile.email }})
- **Office:** {{ site.data.profile.office }}
- **Location:** {{ site.data.profile.location }}

<div class="map-container">
  <iframe
    src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d588.483638882754!2d9.166579684632861!3d45.443293569929004!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x4786c3ed336e890d%3A0xff25cabf8cbc6ede!2sBehavior%20and%20Brain%20Lab%20-%20IULM%20Edificio%207!5e0!3m2!1sit!2sit!4v1781079908907!5m2!1sit!2sit" width="600" height="450" style="border:0;" allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade"
    style="border:0;"
    allowfullscreen=""
    loading="lazy"
    referrerpolicy="no-referrer-when-downgrade">
  </iframe>
</div>

## Profiles

<ul class="compact-list">
  {%- if site.data.profile.links.orcid -%}
    <li><a href="{{ site.data.profile.links.orcid }}">ORCID</a></li>
  {%- endif -%}
  {%- if site.data.profile.links.google_scholar -%}
    <li><a href="{{ site.data.profile.links.google_scholar }}">Google Scholar</a></li>
  {%- endif -%}
  <li><a href="https://www.scopus.com/authid/detail.uri?authorId=57188983512">Scopus</a></li>
  <li><a href="https://www.webofscience.com/wos/author/record/HNC-3309-2023">Web of Science</a></li>
  <li><a href="https://www.researchgate.net/profile/Marco-Bilucaglia">Research Gate</a></li>
  {%- if site.data.profile.links.linkedin -%}
    <li><a href="{{ site.data.profile.links.linkedin }}">LinkedIn</a></li>
  {%- endif -%}

</ul>
