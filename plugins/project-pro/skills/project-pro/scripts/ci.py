"""GitHub Actions workflow renderers for stacks with first-class CI (Rust, Nintendo Switch)."""

from __future__ import annotations



def render_rust_ci_workflow() -> str:
    return """name: Rust CI

on:
  push:
  pull_request:
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: rust-ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  verify:
    name: Verify (${{ matrix.os }})
    runs-on: ${{ matrix.os }}
    timeout-minutes: 30
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    steps:
      - uses: actions/checkout@v4
      - uses: actions-rust-lang/setup-rust-toolchain@v1
        with:
          toolchain: stable
          components: rustfmt, clippy
      - name: Check formatting
        run: cargo fmt --all -- --check
      - name: Build workspace
        run: cargo build --workspace
      - name: Run Clippy
        run: cargo clippy --workspace --all-targets -- -D warnings
      - name: Run tests
        run: cargo test --workspace

  dependency-audit:
    name: Audit dependencies
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions-rust-lang/setup-rust-toolchain@v1
        with:
          toolchain: stable
      - name: Install cargo-audit
        run: cargo install cargo-audit --locked
      - name: Audit dependencies
        run: cargo audit
"""


def render_cpp_switch_ci_workflow(project_name: str = "SwitchFS") -> str:
    return f"""name: Nintendo Switch Build CI

on:
  push:
    branches: [ main, dev ]
  pull_request:
    branches: [ main, dev ]
  workflow_dispatch:

jobs:
  build-nx:
    name: Build Switch NRO
    runs-on: ubuntu-latest
    container:
      image: devkitpro/devkita64:latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive
      - name: Install Switch Dependencies
        run: |
          dkp-pacman --noconfirm -Syu
          dkp-pacman --noconfirm -S switch-curl switch-mbedtls switch-libarchive switch-pkg-config
          git config --system --add safe.directory $GITHUB_WORKSPACE
      - name: Build NRO
        run: |
          cmake -B build \\
            -DCMAKE_BUILD_TYPE=Release \\
            -DPLATFORM_SWITCH=ON \\
            -DVERSION_BUILD=${{{{ github.run_number }}}}
          make -C build {project_name}.nro -j$(nproc)
      - name: Upload NRO Artifact
        uses: actions/upload-artifact@v4
        with:
          name: {project_name}-Switch-${{{{ github.run_number }}}}
          path: build/{project_name}.nro
"""
