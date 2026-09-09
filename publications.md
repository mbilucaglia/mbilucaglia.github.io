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

<div class="publication-search">
  <label for="publication-search-input" class="publication-search-label">
    Search publications
  </label>

  <input
    type="search"
    id="publication-search-input"
    class="publication-search-input"
    placeholder="Search by title, author, year, journal, keyword..."
    autocomplete="off"
    spellcheck="false"
  >

  <small
    id="publication-search-status"
    class="publication-search-status"
    aria-live="polite"
  ></small>
</div>

<p
  id="publication-no-results"
  class="publication-no-results"
  hidden
>
  No publications match your search.
</p>


### Journal Articles (<span data-publication-count="journal">{% bibliography_count --query @article %}</span>) {#journal-articles}

<small>† Equal contribution (co-first author) | * Corresponding author</small>

<div
  class="publication-section"
  data-publication-section="journal"
>
{% bibliography --query @article %}
</div>


### Conference Proceedings (<span data-publication-count="proceedings">{% bibliography_count --query @inproceedings[keywords=paper] %}</span>) {#conference-proceedings}

<small>† Equal contribution (co-first author) | * Corresponding author</small>

<div
  class="publication-section"
  data-publication-section="proceedings"
>
{% bibliography --query @inproceedings[keywords=paper] %}
</div>


### Conference Abstracts / Presentations (<span data-publication-count="presentations">{% bibliography_count --query @inproceedings[keywords=presentation] %}</span>) {#conference-presentations}

<small>† Equal contribution (co-first author) | * Corresponding author</small>

<div
  class="publication-section"
  data-publication-section="presentations"
>
{% bibliography --query @inproceedings[keywords=presentation] %}
</div>


<script src="{{ '/assets/js/publications.js' | relative_url }}"></script>
