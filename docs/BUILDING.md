# 🛠 Building Pits n' Giggles with PyInstaller

This document outlines how to build the `Pits n' Giggles` app into a standalone executable using PyInstaller.

---

## 🔧 Requirements

- **Python 3.13**
- **[Poetry](https://python-poetry.org/)** for dependency management
- A Windows machine (macOS support is planned but not yet active)

---

## 📝 Setup

1. **Install production dependencies (excluding dev tools):**

   ```bash
   poetry install --without dev
   ```

   This will install everything required to build and run the app in production, including PyInstaller.

---

## 🏗 Building the Executable

To build the app:

```bash
poetry run python scripts/build.py
```

- This must be run from the **root of the project**.
- The resulting executable will appear in the `dist/` folder with a name like:

  ```
  dist/pits_n_giggles_<ver>.exe
  dist/pits_n_giggles_<ver>.app
  ```

---

## ⚙️ How the Build System Works

Pits n' Giggles uses a modular launcher architecture to simplify distribution and reduce antivirus issues:

- ✅ The **main launcher** is built as a single executable.
- ✅ **Subsystems** (e.g., backend, save viewer) are launched as Python modules using the **main binary’s interpreter**.

### 📦 Version Management

- The version is maintained **once**, at the top of the `scripts/png.spec` file.
- It is injected at runtime into the environment variable `PNG_VERSION` using a PyInstaller **runtime hook**.
- The launcher and all subsystems read this environment variable.

---

## ➕ Adding New Subsystems

To add a new subsystem to the suite:

1. **Create the module**
   Place it under `apps/<your_subsystem>/` with a proper `__init__.py` and `__main__.py`.

2. **Implement the entry point**
   Your `__main__.py` should import and invoke an `entry_point()` function from your core logic module.

   ```python
   # apps/your_subsystem/__main__.py
   from .your_subsystem import entry_point

   if __name__ == "__main__":
       entry_point()
   ```

3. **Add to launcher**
   Define a new subclass of `PngAppMgrBase` (in `apps/launcher/app_managers/`) to manage this subsystem. Register it in the launcher UI.

4. **Update `png.spec`**
   Add the new module to `hiddenimports` in `scripts/png.spec`:

   ```python
   hiddenimports = (
       collect_submodules("apps.launcher") +
       collect_submodules("apps.backend") +
       collect_submodules("apps.save_viewer") +
       collect_submodules("apps.your_subsystem")  # 👈 Add this line
   )
   ```

5. **Rebuild**
   Run the build command again:

   ```bash
   poetry run pyinstaller --clean --noconfirm scripts/png.spec
   ```

You can now launch your new subsystem via:

```bash
dist/pits_n_giggles_2.8.0.exe --module apps.your_subsystem
```

Or from within the launcher window.

---

## ❗ Tips & Notes

- The launcher entry point is:
  `apps/launcher/__main__.py`
- The `scripts/png.spec` file controls:
  - Entry script
  - Icon
  - Version
  - Embedded assets
  - Runtime environment setup

If you need to customize the build (add files, change version, etc.), do it in `scripts/png.spec`.

---

## 🧹 Cleaning Up

To clean up build artifacts:

```bash
rm -rf build/ dist/
```

Or just rebuild from scratch:

```bash
poetry run python scripts/build.py
```

---

## 🧪 Testing the Executable

To test the launcher:

```bash
dist/pits_n_giggles_2.8.0.exe
```

To run subsystems directly (for debugging):

```bash
dist/pits_n_giggles_2.8.0.exe --module apps.backend
dist/pits_n_giggles_2.8.0.exe --module apps.save_viewer
dist/pits_n_giggles_2.8.0.exe --module apps.your_subsystem
```

---
