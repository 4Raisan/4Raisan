# Maintaining this profile

This repository is the GitHub profile for 4Raisan. The profile copy lives in
README.md; the featured application source lives in the linked repositories.

## Requirements and settings

Use Python 3.10 or newer. No Python packages need to be installed.
Edit profile.json for the GitHub username, header text, and fixed UTC offset.
Update the introduction, links, and image alt text in README.md when changing
profile identity. Long header text may need layout adjustments in build_design.py.

The default timezone is Sri Lanka, UTC+05:30. Fixed offsets do not track daylight
saving time. Contribution calendar dates are used exactly as GitHub returns them.
The query requests the trailing 365 days through the end of the current local day, including
activity GitHub has already processed today.

## Local checks and artwork

Run from the repository root:

```powershell
python -m unittest discover -s tests -v
python scripts/build_design.py
```

Artwork generation updates the three assets/header SVGs without network access.
Tool icons are checked in; their source and license are in assets/SOURCES.md.

## Refresh activity locally

Provide a GitHub token through GITHUB_TOKEN. Do not save it in this repository.
If GitHub CLI is already authenticated, PowerShell users can run:

```powershell
$env:GITHUB_TOKEN = gh auth token
try {
    python scripts/generate_stats.py
    if ($LASTEXITCODE -ne 0) { throw 'Activity generation failed' }
    python scripts/publish_activity.py
    if ($LASTEXITCODE -ne 0) { throw 'Activity publishing failed' }
} finally {
    Remove-Item Env:GITHUB_TOKEN -ErrorAction SilentlyContinue
}
```

Generation writes ignored staging files under .generated/. Publishing validates
the calendar, statistics, dates, SVGs, and README timestamp marker before updating
assets/stats.svg, assets/calendar.svg, assets/snake.svg, and README.md.

Each replacement is atomic. A journal retains the previous snapshot until all
four writes finish; a caught failure rolls back, and the next publishing attempt
recovers after a process interruption. Multiple files cannot change atomically as
one filesystem operation. Do not run publishers concurrently or delete .generated/
while its publish-backup.json recovery journal exists.

## GitHub automation

The Refresh profile activity workflow runs at minute 17 every six hours (UTC),
can be started manually from Actions, and runs when its workflow, scripts, tests,
or profile.json change. It tests first, generates artwork, fetches activity using
the built-in GITHUB_TOKEN, validates the snapshot, and commits changed outputs.
It requires repository contents write permission. Overlapping refreshes are queued.

README-only edits do not automatically refresh statistics. Editing profile.json
does regenerate artwork and activity. The public profile can display cached images
briefly after a successful commit.

## Troubleshooting

- Missing token or authentication failure: check GITHUB_TOKEN and its permissions.
- Temporary network, server, or rate-limit failure: requests use up to four attempts
  with bounded delays. A persistent failure stops the job; existing committed cards
  remain available. Inspect the Actions log before retrying manually.
- Validation failure: inspect staged data and rerun generation. Do not bypass checks
  or edit SVG counts by hand.
- Timestamp failure: retain exactly one activity-date comment pair in README.md.
- Missing activity: these cards show public contribution fields. GitHub controls
  contribution eligibility, processing delays, and calendar dates.

The tests use synthetic responses and temporary folders, including leap-day dates,
network failures, invalid statistics, interrupted publishing, and rollback failures
at the file-replacement boundary. They do not require credentials or modify the
published profile.

## Contribution snake

The original Platane/snk action generates the snake using the original pinned
revision and emerald palette. Its pathfinding animation is preserved, including
the contribution collection bar. The publisher adds the original dark frame,
year heading, and month labels. The profile uses assets/snake.svg by default and
assets/calendar.svg when reduced motion is requested.

The action fetches its own GitHub contribution snapshot, so it may briefly differ
from the statistics while GitHub processes activity. Local statistics generation
does not generate a replacement snake. To publish locally, first obtain a fresh
raw Platane SVG at .generated/snake.svg, or use the GitHub workflow for the full
refresh. Keep the last published snake if upstream generation fails.
