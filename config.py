BASE_URL = "https://www.vut.cz"
PROGRAMS_URL_CS = "https://www.vut.cz/studenti/programy"
PROGRAMS_URL_EN = "https://www.vut.cz/en/students/programmes"

DATA_DIR = "data"

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

FACULTY_BASE = f"{DATA_DIR}/fakulty_"
FACULTY_CS = f"{FACULTY_BASE}cs.json"
FACULTY_EN = f"{FACULTY_BASE}en.json"

def get_faculty_file(language="cs"):
    if language == "cs":
        return FACULTY_CS
    elif language == "en":
        return FACULTY_EN
    else:
        raise ValueError("Neznámý jazyk. Použijte 'cs' nebo 'en'.")

SUBJECTS_DIR = f"{DATA_DIR}/subjects"

STUDY_PLANS_DIR = f"{DATA_DIR}/study_plans"
STUDY_PLANS_OUTPUT = f"{STUDY_PLANS_DIR}/studijni_plany.json"
STUDY_PLANS_PROGRESS = f"{STUDY_PLANS_DIR}/progress.json"
STUDY_PLANS_QUEUE = f"{STUDY_PLANS_DIR}/queue.json"
