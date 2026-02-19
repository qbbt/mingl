import os
import ast
import json
from datetime import datetime
from typing import List, Dict

class NightWatchman:
    """
    Autonomous Architectural Auditor.
    Scans the codebase for 'Architectural Drift' (pattern violations).
    """
    
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.violations = []

    def scan_for_drift(self):
        """Scans routers for direct database imports or dependencies."""
        self.violations = []
        router_dir = os.path.join(self.root_dir, "backend", "app", "routers")
        
        for filename in os.listdir(router_dir):
            if filename.endswith(".py"):
                filepath = os.path.join(router_dir, filename)
                self._check_file(filepath)
        
        return self.violations

    def _check_file(self, filepath: str):
        with open(filepath, "r") as f:
            try:
                tree = ast.parse(f.read())
            except SyntaxError:
                return

        for node in ast.walk(tree):
            # Check for direct duckdb or sqlalchemy imports in routers
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in ["duckdb", "sqlalchemy"]:
                        self.violations.append({
                            "file": filepath,
                            "type": "Direct DB Import",
                            "detail": f"Router imports '{alias.name}' - Violation of 3-Layer Cake."
                        })
            elif isinstance(node, ast.ImportFrom):
                if node.module in ["duckdb", "sqlalchemy"] or (node.module and node.module.startswith("sqlalchemy")):
                    self.violations.append({
                        "file": filepath,
                        "type": "Direct DB Import",
                        "detail": f"Router imports from '{node.module}' - Violation of 3-Layer Cake."
                    })

    def generate_fix_plan(self):
        """Generates a fix_plan.md if drift is detected."""
        if not self.violations:
            if os.path.exists("fix_plan.md"):
                os.remove("fix_plan.md")
            return

        plan_content = f"# 🛠️ Night Watchman: Fix Plan - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}\n\n"
        plan_content += "Architectural Drift detected. The following violations must be reconciled:\n\n"
        
        for v in self.violations:
            plan_content += f"- [ ] **{v['type']}** in `{os.path.basename(v['file'])}`: {v['detail']}\n"
        
        plan_content += "\n## Proposed Action: Refactor routers to use the Service layer exclusively."
        
        with open("fix_plan.md", "w", encoding="utf-8") as f:
            f.write(plan_content)
        
        print(f"[WATCHMAN] Generated fix_plan.md with {len(self.violations)} violations.")

if __name__ == "__main__":
    # Running from project root
    watchman = NightWatchman(os.getcwd())
    violations = watchman.scan_for_drift()
    watchman.generate_fix_plan()
