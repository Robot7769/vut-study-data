# VUT study data

Data jsou získávána z [webu VUT Brno](https://www.vut.cz/studenti/programy) pomocí [study_plan_scraper.py](./study_plan_scraper.py). Analýza a zpracování dat probíhá v [DataAnalyst.py](./DataAnalyst.py), který generuje výstupní soubory ve formátu JSON.

Data jsou automaticky aktualizována pomocí [GitHub Actions](./.github/workflows/update_study_plans.yml).

#### Podporované jazyky
- Čeština (cs)
- Angličtina (en)

### Získání studijních programů
Vrací seznam studijních programů na VUT Brno, včetně jejich zkratek, názvů, specializací a URL odkazů.

```
https://raw.githubusercontent.com/Robot7769/vut-study-data/refs/heads/master/data/{cs,en}/study_programmes/programmes.json
```

### Získání předmětů
Vrací seznam předmětů pro každý studijní program, včetně jejich zkratky, názvu a URL odkazu.

```
https://raw.githubusercontent.com/Robot7769/vut-study-data/refs/heads/master/data/{cs,en}/subjects/{programme_code}.json
```
#### Pokud má program specializace, jsou předměty rozděleny podle nich.
```
https://raw.githubusercontent.com/Robot7769/vut-study-data/refs/heads/master/data/{cs,en}/subjects/{programme_code}_{specialization_code}.json
```

### Příklad:

FIT - Fakulta informačních technologií
 - MITAI - Informační technologie a umělá inteligence
 - NMAL: Strojové učení
   [https://www.vut.cz/studenti/programy/obor/17682/9506](https://www.vut.cz/studenti/programy/obor/17682/9506)
```
https://raw.githubusercontent.com/Robot7769/vut-study-data/refs/heads/master/data/cs/subjects/MITAI/NMAL.json
```

## Jak spustit vlastní sběr dat
 - Instalace závislostí
```bash
pip install -r requirements.txt
```
 - Spuštění scraperu

```bash
python study_plan_scraper.py
```
```bash
usage: study_plan_scraper.py [-h] [--language {cs,en}] [--no-resume] [--delay-min DELAY_MIN] [--delay-max DELAY_MAX]

VUT Study Plan Scraper – stahování studijních plánů

options:
  -h, --help            show this help message and exit
  --language {cs,en}, -l {cs,en}
                        Jazyk stránek (default: cs)
  --no-resume           Ignorovat uložený stav a začít od začátku
  --delay-min DELAY_MIN
                        Minimální zpoždění mezi požadavky v sekundách (default: 2.0)
  --delay-max DELAY_MAX
                        Maximální zpoždění mezi požadavky v sekundách (default: 5.0)
```

 - Vytvoření výstupních souborů
```bash
python DataAnalyst.py
```
