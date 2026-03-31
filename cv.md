---
title: CV
---

You can either:
1. Upload a PDF to <code>assets/files/cv.pdf</code> and link it below.
2. Write a short CV directly on this page in Markdown.

## Education
- PhD in [Your Field], [University], [Year]
- MSc in [Your Field], [University], [Year]

## Academic Positions
- Position, Institution, Years

## Awards
- Award or grant, Year

## Service
- Reviewer, committee, or organizer roles

{% if site.data.profile.links.cv_pdf != "" %}
[Download CV PDF]({{ site.data.profile.links.cv_pdf | relative_url }})
{% endif %}
