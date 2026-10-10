import ollama

MODELE = "qwen2.5:7b"

def demander(prompt):
    r = ollama.chat(model=MODELE, messages=[{"role": "user", "content": prompt}])
    return r["message"]["content"]

def decouper(texte, taille=6000):
    mots = texte.split()
    return [" ".join(mots[i:i+taille//6*1]) for i in range(0, len(mots), taille//6)]

def resumer_live(chemin):
    texte = open(chemin, encoding="utf-8").read()
    blocs = decouper(texte)

    partiels = []
    for i, bloc in enumerate(blocs, 1):
        print(f"Bloc {i}/{len(blocs)}...")
        partiels.append(demander(
            "Voici un extrait de la transcription d'un live TikTok. "
            "Résume en français les points clés, sujets abordés et moments importants :\n\n" + bloc
        ))

    return demander(
        "Voici des résumés successifs d'un live TikTok. Fais-en un résumé final "
        "structuré en français (thèmes principaux, points importants, conclusion) :\n\n"
        + "\n\n".join(partiels)
    )

print(resumer_live("./resume/madamemeletout/09102026_2121/retranscription.txt"))