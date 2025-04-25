# Pits n' Giggles Backend

This app is the brain (and heart) behind Pits n' Giggles. It does the following
- Receive data from the F1 game
- Parse compute and maintain the state of the session
- Coordinate with the UI clients

## Running

From the root directory
```bash
poetry run python -m apps.backend.pits_n_giggles
```