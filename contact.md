---
title: Contact
---

- **Email:** {{ site.data.profile.email }}
- **Office:** {{ site.data.profile.office }}
- **Location:** {{ site.data.profile.location }}

## Profiles
{%- if site.data.profile.links.orcid -%}
  <li><a href="{{ site.data.profile.links.orcid }}">ORCID</a></li>
{%- endif -%}
<ul class="compact-list">
{%- if site.data.profile.links.google_scholar -%}
  <li><a href="{{ site.data.profile.links.google_scholar }}">Google Scholar</a></li>
{%- endif -%}
<li><a href="{https://www.scopus.com/authid/detail.uri?authorId=57188983512}">Scopus</a></li>
<li><a href="{https://www.webofscience.com/wos/author/record/HNC-3309-2023}">Web of Science</a></li>

{%- if site.data.profile.links.linkedin -%}
  <li><a href="{{ site.data.profile.links.linkedin }}">LinkedIn</a></li>
{%- endif -%}
<li><a href="{{ site.data.profile.links.website }}">Website</a></li>
</ul>
