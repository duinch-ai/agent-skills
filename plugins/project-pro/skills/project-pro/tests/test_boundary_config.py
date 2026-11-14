import configparser
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from scaffolder import init_project  # noqa: E402

GO_LINT = shutil.which("golangci-lint")
PY_LINT = shutil.which("lint-imports")


def gen(stack, arch=None, features=("solid-dry", "arch-lint"), pre=None, **kw):
    d = tempfile.TemporaryDirectory()
    root = Path(d.name)
    for rel, text in (pre or {}).items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text)
    from catalog import STACK_CATALOG
    info = STACK_CATALOG[stack]
    out = init_project(root, stack, arch or info["recommended_arch"], info["recommended_pattern"], list(features), ["agents-root"], **kw)
    return d, root, out


class GoBoundaryTests(unittest.TestCase):
    def test_generates_depguard_with_citation(self):
        d, root, out = gen("go", go_module="example.com/fx")
        self.addCleanup(d.cleanup)
        text = (root / ".golangci.yml").read_text()
        self.assertIn("default: standard", text)
        self.assertNotIn("default: none", text)
        for needle in ("golangci-lint v2.15.0", "golangci/golangci-lint/blob/v2.15.0/.golangci.reference.yml", "golangci-lint.run/docs",
                       'version: "2"', "- depguard", "$gostd", "example.com/fx/internal/adapter/external", "net/http"):
            self.assertIn(needle, text)
        self.assertTrue(any(l.startswith("WRITE: .golangci.yml") for l in out))

    def test_module_from_go_mod(self):
        d, root, _ = gen("go", pre={"go.mod": "module github.com/acme/app\n\ngo 1.21\n"})
        self.addCleanup(d.cleanup)
        self.assertIn('"github.com/acme/app/internal/controller"', (root / ".golangci.yml").read_text())

    def test_no_module_prints_snippet_and_writes_nothing(self):
        d, root, out = gen("go")
        self.addCleanup(d.cleanup)
        self.assertFalse((root / ".golangci.yml").exists())
        self.assertTrue(any("needs the module path" in l for l in out))
        self.assertTrue(any("<module>" in l for l in out))

    def test_existing_config_never_overwritten_even_with_force(self):
        d, root, out = gen("go", pre={".golangci.yml": "# mine\n"}, go_module="example.com/fx", force=True)
        self.addCleanup(d.cleanup)
        self.assertEqual((root / ".golangci.yml").read_text(), "# mine\n")
        self.assertTrue(any(l.startswith("SKIP (exists): .golangci.yml") for l in out))
        self.assertTrue(any("depguard:" in l for l in out))

    def test_non_layered_arch_and_arch_lint_off(self):
        d, root, out = gen("go", arch="vertical-slice", go_module="example.com/fx")
        self.addCleanup(d.cleanup)
        self.assertFalse((root / ".golangci.yml").exists())
        self.assertTrue(any("not yet automated" in l for l in out))
        d2, root2, out2 = gen("go", features=("solid-dry",), go_module="example.com/fx")
        self.addCleanup(d2.cleanup)
        self.assertFalse((root2 / ".golangci.yml").exists())

    @unittest.skipUnless(GO_LINT, "golangci-lint not installed: not verified")
    def test_real_golangci_lint_flags_bad_imports(self):
        d, root, _ = gen("go", go_module="example.com/fx")
        self.addCleanup(d.cleanup)
        (root / "go.mod").write_text("module example.com/fx\n\ngo 1.21\n")
        files = {
            "internal/domain/user.go": "package domain\n\ntype User struct{ ID string }\n",
            "internal/adapter/postgres/repo.go": 'package postgres\n\nimport _ "example.com/fx/internal/domain"\n',
            "internal/adapter/external/x.go": "package external\n",
            "internal/usecase/u.go": 'package usecase\n\nimport _ "example.com/fx/internal/domain"\n',
            "internal/controller/http/h.go": 'package http\n\nimport _ "example.com/fx/internal/usecase"\n',
        }
        for rel, text in files.items():
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text(text)
        run = lambda: subprocess.run([GO_LINT, "run", "./..."], cwd=root, capture_output=True, text=True)
        good = run()
        self.assertEqual(good.returncode, 0, good.stdout + good.stderr)
        bads = {
            "internal/domain/bad.go": 'package domain\n\nimport _ "net/http"\n',
            "internal/usecase/bad.go": 'package usecase\n\nimport _ "example.com/fx/internal/adapter/postgres"\n',
            "internal/adapter/postgres/bad.go": 'package postgres\n\nimport _ "example.com/fx/internal/adapter/external"\n',
            "internal/controller/http/bad.go": 'package http\n\nimport _ "example.com/fx/internal/adapter/postgres"\n',
        }
        for rel, text in bads.items():
            (root / rel).write_text(text)
        bad = run()
        self.assertNotEqual(bad.returncode, 0)
        for rel in bads:
            self.assertIn(rel, bad.stdout)


