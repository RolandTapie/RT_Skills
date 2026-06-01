#!/usr/bin/env python3
"""
Code review analyzer pour système RAG.
Effectue des analyses statiques sans modifier le code.
"""

import json
import sys
import subprocess
import re
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
import ast
import os

# Force UTF-8 encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


@dataclass
class Finding:
    file: str
    line: int
    type: str
    message: str
    severity: str  # critical, warning, info


class CodeAnalyzer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.findings: List[Finding] = []
        self.python_files = self._discover_python_files()

    def _discover_python_files(self) -> List[Path]:
        """Découvrir tous les fichiers Python (exclure .venv, __pycache__, etc.)"""
        exclude_dirs = {'.venv', 'venv', '__pycache__', '.git', 'node_modules', '.pytest_cache'}
        py_files = []

        for path in self.project_root.rglob('*.py'):
            if not any(excluded in path.parts for excluded in exclude_dirs):
                py_files.append(path)

        return sorted(py_files)

    def list_operations(self) -> Dict[str, str]:
        """Lister les opérations d'analyse disponibles"""
        return {
            'docstrings': 'Docstrings manquantes ou incomplètes',
            'type_hints': 'Type hints manquants ou incomplets',
            'unused_imports': 'Imports non utilisés',
            'long_functions': 'Fonctions trop longues (>50 lignes)',
            'naming_conventions': 'Violations des conventions de nommage',
            'error_handling': 'Blocs try/except vides ou génériques',
        }

    def analyze_docstrings(self):
        """Vérifier les docstrings manquantes"""
        for py_file in self.python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content)
                rel_path = py_file.relative_to(self.project_root)

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        if not ast.get_docstring(node):
                            severity = 'warning' if isinstance(node, ast.FunctionDef) else 'warning'
                            self.findings.append(Finding(
                                file=str(rel_path),
                                line=node.lineno,
                                type='docstrings',
                                message=f'{node.__class__.__name__} "{node.name}" sans docstring',
                                severity=severity
                            ))
            except Exception as e:
                pass

    def analyze_type_hints(self):
        """Vérifier les type hints manquants"""
        for py_file in self.python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content)
                rel_path = py_file.relative_to(self.project_root)

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Ignorer les méthodes magiques et les tests
                        if node.name.startswith('_') or 'test' in node.name:
                            continue

                        has_args = len(node.args.args) > 0 or len(node.args.posonlyargs) > 0
                        has_return = node.returns is not None
                        has_arg_hints = all(arg.annotation is not None for arg in node.args.args)

                        if has_args and not has_arg_hints:
                            self.findings.append(Finding(
                                file=str(rel_path),
                                line=node.lineno,
                                type='type_hints',
                                message=f'Fonction "{node.name}" sans type hints pour les paramètres',
                                severity='info'
                            ))

                        if not has_return and not node.name.startswith('_'):
                            self.findings.append(Finding(
                                file=str(rel_path),
                                line=node.lineno,
                                type='type_hints',
                                message=f'Fonction "{node.name}" sans type hint de retour',
                                severity='info'
                            ))
            except Exception:
                pass

    def analyze_long_functions(self):
        """Détecter les fonctions trop longues"""
        threshold = 50
        for py_file in self.python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content)
                rel_path = py_file.relative_to(self.project_root)

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        func_lines = node.end_lineno - node.lineno + 1
                        if func_lines > threshold:
                            self.findings.append(Finding(
                                file=str(rel_path),
                                line=node.lineno,
                                type='long_functions',
                                message=f'Fonction "{node.name}" trop longue ({func_lines} lignes, max {threshold})',
                                severity='warning'
                            ))
            except Exception:
                pass

    def analyze_naming_conventions(self):
        """Vérifier les conventions de nommage PEP 8"""
        for py_file in self.python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content)
                rel_path = py_file.relative_to(self.project_root)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Classes doivent être en PascalCase
                        if not self._is_pascal_case(node.name) and not node.name.isupper():
                            self.findings.append(Finding(
                                file=str(rel_path),
                                line=node.lineno,
                                type='naming_conventions',
                                message=f'Classe "{node.name}" devrait être en PascalCase',
                                severity='info'
                            ))

                    elif isinstance(node, ast.FunctionDef):
                        # Fonctions doivent être en snake_case
                        if not self._is_snake_case(node.name):
                            self.findings.append(Finding(
                                file=str(rel_path),
                                line=node.lineno,
                                type='naming_conventions',
                                message=f'Fonction "{node.name}" devrait être en snake_case',
                                severity='info'
                            ))
            except Exception:
                pass

    def analyze_error_handling(self):
        """Vérifier les blocs try/except vides ou génériques"""
        for py_file in self.python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content)
                rel_path = py_file.relative_to(self.project_root)

                for node in ast.walk(tree):
                    if isinstance(node, ast.Try):
                        for handler in node.handlers:
                            # Détecter except: pass ou except Exception:
                            if handler.type is None:  # bare except
                                self.findings.append(Finding(
                                    file=str(rel_path),
                                    line=handler.lineno,
                                    type='error_handling',
                                    message='Bare except: détecté — spécifiez l\'exception exacte',
                                    severity='warning'
                                ))
                            elif isinstance(handler.type, ast.Name) and handler.type.id == 'Exception':
                                self.findings.append(Finding(
                                    file=str(rel_path),
                                    line=handler.lineno,
                                    type='error_handling',
                                    message='except Exception: trop générique — spécifiez l\'exception attendue',
                                    severity='warning'
                                ))

                            # Détecter les blocs pass ou ... sans logging
                            if len(handler.body) == 1:
                                stmt = handler.body[0]
                                if isinstance(stmt, (ast.Pass, ast.Expr)):
                                    self.findings.append(Finding(
                                        file=str(rel_path),
                                        line=handler.lineno,
                                        type='error_handling',
                                        message='Bloc except vide (pass) — ajoutez du logging ou levez l\'exception',
                                        severity='critical'
                                    ))
            except Exception:
                pass

    def analyze_unused_imports(self):
        """Détecter les imports non utilisés"""
        for py_file in self.python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content)
                rel_path = py_file.relative_to(self.project_root)

                # Collecter tous les imports
                imports = {}
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports[alias.asname or alias.name] = node.lineno
                    elif isinstance(node, ast.ImportFrom):
                        for alias in node.names:
                            imports[alias.asname or alias.name] = node.lineno

                # Vérifier l'utilisation
                for name, line in imports.items():
                    count = 0
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Name) and node.id == name:
                            count += 1

                    if count == 1:  # Seulement l'import lui-même
                        self.findings.append(Finding(
                            file=str(rel_path),
                            line=line,
                            type='unused_imports',
                            message=f'Import "{name}" non utilisé',
                            severity='info'
                        ))
            except Exception:
                pass

    @staticmethod
    def _is_snake_case(s: str) -> bool:
        return s.islower() or (s.startswith('_') and s[1:].replace('_', '').isalnum())

    @staticmethod
    def _is_pascal_case(s: str) -> bool:
        return s[0].isupper() and all(c.isalnum() or c == '_' for c in s)

    def run_all_analyses(self) -> tuple[Dict[str, Any], str]:
        """Exécuter toutes les analyses et retourner (report_json, report_markdown)"""
        print("🔍 Exécution des analyses de code...")

        self.analyze_docstrings()
        print("  ✓ Docstrings vérifiées")

        self.analyze_type_hints()
        print("  ✓ Type hints vérifiés")

        self.analyze_long_functions()
        print("  ✓ Longueur des fonctions vérifiée")

        self.analyze_naming_conventions()
        print("  ✓ Conventions de nommage vérifiées")

        self.analyze_error_handling()
        print("  ✓ Gestion d'erreurs vérifiée")

        self.analyze_unused_imports()
        print("  ✓ Imports non utilisés vérifiés")

        json_report = self._generate_report()
        md_report = self.generate_markdown_report()

        return json_report, md_report

    def _generate_report(self) -> Dict[str, Any]:
        """Générer le rapport d'analyse"""
        # Grouper par type et sévérité
        by_type = {}
        for finding in self.findings:
            if finding.type not in by_type:
                by_type[finding.type] = []
            by_type[finding.type].append(finding)

        # Compter par sévérité
        severity_count = {'critical': 0, 'warning': 0, 'info': 0}
        for finding in self.findings:
            severity_count[finding.severity] += 1

        return {
            'project_root': str(self.project_root),
            'total_python_files': len(self.python_files),
            'total_findings': len(self.findings),
            'severity_summary': severity_count,
            'findings_by_type': {k: [asdict(f) for f in v] for k, v in by_type.items()},
            'all_findings': [asdict(f) for f in sorted(self.findings, key=lambda x: (x.severity, x.file, x.line))]
        }

    def _severity_emoji(self, severity: str) -> str:
        """Retourner l'emoji de sévérité"""
        return {'critical': '🔴', 'warning': '🟠', 'info': 'ℹ️'}.get(severity, '•')

    def generate_markdown_report(self) -> str:
        """Générer un rapport en Markdown groupé par fichier"""
        report_data = self._generate_report()

        # Grouper les findings par fichier
        by_file = {}
        for finding in self.findings:
            if finding.file not in by_file:
                by_file[finding.file] = []
            by_file[finding.file].append(finding)

        # Trier les fichiers alphabétiquement (arborescence)
        sorted_files = sorted(by_file.keys())

        # Construire le markdown
        md_lines = []
        md_lines.append("# 📊 Rapport d'Analyse de Code\n")
        md_lines.append(f"**Projet:** `{self.project_root}`\n")
        md_lines.append(f"**Date d'analyse:** {self._get_timestamp()}\n")
        md_lines.append("")

        # Section résumé
        md_lines.append("## 📈 Résumé\n")
        md_lines.append("| Métrique | Valeur |")
        md_lines.append("|----------|--------|")
        md_lines.append(f"| Fichiers Python | {report_data['total_python_files']} |")
        md_lines.append(f"| Problèmes totaux | {report_data['total_findings']} |")
        md_lines.append(f"| 🔴 Critiques | {report_data['severity_summary']['critical']} |")
        md_lines.append(f"| 🟠 Avertissements | {report_data['severity_summary']['warning']} |")
        md_lines.append(f"| ℹ️ Infos | {report_data['severity_summary']['info']} |")
        md_lines.append("")

        # Statistiques par type
        md_lines.append("## 📋 Par type d'analyse\n")
        by_type = {}
        for finding in self.findings:
            by_type[finding.type] = by_type.get(finding.type, 0) + 1

        for analysis_type, count in sorted(by_type.items(), key=lambda x: -x[1]):
            md_lines.append(f"- **{analysis_type}:** {count} problème(s)")
        md_lines.append("")

        # Problèmes critiques (si peu nombreux)
        if report_data['severity_summary']['critical'] > 0 and report_data['severity_summary']['critical'] <= 20:
            md_lines.append("## 🚨 Problèmes Critiques\n")
            md_lines.append("Ces problèmes doivent être corrigés en priorité.\n")
            for finding in self.findings:
                if finding.severity == 'critical':
                    md_lines.append(f"- **{finding.file}:{finding.line}** `[{finding.type}]`")
                    md_lines.append(f"  - {finding.message}\n")
            md_lines.append("")

        # Détail par fichier
        md_lines.append("## 📁 Détail par fichier\n")

        for file_path in sorted_files:
            findings = sorted(by_file[file_path], key=lambda x: (x.line, x.type))
            severity_counts = {}
            for f in findings:
                severity_counts[f.severity] = severity_counts.get(f.severity, 0) + 1

            # En-tête du fichier
            severity_str = ", ".join(
                [f"{self._severity_emoji(sev)} {count}" for sev, count in sorted(severity_counts.items())]
            )
            md_lines.append(f"### `{file_path}` ({len(findings)} problème(s)) {severity_str}\n")

            # Grouper par ligne
            by_line = {}
            for finding in findings:
                if finding.line not in by_line:
                    by_line[finding.line] = []
                by_line[finding.line].append(finding)

            for line_num in sorted(by_line.keys()):
                findings_at_line = by_line[line_num]
                md_lines.append(f"**Ligne {line_num}:**")

                for finding in findings_at_line:
                    emoji = self._severity_emoji(finding.severity)
                    md_lines.append(
                        f"  - {emoji} `[{finding.type}]` {finding.message}"
                    )

                md_lines.append("")

        # Footer
        md_lines.append("---\n")
        md_lines.append("*Rapport généré automatiquement par l'analyseur de code.*\n")

        return "\n".join(md_lines)

    @staticmethod
    def _get_timestamp() -> str:
        """Retourner le timestamp courant"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyzer.py <project_root> [--operations|--analyze]")
        print("")
        print("Examples:")
        print("  python analyzer.py /path/to/project --operations")
        print("  python analyzer.py /path/to/project --analyze")
        sys.exit(1)

    project_root = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else '--analyze'

    if not Path(project_root).exists():
        print(f"❌ Erreur: {project_root} n'existe pas")
        sys.exit(1)

    analyzer = CodeAnalyzer(project_root)

    if command == '--operations':
        print("\n📋 Opérations d'analyse disponibles:")
        print("=" * 60)
        for op_id, description in analyzer.list_operations().items():
            print(f"  • {op_id:20} — {description}")
        print("=" * 60)

    elif command == '--analyze':
        json_report, md_report = analyzer.run_all_analyses()

        print("\n" + "=" * 80)
        print("📊 RAPPORT D'ANALYSE DE CODE")
        print("=" * 80)
        print(f"Projet: {json_report['project_root']}")
        print(f"Fichiers Python analysés: {json_report['total_python_files']}")
        print(f"Problèmes trouvés: {json_report['total_findings']}")
        print()
        print("Résumé par sévérité:")
        print(f"  🔴 Critiques: {json_report['severity_summary']['critical']}")
        print(f"  🟠 Avertissements: {json_report['severity_summary']['warning']}")
        print(f"  ℹ️  Infos: {json_report['severity_summary']['info']}")
        print()

        # Afficher par type
        if json_report['findings_by_type']:
            print("Résumé par type:")
            for ftype, findings in json_report['findings_by_type'].items():
                print(f"  • {ftype}: {len(findings)} problème(s)")
            print()

            # Afficher les problèmes critiques en priorité
            critical_findings = [f for f in json_report['all_findings'] if f['severity'] == 'critical']
            if critical_findings:
                print("🔴 PROBLÈMES CRITIQUES (premiers 10):")
                print("-" * 80)
                for f in critical_findings[:10]:
                    print(f"  {f['file']}:{f['line']}")
                    print(f"    [{f['type']}] {f['message']}")
                print()

        # Sauvegarder les rapports
        claude_dir = Path(project_root) / '.claude'
        claude_dir.mkdir(parents=True, exist_ok=True)

        # Rapport JSON
        json_file = claude_dir / 'code_review_report.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_report, f, indent=2, ensure_ascii=False)
        print(f"✅ Rapport JSON sauvegardé: {json_file}")

        # Rapport Markdown
        md_file = claude_dir / 'code_review_report.md'
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_report)
        print(f"✅ Rapport Markdown sauvegardé: {md_file}")
        print()
        print("📖 Ouvrez le rapport Markdown pour une meilleure lisibilité !")

    else:
        print(f"❌ Commande inconnue: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
