document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.getElementById("publication-search-input");

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
    const terms = normalizeText(searchInput.value.trim())
      .split(/\s+/)
      .filter(Boolean);

    sections.forEach((section) => {
      const sectionName = section.dataset.publicationSection;

      const publications = section.querySelectorAll(
        ".bibliography > li"
      );

      const emptyMessage = section.querySelector(
        ".publication-section-empty"
      );

      let visibleCount = 0;

      publications.forEach((publication) => {
        const reference = publication.querySelector(
          ".publication-reference"
        );

        const abstract = publication.querySelector(
          ".publication-abstract"
        );

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
          visibleCount++;
        }
      });

      document
        .querySelectorAll(
          `[data-publication-count="${sectionName}"]`
        )
        .forEach((counter) => {
          counter.textContent = visibleCount;
        });

      if (emptyMessage) {
        emptyMessage.hidden =
          terms.length === 0 || visibleCount > 0;
      }
    });
  }

  searchInput.addEventListener(
    "input",
    filterPublications
  );

  searchInput.addEventListener(
    "keydown",
    (event) => {
      if (event.key === "Escape") {
        searchInput.value = "";
        filterPublications();
      }
    }
  );
});
