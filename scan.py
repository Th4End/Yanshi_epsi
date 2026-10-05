from yanshee import Yanshee
import requests

robot = Yanshee("10.0.3.234")
tests = ["fr", "fr-FR", "fr_FR", "french", "fra"]

for lang in tests:
    try:
        print(f"Test de la langue : {lang}...")
        robot.set_language(lang)
        print(f"✅ SUCCÈS : {lang} est accepté !")
        break # On s'arrête dès qu'on en trouve une qui marche
    except requests.exceptions.HTTPError:
        print(f"❌ ÉCHEC : {lang} n'est pas supporté (400).")