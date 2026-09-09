document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.getElementById("publication-search-input");
  const searchStatus = document.getElementById("publication-search-status");
  const noResults = document.getElementById("publication-no-results");

  if (!searchInput) {
    return;
  }

  const sections = document.querySelectorAll(
    "[data-publication-section]"
  );

  function normalizeText(text) {
    return text
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase();
  }

  function filterPublications() {
    const rawQuery = searchInput.value.trim();
    const normalizedQuery = normalizeText(rawQuery);

    const terms = normalizedQuery
      .split(/\s+/)
      .filter(Boolean);

    let totalVisible = 0;

    sections.forEach((section) => {
      const sectionName = section.dataset.publicationSection;
      const publications = section.querySelectorAll(".bibliography > li");

      let sectionVisible = 0;

      publications.forEach((publication) => {
        const reference =
          publication.querySelector(".publication-reference");

        const abstract =
          publication.querySelector(".publication-abstract");

        const searchableText = normalizeText(
          [
            reference ? reference.textContent : "",
            abstract ? abstract.textContent : ""
          ].join(" ")
        );

        const matches = terms.every((term) =>
          searchableText.includes(term)
        );

        publication.hidden = !matches;

        if (matches) {
          sectionVisible++;
          totalVisible++;
        }
      });

      document
        .querySelectorAll(
          `[data-publication-count="${sectionName}"]`
        )
        .forEach((counter) => {
          counter.textContent = sectionVisible;
        });
    });

    if (rawQuery === "") {
      searchStatus.textContent =
        `${totalVisible} publication${totalVisible === 1 ? "" : "s"}`;
    } else {
      searchStatus.textContent =
        `${totalVisible} result${totalVisible === 1 ? "" : "s"} for “${rawQuery}”`;
    }

    noResults.hidden = totalVisible !== 0;
  }

  searchInput.addEventListener("input", filterPublications);

  searchInput.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && searchInput.value !== "") {
      searchInput.value = "";
      filterPublications();
    }
  });

  filterPublications();
});
