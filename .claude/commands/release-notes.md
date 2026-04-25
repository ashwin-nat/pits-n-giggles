---
description: Generate user-facing release notes from git commits since the last tag
allowed-tools: Bash(git log:*), Bash(git show:*), Bash(git describe:*), Bash(gh release view:*)
---

Generate user-facing release notes for the next release of Pits n' Giggles.

## Steps

1. **Get commits since the last tag:**
   ```bash
   git log $(git describe --tags --abbrev=0)..HEAD --format="%H %s"
   ```
   Also fetch the full body of each commit (they are often squash merges with detail in the body):
   ```bash
   git log $(git describe --tags --abbrev=0)..HEAD --format="%B---COMMIT_SEP---"
   ```

2. **Look at a recent release for tone and format reference:**
   ```bash
   gh release view $(git describe --tags --abbrev=0) 2>/dev/null
   ```

3. **Filter ruthlessly.** Exclude anything that is purely internal or developer-facing:
   - CI/CD changes, GitHub Actions, build system tweaks
   - IPC refactors, internal architecture changes
   - Unit test additions or improvements
   - Logging improvements (unless they surface to the user as a visible change)
   - Code cleanup, linting, dependency bumps
   - Version bumps, CONTRIBUTING/README changes
   - Anything with prefixes like `ci:`, `chore:`, `refactor:`, `test:`

   **Include** anything a user running the app would notice:
   - New features or overlays
   - Bug fixes affecting visible behaviour
   - Settings/config changes (new knobs, UI improvements)
   - Performance improvements the user would feel
   - New UDP action codes or interactions
   - Changes to how data is displayed or calculated
   - New integrations or external tool support

4. **Write the release notes** in the same style as past releases:
   - Start with a short paragraph summarising the overall theme of the release (1-3 sentences)
   - Use `###` headings for each logical group of changes
   - Use bullet points under each heading
   - Write for a non-technical user who races in F1 games — avoid internal code terms
   - Be specific about what changed and what it means for the user (e.g. "The pit rejoin prediction now accounts for time spent in the pit lane, giving a more accurate result")
   - If a fix addresses a regression from a specific prior version, call that out
   - Emoji headings are fine if the past release used them

5. **Always write the notes to a file** named `release-notes-vX.Y.Z.md` in the repo root. Determine the version from `meta/meta.py` (`APP_VERSION`), not from the last tag. Also print the notes to the terminal.

6. **Keep length in check.** Aim for concise bullets — one line per item. Avoid repeating the same theme across multiple sections. If a fix was already shipped in a hotfix release (visible in the commit log as "Hotfix vX.Y.Z"), skip it.

7. **Credit contributors.** Check `git log ... --format="%an|%ae"` for authors other than `ashwin-nat`. If any exist, extract their GitHub username from the noreply email (`<id>+<username>@users.noreply.github.com`) and add a `### 🙏 Contributors` section at the end crediting them by `@username` with a brief summary of what they worked on.

If there are no user-facing changes (e.g. the only commits are CI/internal), say so explicitly rather than generating empty notes.
