"""
Résumé d'une retranscription de live TikTok via un LLM local (Ollama) — gratuit, aucune clé API.

Prérequis :
    1. Installer Ollama : https://ollama.com/download
    2. Télécharger un modèle :  ollama pull mistral
    3. pip install requests

Utilisation :
    python resume_live_ollama.py transcript.txt
"""

import sys
import re
import os
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "mistral"  # change en "llama3.1" si tu as téléchargé ce modèle à la place

CHUNK_SIZE = 8_000  # caractères par bloc (les modèles locaux ont un contexte plus limité)


def nettoyer_transcription(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        raw = f.read()

    lignes = []
    for ligne in raw.splitlines():
        ligne = re.sub(r"^\[\d{1,2}:\d{2}:\d{2}\]\s*", "", ligne).strip()
        if ligne:
            lignes.append(ligne)

    return " ".join(lignes)


def chunk_text(text: str, chunk_size: int) -> list[str]:
    mots = text.split(" ")
    chunks = []
    current = []
    current_len = 0

    for mot in mots:
        if current_len + len(mot) > chunk_size and current:
            chunks.append(" ".join(current))
            current = []
            current_len = 0
        current.append(mot)
        current_len += len(mot) + 1

    if current:
        chunks.append(" ".join(current))

    return chunks


def ask_ollama(prompt: str) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={"model": MODEL, "prompt": prompt, "stream": False},
        timeout=300,
    )
    response.raise_for_status()
    return response.json()["response"].strip()


def resume_chunk(chunk: str, i: int, total: int) -> str:
    contexte = f" (partie {i}/{total})" if total > 1 else ""
    prompt = f"""Voici un extrait de la retranscription orale d'un live TikTok{contexte}.
Le texte est du langage parlé, familier, avec des répétitions et parfois des erreurs de transcription.

Fais-en un résumé COURT et INFORMEL, comme si tu racontais à un pote ce qui s'est dit, dans ce style :
"Ils ont parlé de X, puis la discussion a dévié sur Y, ensuite il y a eu Z."

Ne cite pas de phrases exactes, reformule avec tes propres mots. Reste factuel sur ce qui a été dit, pas de jugement.

Transcription :
{chunk}

Résumé informel :"""
    return ask_ollama(prompt)


def resume_final(resumes_partiels: list[str]) -> str:
    combined = "\n\n".join(resumes_partiels)
    prompt = f"""Voici plusieurs résumés partiels d'un même live TikTok, dans l'ordre chronologique.
Fusionne-les en UN SEUL résumé global, fluide et informel, du style :
"Ils ont commencé par parler de X, puis ça a dévié sur Y, avant de finir sur Z."

Résumés partiels :
{combined}

Résumé global informel :"""
    return ask_ollama(prompt)


def main():
    if len(sys.argv) < 2:
        print("Usage : python resume_live_ollama.py <fichier_transcription.txt>")
        sys.exit(1)

    path = sys.argv[1]
    if not os.path.exists(path):
        print(f"Fichier introuvable : {path}")
        sys.exit(1)

    print("Nettoyage de la transcription...")
    texte = nettoyer_transcription(path)
    print(f"{len(texte)} caractères après nettoyage")

    chunks = chunk_text(texte, CHUNK_SIZE)
    print(f"{len(chunks)} bloc(s) à traiter")

    resumes = []
    for i, chunk in enumerate(chunks, start=1):
        print(f"Résumé du bloc {i}/{len(chunks)}...")
        try:
            resumes.append(resume_chunk(chunk, i, len(chunks)))
        except requests.exceptions.ConnectionError:
            print("\nErreur : impossible de contacter Ollama.")
            print("Vérifie qu'Ollama tourne bien (lance 'ollama serve' ou l'appli Ollama).")
            sys.exit(1)

    if len(resumes) > 1:
        print("Fusion des résumés...")
        final = resume_final(resumes)
    else:
        final = resumes[0]

    print("\n" + "=" * 60)
    print("RÉSUMÉ")
    print("=" * 60 + "\n")
    print(final)

    output_path = os.path.splitext(path)[0] + "_resume.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final)
    print(f"\nSauvegardé dans : {output_path}")


if __name__ == "__main__":
    print(main("./resume/mon.copain45/25092026_2040/retranscription.txt"))