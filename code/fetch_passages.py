"""Download the public test passages used in KarmaQuiz experiments.

Each passage is the plain-text introduction of an English Wikipedia article
(licence: CC BY-SA 4.0). The exact revision ID is saved so the input can be
reproduced. Run once: python code/fetch_passages.py
"""
import json
import pathlib
import urllib.parse
import urllib.request

OUT = pathlib.Path(__file__).resolve().parent.parent / "test-data" / "passages"

ARTICLES = {
    "P1_rti": ("Right_to_Information_Act,_2005", "Domain: Right to Information"),
    "P2_gem": ("Government_e_Marketplace", "Functional: Public Procurement"),
    "P3_cvc": ("Central_Vigilance_Commission", "Functional: Vigilance and Ethics"),
    "P4_sbm": ("Swachh_Bharat_Mission", "Domain: Sanitation Programmes"),
    "P5_digital_india": ("Digital_India", "Domain: e-Governance"),
    # Hindi article, used for the language edge case
    "P6_rti_hindi": ("सूचना_का_अधिकार", "Domain: Right to Information", "hi"),
}


def fetch(title, lang="en"):
    q = urllib.parse.urlencode({
        "action": "query", "prop": "extracts|revisions", "rvprop": "ids",
        "explaintext": 1, "exintro": 1, "redirects": 1, "format": "json", "titles": title,
    })
    req = urllib.request.Request(
        f"https://{lang}.wikipedia.org/w/api.php?" + q,
        headers={"User-Agent": "KarmaQuiz-course-project/0.1"},
    )
    page = list(json.load(urllib.request.urlopen(req))["query"]["pages"].values())[0]
    return page["extract"].strip(), page["revisions"][0]["revid"]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for pid, spec in ARTICLES.items():
        title, competency = spec[0], spec[1]
        lang = spec[2] if len(spec) > 2 else "en"
        text, revid = fetch(title, lang)
        # keep the first ~1800 characters, cut at a sentence end
        if len(text) > 1800:
            cut = text[:1800].rfind(". ")
            text = text[: cut + 1]
        meta = {
            "id": pid,
            "title": title.replace("_", " "),
            "competency": competency,
            "source": f"https://{lang}.wikipedia.org/w/index.php?oldid={revid}",
            "licence": "CC BY-SA 4.0 (Wikipedia)",
            "language": lang,
            "chars": len(text),
            "text": text,
        }
        (OUT / f"{pid}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        print(pid, revid, len(text))


if __name__ == "__main__":
    main()
