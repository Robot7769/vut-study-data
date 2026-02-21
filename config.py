BASE_URL = "https://www.vut.cz"
PROGRAMS_URL_CS = "https://www.vut.cz/studenti/programy"
PROGRAMS_URL_EN = "https://www.vut.cz/en/students/programmes"

LANGUAGES = ("cs", "en")

DATA_DIR = "data"
DATA_DIR_CS = f"{DATA_DIR}/cs"
DATA_DIR_EN = f"{DATA_DIR}/en"

PROGRAMS_BASE = f"{DATA_DIR}/programy_"
PROGRAMS_CS = f"{PROGRAMS_BASE}cs.json"
PROGRAMS_EN = f"{PROGRAMS_BASE}en.json"

def get_programs_file(language="cs"):
    if language == "cs":
        return PROGRAMS_CS
    elif language == "en":
        return PROGRAMS_EN
    else:
        raise ValueError("Neznámý jazyk. Použijte 'cs' nebo 'en'.")

SUBJECTS_BASE = "subjects"
SUBJECTS_DIR_CS = f"{DATA_DIR_CS}/{SUBJECTS_BASE}"
SUBJECTS_DIR_EN = f"{DATA_DIR_EN}/{SUBJECTS_BASE}"

def get_subjects_dir(language="cs"):
    if language == "cs":
        return SUBJECTS_DIR_CS
    elif language == "en":
        return SUBJECTS_DIR_EN
    else:
        raise ValueError("Neznámý jazyk. Použijte 'cs' nebo 'en'.")

STUDY_PLANS_DIR = f"{DATA_DIR}/raw_study_plans"
STUDY_PLANS_OUTPUT_CS = f"{STUDY_PLANS_DIR}/plans_cs.json"
STUDY_PLANS_OUTPUT_EN = f"{STUDY_PLANS_DIR}/plans_en.json"

def get_study_plans_output(language="cs"):
    if language == "cs":
        return STUDY_PLANS_OUTPUT_CS
    elif language == "en":
        return STUDY_PLANS_OUTPUT_EN
    else:
        raise ValueError("Neznámý jazyk. Použijte 'cs' nebo 'en'.")

STUDY_PLANS_PROGRESS_CS = f"{STUDY_PLANS_DIR}/progress_cs.json"
STUDY_PLANS_PROGRESS_EN = f"{STUDY_PLANS_DIR}/progress_en.json"

def get_study_plans_progress(language="cs"):
    if language == "cs":
        return STUDY_PLANS_PROGRESS_CS
    elif language == "en":
        return STUDY_PLANS_PROGRESS_EN
    else:
        raise ValueError("Neznámý jazyk. Použijte 'cs' nebo 'en'.")
    
STUDY_PROGRAMMES_BASE = "study_programmes"
STUDY_PROGRAMMES_OUTPUT_CS = f"{DATA_DIR_CS}/{STUDY_PROGRAMMES_BASE}/programmes.json"
STUDY_PROGRAMMES_OUTPUT_EN = f"{DATA_DIR_EN}/{STUDY_PROGRAMMES_BASE}/programmes.json"

def get_study_programmes_output(language="cs"):
    if language == "cs":
        return STUDY_PROGRAMMES_OUTPUT_CS
    elif language == "en":
        return STUDY_PROGRAMMES_OUTPUT_EN
    else:
        raise ValueError("Neznámý jazyk. Použijte 'cs' nebo 'en'.")
