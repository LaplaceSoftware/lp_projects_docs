# Laplace Projects Documentation

Documentation for Laplace Software projects, published as a searchable website.

**📖 Read it here: <https://lp-projects-docs.ahmed-fouad.workers.dev/>**

---

## What is in here

| Set | For | Location |
|-----|-----|----------|
| **User Guide** | Account Managers, Sales, Customer Service, Client Users, Business Administrators | [`docs/b2b_ecommerce_docs/_user_guide/`](docs/b2b_ecommerce_docs/_user_guide/) |
| **Technical Documentation** | Technical Managers, Solution Architects, developers | [`docs/b2b_ecommerce_docs/_technical_docs/`](docs/b2b_ecommerce_docs/_technical_docs/) |

Other folders under `docs/b2b_ecommerce_docs/` hold working notes, proposals and release
records. They are kept in the repository but are not part of the published site navigation.

---

## Editing the documentation

Everything is plain Markdown. Edit a file, commit to `main`, and the site rebuilds and
redeploys automatically — usually within a couple of minutes.

You can edit directly on GitHub: open any page on the site and use the ✏️ pencil icon at the
top right.

### Adding a new page

1. Add the `.md` file under `docs/`.
2. Add it to the `nav:` section of [`mkdocs.yml`](mkdocs.yml) so it appears in the sidebar.
3. Commit to `main`.

---

## Previewing locally

```bash
pip install -r requirements.txt
mkdocs serve
```

Then open <http://127.0.0.1:8000>. The preview reloads as you save.

---

## A note on redacted values

This repository is **public**. Internal host addresses appear as placeholders:

| Placeholder | Stands for |
|-------------|-----------|
| `<build-server>` | The internal build/host server address |
| `<registry-host>` | The private Docker registry address |
| `<staging-erp-build>` | The `staging-erp` Odoo.sh build identifier |

The real values live in the internal copy of these documents and in each environment's
configuration. **Do not commit them here.**

---

## Hosting

The site is served from **Cloudflare Workers** (static assets), built from `main` on every push.

| Setting | Value |
|---------|-------|
| Project | `lp-projects-docs` |
| Build command | `pip install -r requirements.txt && mkdocs build` |
| Deploy command | `npx wrangler deploy` |
| Output directory | `site` (see `wrangler.jsonc`) |

GitHub Pages is **not** used. Its deploy step timed out indefinitely for this repository on
both the workflow and the branch publishing path, while the build itself always succeeded —
the failure was server-side. The GitHub Actions workflow and the `gh-pages` branch have been
removed, because pushing to `gh-pages` made Cloudflare try to build that branch (which holds
only pre-built HTML, no `requirements.txt`) and fail.
