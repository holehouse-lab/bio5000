# BIO5000 journal club website

A one-page site for the Spring 2027 BIO5000 journal club (transcriptional regulation & disordered proteins). Everything you'd want to change lives in one file, `index.md`. The rest of the repo just turns that file into a web page.

## Editing the site

Open `index.md`. The block at the top between the two `---` lines holds the facts shown in the page header; everything below it is the page content in plain Markdown.

```yaml
---
course: BIO5000 Journal Club
semester: Spring 2027
title: Transcriptional regulation & disordered proteins
tagline: An interdisciplinary journal club where we present ideas, not papers.
schedule_year: 2027                 # used to work out which session is next
details:                            # shown under the title; add, remove, or rename rows freely
  When: Tuesdays · 2 – 3 pm
  Where: McDonnell Sciences 264
  Runs: Jan 19 – May 11
  Course master: Alex Holehouse
---
```

If a value in `details` contains a colon followed by a space, or looks like a number or a time (e.g. `14:00`), wrap it in quotes. The build will stop and tell you if it can't read something.

### Filling in the schedule

The schedule is a Markdown table with one row per week. Swap `TBD` for the presenter and the paper, and link the paper with `[text](url)`:

```markdown
| Date | Presenter | Paper |
| --- | --- | --- |
| Jan 19 | Jane Doe | Author, A. B. et al. [Title of the paper](https://doi.org/10.xxxx/xxxxx). *Journal* **12**, 345–678 (2026). |
| Jan 26 | TBD | TBD |
```

Keep dates in the `Jan 19` style. The page uses them to grey out past sessions and flag the next one. To skip a week, delete its row (or write something like `No meeting` in the presenter column).

### Adding an announcement

Add a line to the top of the list under `## Announcements`:

```markdown
- **2027-01-12:** First meeting is in a different room this week.
```

### Adding or renaming sections

Every `## Heading` becomes a numbered section and gets a link in the navigation bar automatically.

### Changing the header figure

The banner under the title is `static/hero.png` (the source artwork is in `logo/`). To change it, save a new PNG over that file (same name, all lowercase) and rebuild. It's shown at the full width of the page (about 740 px), so exporting at around 1500 px wide keeps it sharp on high-resolution screens. Use a white background: it blends into the page colour, and on the dark theme the image is colour-inverted so white becomes the dark page and dark lines become light. The bottom edge of the image sits right on the rule above the details, so artwork that runs off the bottom looks anchored. If the file's missing, the build prints a warning and the page renders without a figure.

## Building it locally

You only need this to preview changes before pushing; GitHub rebuilds the site for you on every push.

```bash
pip install -r requirements.txt   # one-off: installs markdown and pyyaml
python build.py                   # writes the site to _site/
open _site/index.html             # take a look
```

## Putting it on GitHub Pages

This is a one-time setup. After it, every push to `main` rebuilds and republishes the site.

1. Create a new, empty repository on GitHub (no README or license, so there's nothing to merge). It needs to be public unless your account or organization has a paid plan.
2. From this directory, make the first commit and push it:

    ```bash
    git init -b main
    git add .
    git commit -m "BIO5000 2027 journal club site"
    git remote add origin git@github.com:<your-username>/<repo-name>.git
    git push -u origin main
    ```

3. On GitHub, go to the repository's **Settings → Pages**, and under **Build and deployment** set **Source** to **GitHub Actions**.
4. Go to the **Actions** tab. If the first run failed (it will if it started before step 3), open it and click **Re-run all jobs**. When it goes green, the site is live at `https://<your-username>.github.io/<repo-name>/`.

From then on the whole workflow is: edit `index.md`, commit, push. The site updates a minute or so later.

## What's in here

| File | What it does |
| --- | --- |
| `index.md` | All the content. The only file you normally edit. |
| `template.html` | The page skeleton the content gets dropped into. |
| `static/style.css` | Fonts, colours, and layout (with a dark mode that follows the reader's system setting). |
| `static/hero.png` | The banner figure shown under the title. |
| `logo/` | Source artwork for the banner (not published). |
| `static/favicon.svg` | The browser-tab icon. |
| `build.py` | Turns `index.md` + `template.html` into `_site/index.html`. |
| `.github/workflows/deploy.yml` | Tells GitHub to run `build.py` and publish `_site/` on every push to `main`. |
