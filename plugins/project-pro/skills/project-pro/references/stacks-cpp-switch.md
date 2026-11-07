# C++ Stack — Modern C++ & Nintendo Switch Homebrew (CMake + libnx + Borealis)

Build high-performance, rock-solid Nintendo Switch homebrew applications using Modern C++ (C++17/C++20), devkitPro (`devkitA64`), the `libnx` hardware abstraction library, and the `Borealis` UI framework.

---

## 1. Core Architecture & Design Guardrails

- **Clean Layered Separation**:
  - `Domain Layer` (Pure C++): Business logic, data models, domain repositories, state machines. **Strictly forbidden** to include platform headers (`switch.h`), UI headers (`borealis.hpp`), or network transport headers (`curl/curl.h`).
  - `Data / Adapter Layer`: API client (`libcurl` + `nlohmann/json`), archive extraction (`libarchive`), title/storage management (`libnx` `ncm`, `ns`, `es`, `fs` services).
  - `Presentation Layer`: Borealis activities, frames, custom views, recycling lists, focus management, Switch on-screen keyboard (Swkbd applet).
- **RAII & Memory Safety**:
  - **Zero Raw Pointers for Ownership**: Always use `std::unique_ptr` for exclusive ownership and `std::shared_ptr` / `std::weak_ptr` for shared resources.
  - Wrap all `libnx` service sessions and resource handles in RAII structs with automatic destructor cleanup (e.g. `ncmCloseContentStorage()`, `curl_easy_cleanup()`).
  - Beware of memory leaks during image loading: limit texture caches, downscale remote covers, and unload off-screen textures.
- **Concurrency & Thread Safety**:
  - Nintendo Switch has 3 available CPU cores for homebrew. Limit background worker threads to 2 (`ThreadPool::max_thread_num = 2`) to avoid thread contention.
  - All Borealis UI operations and view mutations **MUST execute on the main UI thread** via `brls::sync()` or `brls::async()`.
- **String Handling & Error Management**:
  - Avoid throwing C++ exceptions across C library boundaries (`libnx`, `libcurl`).
  - Use `std::optional<T>` or a typed `Result<T, ErrorCode>` pattern for recoverable I/O failures.

---

## 2. Nintendo Switch System Services (`libnx`) Protocol

When performing title installation, storage management, or system operations:
- **`ncm` (Content Manager)**: Managing content storages (NAND User, SD card), creating placeholder NCAs, registering installed contents.
- **`ns` (Nintendo Shell)**: Registering application titles to Horizon OS Home Menu, querying installed title versions.
- **`es` (Electronic Software)**: Importing tickets for title keys (handled by sigpatches on CFW).
- **`fs` / `fsdev`**: SD card filesystem I/O (`sdmc:/`).
- **`applet` / `swkbd`**: Interacting with system software keyboard for user text input.

---

## 3. Curated Gold-Standard Reference Repositories

| Repository | Focus & Strengths | Architecture Reference |
| :--- | :--- | :--- |
| [`dragonflylee/switchfin`](https://github.com/dragonflylee/switchfin) | Jellyfin media client for Switch (deko3d & OpenGL), multi-platform CMake, async networking, custom recycling views. | **Borealis UI + Async Network Architecture** |
| [`PoloNX/TinWoo`](https://github.com/PoloNX/TinWoo) | Production-grade NSP / NSZ / XCI installer for Horizon OS with USB, MTP, and network install engines. | **Title Installation & libnx Service Core** |
| [`XorTroll/Goldleaf`](https://github.com/XorTroll/Goldleaf) | Gold standard multipurpose content, file, ticket, and title manager for Nintendo Switch. | **Clean C++ System Tool Design** |
| [`ITotalJustice/aio-switch-updater`](https://github.com/ITotalJustice/aio-switch-updater) | All-in-one updater using Borealis, libcurl download engine, and ZIP/archive extraction. | **Download Pipeline & Progress Reporting** |

---

## 4. Build System & Toolchain (devkitPro)

- Use CMake with `Borealis` build options (`include(${BOREALIS_LIBRARY}/cmake/commonOption.cmake)`).
- Cross-compilation target: `aarch64-none-elf` via `devkitA64`.
- Desktop execution: Borealis supports running natively on macOS/Linux/Windows with GLFW/OpenGL for rapid local UI debugging before building for Switch hardware.
