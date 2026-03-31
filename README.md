# Academic website with BibTeX publications

This version is designed for the workflow you chose:

- edit your profile in `_data/profile.yml`
- edit your publications in `_bibliography/publications.bib`
- edit your teaching in `_data/teaching.yml`
- edit `cv.md` and `contact.md` in Markdown
- push to GitHub
- GitHub Actions builds and deploys the site to GitHub Pages

## Why this version uses GitHub Actions

GitHub Pages can use custom GitHub Actions workflows, and GitHub's docs describe the standard pattern: check out the repo, build the site, upload the built artifact, and deploy it to Pages. The default GitHub Pages Jekyll build does not allow unsupported plugins. Jekyll-Scholar's documentation explicitly notes that it does not work with the default GitHub Pages workflow.

That is why this site includes:

- `Gemfile`
- `.github/workflows/pages.yml`
- Jekyll-Scholar configuration in `_config.yml`

## First-time setup

1. Unzip this package on your computer.
2. Open your `<username>.github.io` repository on GitHub.
3. Delete the old example files from the repository root.
4. Upload the **contents** of this folder to the repository root.
5. In GitHub: **Settings → Pages → Source → GitHub Actions**.
6. Commit and push.
7. Wait for the Actions workflow to finish.
8. Open your site.

## Files you will edit most often

- `_data/profile.yml`
- `_bibliography/publications.bib`
- `_data/teaching.yml`
- `cv.md`
- `contact.md`

## How to add publications

Open `_bibliography/publications.bib` and paste your BibTeX entries there.

Example:

```bibtex
@article{surname2026paper,
  author   = {Surname, Name and Coauthor, Name},
  title    = {Paper title},
  journal  = {Journal name},
  year     = {2026},
  doi      = {10.1234/example},
  url      = {https://example.com/paper}
}
```

## Optional extra fields

You can also use these optional custom fields in your BibTeX entries:

- `abstract`
- `code`
- `slides`
- `selected`

The publications template will display links for `code` and `slides`, and an expandable abstract if `abstract` is present.

## Automatic PDF links

If you want a PDF link to appear automatically, put the PDF in:

`assets/files/papers/`

and name the file with the same BibTeX key as the publication, for example:

- BibTeX key: `surname2026paper`
- PDF file: `assets/files/papers/surname2026paper.pdf`

## Citation style

The citation style is configured in `_config.yml` under:

```yml
scholar:
  style: apa
```

You can change `apa` to another CSL style supported by Jekyll-Scholar.

## Notes

- For a user site like `<username>.github.io`, keep `baseurl: ""`.
- For a project site like `username.github.io/project-name`, set `baseurl: "/project-name"`.
- If your default branch is `main`, this workflow will work as-is. It also listens to `master`.
