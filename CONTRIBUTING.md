# Contributing to Pits n' Giggles

Thanks for your interest in contributing!  Whether it's bug reports, feature suggestions, code, or docs — all contributions are welcome.

---

## Project Setup

For detailed instructions on setting up the project, please refer to the [RUNNING.md](docs/RUNNING.md) file.

---

## Before You Start

### Small Changes (No Prior Discussion Needed)

You can directly open a PR for small, self-contained changes such as:
- Typo fixes
- Minor bug fixes
- Incorrect constants or small logic corrections
- Documentation updates

---

### Non-Trivial Changes (Discussion Required)

For **larger fixes or features**, you must discuss your idea with the maintainer (@ashwin-nat) before starting work.

This helps avoid duplicate work, ensures alignment with the project direction, and saves everyone time.

### What counts as a non-trivial change?

Examples include:
- Changes to telemetry ingestion or core data flow
- Backend architecture changes
- Introducing new pipelines, services, or subsystems
- Large changes (roughly >500 lines or spanning multiple areas)

If you're unsure, it's always better to ask first.

You can start a discussion via:
- GitHub Issues (comments)
- GitHub Discussions
- [Discord](https://discord.gg/qQsSEHhW2V) (**preferred**)

---

## Pull Request Guidelines

### Keep PRs Small and Focused

- PRs should address a **single concern**
- **Small PRs are strongly preferred**

If you're working on a large feature:
- Break it into **multiple smaller PRs**
- Discuss the feature beforehand (see above)

If you're working on a UI change/feature, please include screenshots in the PR description

---

### PRs Must Be Independent

Each PR must be:
- **Independently reviewable**
- **Independently mergeable**

Do not submit PRs that:
- Depend on other open PRs
- Require other unmerged changes to function or be reviewed

If your work requires multiple steps, please discuss the approach beforehand so that a good merge plan can be figured out

---

### Large Features / Multi-PR Work

If your change is large and cannot reasonably be split into fully independent PRs, please include this in the discussion as well

---

### Before Opening a PR

- Ensure the change has already been discussed if it is non-trivial
- Make sure the PR is focused and not doing too many things at once

---

### Important

PRs may be closed or deferred without detailed review if they:
- Are too large or unfocused
- Introduce architectural changes without prior discussion
- Depend on other unmerged PRs
- Appear to be blindly generated or not well understood

---

## Reviews & Feedback

- The maintainer (@ashwin-nat) may leave comments or request changes on your PR
- Please address feedback in a timely manner
- You may be asked questions about your approach, design decisions, or edge cases
- Be prepared to explain and justify your implementation

---

## Use of AI Tools

AI-assisted tools (e.g. ChatGPT, Copilot) are allowed.

However:
- You must fully understand any code you submit and be able to explain it
- You are responsible for correctness, edge cases, and overall design

---

## Need Help?

Open an issue or reach out via discussions/[Discord](https://discord.gg/qQsSEHhW2V).

Thanks again for contributing!
