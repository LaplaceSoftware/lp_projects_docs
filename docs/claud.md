# Claud

This page documents the Cloudflare project setup and sharing workflow for the Laplace documentation site.

## Purpose

- Capture the Cloudflare deployment and publishing approach.
- Provide a reference page for collaborators who need to understand how the site is built and deployed.

## Notes

- The site is built from `main` and served from Cloudflare Workers.
- The deployment is managed with `wrangler` and the `wrangler.jsonc` configuration file.
- The build command is defined in the Cloudflare project and uses the `site` output directory.

## Related files

- `mkdocs.yml`
- `wrangler.jsonc`
- `README.md`

## Share documentation

Push changes to `main` to trigger the Cloudflare project to rebuild and publish the updated documentation.
