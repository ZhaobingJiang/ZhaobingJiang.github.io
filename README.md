# Zhaobing Jiang's Personal Homepage

Personal homepage of **Zhaobing Jiang (江召兵)** — Chairman of Nanjing Opatiya Information Technology Co., Ltd., Associate Professor, and adjunct supervisor at Northwestern Polytechnical University, Nanjing University of Aeronautics and Astronautics, and Xi'an Jiaotong University.

Live at: <https://ZhaobingJiang.github.io/>

## Structure

```
├── index.html          # English homepage
├── zh/index.html       # Chinese homepage
├── publications/       # Selected publications
└── assets/css/         # Stylesheet
```

## About the design

The layout follows the [minimal-light](https://github.com/yaoyao-liu/minimal-light) academic homepage style.
It is a pure static site (plain HTML + CSS), no build step required.

## Visit counter

The homepage footer shows the site-wide visit total:

```
displayed total = BASELINE (historical visits before 2026-10-21, 2189)
                + busuanzi site_pv (live PV of every page)
```

- Every HTML page loads `assets/js/site-counter.js`; each page load reports one PV, so visits to any page (publications, projects, poems detail pages, …) count toward the same total.
- `BASELINE` lives in `assets/js/site-counter.js`; the `data-base` attribute of both homepage counters carries the same value as a fallback. Never delete or lower them, and keep `data-base` equal to `BASELINE`.
- When editing the script, bump `?v=N` in every page's `<script src="/assets/js/site-counter.js?v=N" defer></script>` so browsers load the new version.
- `scripts/verify_visit_counter.py` enforces all of the above locally and in CI (`.github/workflows/visit-counter-guard.yml`); a change that drops the historical total, skips a page, or mixes script versions fails the check.

## Deployment

Push to the `main` branch of the `ZhaobingJiang.github.io` repository — GitHub Pages serves it automatically at `https://ZhaobingJiang.github.io/`.
