import json
import time
import requests

BASE_URL = "https://www.dnd5eapi.co/api/2014"
OUTPUT_FILE = "spells_fr.json"

session = requests.Session()
session.headers.update({
    "Accept": "application/json",
    "User-Agent": "JDR-Site/1.0"
})


def get_json(url, params=None):
    response = session.get(url, params=params, timeout=15)
    response.raise_for_status()
    return response.json()


def get_all_spells():
    """
    Récupère la liste de tous les sorts.
    """
    print("Récupération de la liste des sorts...")

    data = get_json(f"{BASE_URL}/spells")

    return data["results"]


def get_spell_details(spell_index):
    """
    Récupère les détails d'un sort en français.
    """
    url = f"{BASE_URL}/spells/{spell_index}"

    # lang=fr-FR demande la traduction française
    return get_json(url, params={"lang": "fr-FR"})


def main():
    spells = get_all_spells()

    print(f"{len(spells)} sorts trouvés.\n")

    all_spells = []

    for i, spell in enumerate(spells, start=1):
        index = spell["index"]

        print(f"[{i}/{len(spells)}] {spell['name']}...", end=" ")

        try:
            details = get_spell_details(index)

            all_spells.append(details)

            print("OK")

        except requests.RequestException as e:
            print(f"ERREUR : {e}")

        # Petite pause pour éviter d'envoyer trop de requêtes
        time.sleep(0.05)

    print("\nSauvegarde...")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(
            all_spells,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(f"\nTerminé !")
    print(f"{len(all_spells)} sorts sauvegardés dans {OUTPUT_FILE}")


if __name__ == "__main__":
    main()