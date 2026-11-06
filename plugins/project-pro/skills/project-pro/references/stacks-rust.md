# Rust Stack — Idiomatic Design, Cross-Platform Builds & CI/CD

Use Rust's type system and Cargo conventions directly. Clean Architecture is a
dependency-direction guide, not a reason to reproduce class-heavy DTO/Entity,
DI-container, or sealed-UI-state patterns from other languages.

## 1. Rust Design Guardrails

- **Ownership first**: Prefer owned values at clear boundaries and borrowed
  references for temporary access. Use lifetimes only when they express a real
  relationship; do not add `Arc<Mutex<_>>`, `Rc<RefCell<_>>`, or clones to work
  around an unclear ownership model.
- **Model states in types**: Use enums and exhaustive `match` for alternatives,
  newtypes for values with distinct meaning, and traits for stable behavior
  boundaries. Prefer generics/static dispatch by default; use `dyn Trait` when
  runtime polymorphism or object safety is actually needed.
- **Errors**: Return `Result<T, E>` for recoverable failures. Libraries should
  expose meaningful error types and avoid imposing an application-wide error
  policy; applications may add context at process/I/O boundaries. Do not use
  `unwrap()`/`expect()` on ordinary runtime paths or erase errors with
  `Box<dyn Error>` without a reason.
- **Architecture**: Keep domain crates/modules independent of UI, transport,
  database, and runtime frameworks. Put traits at the boundary that consumes
  them; add adapter crates when they enforce a real dependency boundary, not
  just to mirror a diagram.
- **Async/concurrency**: Add an async runtime only when asynchronous I/O is
  needed. Keep sync APIs sync, do not hold locks across `.await`, propagate
  cancellation, and use `Send`/`Sync` bounds only where the executor or thread
  boundary requires them.
- **Unsafe**: Avoid `unsafe` unless a safe API cannot meet a concrete
  requirement. Keep each unsafe block small, document its safety invariants
  next to the block, and test the safe abstraction around it.
- **Tests**: Keep pure domain tests fast; use integration tests for crate/API
  boundaries and explicit test fixtures for I/O. Run tests on native runners;
  for cross targets without an executable runner, require a successful target
  compile rather than pretending that host tests cover that target.

## 2. Workspace & Tooling Baseline

- Use a Cargo workspace when packages have independent responsibilities or
  build boundaries. Centralize shared dependency versions in `[workspace.dependencies]`
  only when it reduces drift.
- Commit `Cargo.lock` for applications and binaries. Libraries may choose not
  to commit it; CI commands must match that policy.
- Keep `cargo fmt --all -- --check`, `cargo clippy --workspace --all-targets
  -- -D warnings`, and `cargo test --workspace` green. Run `cargo audit` and
  review dependency changes; use `cargo-deny` when license/source policy or
  dependency allowlists require it.
- Declare the supported Rust toolchain/MSRV and target triples. Check the
  declared MSRV in CI when it is a compatibility promise; do not silently
  depend on stable-only APIs.

## 3. Platform Build Matrix

Rust can target many operating systems and architectures, but not every crate
or application supports every target. Treat the project's declared target list
as the contract; do not claim universal support from a successful host build.

| Platform family | Common target(s) | CI/build guidance |
|---|---|---|
| Linux | `x86_64-unknown-linux-gnu`, optionally `aarch64-unknown-linux-gnu` | Build and test on Linux runners. Add musl targets only when static/musl deployment is required and the linker is configured. |
| macOS | `aarch64-apple-darwin`, optionally `x86_64-apple-darwin` | Build/test on macOS; use Xcode and Apple signing/notarization for distributable apps. |
| Windows | `x86_64-pc-windows-msvc` | Build/test on Windows with the MSVC toolchain; use the GNU target only when the project explicitly supports it. |
| Android | `aarch64-linux-android`, optionally `x86_64-linux-android` | Install the Android NDK and target-specific linker; package/sign through the Android app toolchain. |
| iOS | `aarch64-apple-ios` and simulator targets as needed | Requires macOS/Xcode for the full build and signing flow; device and simulator artifacts are distinct. |
| WebAssembly | `wasm32-unknown-unknown`, `wasm32-wasip1` | Select the target matching the host (browser vs WASI); run browser/WASI integration tests in their actual runtime. |
| Embedded / other | Project-specific target triples | Pin the target/toolchain, install the cross-linker and SDK, and use hardware/emulation tests where available. Do not add a generic runner matrix without verifying the toolchain. |

### CI Expectations

The generated GitHub Actions workflow runs formatting, Clippy, build, and tests
on Linux, macOS, and Windows. Add target-specific compile jobs for Android,
iOS, WebAssembly, musl, or embedded **only when the project declares those
targets**. A target job must install its Rust target and required SDK/linker;
platform-specific dependencies may need feature or package selection.

For each supported target:

1. Run native tests on a matching runner when one exists.
2. Cross-compile on the appropriate host for targets that require an SDK
   (notably Apple and Android targets).
3. Keep target-specific setup and feature selection in the workflow, not in
   unconditional project code.
4. Cache Cargo registry/git/build data where useful, and scope cache keys by
   OS, toolchain, and lockfile.
5. Test the exact artifacts intended for release; a `cargo check` cross-build
   does not verify linking, packaging, signing, or runtime behavior.

## 4. CD & Release by Artifact Type

Do not generate one release pipeline for every Rust project: publishing a
library, shipping a desktop app, and deploying a Wasm application have different
credentials and signing requirements.

- **Crates.io library**: validate metadata and run `cargo publish --dry-run`;
  publish from a protected tag/release workflow with a narrowly scoped
  `CARGO_REGISTRY_TOKEN` secret and an explicit maintainer approval policy.
- **Desktop binary/app**: use a release tool such as `cargo-dist` or an
  equivalent project-owned pipeline to build the declared Linux/macOS/Windows
  artifacts, create checksums, and attach them to a tagged GitHub Release.
  Add Apple signing/notarization or Windows signing only when configured.
- **Android/iOS app**: build and sign through the platform's supported toolchain;
  keep keystores, certificates, provisioning profiles, and store credentials in
  protected CI secrets. Never put signing material in the repository.
- **WebAssembly**: build the declared browser/WASI target, test in its runtime,
  then deploy to the selected hosting/runtime environment with least-privilege
  credentials.

Protect release environments, grant only the permissions each job needs, pin
third-party actions according to repository policy, and avoid exposing release
secrets to untrusted pull-request workflows.
