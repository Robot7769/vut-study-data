import json
import os
from collections import OrderedDict

from config import *


class DataAnalyst:
    """Analýza studijních plánů – seskupení podle fakult."""

    # ------------------------------------------------------------------
    # Veřejné rozhraní
    # ------------------------------------------------------------------

    def run(self):
        """Spustí analýzu pro obě jazykové verze (cs i en)."""
        for lang in LANGUAGES:
            self._process_language(lang)

    # ------------------------------------------------------------------
    # Interní metody
    # ------------------------------------------------------------------

    def _process_language(self, language: str):
        """Zpracuje jednu jazykovou verzi studijních plánů."""
        input_path = get_study_plans_output(language)
        output_path = get_study_programmes_output(language)

        # Kontrola existence vstupního souboru
        if not os.path.isfile(input_path):
            print(f"[WARN] Soubor '{input_path}' neexistuje – přeskakuji ({language}).")
            return

        # Načtení dat
        with open(input_path, "r", encoding="utf-8") as f:
            plans: list[dict] = json.load(f)

        # Seskupení podle fakulty
        grouped = self._group_by_faculty(plans)

        # Uložení výstupu
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(grouped, f, ensure_ascii=False, indent=2)

        print(f"[OK] Vytvořen soubor '{output_path}' – {len(grouped)} fakult, jazyk: {language}")

    @staticmethod
    def _group_by_faculty(plans: list[dict]) -> list[dict]:
        """Seskupí studijní plány podle zkratky fakulty.

        Vrací seznam objektů:
        {
            "zkratka_fakulty": "...",
            "fakulta": "...",
            "programy": [
                {
                    "zkratka_programu": "...",
                    "nazev_programu": "...",
                    "specializace": "...",
                    "url_planu": "..."
                },
                ...
            ]
        }
        """
        faculties: OrderedDict[str, dict] = OrderedDict()

        for plan in plans:
            key = plan.get("zkratka_fakulty", "UNKNOWN")

            if key not in faculties:
                faculties[key] = {
                    "zkratka_fakulty": key,
                    "fakulta": plan.get("fakulta", ""),
                    "programy": [],
                }

            raw_spec = plan.get("specializace", "")
            if raw_spec and ":" in raw_spec:
                spec_code, spec_name = raw_spec.split(":", 1)
                specializace = spec_code.strip()
                nazev = f"{plan.get('nazev_programu', '')} - {spec_name.strip()}"
            else:
                specializace = raw_spec
                nazev = plan.get("nazev_programu", "")

            faculties[key]["programy"].append({
                "zkratka_programu": plan.get("zkratka_programu", ""),
                "specializace": specializace,
                "nazev_programu": nazev,
                "url": plan.get("url_planu", ""),
            })

        return list(faculties.values())


# ------------------------------------------------------------------
# Přímé spuštění
# ------------------------------------------------------------------
if __name__ == "__main__":
    analyst = DataAnalyst()
    analyst.run()
