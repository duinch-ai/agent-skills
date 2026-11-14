# iOS / Swift (SwiftUI + Swift 6 Concurrency) Reference Architecture

Always ground module layouts, build setup, DI wiring, and UDF state holders in these battle-tested open-source repositories instead of inventing custom structures.

---

## Famous Reference Repositories
1. **`pointfreeco/swift-composable-architecture`** *(TCA — inspect `Examples/SyncUps` and `Examples/CaseStudies` for gold-standard `@Reducer`, `@ObservableState`, `@Dependency`, and `TestStore`)*
2. **`nalexn/clean-architecture-swiftui`** *(Clean Architecture + SwiftUI + Environment DI without external frameworks)*
3. **`kudoleh/iOS-Clean-Architecture-MVVM`** *(Modular Clean Architecture + MVVM + Coordinator/Flow separation)*

## Canonical iOS Modular Structure (Local Swift Package Manager `Packages/` — Zero Xcode `.xcodeproj` Merge Conflicts!)
```text
project-root/
├── App/                           # Thin Xcode target (Assets, Info.plist, AppEntrypoint)
└── Packages/                      # Local SPM Workspace enforcing strict compile-time boundaries
    ├── CoreDomain/                # Pure Swift entities, Value Objects, Repository protocols, DomainError
    ├── CoreData/                  # URLSession/HTTPClient, SwiftData/GRDB persistence, DTOs, Repository impls
    ├── CoreDesignSystem/          # SwiftUI Design tokens, reusable Views, #Preview catalog
    └── Features/
        ├── AuthFeature/           # TCA @Reducer (or @Observable @MainActor ViewModel) + SwiftUI Views + Tests
        └── HomeFeature/           # Depends ONLY on CoreDomain + CoreDesignSystem (never CoreData impl!)
```

## iOS Non-Negotiables
- Favor **Local Swift Packages (`Package.swift`)** over monolithic Xcode targets: SPM enforces module encapsulation at compile time and lets you run `swift test` in < 2 seconds without booting the iOS Simulator!
- Embrace Swift 6 strict concurrency (`Sendable` value types/`struct` in Domain, `@MainActor` isolated UI state holders, structured `async let` / `TaskGroup`).
