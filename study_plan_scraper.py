"""
VUT Study Plan Scraper - dvoufázový scraper studijních plánů VUT

Fáze 1 (Discovery): Načte hlavní index programů, detekuje programy se
    specializacemi vs. koncové programy a sestaví frontu URL ke zpracování.
Fáze 2 (Extraction): Projde frontu, stáhne studijní plány a extrahuje
    tabulky předmětů. Podporuje resume (pokračování po přerušení).

Výstup: JSON se strukturou:
[{
    zkratka_fakulty, fakulta, zkratka_programu, nazev_programu,
    specializace, url_planu,
    predmety: [{zkratka, nazev, kredity, povinnost, zakonceni,
                skupina, semestr, rocnik, url}]
}]
"""

import json
import os
import re
from collections import deque
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Deque

from config import *
from HttpClient import HttpClient


# ---------------------------------------------------------------------------
# Třída StudyPlanScraper
# ---------------------------------------------------------------------------

class StudyPlanScraper:
    """
    Dvoufázový scraper studijních plánů VUT.

    Fáze 1 – Discovery: Sestaví frontu URL z hlavního indexu programů.
    Fáze 2 – Extraction: Prochází frontu, stahuje studijní plány a parsuje
        tabulky předmětů. Podporuje průběžné ukládání a resume.
    """

    MAX_RETRIES = 3

    def __init__(
        self,
        language: str = "cs",
        delay_range: tuple = (2.0, 5.0),
        output_dir: Optional[str] = None,
    ):
        self.language = language
        self.base_url = BASE_URL
        self.programs_url = PROGRAMS_URL_CS if language == "cs" else PROGRAMS_URL_EN

        # Cesty k souborům
        self.output_file = get_study_plans_output(language)
        self.progress_file = get_study_plans_progress(language)
        
        # Vytvoř adresář pro výstupní soubory
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        
        # HTTP klient
        self.client = HttpClient(
            delay_range=delay_range, max_retries=self.MAX_RETRIES
        )

        # Stav
        self.queue: Deque[Dict] = deque()
        self.processed_urls: set = set()
        self.results: List[Dict] = []

    # ------------------------------------------------------------------
    # Persistence – ukládání / načítání stavu
    # ------------------------------------------------------------------

    def _save_progress(self) -> None:
        """Uloží aktuální stav (fronta, zpracované URL, výsledky)."""
        state = {
            "processed_urls": list(self.processed_urls),
            "queue": list(self.queue),
            "results": self.results,
        }
        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def _load_progress(self) -> bool:
        """
        Načte předchozí stav pokud existuje.

        Returns:
            True pokud byl stav úspěšně načten.
        """
        if not os.path.exists(self.progress_file):
            return False
        try:
            with open(self.progress_file, "r", encoding="utf-8") as f:
                state = json.load(f)
            self.processed_urls = set(state.get("processed_urls", []))
            self.queue = deque(state.get("queue", []))
            self.results = state.get("results", [])
            print(
                f"✓ Načten uložený stav: {len(self.processed_urls)} zpracováno, "
                f"{len(self.queue)} ve frontě, {len(self.results)} výsledků"
            )
            return True
        except (json.JSONDecodeError, KeyError) as e:
            print(f"✗ Nelze načíst progress soubor: {e}")
            return False

    def _save_results(self) -> None:
        """Uloží finální výsledky do JSON."""
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"\n✓ Výsledky uloženy do {self.output_file}")

    # ------------------------------------------------------------------
    # Pomocné metody
    # ------------------------------------------------------------------

    @staticmethod
    def _clean_text(text: Optional[str]) -> str:
        """Vyčistí text od nadbytečných mezer."""
        if text:
            return " ".join(text.split())
        return ""

    def _full_url(self, path: str) -> str:
        """Sestaví plné URL z relativní cesty."""
        if path.startswith("http"):
            return path
        return f"{self.base_url}{path}"

    @staticmethod
    def _parse_program_info(full_text: str):
        """
        Rozdělí 'Název programu (ZKRATKA)' na (název, zkratka).

        Příklad:
            "Informační technologie (BIT)" -> ("Informační technologie", "BIT")
        """
        full_text = " ".join(full_text.split())
        match = re.match(r"^(.*?)\s*\(([^)]+)\)$", full_text)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        return full_text, None

    def _normalize_specialization(self, spec: str) -> str:
        """
        Normalizuje specializaci podle pravidla:
        - Pokud obsahuje ':', je to skutečná specializace
        - Pokud ne, vrátí prázdný řetězec (= bez specializace)
        
        Args:
            spec: Řetězec se specializací
            
        Returns:
            Normalizovaná specializace nebo prázdný řetězec
        """
        if not spec:
            return ""
        spec = spec.strip()
        if ":" in spec:
            return spec
        return ""

    @staticmethod
    def _extract_study_duration(element) -> str:
        """
        Extrahuje standardní dobu studia z HTML elementu.
        
        Hledá text ve formátu "X roky", "X rok", "X years", "X year".
        
        Args:
            element: BeautifulSoup element (např. .b-programme nebo row)
            
        Returns:
            Standardní doba studia (např. "4 roky") nebo prázdný řetězec
        """
        if not element:
            return ""
        
        # Hledání v meta informacích (např. .b-branch__meta-title, .b-programme__meta)
        meta_selectors = [
            ".b-branch__meta-title",
            ".b-programme__meta",
            ".b-meta",
        ]
        
        for selector in meta_selectors:
            meta_elem = element.select_one(selector)
            if meta_elem:
                text = meta_elem.get_text().strip()
                # Hledání patternu "X roky/rok" nebo "X years/year"
                match = re.search(r'(\d+)\s*(rok[ůy]?|years?)', text, re.IGNORECASE)
                if match:
                    return text
        
        # Hledání v celém textu elementu jako fallback
        text = element.get_text()
        match = re.search(r'(\d+)\s*(rok[ůy]?|years?)(?!\s*[,.]?\s*ročník)', text, re.IGNORECASE)
        if match:
            return match.group(0)
        
        return ""

    @staticmethod
    def _extract_credits(soup: BeautifulSoup) -> str:
        """
        Extrahuje počet kreditů ze stránky studijního plánu.
        
        Hledá všechny výskyty "X credits", "X kreditů", "X ECTS kreditů" apod.
        a vrací nejvyšší hodnotu.
        
        Args:
            soup: BeautifulSoup objekt celé stránky
            
        Returns:
            Počet kreditů jako řetězec (např. "120") nebo prázdný řetězec
        """
        if not soup:
            return ""
        
        text = soup.get_text()
        credits_values = []
        
        # Hledání všech výskytů kreditů v různých formátech
        patterns = [
            r'(\d+)\s*ECTS\s*kredit[ůy]?',  # "120 ECTS kreditů"
            r'(\d+)\s*ECTS\s*credits?',       # "120 ECTS credits"
            r'(\d+)\s*ECTS',                  # "120 ECTS"
            r'(\d+)\s*credits?',              # "120 credits"
            r'(\d+)\s*kredit[ůy]?',           # "120 kreditů"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            credits_values.extend([int(m) for m in matches])
        
        # Vrátí maximální hodnotu nebo prázdný řetězec
        if credits_values:
            return str(max(credits_values))
        
        return ""

    @staticmethod
    def _parse_caption(caption_text: str) -> Dict[str, str]:
        """
        Parsuje caption tabulky na ročník a semestr.

        Příklady:
            "1. ročník, zimní semestr" -> {"rocnik": "1", "semestr": "zimní"}
            "Libovolný ročník, letní semestr" -> {"rocnik": "libovolný", "semestr": "letní"}

        Returns:
            {"rocnik": str, "semestr": str}
        """
        caption_text = " ".join(caption_text.split()).strip()
        result = {"rocnik": "", "semestr": ""}

        # Ročník: číslo nebo „libovolný"
        m_year = re.search(r"(\d+)\.\s*ročník", caption_text, re.IGNORECASE)
        if m_year:
            result["rocnik"] = m_year.group(1)
        elif re.search(r"libovoln", caption_text, re.IGNORECASE):
            result["rocnik"] = "libovolný"
        # Anglické varianty
        elif re.search(r"any\s+year", caption_text, re.IGNORECASE):
            result["rocnik"] = "libovolný"
        else:
            # "1. year of study" nebo "1st year"
            m_year_en = re.search(
                r"(\d+)(?:\.|st|nd|rd|th)\s+year", caption_text, re.IGNORECASE
            )
            if m_year_en:
                result["rocnik"] = m_year_en.group(1)

        # Semestr
        if re.search(r"zimn", caption_text, re.IGNORECASE):
            result["semestr"] = "zimní"
        elif re.search(r"letn", caption_text, re.IGNORECASE):
            result["semestr"] = "letní"
        elif re.search(r"winter", caption_text, re.IGNORECASE):
            result["semestr"] = "zimní"
        elif re.search(r"summer", caption_text, re.IGNORECASE):
            result["semestr"] = "letní"

        return result

    # ------------------------------------------------------------------
    # Fáze 1 – Discovery
    # ------------------------------------------------------------------

    def phase1_discover(self) -> None:
        """
        Fáze 1: Načte hlavní index programů a sestaví frontu URL.

        Pro každou fakultu extrahuje zkratku (FIT, FEKT, …) a plný název.
        Pro každý program extrahuje zkratku (BIT, MIT, …) a název.
        """
        print("=" * 70)
        print("FÁZE 1: Discovery – sestavení fronty URL")
        print("=" * 70)

        resp = self.client.get(self.programs_url, delay=False)
        if not resp:
            raise ConnectionError(
                f"Nelze stáhnout hlavní stránku: {self.programs_url}"
            )

        soup = BeautifulSoup(resp.text, "html.parser")
        faculty_items = soup.select(".c-faculties-list__item")
        print(f"Nalezeno fakult: {len(faculty_items)}")

        for item in faculty_items:
            fac_abbr_elem = item.select_one(".b-faculty-list__faculty")
            fac_title_elem = item.select_one(".b-faculty-list__title")
            if not fac_abbr_elem or not fac_title_elem:
                continue

            faculty_name = self._clean_text(fac_title_elem.get_text())
            faculty_abbr = self._clean_text(fac_abbr_elem.get_text())
            print(f"\n  {faculty_abbr} – {faculty_name}")

            program_nodes = item.select(".b-programme")
            for prog in program_nodes:
                link_elem = prog.select_one(
                    ".b-programme__title .b-programme__link"
                )
                if not link_elem:
                    continue

                full_name = link_elem.get_text()
                href = link_elem.get("href")
                name, abbr = self._parse_program_info(full_name)

                if not href:
                    print(f"    – {abbr or name} (bez URL, přeskakuji)")
                    continue

                # Extrakce standardní doby studia
                duration = self._extract_study_duration(prog)

                queue_item = {
                    "url": href,
                    "zkratka_fakulty": faculty_abbr,
                    "fakulta": faculty_name,
                    "zkratka_programu": abbr or "",
                    "nazev_programu": name,
                    "specializace": "",
                    "doba_studia": duration,
                    "typ": "program",
                    "retries": 0,
                }
                self.queue.append(queue_item)
                duration_info = f" ({duration})" if duration else ""
                print(f"    + {abbr}: {name}{duration_info}")

        print(
            f"\n✓ Fáze 1 dokončena. Fronta obsahuje {len(self.queue)} položek."
        )
        self._save_progress()

    # ------------------------------------------------------------------
    # Fáze 2 – Extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_page_type(soup: BeautifulSoup) -> str:
        """
        Detekuje typ stránky.

        Returns:
            'specializations' – stránka se seznamem specializací
            'study_plan'      – stránka se studijním plánem
            'unknown'         – nelze rozpoznat
        """
        # Detekce specializací
        h3_spec = soup.find(
            "h3",
            string=re.compile(
                r"Specializace|Specialisations?|Specializations?", re.IGNORECASE
            ),
        )
        if h3_spec:
            table = soup.select_one("table.data")
            if table:
                return "specializations"

        # Detekce studijního plánu – tabulka s caption „X. ročník, …"
        for table in soup.select("table"):
            caption = table.select_one("caption")
            if caption:
                cap_text = caption.get_text().lower()
                if "ročník" in cap_text or "semestr" in cap_text or "year" in cap_text:
                    return "study_plan"
            # Fallback: headers s Zkratka + Kr.
            headers = [
                th.get_text().strip().lower() for th in table.select("thead th")
            ]
            header_joined = " ".join(headers)
            has_abbr = "zkr" in header_joined or "abbr" in header_joined
            has_credits = "kr" in header_joined or "cr" in header_joined
            if has_abbr and has_credits:
                return "study_plan"

        return "unknown"

    def _extract_specializations(
        self, soup: BeautifulSoup, parent_item: Dict
    ) -> List[Dict]:
        """
        Extrahuje specializace z rozcestníku a vrátí nové položky fronty.
        """
        new_items = []
        table = soup.select_one("table.data")
        if not table:
            return new_items

        rows = table.select("tbody tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 2:
                continue

            # Zkratka specializace je v prvním sloupci
            spec_abbr = self._clean_text(cells[0].get_text())

            link_elem = cells[1].find("a")
            if not link_elem:
                continue

            spec_name = self._clean_text(link_elem.get_text())
            spec_href = link_elem.get("href")
            if not spec_href:
                continue

            # Název specializace = „ZKRATKA: Název"
            if spec_abbr and spec_abbr != "---":
                spec_label = f"{spec_abbr}: {spec_name}"
            else:
                spec_label = spec_name

            # Extrakce standardní doby studia ze řádku tabulky
            duration = self._extract_study_duration(row)
            # Pokud není v řádku, zkusit zdědit z parent_item
            if not duration:
                duration = parent_item.get("doba_studia", "")

            item = {
                "url": spec_href,
                "zkratka_fakulty": parent_item["zkratka_fakulty"],
                "fakulta": parent_item["fakulta"],
                "zkratka_programu": parent_item["zkratka_programu"],
                "nazev_programu": parent_item["nazev_programu"],
                "specializace": spec_label,
                "doba_studia": duration,
                "typ": "specializace",
                "retries": 0,
            }
            new_items.append(item)

        return new_items

    def _extract_subjects_with_semesters(
        self, soup: BeautifulSoup
    ) -> List[Dict]:
        """
        Extrahuje předměty ze VŠECH per-semestrových tabulek na stránce.

        Používá <caption> element k určení ročníku a semestru.
        Předměty, které se vyskytují ve více semestrech, jsou sloučeny:
        - semestr se nastaví na seznam unikátních hodnot
        - ročník se nastaví na minimální hodnotu

        Returns:
            Seznam deduplikovaných předmětů s informací o semestru a ročníku.
        """
        raw_subjects: List[Dict] = []

        for table in soup.select("table"):
            # Musí mít <caption> s informací o ročníku/semestru
            caption = table.select_one("caption")
            if not caption:
                continue

            cap_text = caption.get_text()
            cap_lower = cap_text.lower()
            if not any(
                kw in cap_lower
                for kw in ["ročník", "semestr", "year", "semester"]
            ):
                continue

            semester_info = self._parse_caption(cap_text)

            # Ověříme hlavičky
            headers_raw = [
                self._clean_text(th.get_text()).lower()
                for th in table.select("thead th")
            ]
            if not headers_raw:
                continue

            header_joined = " ".join(headers_raw)
            if "zkr" not in header_joined and "abbr" not in header_joined:
                continue

            col_map = self._map_columns(headers_raw)

            # Parsování řádků
            for row in table.select("tbody tr"):
                cells = row.find_all("td")
                if not cells or len(cells) < 3:
                    continue

                subject = self._parse_subject_row(cells, col_map)
                if subject:
                    subject["semestr"] = semester_info["semestr"]
                    subject["rocnik"] = semester_info["rocnik"]
                    raw_subjects.append(subject)

        # Deduplikace
        return self._merge_subjects(raw_subjects)

    @staticmethod
    def _map_columns(headers: List[str]) -> Dict[str, int]:
        """
        Namapuje názvy sloupců na indexy.

        Rozpoznává zkrácené české hlavičky:
        Zkratka | Název | J. | Kr. | Pov. | Prof. | Uk. | Hod. rozsah | Sk. | Ot.
          0        1      2    3     4       5       6       7            8     9
        """
        col_map: Dict[str, int] = {}
        for idx, h in enumerate(headers):
            hl = h.strip().rstrip(".")
            if hl in ("zkratka", "zkr", "abbr", "abbreviation"):
                col_map.setdefault("zkratka", idx)
            elif hl in ("název", "nazev", "name", "název (zaměření)", "title"):
                col_map.setdefault("nazev", idx)
            elif hl in ("kr", "cr", "kredity", "credits", "cred"):
                col_map.setdefault("kredity", idx)
            elif hl in ("pov", "com", "povinnost", "povinný", "obligation", "type"):
                col_map.setdefault("povinnost", idx)
            elif hl in ("uk", "compl", "ukončení", "zakončení", "completion", "exam"):
                col_map.setdefault("zakonceni", idx)
            elif hl in ("sk", "gr", "skupina", "group"):
                col_map.setdefault("skupina", idx)
        return col_map

    def _parse_subject_row(
        self, cells: list, col_map: Dict[str, int]
    ) -> Optional[Dict]:
        """Parsuje jeden řádek tabulky předmětů."""

        def _cell_text(key: str) -> str:
            idx = col_map.get(key)
            if idx is not None and idx < len(cells):
                return self._clean_text(cells[idx].get_text())
            return ""

        zkratka = _cell_text("zkratka")
        nazev = _cell_text("nazev")

        if not zkratka and not nazev:
            return None

        # URL předmětu
        url = ""
        for key in ("nazev", "zkratka"):
            idx = col_map.get(key)
            if idx is not None and idx < len(cells):
                link = cells[idx].find("a")
                if link and link.get("href"):
                    url = self._full_url(link["href"])
                    if not nazev:
                        nazev = self._clean_text(link.get_text())
                    break

        return {
            "zkratka": zkratka,
            "nazev": nazev,
            "kredity": _cell_text("kredity"),
            "povinnost": _cell_text("povinnost"),
            "zakonceni": _cell_text("zakonceni"),
            "skupina": _cell_text("skupina"),
            "url": url,
        }

    @staticmethod
    def _merge_subjects(raw: List[Dict]) -> List[Dict]:
        """
        Sloučí duplicitní předměty (stejná zkratka) v rámci jednoho plánu.

        - semestr → seznam unikátních hodnot (["zimní"] nebo ["zimní", "letní"])
        - rocnik  → minimální numerický ročník; „libovolný" má nejnižší prioritu
        """
        merged: Dict[str, Dict] = {}

        for subj in raw:
            key = subj["zkratka"]
            if not key:
                merged[f"_no_key_{id(subj)}"] = {
                    **subj,
                    "semestr": [subj["semestr"]] if subj["semestr"] else [],
                    "rocnik": subj["rocnik"],
                }
                continue

            if key not in merged:
                merged[key] = {
                    **subj,
                    "semestr": [subj["semestr"]] if subj["semestr"] else [],
                    "rocnik": subj["rocnik"],
                }
            else:
                existing = merged[key]
                # Sloučení semestru
                if subj["semestr"] and subj["semestr"] not in existing["semestr"]:
                    existing["semestr"].append(subj["semestr"])
                # Sloučení ročníku: numerický min, libovolný pouze pokud nic jiného
                existing["rocnik"] = _min_rocnik(
                    existing["rocnik"], subj["rocnik"]
                )

        return list(merged.values())

    # ------------------------------------------------------------------
    # Fáze 2 – hlavní smyčka
    # ------------------------------------------------------------------

    def phase2_extract(self) -> None:
        """
        Fáze 2: Prochází frontu URL, stahuje studijní plány a extrahuje
        tabulky předmětů. Ukládá průběžný stav po každé položce.
        """
        print("\n" + "=" * 70)
        print("FÁZE 2: Extraction – stahování studijních plánů")
        print("=" * 70)

        total_initial = len(self.queue) + len(self.processed_urls)
        counter = len(self.processed_urls)

        while self.queue:
            item = self.queue.popleft()
            url = item["url"]
            full_url = self._full_url(url)

            if full_url in self.processed_urls:
                continue

            counter += 1
            remaining = len(self.queue)
            label = (
                f"{item['zkratka_fakulty']} → "
                f"{item['zkratka_programu']}: {item['nazev_programu']}"
            )
            if item.get("specializace"):
                label += f" → {item['specializace']}"

            print(f"\n[{counter}/{total_initial + remaining}] {label}")
            print(f"    URL: {full_url}")

            # Random delay
            self.client.delay()

            resp = self.client.get(full_url)
            if not resp:
                retries = item.get("retries", 0)
                if retries < self.MAX_RETRIES:
                    item["retries"] = retries + 1
                    self.queue.append(item)
                    print(
                        f"    ↻ Zařazeno zpět do fronty "
                        f"(pokus {retries + 1}/{self.MAX_RETRIES})"
                    )
                else:
                    print(
                        f"    ✗ Přeskočeno po {self.MAX_RETRIES} "
                        f"neúspěšných pokusech"
                    )
                    self.processed_urls.add(full_url)
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            page_type = self._detect_page_type(soup)

            if page_type == "specializations":
                new_items = self._extract_specializations(soup, item)
                added = 0
                for ni in new_items:
                    ni_url = self._full_url(ni["url"])
                    if ni_url not in self.processed_urls:
                        self.queue.append(ni)
                        added += 1
                print(
                    f"    → Rozcestník: přidáno {added} specializací do fronty"
                )

            elif page_type == "study_plan":
                subjects = self._extract_subjects_with_semesters(soup)
                credits = self._extract_credits(soup)
                result = {
                    "zkratka_fakulty": item["zkratka_fakulty"],
                    "fakulta": item["fakulta"],
                    "zkratka_programu": item["zkratka_programu"],
                    "nazev_programu": item["nazev_programu"],
                    "specializace": self._normalize_specialization(
                        item.get("specializace", "")
                    ) or "Bez specializace",
                    "doba_studia": item.get("doba_studia", ""),
                    "kredity": credits,
                    "url_planu": full_url,
                    "predmety": subjects,
                }
                self.results.append(result)
                credits_info = f" ({credits} kreditů)" if credits else ""
                print(f"    ✓ Extrahováno {len(subjects)} předmětů{credits_info}")

            else:
                subjects = self._extract_subjects_with_semesters(soup)
                if subjects:
                    credits = self._extract_credits(soup)
                    result = {
                        "zkratka_fakulty": item["zkratka_fakulty"],
                        "fakulta": item["fakulta"],
                        "zkratka_programu": item["zkratka_programu"],
                        "nazev_programu": item["nazev_programu"],
                        "specializace": self._normalize_specialization(
                            item.get("specializace", "")
                        ) or "Bez specializace",
                        "doba_studia": item.get("doba_studia", ""),
                        "kredity": credits,
                        "url_planu": full_url,
                        "predmety": subjects,
                    }
                    self.results.append(result)
                    credits_info = f" ({credits} kreditů)" if credits else ""
                    print(
                        f"    ? Neznámý typ, ale nalezeno "
                        f"{len(subjects)} předmětů{credits_info}"
                    )
                else:
                    print(
                        "    ? Neznámý typ stránky, žádné předměty nenalezeny"
                    )

            self.processed_urls.add(full_url)
            self._save_progress()

        print(
            f"\n✓ Fáze 2 dokončena. "
            f"Celkem {len(self.results)} studijních plánů."
        )

    # ------------------------------------------------------------------
    # Hlavní orchestrace
    # ------------------------------------------------------------------

    def run(self, resume: bool = True) -> List[Dict]:
        """
        Spustí kompletní scraping (Fáze 1 + Fáze 2).

        Args:
            resume: Pokud True, pokusí se navázat na předchozí běh.

        Returns:
            Seznam studijních plánů s předměty.
        """
        loaded = False
        if resume:
            loaded = self._load_progress()

        if not loaded or not self.queue:
            self.queue.clear()
            self.processed_urls.clear()
            self.results.clear()
            self.phase1_discover()

        self.phase2_extract()
        self._save_results()
        self._print_statistics()

        if os.path.exists(self.progress_file):
            os.remove(self.progress_file)
            print("✓ Progress soubor odstraněn (scraping dokončen).")

        return self.results

    def _print_statistics(self) -> None:
        """Vypíše statistiky o získaných datech."""
        total_subjects = sum(len(r["predmety"]) for r in self.results)
        faculties = set(r["zkratka_fakulty"] for r in self.results)

        print("\n" + "=" * 70)
        print("STATISTIKY:")
        print(f"  Studijních plánů: {len(self.results)}")
        print(f"  Předmětů celkem:  {total_subjects}")
        print(f"  Fakult:           {len(faculties)}")
        print()

        fac_counts: Dict[str, int] = {}
        for r in self.results:
            key = r["zkratka_fakulty"]
            fac_counts[key] = fac_counts.get(key, 0) + len(r["predmety"])
        for fac, cnt in sorted(fac_counts.items()):
            print(f"    {fac}: {cnt} předmětů")
        print("=" * 70)


# ---------------------------------------------------------------------------
# Pomocné funkce mimo třídu
# ---------------------------------------------------------------------------

def _min_rocnik(a: str, b: str) -> str:
    """
    Vrátí menší ročník pro deduplikaci.

    Numerické hodnoty mají přednost před „libovolný".
    """
    if not a:
        return b
    if not b:
        return a
    a_is_num = a.isdigit()
    b_is_num = b.isdigit()
    if a_is_num and b_is_num:
        return str(min(int(a), int(b)))
    if a_is_num:
        return a
    if b_is_num:
        return b
    return a  # oba „libovolný"


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    """Spustí scraper studijních plánů z příkazové řádky."""
    import argparse

    parser = argparse.ArgumentParser(
        description="VUT Study Plan Scraper – stahování studijních plánů"
    )
    parser.add_argument(
        "--language",
        "-l",
        choices=["cs", "en"],
        default="cs",
        help="Jazyk stránek (default: cs)",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Ignorovat uložený stav a začít od začátku",
    )
    parser.add_argument(
        "--delay-min",
        type=float,
        default=2.0,
        help="Minimální zpoždění mezi požadavky v sekundách (default: 2.0)",
    )
    parser.add_argument(
        "--delay-max",
        type=float,
        default=5.0,
        help="Maximální zpoždění mezi požadavky v sekundách (default: 5.0)",
    )
    args = parser.parse_args()

    print("VUT Study Plan Scraper")
    print(f"Jazyk: {args.language}")
    print(f"Delay: {args.delay_min}–{args.delay_max}s")
    print(f"Resume: {'ano' if not args.no_resume else 'ne'}")
    print()

    scraper = StudyPlanScraper(
        language=args.language,
        delay_range=(args.delay_min, args.delay_max),
    )

    scraper.run(resume=not args.no_resume)


if __name__ == "__main__":
    main()
