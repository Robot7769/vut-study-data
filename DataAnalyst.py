import json
import os
import re
from collections import OrderedDict

from config import *


class DataAnalyst:
    """Analýza studijních plánů – seskupení podle fakult."""

    # ------------------------------------------------------------------
    # Veřejné rozhraní
    # ------------------------------------------------------------------

    def run(self):
        """Spustí analýzu pro obě jazykové verze (cs-CS i en-US)."""
        for lang in LANGUAGES:
            self._process_language(lang)
            self._export_subjects(lang)

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

    def _export_subjects(self, language: str):
        """Exportuje předměty pro každý studijní plán do samostatných souborů.

        Struktura výstupu:
          - Bez specializace: {subjects_dir}/{zkratka_programu}.json
          - Se specializací:  {subjects_dir}/{zkratka_programu}/{kod_specializace}.json
        """
        input_path = get_study_plans_output(language)
        subjects_dir = get_subjects_dir(language)

        if not os.path.isfile(input_path):
            print(f"[WARN] Soubor '{input_path}' neexistuje – přeskakuji export předmětů ({language}).")
            return

        with open(input_path, "r", encoding="utf-8") as f:
            plans: list[dict] = json.load(f)

        os.makedirs(subjects_dir, exist_ok=True)

        file_count = 0
        for plan in plans:
            zkratka = plan.get("zkratka_programu", "UNKNOWN")
            raw_spec = plan.get("specializace", "")
            predmety = plan.get("predmety", [])

            if raw_spec and ":" in raw_spec:
                # Se specializací → složka programu / soubor specializace
                spec_code = raw_spec.split(":", 1)[0].strip()
                # Extrakce kódu ze závorek (např. --- (AM1) → AM1)
                match = re.search(r'\(([^)]+)\)', spec_code)
                if match:
                    spec_code = match.group(1).strip()
                dir_path = os.path.join(subjects_dir, zkratka)
                os.makedirs(dir_path, exist_ok=True)
                file_path = os.path.join(dir_path, f"{spec_code}.json")
            else:
                # Bez specializace → přímo soubor
                file_path = os.path.join(subjects_dir, f"{zkratka}.json")

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(predmety, f, ensure_ascii=False, indent=2)
            file_count += 1

        print(f"[OK] Exportováno {file_count} souborů předmětů do '{subjects_dir}', jazyk: {language}")

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
                    "specializace": "..." (volitelné),
                    "doba_studia": "..." (volitelné),
                    "kredity": "..." (volitelné),
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
                spec_code = spec_code.strip()
                # Extrakce kódu ze závorek (např. --- (AM1) → AM1)
                match = re.search(r'\(([^)]+)\)', spec_code)
                if match:
                    spec_code = match.group(1).strip()
                specializace = spec_code
                nazev = f"{plan.get('nazev_programu', '')} - {spec_name.strip()}"
            else:
                specializace = raw_spec
                nazev = plan.get("nazev_programu", "")

            program_entry = {
                "zkratka_programu": plan.get("zkratka_programu", ""),
                "nazev_programu": nazev,
                "url": plan.get("url_planu", ""),
            }
            
            if specializace and specializace.lower() != "bez specializace":
                program_entry["specializace"] = specializace
            
            # Přidání standardní doby studia, pokud existuje
            duration = plan.get("doba_studia", "")
            if duration:
                duration = duration.split(" ")[0]  # Extrakce pouze čísla (např. "3 roky" → "3")
                program_entry["doba_studia"] = duration

            study_type = plan.get("typ_studia", "")
            if study_type:
                program_entry["typ_studia"] = study_type
            
            # Přidání kreditů, pokud existují
            credits = plan.get("kredity", "")
            if credits:
                program_entry["kredity"] = credits
            
            faculties[key]["programy"].append(program_entry)

        return list(faculties.values())


# ------------------------------------------------------------------
# Přímé spuštění
# ------------------------------------------------------------------
if __name__ == "__main__":
    analyst = DataAnalyst()
    analyst.run()
