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

## App Architecture

![alt text](../../docs/arch-diagram.png)

## Profiling the backend

Follow these steps to profile Pits n' Giggles using Yappi:

### 1. Enable Profiler Mode
- Open your app's entry point.
- **Comment out** the production `if __name__ == "__main__"` block in pits_n_giggles.py.
- **Uncomment** the `PROFILER MODE` section just below it.

### 2. Enable Profiler in `telemetry_handler.py`
- Search for `PROFILER MODE` in `telemetry_handler.py`.
- **Uncomment** the related lines to enable profiling hooks.

### 3. Start the Backend
Run the backend in debug mode with the replay server enabled:

```bash
poetry run python -m apps.backend.pits_n_giggles --replay-server --debug
````

### 4. Play a Replay File

Use the telemetry replayer to feed in a replay:

```bash
poetry run python -m apps.dev_tools.telemetry_replayer --file-name f1_24_sp_austria.f1pcap
```

### 5. Wait for Completion

Once the replay finishes:

* The backend will terminate automatically.
* Yappi will generate two files:

  * `yappi_profile.txt` (text output)
  * `yappi_profile.html` (interactive profile viewer)

### 6. Filter Your App's Code Only

To grep only your app’s code and exclude libraries and virtual environments:

```bash
grep 'C:\\Users\\<your-username>\\Documents\\f1-telemetry\\pits-n-giggles\\' yappi_profile.txt
```

> **Note:**
> If your virtual environment is located inside the code directory (e.g., `.venv/`), you may need to refine the grep further. If you're unsure how, ask ChatGPT!

