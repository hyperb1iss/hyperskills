"""Address normalization so equivalent spellings share a cache key."""
import re

ABBREVIATIONS = {
    "street": "st",
    "avenue": "ave",
    "road": "rd",
    "boulevard": "blvd",
    "north": "n",
    "south": "s",
    "east": "e",
    "west": "w",
}
UNIT = re.compile(r"[\s,]+(?:(?:apt|apartment|unit|suite)\b\.?|#)\s*\w*\d\w*[\s,.]*$")


def normalize(address):
    text = UNIT.sub("", address.lower())
    words = re.sub(r"[^\w\s]", " ", text).split()
    return " ".join(ABBREVIATIONS.get(word, word) for word in words)
