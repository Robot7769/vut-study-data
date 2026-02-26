BASE_URL = "https://www.vut.cz"
PROGRAMS_URL_CS = "https://www.vut.cz/studenti/programy"
PROGRAMS_URL_EN = "https://www.vut.cz/en/students/programmes"

LANGUAGES = ("cs-CZ", "en-US")

DATA_DIR = "data"
DATA_DIR_CS = f"{DATA_DIR}/cs-CZ"
DATA_DIR_EN = f"{DATA_DIR}/en-US"

PROGRAMS_BASE = f"{DATA_DIR}/programy_"
PROGRAMS_CS = f"{PROGRAMS_BASE}cs.json"
PROGRAMS_EN = f"{PROGRAMS_BASE}en.json"

def get_programs_file(language=LANGUAGES[0]):
    if language == LANGUAGES[0]:  # "cs-CZ"
        return PROGRAMS_CS
    elif language == LANGUAGES[1]:  # "en-US"
        return PROGRAMS_EN
    else:
        raise ValueError("Neznámý jazyk. Použijte 'cs-CZ' nebo 'en-US'.")

SUBJECTS_BASE = "subjects"
SUBJECTS_DIR_CS = f"{DATA_DIR_CS}/{SUBJECTS_BASE}"
SUBJECTS_DIR_EN = f"{DATA_DIR_EN}/{SUBJECTS_BASE}"

def get_subjects_dir(language=LANGUAGES[0]):
    if language == LANGUAGES[0]:  # "cs-CZ"
        return SUBJECTS_DIR_CS
    elif language == LANGUAGES[1]:  # "en-US"
        return SUBJECTS_DIR_EN
    else:
        raise ValueError("Neznámý jazyk. Použijte 'cs-CZ' nebo 'en-US'.")

STUDY_PLANS_DIR = f"{DATA_DIR}/raw_study_plans"
STUDY_PLANS_OUTPUT_CS = f"{STUDY_PLANS_DIR}/plans_cs.json"
STUDY_PLANS_OUTPUT_EN = f"{STUDY_PLANS_DIR}/plans_en.json"

def get_study_plans_output(language=LANGUAGES[0]):
    if language == LANGUAGES[0]:  # "cs-CZ"
        return STUDY_PLANS_OUTPUT_CS
    elif language == LANGUAGES[1]:  # "en-US"
        return STUDY_PLANS_OUTPUT_EN
    else:
        raise ValueError("Neznámý jazyk. Použijte 'cs-CZ' nebo 'en-US'.")

STUDY_PLANS_PROGRESS_CS = f"{STUDY_PLANS_DIR}/progress_cs.json"
STUDY_PLANS_PROGRESS_EN = f"{STUDY_PLANS_DIR}/progress_en.json"

def get_study_plans_progress(language=LANGUAGES[0]):
    if language == LANGUAGES[0]:  # "cs-CZ"
        return STUDY_PLANS_PROGRESS_CS
    elif language == LANGUAGES[1]:  # "en-US"
        return STUDY_PLANS_PROGRESS_EN
    else:
        raise ValueError("Neznámý jazyk. Použijte 'cs-CZ' nebo 'en-US'.")
    
STUDY_PROGRAMMES_BASE = "study_programmes"
STUDY_PROGRAMMES_OUTPUT_CS = f"{DATA_DIR_CS}/{STUDY_PROGRAMMES_BASE}/programmes.json"
STUDY_PROGRAMMES_OUTPUT_EN = f"{DATA_DIR_EN}/{STUDY_PROGRAMMES_BASE}/programmes.json"

def get_study_programmes_output(language=LANGUAGES[0]):
    if language == LANGUAGES[0]:  # "cs-CZ"
        return STUDY_PROGRAMMES_OUTPUT_CS
    elif language == LANGUAGES[1]:  # "en-US"
        return STUDY_PROGRAMMES_OUTPUT_EN
    else:
        raise ValueError("Neznámý jazyk. Použijte 'cs-CZ' nebo 'en-US'.")
