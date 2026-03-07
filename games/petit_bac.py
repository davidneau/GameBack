import json

celebrities = [x.casefold() for x in json.load(open("./data/celebrities.json", "r", encoding="utf8"))]
legumesfruits = [x.casefold() for x in json.load(open("./data/legumesfruits.json", "r", encoding="utf8"))]
metiers = [x.casefold() for x in json.load(open("./data/metiers.json", "r", encoding="utf8"))]
paysvilles = [x.casefold() for x in json.load(open("./data/paysvilles.json", "r", encoding="utf8"))]
prenomsF = [x.casefold() for x in json.load(open("./data/prenomsF.json", "r", encoding="utf8"))]
prenomsM = [x.casefold() for x in json.load(open("./data/prenomsM.json", "r", encoding="utf8"))]

def map_cat(nomCat):
    if nomCat == "celebrities":
        return celebrities
    if nomCat == "legumesfruits":
        return legumesfruits
    if nomCat == "metiers":
        return metiers
    if nomCat == "prenomsF":
        return prenomsF
    if nomCat == "prenomsM":
        return prenomsM
    if nomCat == "paysvilles":
        return paysvilles
    

def belongTo(nom, cat):
    listCat = map_cat(cat)
    return nom.casefold() in listCat

#belongTo("ivana", "prenomsF")