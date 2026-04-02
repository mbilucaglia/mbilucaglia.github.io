---
title: Contact
---

- **Email:** {{ site.data.profile.email }}
- **Office:** {{ site.data.profile.office }}
- **Location:** {{ site.data.profile.location }}

## Profiles
## Profiles
<ul class="compact-list">
{%- if site.data.profile.links.google_scholar -%}
  <li><a href="{{ site.data.profile.links.google_scholar }}">Google Scholar</a></li>
{%- endif -%}
{%- if site.data.profile.links.orcid -%}
  <li><a href="{{ site.data.profile.links.orcid }}">ORCID</a></li>
{%- endif -%}
{%- if site.data.profile.links.github -%}
  <li><a href="{{ site.data.profile.links.github }}">GitHub</a></li>
{%- endif -%}
{%- if site.data.profile.links.linkedin -%}
  <li><a href="{{ site.data.profile.links.linkedin }}">LinkedIn</a></li>
{%- endif -%}
{%- if site.data.profile.links.website -%}
  <li><a href="{{ site.data.profile.links.website }}">Website</a></li>
{%- endif -%}
</ul>