class PythonBoundaryTests(unittest.TestCase):
    def test_hexagonal_contracts_parse(self):
        d, root, out = gen("python", arch="hexagonal")
        self.addCleanup(d.cleanup)
        text = (root / ".importlinter").read_text()
        self.assertIn("import-linter 2.16", text)
        self.assertIn("https://import-linter.readthedocs.io/en/stable/contract_types/layers/", text)
        cp = configparser.ConfigParser()
        cp.read_string(text)
        self.assertEqual(cp["importlinter"]["root_package"], "src")
        layers = cp["importlinter:contract:layers"]
        self.assertEqual(layers["type"], "layers")
        self.assertIn("src.modules.users.entrypoints | src.modules.users.adapters", layers["layers"])
        self.assertIn("fastapi", cp["importlinter:contract:domain-pure"]["forbidden_modules"])
        self.assertTrue(any(l.startswith("WRITE: .importlinter") for l in out))

    def test_vertical_slice_default(self):
        d, root, _ = gen("python")
        self.addCleanup(d.cleanup)
        cp = configparser.ConfigParser()
        cp.read_string((root / ".importlinter").read_text())
        self.assertEqual(cp["importlinter:contract:slices"]["type"], "independence")
        mods = cp["importlinter:contract:slices"]["modules"].split()
        self.assertEqual(mods, ["src.modules.health", "src.modules.users"])
        self.assertIn("scaffold dirs", (root / ".importlinter").read_text())

    def test_slices_follow_scaffold_dirs(self):
        from boundary_py import render_config
        from catalog import STACK_CATALOG
        info = {**STACK_CATALOG["python"], "scaffold_dirs": {"vertical-slice": ["src/shared", "src/modules/billing", "src/modules/orders", "src/modules/orders/sub"]}}
        text = render_config("vertical-slice", info)
        self.assertIn("src.modules.billing", text)
        self.assertIn("src.modules.orders", text)
        self.assertNotIn("src.modules.health", text)
        self.assertNotIn("orders.sub", text)

    def test_existing_config_not_overwritten(self):
        d, root, out = gen("python", pre={".importlinter": "# mine\n"}, force=True)
        self.addCleanup(d.cleanup)
        self.assertEqual((root / ".importlinter").read_text(), "# mine\n")
        self.assertTrue(any(l.startswith("SKIP (exists): .importlinter") for l in out))
        d2, root2, out2 = gen("python", pre={"pyproject.toml": "[tool.importlinter]\nroot_package='x'\n"})
        self.addCleanup(d2.cleanup)
        self.assertFalse((root2 / ".importlinter").exists())
        self.assertTrue(any("pyproject.toml already has import-linter" in l for l in out2))

    @unittest.skipUnless(PY_LINT, "lint-imports not installed: not verified")
    def test_real_lint_imports_flags_bad_import(self):
        d, root, _ = gen("python", arch="hexagonal")
        self.addCleanup(d.cleanup)
        pkg = root / "src" / "modules" / "users"
        for sub in ("domain", "application", "adapters", "entrypoints"):
            (pkg / sub).mkdir(parents=True, exist_ok=True)
            (pkg / sub / "__init__.py").write_text("")
        for p in (root / "src", root / "src" / "modules", pkg):
            (p / "__init__.py").write_text("")
        run = lambda: subprocess.run([PY_LINT], cwd=root, capture_output=True, text=True)
        self.assertEqual(run().returncode, 0)
        (pkg / "domain" / "bad.py").write_text("from src.modules.users import adapters\n")
        self.assertNotEqual(run().returncode, 0)


class OtherStacksTests(unittest.TestCase):
    def test_other_stacks_report_not_yet_automated(self):
        for stack in ("android", "kmp", "flutter", "ios", "web", "nestjs", "rust", "cpp-switch"):
            d, root, out = gen(stack)
            self.addCleanup(d.cleanup)
            self.assertTrue(any("not yet automated" in l for l in out), stack)
            self.assertFalse((root / ".golangci.yml").exists() or (root / ".importlinter").exists())


if __name__ == "__main__":
    unittest.main()
