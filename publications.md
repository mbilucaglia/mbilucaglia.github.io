---
layout: default
title: Publications
permalink: /publications/
---

# Publications
{% assign scholar = site.data.scholar %}

## Bibliographic Indices
<small>Source: [Google Scholar](https://scholar.google.it/citations?user=RvAqXUIAAAAJ&hl=en) | Last updated: {{ scholar.updated_at | date: "%d %B %Y" }}</small>

- **Citations:** {{ scholar.citations }}
- **h-index:** {{ scholar.h_index }}
- **i10-index:** {{ scholar.i10_index }}


## Summary
- [**Journal Articles:**](/publications/#journal-articles) <span data-publication-count="journal">{% bibliography_count --query @article %}</span>
- [**Conference Proceedings:**](/publications/#conference-proceedings) <span data-publication-count="proceedings">{% bibliography_count --query @inproceedings[keywords=paper] %}</span>
- [**Conference Abstracts / Presentations:**](/publications/#conference-presentations) <span data-publication-count="presentations">{% bibliography_count --query @inproceedings[keywords=presentation] %}</span>


## List of Publications
<small>Source: [Google Scholar](https://scholar.google.it/citations?user=RvAqXUIAAAAJ&hl=en) & [Scopus](https://www.scopus.com/sources.uri) | Last updated: {{ scholar.updated_at | date: "%d %B %Y" }}</small>

<div class="publication-search" role="search">
  <label for="publication-search-input" class="visually-hidden">
    Search publications
  </label>

  <div class="publication-search-field">
    <svg
      class="publication-search-icon"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <circle cx="11" cy="11" r="7"></circle>
      <path d="M20 20l-4-4"></path>
    </svg>

    <input
      type="search"
      id="publication-search-input"
      class="publication-search-input"
      placeholder="Search publications..."
      autocomplete="off"
      spellcheck="false"
    >
  </div>
</div>


### Journal Articles {#journal-articles}
<small>† Equal contribution (co-first author) | * Corresponding author</small>

<div
  class="publication-section"
  data-publication-section="journal"
>
{% bibliography --query @article %}

<p class="publication-section-empty" hidden>
  No matching Journal Articles.
</p>
</div>


### Conference Proceedings {#conference-proceedings}
<small>† Equal contribution (co-first author) | * Corresponding author</small>

<div
  class="publication-section"
  data-publication-section="proceedings"
>
{% bibliography --query @inproceedings[keywords=paper] %}

<p class="publication-section-empty" hidden>
  No matching Conference Proceedings.
</p>
</div>


### Conference Abstracts / Presentations {#conference-presentations}
<small>† Equal contribution (co-first author) | * Corresponding author</small>

<div
  class="publication-section"
  data-publication-section="presentations"
>
{% bibliography --query @inproceedings[keywords=presentation] %}

<p class="publication-section-empty" hidden>
  No matching Conference Abstracts / Presentations.
</p>
</div>


<script src="{{ '/assets/js/publications.js' | relative_url }}"></script>
