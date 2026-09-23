# National Forest Products Tax Credit Sourcebook Website

Static, searchable website for the **National Forest Products Tax Credit Sourcebook, 2026 Edition**.

Production domain: `https://tax.lumbermen.org`

## Run locally

This site is fully static. From the repository root, serve the folder with any static server:

```bash
python -m http.server 8080
```

Then open `http://localhost:8080`.

## Content organization

- `content/programs.json` contains one structured record per retained incentive.
- `content/pages.json` contains extracted page text from the full sourcebook.
- `content/publication-sections.json` contains long-form publication sections.
- `content/site-config.json` stores the publication edition, revision date and full-PDF URL.
- `assets/js/site.js` powers browser search, filters, compare, shortlist and feedback preparation.

The generated HTML pages are indexable and shareable. Program URLs use permanent sourcebook identifiers such as `FED-RD-001`.

## Updating records

Update `content/programs.json` from the reviewed publication source, then regenerate pages or edit the generated pages consistently. Keep record IDs stable when program names change.

Required checks:

- exactly 167 retained entries for the 2026 baseline;
- seven federal entries;
- unique program IDs;
- valid 1-3 difficulty and forest-products fit ratings;
- sourcebook page references;
- official-source text retained with the relevant program;
- removed records remain absent: `AZ-QJ-001`, `AZ-REC-001`, `PA-JCTC-001`, `VT-DT-001`.

## Feedback

This static build prepares a correction email with page and program context. No fake submission endpoint is included. To enable direct form delivery later, add a serverless endpoint or form service and store the destination/keys outside public source control.

Suggested environment variables for a future hosted endpoint:

```bash
FEEDBACK_EMAIL=
FEEDBACK_PROVIDER_API_KEY=
```

## Deployment

The site can deploy from GitHub Pages or any static host.

For GitHub Pages:

1. Push this repository to GitHub.
2. In repository settings, enable Pages for the default branch root.
3. Add the custom domain `tax.lumbermen.org`.
4. Create a DNS `CNAME` record for `tax` pointing to the GitHub Pages hostname shown in settings.
5. Enable HTTPS after DNS validates.

If using another static host, keep canonical URLs and sitemap entries pointed at `https://tax.lumbermen.org`.

## Publication limits

This is a screening guide, not tax advice or a guarantee of eligibility. Confirm current rules with the administering agency and a qualified tax adviser before committing funds or filing a return.
