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

5. **Output the notes as markdown** directly to the terminal. Do not write to a file unless asked.

If there are no user-facing changes (e.g. the only commits are CI/internal), say so explicitly rather than generating empty notes.
