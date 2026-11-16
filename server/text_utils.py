import re 
from string import capwords

with open("abbreviations.txt", encoding="utf-8") as f:
    ABBREV = dict(line.strip().split("=", 1) for line in f if "=" in line)

def clean_description(description: str):
    clean_str = re.sub(r"^(?:E\s*\d+|\d{4,})\s*", "", description)
    desc = clean_str.split()
    desc = " ".join(ABBREV.get(w.upper(), w) for w in desc)
    desc = capwords(desc)
    return desc

# TESTING 
if __name__ == "__main__":
    print(clean_description("E4860002 KS BF HAM EGGS"))
