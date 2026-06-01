#!/usr/bin/env python3
"""
Code Review Fixer — Applique les corrections aux problèmes détectés
Mode semi-automatique avec confirmation de l'utilisateur.
"""

import json
import sys
import ast
import re
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from collections import defaultdict

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


@dataclass
class Finding:
    file: str
    line: int
    type: str
    message: str
    severity: str


class CodeReviewFixer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.report_file = self.project_root / '.claude' / 'code_review_report.json'
        self.findings: List[Finding] = []
        self.corrections_applied = 0
        self.corrections_skipped = 0

    def find_report(self) -> bool:
        """Chercher le rapport JSON"""
        if not self.report_file.exists():
            print(f"❌ Rapport non trouvé: {self.report_file}")
            print("")
            print("Générez d'abord un rapport avec:")
            print(f'  python "$env:USERPROFILE\\.claude\\skills\\code-review-analysis\\analyzer.py" "." --analyze')
            return False

        try:
            with open(self.report_file, 'r', encoding='utf-8') as f:
                report = json.load(f)

            # Parser les findings
            for finding_dict in report.get('all_findings', []):
                self.findings.append(Finding(**finding_dict))

            return True
        except Exception as e:
            print(f"❌ Erreur lecture rapport: {e}")
            return False

    def group_by_type(self) -> Dict[str, List[Finding]]:
        """Grouper les findings par type"""
        grouped = defaultdict(list)
        for finding in self.findings:
            grouped[finding.type].append(finding)
        return dict(grouped)

    def summary(self):
        """Afficher le résumé des problèmes"""
        if not self.findings:
            print("✅ Aucun problème détecté!")
            return

        print("📊 RAPPORT DE CODE REVIEW")
        print("=" * 80)
        print(f"Projet: {self.project_root}")
        print(f"Rapport: {self.report_file}")
        print(f"Total problèmes: {len(self.findings)}")
        print("")

        by_type = self.group_by_type()
        print("Résumé par type:")
        for analysis_type, findings in sorted(by_type.items(), key=lambda x: -len(x[1])):
            count = len(findings)
            correctable = self._count_correctable(analysis_type)
            status = "✅ Corrigible" if correctable > 0 else "ℹ️ Manuel"
            print(f"  • {analysis_type:20} : {count:3} ({correctable} corrigibles) {status}")
        print("")

    def _count_correctable(self, analysis_type: str) -> int:
        """Compter les findings corrigibles d'un type"""
        if analysis_type in ('error_handling', 'unused_imports', 'docstrings', 'naming_conventions', 'type_hints'):
            return len([f for f in self.findings if f.type == analysis_type])
        return 0

    def interactive_fix(self):
        """Mode semi-automatique: propose les corrections avec confirmation"""
        if not self.findings:
            print("✅ Aucun problème à corriger!")
            return

        by_type = self.group_by_type()

        print("🔧 MODE CORRECTION SEMI-AUTOMATIQUE")
        print("=" * 80)
        print("")

        # Traiter chaque type
        for analysis_type in sorted(by_type.keys()):
            findings = by_type[analysis_type]

            if analysis_type == 'long_functions':
                self._handle_long_functions(findings)
            elif analysis_type == 'error_handling':
                self._handle_error_handling(findings)
            elif analysis_type == 'unused_imports':
                self._handle_unused_imports(findings)
            elif analysis_type == 'docstrings':
                self._handle_docstrings(findings)
            elif analysis_type == 'naming_conventions':
                self._handle_naming_conventions(findings)
            elif analysis_type == 'type_hints':
                self._handle_type_hints(findings)
            else:
                print(f"⚠️ Type non géré: {analysis_type} ({len(findings)} problèmes)")
                print("")

        self._print_summary()

    def _handle_error_handling(self, findings: List[Finding]):
        """Corriger les blocs except vides"""
        print(f"🔴 ERROR HANDLING ({len(findings)} problèmes)")
        print("-" * 80)

        for finding in findings:
            file_path = self.project_root / finding.file
            if not file_path.exists():
                continue

            print(f"  {finding.file}:{finding.line}")
            print(f"    Problème: {finding.message}")

            # Proposer la correction
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            if finding.line - 1 < len(lines):
                context = lines[finding.line - 1].strip()
                print(f"    Ligne: {context[:60]}")

                response = input("    Corriger? (o/n) [o]: ").strip().lower() or 'o'
                if response == 'o':
                    self._fix_error_handling(file_path, finding.line)
                    self.corrections_applied += 1
                else:
                    self.corrections_skipped += 1

            print("")

    def _fix_error_handling(self, file_path: Path, line_num: int):
        """Ajouter logging.exception() dans le bloc except"""
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Trouver et remplacer le 'pass' par logging.exception()
        for i in range(line_num - 1, min(line_num + 5, len(lines))):
            if 'pass' in lines[i]:
                indent = len(lines[i]) - len(lines[i].lstrip())
                lines[i] = ' ' * indent + 'logging.exception("Erreur")\n'
                break

        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"    ✅ Corrigé: ajout logging.exception()")

    def _handle_unused_imports(self, findings: List[Finding]):
        """Supprimer les imports non utilisés"""
        print(f"📦 UNUSED IMPORTS ({len(findings)} problèmes)")
        print("-" * 80)

        by_file = defaultdict(list)
        for finding in findings:
            by_file[finding.file].append(finding)

        for file_str, file_findings in by_file.items():
            file_path = self.project_root / file_str
            if not file_path.exists():
                continue

            print(f"  {file_str}")
            for finding in file_findings:
                print(f"    Ligne {finding.line}: {finding.message}")

            response = input("    Supprimer tous? (o/n) [o]: ").strip().lower() or 'o'
            if response == 'o':
                self._fix_unused_imports(file_path, file_findings)
                self.corrections_applied += len(file_findings)
            else:
                self.corrections_skipped += len(file_findings)

            print("")

    def _fix_unused_imports(self, file_path: Path, findings: List[Finding]):
        """Supprimer les imports non utilisés du fichier"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extraire les noms des imports non utilisés
        imports_to_remove = set()
        for finding in findings:
            # Parser le message pour extraire le nom
            match = re.search(r'"([^"]+)"', finding.message)
            if match:
                imports_to_remove.add(match.group(1))

        # Utiliser AST pour trouver et supprimer les imports
        try:
            tree = ast.parse(content)
            lines = content.split('\n')
            lines_to_remove = set()

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in imports_to_remove or alias.asname in imports_to_remove:
                            lines_to_remove.add(node.lineno - 1)

                elif isinstance(node, ast.ImportFrom):
                    remaining_names = []
                    for alias in node.names:
                        if alias.name not in imports_to_remove and alias.asname not in imports_to_remove:
                            remaining_names.append(alias)

                    if not remaining_names and node.names:
                        lines_to_remove.add(node.lineno - 1)
                    elif remaining_names and len(remaining_names) < len(node.names):
                        # Modifier la ligne pour garder les imports valides
                        import_names = ', '.join(
                            alias.asname or alias.name for alias in remaining_names
                        )
                        lines[node.lineno - 1] = f"from {node.module} import {import_names}"

            # Supprimer les lignes
            lines = [line for i, line in enumerate(lines) if i not in lines_to_remove]

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))

            print(f"    ✅ Supprimes {len(lines_to_remove)} imports")

        except Exception as e:
            print(f"    ⚠️ Erreur lors de la suppression: {e}")

    def _handle_docstrings(self, findings: List[Finding]):
        """Ajouter des docstrings"""
        print(f"📝 DOCSTRINGS ({len(findings)} problèmes)")
        print("-" * 80)
        print(f"  {len(findings)} docstrings manquantes")
        print("")
        print("  ℹ️ Vous devez les ajouter manuellement.")
        print("  Utilisez le rapport Markdown pour les localiser rapidement.")
        print("")

    def _handle_naming_conventions(self, findings: List[Finding]):
        """Renommer les variables/fonctions"""
        print(f"🔤 NAMING CONVENTIONS ({len(findings)} problèmes)")
        print("-" * 80)
        print(f"  {len(findings)} violations de conventions PEP 8")
        print("")
        print("  ℹ️ Les renommages automatiques sont risqués.")
        print("  Corrigez-les manuellement ou consultez le rapport Markdown.")
        print("")

    def _handle_type_hints(self, findings: List[Finding]):
        """Ajouter des type hints basiques"""
        print(f"🏷️ TYPE HINTS ({len(findings)} problèmes)")
        print("-" * 80)
        print(f"  {len(findings)} fonctions sans type hints")
        print("")
        print("  ℹ️ Les type hints automatiques risquent d'être imprécis.")
        print("  Ajoutez-les manuellement ou générez-les avec un outil spécialisé.")
        print("")

    def _handle_long_functions(self, findings: List[Finding]):
        """Afficher les fonctions trop longues (manual fix)"""
        print(f"⚠️ LONG FUNCTIONS ({len(findings)} problèmes)")
        print("-" * 80)
        print("  Ces fonctions doivent être refactorisées MANUELLEMENT")
        print("  (Trop de contexte métier pour corriger automatiquement)")
        print("")

        for finding in findings:
            file_path = self.project_root / finding.file
            if file_path.exists():
                print(f"  • {finding.file}:{finding.line}")
                print(f"    {finding.message}")
                print("")

        input("  Appuyez sur Entrée pour continuer...")
        print("")

    def _print_summary(self):
        """Afficher le résumé des corrections"""
        print("=" * 80)
        print("📋 RÉSUMÉ DES CORRECTIONS")
        print("=" * 80)
        print(f"  ✅ Appliquées: {self.corrections_applied}")
        print(f"  ⏭️  Ignorées: {self.corrections_skipped}")
        print(f"  ℹ️  Manuelles: {len(self.findings) - self.corrections_applied - self.corrections_skipped}")
        print("")

        if self.corrections_applied > 0:
            print("✅ Corrections appliquées!")
            print("   Relancez l'analyse pour vérifier la progression:")
            print(f'   python "$env:USERPROFILE\\.claude\\skills\\code-review-analysis\\analyzer.py" "." --analyze')
            print("")


def main():
    if len(sys.argv) < 2:
        print("Usage: python fixer.py <project_root> [--summary|--fix]")
        print("")
        print("Options:")
        print("  --summary    Afficher le résumé des problèmes")
        print("  --fix        Mode correction semi-automatique (défaut)")
        sys.exit(1)

    project_root = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else '--fix'

    if not Path(project_root).exists():
        print(f"❌ Projet non trouvé: {project_root}")
        sys.exit(1)

    fixer = CodeReviewFixer(project_root)

    if not fixer.find_report():
        sys.exit(1)

    if command == '--summary':
        fixer.summary()
    elif command == '--fix':
        fixer.interactive_fix()
    else:
        print(f"❌ Commande inconnue: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
