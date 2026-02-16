"""
VUT Scraper - web scraping studijních programů VUT
Získává seznam fakult a jejich studijních programů z webu VUT
"""

import json
import re
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple

from config import *
class VutScraper:
    """
    Třída pro získání dat o studijních programech z webu VUT Brno.
    """
    

    
    def __init__(self, language: str = "cs"):
        """
        Inicializace scraperu.
        
        Args:
            language: Jazyk stránky ('cs' nebo 'en')
        """
        self.language = language
        self.url = PROGRAMS_URL_CS if language == "cs" else PROGRAMS_URL_EN
        self.soup = None
        self.data = []
        
    def _fetch_html(self) -> str:
        """
        Stáhne HTML ze stránky VUT.
        
        Returns:
            HTML obsah stránky
            
        Raises:
            requests.RequestException: Pokud se nepodaří stáhnout stránku
        """
        print(f"Stahuji data z: {self.url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            response = requests.get(self.url, headers=headers, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            print(f"✓ Stránka úspěšně stažena (velikost: {len(response.text)} znaků)")
            return response.text
        except requests.RequestException as e:
            print(f"✗ Chyba při stahování stránky: {e}")
            raise
    
    def _clean_text(self, text: Optional[str]) -> str:
        """
        Očistí text od nadbytečných mezer a nových řádků.
        
        Args:
            text: Text k očištění
            
        Returns:
            Očištěný text
        """
        if text:
            return " ".join(text.split())
        return ""
    
    def _parse_program_info(self, full_text: str) -> Tuple[str, Optional[str]]:
        """
        Rozdělí řetězec 'Název programu (ZKRATKA)' na název a zkratku.
        
        Args:
            full_text: Celý text s názvem a zkratkou
            
        Returns:
            Tuple (název, zkratka)
            
        Příklad:
            "Sportovní technologie (BPC-STC)" -> ("Sportovní technologie", "BPC-STC")
        """
        full_text = self._clean_text(full_text)
        
        # Regex hledá text následovaný závorkou s obsahem na konci řetězce
        match = re.match(r"^(.*?)\s*\(([^)]+)\)$", full_text)
        
        if match:
            return match.group(1).strip(), match.group(2).strip()
        
        # Fallback pokud není zkratka v závorce
        return full_text, None
    
    def _extract_id_from_url(self, url: Optional[str]) -> Optional[str]:
        """
        Vytáhne ID z URL.
        
        Args:
            url: URL adresa
            
        Returns:
            ID programu nebo None
            
        Příklad:
            "/studenti/programy/program/9488" -> "9488"
        """
        if not url:
            return None
        
        # Najde posloupnost čísel na konci url
        match = re.search(r'/(\d+)$', url)
        return match.group(1) if match else None
    
    def scrape(self) -> List[Dict]:
        """
        Hlavní metoda pro získání dat o fakultách a programech.
        
        Returns:
            Seznam slovníků s informacemi o fakultách a jejich programech
        """
        # Stáhne HTML
        html_content = self._fetch_html()
        self.soup = BeautifulSoup(html_content, 'html.parser')
        
        # Najde všechny položky fakult
        faculty_items = self.soup.select('.c-faculties-list__item')
        
        print(f"\nNalezeno fakult: {len(faculty_items)}")
        
        for item in faculty_items:
            # 1. Získání informací o fakultě
            fac_abbr_elem = item.select_one('.b-faculty-list__faculty')
            fac_title_elem = item.select_one('.b-faculty-list__title')
            
            if not fac_abbr_elem or not fac_title_elem:
                continue
            
            faculty_abbr = self._clean_text(fac_abbr_elem.get_text())
            faculty_name = self._clean_text(fac_title_elem.get_text())
            
            print(f"\nZpracovávám fakultu: {faculty_abbr} - {faculty_name}")
            
            faculty_info = {
                "zkratka": faculty_abbr,
                "nazev": faculty_name,
                "programy": []
            }
            
            # 2. Hledání programů v rámci fakulty
            program_nodes = item.select('.b-programme')
            
            print(f"  Nalezeno programů: {len(program_nodes)}")
            
            for prog in program_nodes:
                # Odkaz obsahuje název i zkratku
                link_elem = prog.select_one('.b-programme__title .b-programme__link')
                
                if link_elem:
                    full_name = link_elem.get_text()
                    href = link_elem.get('href')
                    
                    name, abbr = self._parse_program_info(full_name)
                    prog_id = self._extract_id_from_url(href)
                    
                    program_info = {
                        "id": prog_id,
                        "nazev": name,
                        "zkratka_programu": abbr,
                        "url": href,
                        "full_url": f"{BASE_URL}{href}" if href else None
                    }
                    
                    faculty_info["programy"].append(program_info)
            
            self.data.append(faculty_info)
        
        print(f"\n✓ Scraping dokončen. Celkem fakult: {len(self.data)}")
        total_programs = sum(len(f['programy']) for f in self.data)
        print(f"✓ Celkem programů: {total_programs}")
        
        return self.data
    
    def to_json(self, indent: int = 4) -> str:
        """
        Vrátí data jako formátovaný JSON string.
        
        Args:
            indent: Počet mezer pro odsazení
            
        Returns:
            JSON string
        """
        return json.dumps(self.data, ensure_ascii=False, indent=indent)
    
    def save_to_file(self, filename: str = "vut_programy.json"):
        """
        Uloží data do JSON souboru.
        
        Args:
            filename: Název výstupního souboru
        """
        json_output = self.to_json()
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(json_output)
        
        print(f"\n✓ Data uložena do souboru: {filename}")
    
    def get_statistics(self) -> Dict:
        """
        Vrátí statistiky o získaných datech.
        
        Returns:
            Slovník se statistikami
        """
        stats = {
            "pocet_fakult": len(self.data),
            "pocet_programu_celkem": sum(len(f['programy']) for f in self.data),
            "programy_po_fakultach": {}
        }
        
        for faculty in self.data:
            stats["programy_po_fakultach"][faculty["zkratka"]] = len(faculty["programy"])
        
        return stats
    
    def get_faculties(self) -> List[Dict]:
        """
        Vrátí seznam fakult.
        
        Returns:
            Seznam fakult jako slovníky
        """

        # Export jen fakult (pro použití v REST API)
        faculties_only = [
            {
                "zkratka": f['zkratka'],
                "nazev": f['nazev'],
            }
            for f in self.data
        ]
        name = get_faculty_file(self.language)
        with open(name, "w", encoding="utf-8") as f:
            json.dump(faculties_only, f, ensure_ascii=False, indent=2)

        print(f"✓ Seznam fakult exportován do {name}")


def scrape_and_filter_data():
    """
    Hlavní funkce pro spuštění scraperu.
    """
    print("VUT Scraper - získání dat o studijních programech")
    
    # Scraping české verze
    print("\n>>> Zpracovávám ČESKOU verzi stránky <<<\n")
    scraper_cs = VutScraper(language="cs")
    
    try:
        data_cs = scraper_cs.scrape()
        scraper_cs.save_to_file(PROGRAMS_CS)
        scraper_cs.get_faculties()
        
        # Výpis statistik
        stats = scraper_cs.get_statistics()
        print("\n" + "=" * 70)
        print("STATISTIKY (ČJ):")
        print(f"  Fakult: {stats['pocet_fakult']}")
        print(f"  Programů celkem: {stats['pocet_programu_celkem']}")
        print("\n  Programy po fakultách:")
        for fac, count in stats['programy_po_fakultach'].items():
            print(f"    {fac}: {count}")
        print("=" * 70)
        
    except Exception as e:
        print(f"\nERROR in 'scrape_cs': {e}")
        return
    
    # Volitelně i anglická verze
    print("\n\n>>> Zpracovávám ANGLICKOU verzi stránky <<<\n")
    scraper_en = VutScraper(language="en")
    
    try:
        data_en = scraper_en.scrape()
        scraper_en.save_to_file(PROGRAMS_EN)
        scraper_en.get_faculties()
        stats_en = scraper_en.get_statistics()
        print("\n" + "=" * 70)
        print("STATISTIKY (EN):")
        print(f"  Fakult: {stats_en['pocet_fakult']}")
        print(f"  Programů celkem: {stats_en['pocet_programu_celkem']}")
        print("=" * 70)
        
    except Exception as e:
        print(f"\nERROR in 'scrape_en': {e}")
    
    print("\nDone!")


if __name__ == "__main__":
    scrape_and_filter_data()
