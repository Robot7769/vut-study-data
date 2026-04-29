"""
VUT Sports Scraper - Scraper sportů CESA VUT

Stahuje dostupné sporty z VUT CESA portálu.
Podporuje češtinu (cs-CZ) i angličtinu (en-US).

Výstup: JSON se strukturou:
[{
    id, nazev (name), zkratka (abbreviation), semestr (semester), url
}]
"""

import json
import os
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

from config import *
from HttpClient import HttpClient


# ---------------------------------------------------------------------------
# Třída SportsScraper
# ---------------------------------------------------------------------------

class SportsScraper:
    """
    Scraper sportů z VUT CESA.
    
    Stahuje seznam dostupných sportů v češtině nebo angličtině.
    """

    MAX_RETRIES = 3
    MAX_PAGES = 30

    def __init__(
        self,
        language: str = "cs-CZ",
        delay_range: tuple = (2.0, 5.0),
        max_pages: int = MAX_PAGES,
    ):
        self.language = language
        self.max_pages = max_pages

        # URL na základě jazyka
        if language == "cs-CZ":
            self.base_url = SPORTS_URL_CS
            self.empty_message = "nebyl nalezen žádný sport"
            self.semester_keywords = {
                "winter": "zimní",
                "summer": "letní",
            }
        else:  # en-US
            self.base_url = SPORTS_URL_EN
            self.empty_message = "no sports found"
            self.semester_keywords = {
                "winter": "winter",
                "summer": "summer",
            }

        # Cesta k výstupnímu souboru
        self.output_file = get_sports_output(language)
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)

        # HTTP klient
        self.client = HttpClient(
            delay_range=delay_range, max_retries=self.MAX_RETRIES
        )

        # Výsledky
        self.results: List[Dict] = []

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _clean_text(text: Optional[str]) -> str:
        """Vyčistí text od nadbytečných mezer."""
        if text:
            return " ".join(text.split())
        return ""

    def _extract_semester(self, annot_text: str) -> List[str]:
        """Detekuje semestr z anotace. Vrací seznam."""
        semesters = []
        annot_lower = annot_text.lower()
        if self.semester_keywords["winter"] in annot_lower:
            semesters.append("zimní" if self.language == "cs-CZ" else "winter")
        if self.semester_keywords["summer"] in annot_lower:
            semesters.append("letní" if self.language == "cs-CZ" else "summer")
        return semesters if semesters else ["unknown"]

    # ------------------------------------------------------------------
    # Scraping
    # ------------------------------------------------------------------

    def fetch_all_sports(self) -> bool:
        """
        Prochází stránky a sbírá data o sportech.
        
        Returns:
            True pokud se vázně podařilo, False pokud vznikla chyba.
        """
        all_sports = {}

        print(f"✓ Spouštění scraperu sportů VUT CESA ({self.language})...")

        for page in range(1, self.max_pages + 1):
            url = f"{self.base_url}{page}"

            # Random delay před každým požadavkem
            self.client.delay()
            # Stáhni stránku
            response = self.client.get(url, delay=True)
            if response is None:
                print(f"✗ Chyba při stažení stránky {page} - přerušuji")
                return False

            # Parsuj HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Zkontroluj, zda je stránka prázdná
            if self.empty_message in soup.get_text().lower():
                print(f"✓ Stránka {page} je prázdná - konec")
                break

            # Hledej položky
            items = soup.find_all('li', class_='c-subjects__item')
            if not items:
                print(f"✓ Žádné položky na stránce {page} - konec")
                break

            # Extrahuj data
            for item in items:
                a_tag = item.find('a', class_='b-subject__link')
                if not a_tag:
                    continue

                full_text = a_tag.get_text(strip=True)
                href = a_tag.get('href', '')

                # ID
                id_match = re.search(r'/detail/(\d+)', href)
                sport_id = id_match.group(1) if id_match else href

                # Jméno a zkratka
                name_match = re.search(r'(.*?)\s*[–\-—]\s*(TV-[A-Z0-9\-]+)\b', full_text)
                if name_match:
                    name = self._clean_text(name_match.group(1))
                    abbreviation = name_match.group(2).strip()
                else:
                    name = full_text
                    abbreviation = "N/A"

                # Semestr (seznam)
                semesters = []
                annot_p = item.find('p', class_='b-subject__annot')
                if annot_p:
                    annot_text = annot_p.get_text(separator=" ", strip=True)
                    semesters = self._extract_semester(annot_text)

                # URL
                base_domain = "https://www.cesa.vut.cz"
                sport_url = f"{base_domain}{href}" if href.startswith('/') else href

                # Ulož - stejná struktura jako subjects
                all_sports[sport_id] = {
                    'zkratka': abbreviation,
                    'nazev': name,
                    'kredity': "1",
                    'povinnost': 'sport',
                    'zakonceni': 'zá',
                    'skupina': '',
                    'semestr': semesters,
                    'rocnik': '0',
                    'url': sport_url
                }

            print(f"  ✓ Stránka {page}: {len(items)} sportů")


        self.results = list(all_sports.values())
        return True

    def save_results(self) -> None:
        """Uloží výsledky do JSON."""
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"\n✓ {len(self.results)} sportů uloženo do {self.output_file}")

    def run(self) -> bool:
        """
        Spustí kompletní scraping - stažení a uložení dat.
        
        Returns:
            True pokud vše OK.
        """
        if self.fetch_all_sports():
            self.save_results()
            return True
        return False


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Scrape VUT CESA sports data to JSON."
    )
    parser.add_argument(
        "--language",
        choices=["cs-CZ", "en-US"],
        default="cs-CZ",
        help="Jazyk scrapování",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=30,
        help="Maximální počet stránek k prohledání",
    )
    parser.add_argument(
        "--delay-min",
        type=float,
        default=2.0,
        help="Minimální delay mezi požadavky (sekundy)",
    )
    parser.add_argument(
        "--delay-max",
        type=float,
        default=5.0,
        help="Maximální delay mezi požadavky (sekundy)",
    )
    args = parser.parse_args()

    scraper = SportsScraper(
        language=args.language,
        max_pages=args.max_pages,
        delay_range=(args.delay_min, args.delay_max),
    )
    if not scraper.run():
        exit(1)
