# Flutter / Dart Reference Architecture

Always ground module layouts, build setup, DI wiring, and UDF state holders in these battle-tested open-source repositories instead of inventing custom structures.

---

## Famous Reference Repositories
1. **`bizz84/starter_architecture_flutter_firebase`** *(Andrea Bizzotto's canonical Feature-First Riverpod Architecture: Presentation → Application → Domain → Data)*
2. **`felangel/bloc`** *(Official `flutter_todos` & `github_search` multi-package Clean/Layered BLoC architecture)*
3. **`VGVentures/very_good_cli`** *(Very Good Ventures enterprise Flutter conventions, `very_good_analysis` lint rules, 100% test coverage patterns)*

## Canonical Flutter Directory Structure (`Feature-First Clean / Riverpod or BLoC`)
```text
lib/
├── main_staging.dart / main_production.dart  # Environment flavor entrypoints
├── app/                                      # MaterialApp.router, GoRouter config, DI bootstrap
├── core/
│   ├── error/                                # Result<T>, Failure sealed hierarchy
│   ├── network/                              # Dio client, Auth/Retry interceptors
│   ├── storage/                              # Drift / SecureStorage wrappers
│   └── theme/                                # AppTheme, ThemeExtension tokens, reusable widgets
└── features/
    └── <feature_name>/
        ├── domain/                           # Entities (@freezed / Equatable), Repository abstract interface, UseCases
        ├── data/                             # *Dto (@JsonSerializable), Remote/Local DataSources, RepositoryImpl
        └── presentation/                     # BLoC/Cubit or AsyncNotifier + sealed State + Stateless Screens/Widgets
```

## Flutter Non-Negotiables
- Enable `very_good_analysis` (or strict `analysis_options.yaml` with `strict-casts: true`, `strict-inference: true`, `strict-raw-types: true`).
- Break widgets into small `const`-constructible `StatelessWidget` classes rather than 150-line `_buildSomething()` helper methods (widget classes let Flutter short-circuit element rebuilds!).
- Never pass `BuildContext` into a `Bloc`, `Cubit`, or Riverpod `Notifier`.
