---
title: Contact
---

- **Email:** {{ site.data.profile.email }}
- **Office:** {{ site.data.profile.office }}
- **Location:** {{ site.data.profile.location }}

## Profiles
## Profiles
{%- if site.data.profile.links.google_scholar != "" -%}
- [Google Scholar]({{ site.data.profile.links.google_scholar }})
{%- endif -%}
{%- if site.data.profile.links.orcid != "" -%}
- [ORCID]({{ site.data.profile.links.orcid }})
{%- endif -%}
{%- if site.data.profile.links.github != "" -%}
- [GitHub]({{ site.data.profile.links.github }})
{%- endif -%}
{%- if site.data.profile.links.linkedin != "" -%}
- [LinkedIn]({{ site.data.profile.links.linkedin }})
{%- endif -%}
{%- if site.data.profile.links.website != "" -%}
- [Website]({{ site.data.profile.links.website }})
{%- endif -%}
