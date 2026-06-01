# weave_docs
WEAVE documentations

This repo contains the public documentation for WEAVE.

You can find [tutorials in this directory](docs/tutorials/) as well.

## Versioned docs (Mike)

Some downstream docs (e.g. `StudyWeaver`) are built with `mike` so multiple published versions can coexist in the final static site.

`utils/build_docs.py` runs (for repos whose docs build command includes `mike deploy`):

- `git fetch origin gh-pages` (best-effort) to preserve previously published versions
- `mike deploy --push <version> latest --update-aliases` to update the repo’s `gh-pages`
- exports the resulting `gh-pages` content into `build_docs_dir/<RepoName>/` (this is what `deploy_docs` later copies)

Bootstrap note: the target repo needs an initial `gh-pages` history (created by the first `mike deploy --push ...`) before subsequent runs can diff against older versions.

Hosting note: Mike may represent aliases like `latest/` as symlinks in the `gh-pages` checkout. `utils/build_docs.py` dereferences top-level alias symlinks into real directories in the exported static tree, since symlinks are commonly not served on static web hosts.
