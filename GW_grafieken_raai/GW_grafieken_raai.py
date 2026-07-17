"""
GW-Grafieken_Raai voor Grondwatergrafieken

Deze tool maakt een interactieve kaart waar gebruikers:
1. Een modellaag selecteren (1-24)
2. Een raai (lijn) tekenen op de kaart
3. Een bufferzone invoeren (in meters)
4. Automatisch grafieken zien van peilbuizen binnen de bufferzone

Grafieken worden weergegeven in zijpanelen; 
    - Het linkerzijpaneel bevat de grafieken het dichtst bij de raai en 
    - Het rechterzijpaneel bevat de grafieken verder van de raai.

Auteur: Didier Haagmans, Haskoning
Datum: 2026-06-25
"""

from pathlib import Path
from typing import Optional, Dict, List
import json
import base64

import folium
from folium.plugins import Draw
import geopandas as gpd

# RD coördinaten systeem voor brondata
SOURCE_CRS = "EPSG:28992"
# WGS84 coördinaten systeem voor weergave op de kaart
MAP_CRS = "EPSG:4326"


# ==========================
# HASKONING BRANDING
# Kleuren en helpers overgenomen uit haskoning_branding_1.md (Green theme).
# Pas hier de kleuren aan om de huisstijl van de tool te wijzigen.
# ==========================

HASKONING_COLORS = {
    "primary": "#002E4F",        # Ocean Blue - navigatie, primaire tekst
    "background": "#FAF2E3",     # Eggshell Cream - pagina-achtergrond
    "white": "#FFFFFF",          # Content blocks / secundaire balk
    "input_bg": "#F6F6F6",       # Tekstvelden / dropdowns
    "disabled_bg": "#EEEEEE",
    "disabled_text": "#B4B4B4",
}

THEME_GREEN = {
    "secondary": "#5CBD7D",   # Earth Green - primaire knoppen
    "highlight": "#BDDECC",   # Moss Green - hover / selectie
}

ALARM_COLORS = {
    "critical": "#F74646",
    "high": "#FCB073",
    "medium": "#FFD68A",
    "low": "#009EAB",
    "low_optional": "#BFE1E9",
    "positive": "#5CBD7D",
}

TOOL_TITLE = "GW-Grafieken Raai Tool"
TOOL_PAYOFF = "Enhancing Society Together"
TOPBAR_HEIGHT_PX = 54


# Haskoning-logo (img/haskoning-logo.svg), inline als base64 opgenomen zodat de tool niet
# afhankelijk is van een los logo-bestand op schijf.
_HASKONING_LOGO_SVG_B64 = (
    "PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPHN2ZyBpZD0iTGF5ZXJfMSIgZGF0YS1uYW1lPSJMYXll"
    "ciAxIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHhtbG5zOnhsaW5rPSJodHRwOi8vd3d3LnczLm9yZy8x"
    "OTk5L3hsaW5rIiB2aWV3Qm94PSIwIDAgODI4LjMyIDMwMyI+CiAgPGRlZnM+CiAgICA8c3R5bGU+CiAgICAgIC5jbHMtMSB7"
    "CiAgICAgICAgZmlsbDogdXJsKCNyYWRpYWwtZ3JhZGllbnQtMyk7CiAgICAgIH0KCiAgICAgIC5jbHMtMiB7CiAgICAgICAg"
    "ZmlsbDogdXJsKCNyYWRpYWwtZ3JhZGllbnQtMik7CiAgICAgIH0KCiAgICAgIC5jbHMtMyB7CiAgICAgICAgZmlsbDogIzAw"
    "OWVhYjsKICAgICAgfQoKICAgICAgLmNscy00IHsKICAgICAgICBmaWxsOiB1cmwoI3JhZGlhbC1ncmFkaWVudCk7CiAgICAg"
    "IH0KCiAgICAgIC5jbHMtNSB7CiAgICAgICAgZmlsbDogIzAwMmU0ZjsKICAgICAgfQogICAgPC9zdHlsZT4KICAgIDxyYWRp"
    "YWxHcmFkaWVudCBpZD0icmFkaWFsLWdyYWRpZW50IiBjeD0iODc0LjU0IiBjeT0iLTIxMi45MiIgZng9Ijg3NC41NCIgZnk9"
    "Ii0yMTIuOTIiIHI9IjM2LjUyIiBncmFkaWVudFRyYW5zZm9ybT0idHJhbnNsYXRlKC0zNjU4LjU3IDExMDQuNTQpIHNjYWxl"
    "KDQuMzcpIiBncmFkaWVudFVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+CiAgICAgIDxzdG9wIG9mZnNldD0iLjI5IiBzdG9wLWNv"
    "bG9yPSIjYmZkNzMwIi8+CiAgICAgIDxzdG9wIG9mZnNldD0iMSIgc3RvcC1jb2xvcj0iIzAwOTFhYyIvPgogICAgPC9yYWRp"
    "YWxHcmFkaWVudD4KICAgIDxyYWRpYWxHcmFkaWVudCBpZD0icmFkaWFsLWdyYWRpZW50LTIiIGN4PSI4NzQuNTQiIGN5PSIt"
    "MjEyLjkyIiBmeD0iODc0LjU0IiBmeT0iLTIxMi45MiIgcj0iMzYuNTIiIHhsaW5rOmhyZWY9IiNyYWRpYWwtZ3JhZGllbnQi"
    "Lz4KICAgIDxyYWRpYWxHcmFkaWVudCBpZD0icmFkaWFsLWdyYWRpZW50LTMiIGN4PSI4NzQuNTQiIGN5PSItMjEyLjkyIiBm"
    "eD0iODc0LjU0IiBmeT0iLTIxMi45MiIgcj0iMzYuNTIiIHhsaW5rOmhyZWY9IiNyYWRpYWwtZ3JhZGllbnQiLz4KICA8L2Rl"
    "ZnM+CiAgPGc+CiAgICA8Zz4KICAgICAgPHBhdGggY2xhc3M9ImNscy00IiBkPSJNMTM5LjQ2LDE0My4yNWwtMzkuNTQsMzMu"
    "NjYsMTEuMzItNjUuMzYtNTkuMTctNTQuNiw2NS40LDE4Ljg2QzY4LjUsMTkuMTgsMCwzMC44MSwwLDMwLjgxYzAsMCwxNi42"
    "NCw1Ny4zMiw3OS45LDgzLjcyLTIwLjY3LDM2LjE2LTE3LjA1LDczLjUzLTIuMzIsMTEwLjRsNjAuNjYtNTQuNDhjMi42NCwz"
    "LjE3LDcuNCw3Ljg5LDE2LjQ4LDExLjU2LDguNSwzLjQ0LDIwLjMsNS4xMiwzMywuMTdsLTQ4LjI2LTM4LjkyWiIvPgogICAg"
    "ICA8cGF0aCBjbGFzcz0iY2xzLTIiIGQ9Ik0xNTMuMzQsNTguODFsNi45OS01Ni4zOGMtMTUuNzgtNS41OS0zMS4wOS0xLjA2"
    "LTQxLjE4LDkuMDItMTQuMjksMTQuMjYtMTUuODYsMzguOTgsMCw1NC41Nmw3LjEtNDAuOTIsMjMuNTYsNjAuMDEsNDMuMTks"
    "MTIuNDUtMjguODgsMjQuODNjNTYuODgtNS40Nyw3OS45Ni00Ny4wMSw3OS45Ni00Ny4wMWwtOTAuNzQtMTYuNTZaIi8+CiAg"
    "ICA8L2c+CiAgICA8Zz4KICAgICAgPHBhdGggY2xhc3M9ImNscy01IiBkPSJNMjk1LjMxLDEzNi41OHY4OC44NWgtMTcuMzl2"
    "LTM2LjgxaC0zM3YzNi44MWgtMTcuNTJ2LTg4Ljg1aDE3LjUydjM1LjI5aDMzdi0zNS4yOWgxNy4zOVoiLz4KICAgICAgPHBh"
    "dGggY2xhc3M9ImNscy01IiBkPSJNMzc1LjY2LDE2MS45N3Y2My40N2gtMTYuMzd2LTcuNDljLTQuNTcsNS43MS0xMS40Miw5"
    "LjI3LTIwLjY5LDkuMjctMTYuODgsMC0zMC44NS0xNC42LTMwLjg1LTMzLjUxczEzLjk2LTMzLjUxLDMwLjg1LTMzLjUxYzku"
    "MjcsMCwxNi4xMiwzLjU1LDIwLjY5LDkuMjd2LTcuNDloMTYuMzdaTTM1OS4yOCwxOTMuN2MwLTEwLjY2LTcuNDktMTcuOS0x"
    "Ny42NC0xNy45cy0xNy41Miw3LjIzLTE3LjUyLDE3LjksNy40OSwxNy45LDE3LjUyLDE3LjksMTcuNjQtNy4yNCwxNy42NC0x"
    "Ny45WiIvPgogICAgICA8cGF0aCBjbGFzcz0iY2xzLTUiIGQ9Ik00MzcuODYsMjA2LjljMCwxMy43MS0xMS45MywyMC4zMS0y"
    "NS41MSwyMC4zMS0xMi42OSwwLTIyLjA5LTUuMzMtMjYuNjYtMTUuMTFsMTQuMjItOGMxLjc4LDUuMiw2LjA5LDguMjUsMTIu"
    "NDQsOC4yNSw1LjIsMCw4Ljc2LTEuNzgsOC43Ni01LjQ2LDAtOS4yNy0zMi43NS00LjE5LTMyLjc1LTI2LjUzLDAtMTIuOTUs"
    "MTEuMDQtMjAuMTgsMjQuMTItMjAuMTgsMTAuMjgsMCwxOS4xNyw0LjcsMjQuMTIsMTMuNDZsLTEzLjk2LDcuNjJjLTEuOS00"
    "LjA2LTUuNDYtNi40Ny0xMC4xNS02LjQ3LTQuMDYsMC03LjM2LDEuNzgtNy4zNiw1LjIsMCw5LjM5LDMyLjc1LDMuNTUsMzIu"
    "NzUsMjYuOTFaIi8+CiAgICAgIDxwYXRoIGNsYXNzPSJjbHMtNSIgZD0iTTQ4Ny44NywyMjUuNDNsLTIzLjEtMjguODF2Mjgu"
    "ODFoLTE2LjM3di04OC44NWgxNi4zN3Y1My4zMWwyMS44My0yNy45M2gxOS41NWwtMjUuNTEsMzEuMzUsMjYuMjgsMzIuMTFo"
    "LTE5LjA0WiIvPgogICAgICA8cGF0aCBjbGFzcz0iY2xzLTUiIGQ9Ik01MDcuMTcsMTkzLjdjMC0xOC45MSwxNC44NS0zMy41"
    "MSwzMy41MS0zMy41MXMzMy42NCwxNC42LDMzLjY0LDMzLjUxLTE0Ljk4LDMzLjUxLTMzLjY0LDMzLjUxLTMzLjUxLTE0LjYt"
    "MzMuNTEtMzMuNTFaTTU1Ny45NCwxOTMuN2MwLTEwLjI4LTcuNDktMTcuNTItMTcuMjYtMTcuNTJzLTE3LjE0LDcuMjMtMTcu"
    "MTQsMTcuNTIsNy40OSwxNy41MiwxNy4xNCwxNy41MiwxNy4yNi03LjIzLDE3LjI2LTE3LjUyWiIvPgogICAgICA8cGF0aCBj"
    "bGFzcz0iY2xzLTUiIGQ9Ik02NDUuMTUsMTg2LjQ3djM4Ljk3aC0xNi4zOHYtMzYuOTRjMC04LjYzLTUuMi0xMy4wNy0xMi41"
    "Ny0xMy4wNy04LDAtMTMuOTYsNC43LTEzLjk2LDE1Ljc0djM0LjI3aC0xNi4zN3YtNjMuNDdoMTYuMzd2Ny4xMWMzLjgxLTUu"
    "NzEsMTAuNDEtOC44OSwxOC45MS04Ljg5LDEzLjQ2LDAsMjMuOTksOS4zOSwyMy45OSwyNi4yOFoiLz4KICAgICAgPHBhdGgg"
    "Y2xhc3M9ImNscy01IiBkPSJNNjU3LjIxLDE0NC4zMmMwLTUuNDYsNC41Ny0xMC4xNSwxMC4wMy0xMC4xNXMxMC4xNSw0Ljcs"
    "MTAuMTUsMTAuMTUtNC41NywxMC4wMy0xMC4xNSwxMC4wMy0xMC4wMy00LjU3LTEwLjAzLTEwLjAzWk02NTkuMTEsMTYxLjk3"
    "aDE2LjM3djYzLjQ3aC0xNi4zN3YtNjMuNDdaIi8+CiAgICAgIDxwYXRoIGNsYXNzPSJjbHMtNSIgZD0iTTc0OS43NCwxODYu"
    "NDd2MzguOTdoLTE2LjM3di0zNi45NGMwLTguNjMtNS4yLTEzLjA3LTEyLjU3LTEzLjA3LTgsMC0xMy45Niw0LjctMTMuOTYs"
    "MTUuNzR2MzQuMjdoLTE2LjM3di02My40N2gxNi4zN3Y3LjExYzMuODEtNS43MSwxMC40MS04Ljg5LDE4LjkxLTguODksMTMu"
    "NDYsMCwyMy45OSw5LjM5LDIzLjk5LDI2LjI4WiIvPgogICAgICA8cGF0aCBjbGFzcz0iY2xzLTUiIGQ9Ik04MjguMzIsMTYx"
    "Ljk3djYwLjQyYzAsMjAuODItMTYuMzcsMzAuMjEtMzMuMTMsMzAuMjEtMTMuNTgsMC0yNC41LTUuMjEtMzAuMDgtMTUuNDls"
    "MTMuOTYtOGMyLjY3LDQuOTUsNi44NSw4Ljg5LDE2LjYzLDguODksMTAuMjgsMCwxNi42My01LjU5LDE2LjYzLTE1LjYxdi02"
    "Ljg2Yy00LjQ0LDUuOTctMTEuMyw5LjY1LTIwLjMxLDkuNjUtMTguMDIsMC0zMS42MS0xNC42LTMxLjYxLTMyLjVzMTMuNTgt"
    "MzIuNSwzMS42MS0zMi41YzkuMDEsMCwxNS44NywzLjY4LDIwLjMxLDkuNjV2LTcuODdoMTUuOTlaTTgxMi4zMiwxOTIuNjhj"
    "MC0xMC4wMy03LjQ5LTE3LjI2LTE3Ljc3LTE3LjI2cy0xNy43Nyw3LjI0LTE3Ljc3LDE3LjI2LDcuNDksMTcuMzksMTcuNzcs"
    "MTcuMzksMTcuNzctNy4yNCwxNy43Ny0xNy4zOVoiLz4KICAgICAgPGc+CiAgICAgICAgPHBhdGggY2xhc3M9ImNscy0zIiBk"
    "PSJNMjM4LjAyLDI2NS43M2wtMS40OSw4LjQ1aDEyLjk5bC0uODgsNS4wMWgtMTIuOTlsLTEuNTgsOC44MmgxNC40M2wtLjkz"
    "LDUuMTFoLTE5LjczbDUuNzEtMzIuNDloMTkuNDlsLS44OCw1LjExaC0xNC4xNloiLz4KICAgICAgICA8cGF0aCBjbGFzcz0i"
    "Y2xzLTMiIGQ9Ik0yNzUuNzYsMjc4Ljg2bC0yLjUxLDE0LjI1aC01LjAxbDIuNDEtMTMuNzRjLjYtMy41Ny0xLjAyLTUuMzgt"
    "NC4yNy01LjM4cy02LjAzLDEuNzYtNi45Niw2LjA4bC0yLjI3LDEzLjA0aC01LjAxbDQuMDgtMjMuMjFoNS4wMWwtLjUxLDIu"
    "NzhjMi0yLjMyLDQuNzMtMy4zOSw3LjU3LTMuMzksNS4yLDAsOC40OSwzLjU3LDcuNDcsOS41NloiLz4KICAgICAgICA8cGF0"
    "aCBjbGFzcz0iY2xzLTMiIGQ9Ik0zMDIuMTcsMjc4Ljg2bC0yLjUxLDE0LjI1aC01LjAxbDIuNDEtMTMuNzRjLjYtMy41Ny0x"
    "LjAyLTUuMzgtNC4yNy01LjM4cy02LjA4LDEuNzYtNi45Niw2LjIybC0yLjI3LDEyLjloLTUuMDFsNS43MS0zMi40OWg1LjAx"
    "bC0yLjEzLDEyLjA3YzItMi4zMiw0LjczLTMuMzksNy41Ny0zLjM5LDUuMiwwLDguNDksMy41Nyw3LjQ3LDkuNTZaIi8+CiAg"
    "ICAgICAgPHBhdGggY2xhc3M9ImNscy0zIiBkPSJNMzMyLjQ5LDI2OS45bC00LjA4LDIzLjIxaC01LjAxbC40Ni0yLjc0Yy0y"
    "LjA0LDIuMDktNC44NywzLjM0LTguNDksMy4zNC02Ljk2LDAtMTAuNzctNi4xNy05LjU2LTEyLjcyLDEuMjUtNi45MSw2LjY4"
    "LTExLjcsMTMuMTgtMTEuNywzLjU3LDAsNi4zMSwxLjU4LDcuODQsNC4zNmwuNjUtMy43Nmg1LjAxWk0zMjUuMjksMjgyLjM0"
    "bC4yMy0xLjM1Yy40Ni00LjQ2LTIuNTEtNi45MS02LjI2LTYuOTFzLTcuNjEsMi41NS04LjQ1LDcuMjljLS43NCw0LjMyLDEu"
    "ODEsNy41Nyw2LjAzLDcuNTcsMy45NCwwLDcuNDMtMi42NSw4LjQ1LTYuNTlaIi8+CiAgICAgICAgPHBhdGggY2xhc3M9ImNs"
    "cy0zIiBkPSJNMzU3Ljg4LDI3OC44NmwtMi41MSwxNC4yNWgtNS4wMWwyLjQxLTEzLjc0Yy42LTMuNTctMS4wMi01LjM4LTQu"
    "MjctNS4zOHMtNi4wMywxLjc2LTYuOTYsNi4wOGwtMi4yNywxMy4wNGgtNS4wMWw0LjA4LTIzLjIxaDUuMDFsLS41MSwyLjc4"
    "YzItMi4zMiw0LjczLTMuMzksNy41Ny0zLjM5LDUuMiwwLDguNDksMy41Nyw3LjQ3LDkuNTZaIi8+CiAgICAgICAgPHBhdGgg"
    "Y2xhc3M9ImNscy0zIiBkPSJNMzYxLjUxLDI4MWMxLjE2LTYuODIsNi45Ni0xMS43LDEzLjk3LTExLjcsNC43OCwwLDguMjYs"
    "Mi40MSw5LjY1LDYuMDNsLTQuNSwyLjMyYy0uODQtMi4xMy0yLjc4LTMuNDQtNS42Mi0zLjQ0LTQuMTMsMC03Ljc1LDIuOTIt"
    "OC40OSw3LjE1LS43LDQuMTgsMS43Niw3LjQzLDUuOTQsNy40MywyLjc4LDAsNS4yLTEuNDQsNi42NC0zLjYybDQuMDQsMi42"
    "Yy0yLjQxLDMuOS02LjY0LDUuOTQtMTEuMTksNS45NC03LjEsMC0xMS42LTUuNzEtMTAuNDQtMTIuNzJaIi8+CiAgICAgICAg"
    "PHBhdGggY2xhc3M9ImNscy0zIiBkPSJNMzg5Ljc4LDI2OS45aDUuMDFsLTQuMDgsMjMuMjFoLTUuMDFsNC4wOC0yMy4yMVpN"
    "MzkwLjI0LDI2My4yMmMuMjgtMS43MiwxLjktMy4yLDMuNzEtMy4yczMuMDIsMS40NCwyLjY5LDMuMmMtLjI4LDEuNzItMS44"
    "NiwzLjItMy43NiwzLjJzLTIuOTItMS40OS0yLjY0LTMuMloiLz4KICAgICAgICA8cGF0aCBjbGFzcz0iY2xzLTMiIGQ9Ik00"
    "MjAuMTMsMjc4Ljg2bC0yLjUxLDE0LjI1aC01LjAxbDIuNDEtMTMuNzRjLjYtMy41Ny0xLjAyLTUuMzgtNC4yNy01LjM4cy02"
    "LjAzLDEuNzYtNi45Niw2LjA4bC0yLjI3LDEzLjA0aC01LjAxbDQuMDgtMjMuMjFoNS4wMWwtLjUxLDIuNzhjMi0yLjMyLDQu"
    "NzMtMy4zOSw3LjU3LTMuMzksNS4yLDAsOC40OSwzLjU3LDcuNDcsOS41NloiLz4KICAgICAgICA8cGF0aCBjbGFzcz0iY2xz"
    "LTMiIGQ9Ik00NTAuNDksMjY5LjlsLTMuOSwyMi4xNGMtMS4zNSw3LjctNi44NywxMC45NS0xMy4zNywxMC45NS01LjAxLDAt"
    "OC44Ni0xLjk1LTEwLjU0LTUuNjJsNC41LTIuMzJjLjg0LDEuOSwyLjY5LDMuMzksNi4zNiwzLjM5LDQuNSwwLDcuMzgtMi4y"
    "Nyw4LjEyLTYuNDFsLjQyLTIuNDFjLTIuMDQsMi4yMy00Ljg3LDMuNjItOC40LDMuNjItNy4yOSwwLTEwLjk1LTUuODktOS44"
    "OC0xMi40OCwxLjA3LTYuNTUsNi41LTExLjQ2LDEyLjk5LTExLjQ2LDMuNjcsMCw2LjU5LDEuNjIsOC4wOCw0LjVsLjctMy45"
    "aDQuOTJaTTQ0My41MywyODEuNDJjLjg4LTQuNjktMi4zMi03LjM4LTYuMjItNy4zOHMtNy44LDIuNjktOC40OSw3LjFjLS43"
    "LDQuMjcsMS44Niw3LjM4LDYuMTcsNy4zOHM3Ljc1LTIuODMsOC41NC03LjFaIi8+CiAgICAgICAgPHBhdGggY2xhc3M9ImNs"
    "cy0zIiBkPSJNNDYzLjYzLDI4NS43M2w0LjgzLTIuNTFjLjcsMy4xNiwyLjk3LDUuMzQsNy4zOCw1LjM0LDMuODUsMCw2LjE3"
    "LTEuNjcsNi42OC00LjA4LjctMy4xMS0yLjQ2LTQuMjctNi4yMi01LjUyLTQuODMtMS42Mi05LjU2LTQuMTMtOC40LTEwLjM1"
    "LDEuMDctNS45OSw2LjUtOC41OSwxMS41Ni04LjU5LDUuNDgsMCw5LjEsMi45MiwxMC41OCw3LjFsLTQuNjksMi40NmMtLjk4"
    "LTIuNTUtMi43NC00LjQxLTYuMzEtNC40MS0yLjg4LDAtNS4yNCwxLjM5LTUuNzUsMy44MS0uNjUsMy4wNiwyLjMyLDQuMjcs"
    "Ni4wMyw1LjU3LDQuMzIsMS41Myw5LjkzLDMuNjIsOC42MywxMC40NC0xLjA3LDUuODUtNi4xNyw4LjczLTEyLjQ4LDguNzNz"
    "LTEwLjYzLTMuMTEtMTEuODQtNy45OFoiLz4KICAgICAgICA8cGF0aCBjbGFzcz0iY2xzLTMiIGQ9Ik00OTEuOSwyODAuOWMx"
    "LjMtNi45Niw3LjI5LTExLjYsMTQuMTYtMTEuNnMxMS4zNyw1LjY2LDEwLjE2LDEyLjY3Yy0xLjI1LDcuMDUtNy4zMywxMS43"
    "NC0xMy44MywxMS43NC03LjMzLDAtMTEuODQtNS43MS0xMC40OS0xMi44MVpNNTExLjI2LDI4MS40MmMuODMtNC42LTIuMTQt"
    "Ny4yNC01Ljg5LTcuMjRzLTcuNjEsMi42NS04LjQ1LDcuMzNjLS43OSw0LjY5LDIuMDQsNy4zMyw1Ljg1LDcuMzNzNy42Ni0y"
    "LjY1LDguNDktNy40M1oiLz4KICAgICAgICA8cGF0aCBjbGFzcz0iY2xzLTMiIGQ9Ik01MTkuNjYsMjgxYzEuMTYtNi44Miw2"
    "Ljk2LTExLjcsMTMuOTctMTEuNyw0Ljc4LDAsOC4yNiwyLjQxLDkuNjUsNi4wM2wtNC41LDIuMzJjLS44NC0yLjEzLTIuNzgt"
    "My40NC01LjYyLTMuNDQtNC4xMywwLTcuNzUsMi45Mi04LjQ5LDcuMTUtLjcsNC4xOCwxLjc2LDcuNDMsNS45NCw3LjQzLDIu"
    "NzgsMCw1LjItMS40NCw2LjY0LTMuNjJsNC4wNCwyLjZjLTIuNDEsMy45LTYuNjQsNS45NC0xMS4xOSw1Ljk0LTcuMSwwLTEx"
    "LjYtNS43MS0xMC40NC0xMi43MloiLz4KICAgICAgICA8cGF0aCBjbGFzcz0iY2xzLTMiIGQ9Ik01NDcuOTMsMjY5LjloNS4w"
    "MWwtNC4wOCwyMy4yMWgtNS4wMWw0LjA4LTIzLjIxWk01NDguNCwyNjMuMjJjLjI4LTEuNzIsMS45LTMuMiwzLjcxLTMuMnMz"
    "LjAyLDEuNDQsMi42OSwzLjJjLS4yOCwxLjcyLTEuODYsMy4yLTMuNzYsMy4ycy0yLjkyLTEuNDktMi42NC0zLjJaIi8+CiAg"
    "ICAgICAgPHBhdGggY2xhc3M9ImNscy0zIiBkPSJNNTc5LjM2LDI4MS41NmMtLjA5LjM3LS4zMywxLjM5LS41NiwyLjA5aC0x"
    "OC40N2MuMDksMy43MSwyLjc0LDUuNDgsNi4yNyw1LjQ4LDIuNzQsMCw1LjAxLTEuMDcsNi41NC0yLjkybDMuNjcsMi43OWMt"
    "Mi41MSwzLjExLTYuMzYsNC43My0xMC42Myw0LjczLTcuNjEsMC0xMS44NC01LjY2LTEwLjY3LTEyLjY3LDEuMTYtNi43OCw2"
    "Ljk2LTExLjc0LDEzLjgzLTExLjc0czExLjMyLDUuNDgsMTAuMDMsMTIuMjVaTTU3NC42MiwyNzkuNTFjLjA1LTMuOTktMi40"
    "MS01LjY2LTUuNjItNS42Ni0zLjY3LDAtNi42NCwyLjEzLTcuOTgsNS42NmgxMy42WiIvPgogICAgICAgIDxwYXRoIGNsYXNz"
    "PSJjbHMtMyIgZD0iTTU4OS40OCwyODUuODdjLS41MSwzLjAyLDEuNTgsMi45Nyw1LjI5LDIuNzRsLS43OSw0LjVjLTcuMjQu"
    "OTMtMTAuNTgtMS4yMS05LjUxLTcuMjRsMS45NS0xMS4xNGgtNC4yN2wuODgtNC44M2g0LjI3bC44OC01LjAxLDUuMjQtMS40"
    "OS0xLjE2LDYuNWg1LjhsLS44OCw0LjgzaC01Ljc1bC0xLjk1LDExLjE0WiIvPgogICAgICAgIDxwYXRoIGNsYXNzPSJjbHMt"
    "MyIgZD0iTTYyNC4wNiwyNjkuOWwtMTMuMTMsMjMuOTVjLTMuNDgsNi40NS03Ljc1LDguODYtMTIuODEsOC41NGwuODQtNC42"
    "OWMzLjE2LjE5LDQuOTctMS4zLDYuNzMtNC40NmwuNDItLjY1LTUuNzEtMjIuN2g1LjE1bDMuOTksMTcuMDMsOC45Ni0xNy4w"
    "M2g1LjU3WiIvPgogICAgICAgIDxwYXRoIGNsYXNzPSJjbHMtMyIgZD0iTTY2MS4wMSwyNjUuNzNoLTkuMTRsLTQuODMsMjcu"
    "MzhoLTUuMzRsNC44My0yNy4zOGgtOS4xOWwuODgtNS4xMWgyMy42N2wtLjg4LDUuMTFaIi8+CiAgICAgICAgPHBhdGggY2xh"
    "c3M9ImNscy0zIiBkPSJNNjU2LjUxLDI4MC45YzEuMy02Ljk2LDcuMjktMTEuNiwxNC4xNi0xMS42czExLjM3LDUuNjYsMTAu"
    "MTYsMTIuNjdjLTEuMjUsNy4wNS03LjMzLDExLjc0LTEzLjgzLDExLjc0LTcuMzMsMC0xMS44NC01LjcxLTEwLjQ5LTEyLjgx"
    "Wk02NzUuODcsMjgxLjQyYy44My00LjYtMi4xNC03LjI0LTUuOS03LjI0cy03LjYxLDIuNjUtOC40NSw3LjMzYy0uNzksNC42"
    "OSwyLjA0LDcuMzMsNS44NSw3LjMzczcuNjYtMi42NSw4LjQ5LTcuNDNaIi8+CiAgICAgICAgPHBhdGggY2xhc3M9ImNscy0z"
    "IiBkPSJNNzExLjAxLDI2OS45bC0zLjksMjIuMTRjLTEuMzUsNy43LTYuODcsMTAuOTUtMTMuMzcsMTAuOTUtNS4wMSwwLTgu"
    "ODYtMS45NS0xMC41NC01LjYybDQuNS0yLjMyYy44NCwxLjksMi42OSwzLjM5LDYuMzYsMy4zOSw0LjUsMCw3LjM4LTIuMjcs"
    "OC4xMi02LjQxbC40Mi0yLjQxYy0yLjA0LDIuMjMtNC44NywzLjYyLTguNCwzLjYyLTcuMjksMC0xMC45NS01Ljg5LTkuODgt"
    "MTIuNDgsMS4wNy02LjU1LDYuNS0xMS40NiwxMi45OS0xMS40NiwzLjY3LDAsNi41OSwxLjYyLDguMDgsNC41bC43LTMuOWg0"
    "LjkyWk03MDQuMDQsMjgxLjQyYy44OC00LjY5LTIuMzItNy4zOC02LjIyLTcuMzhzLTcuOCwyLjY5LTguNDksNy4xYy0uNyw0"
    "LjI3LDEuODYsNy4zOCw2LjE3LDcuMzhzNy43NS0yLjgzLDguNTQtNy4xWiIvPgogICAgICAgIDxwYXRoIGNsYXNzPSJjbHMt"
    "MyIgZD0iTTczNy40NywyODEuNTZjLS4wOS4zNy0uMzMsMS4zOS0uNTYsMi4wOWgtMTguNDdjLjA5LDMuNzEsMi43NCw1LjQ4"
    "LDYuMjcsNS40OCwyLjc0LDAsNS4wMS0xLjA3LDYuNTQtMi45MmwzLjY3LDIuNzljLTIuNTEsMy4xMS02LjM2LDQuNzMtMTAu"
    "NjMsNC43My03LjYxLDAtMTEuODQtNS42Ni0xMC42Ny0xMi42NywxLjE2LTYuNzgsNi45Ni0xMS43NCwxMy44My0xMS43NHMx"
    "MS4zMiw1LjQ4LDEwLjAzLDEyLjI1Wk03MzIuNzMsMjc5LjUxYy4wNS0zLjk5LTIuNDEtNS42Ni01LjYyLTUuNjYtMy42Nyww"
    "LTYuNjQsMi4xMy03Ljk4LDUuNjZoMTMuNloiLz4KICAgICAgICA8cGF0aCBjbGFzcz0iY2xzLTMiIGQ9Ik03NDcuNTksMjg1"
    "Ljg3Yy0uNTEsMy4wMiwxLjU4LDIuOTcsNS4yOSwyLjc0bC0uNzksNC41Yy03LjI0LjkzLTEwLjU4LTEuMjEtOS41MS03LjI0"
    "bDEuOTUtMTEuMTRoLTQuMjdsLjg4LTQuODNoNC4yN2wuODgtNS4wMSw1LjI0LTEuNDktMS4xNiw2LjVoNS44bC0uODgsNC44"
    "M2gtNS43NWwtMS45NSwxMS4xNFoiLz4KICAgICAgICA8cGF0aCBjbGFzcz0iY2xzLTMiIGQ9Ik03ODAuMjcsMjc4Ljg2bC0y"
    "LjUxLDE0LjI1aC01LjAxbDIuNDEtMTMuNzRjLjYtMy41Ny0xLjAyLTUuMzgtNC4yNy01LjM4cy02LjA4LDEuNzYtNi45Niw2"
    "LjIybC0yLjI3LDEyLjloLTUuMDFsNS43MS0zMi40OWg1LjAxbC0yLjEzLDEyLjA3YzItMi4zMiw0LjczLTMuMzksNy41Ny0z"
    "LjM5LDUuMiwwLDguNDksMy41Nyw3LjQ3LDkuNTZaIi8+CiAgICAgICAgPHBhdGggY2xhc3M9ImNscy0zIiBkPSJNODA3Ljc1"
    "LDI4MS41NmMtLjA5LjM3LS4zMywxLjM5LS41NiwyLjA5aC0xOC40N2MuMDksMy43MSwyLjc0LDUuNDgsNi4yNyw1LjQ4LDIu"
    "NzQsMCw1LjAxLTEuMDcsNi41NC0yLjkybDMuNjcsMi43OWMtMi41MSwzLjExLTYuMzYsNC43My0xMC42Myw0LjczLTcuNjEs"
    "MC0xMS44NC01LjY2LTEwLjY3LTEyLjY3LDEuMTYtNi43OCw2Ljk2LTExLjc0LDEzLjgzLTExLjc0czExLjMyLDUuNDgsMTAu"
    "MDMsMTIuMjVaTTgwMy4wMiwyNzkuNTFjLjA1LTMuOTktMi40MS01LjY2LTUuNjItNS42Ni0zLjY3LDAtNi42NCwyLjEzLTcu"
    "OTgsNS42NmgxMy42WiIvPgogICAgICAgIDxwYXRoIGNsYXNzPSJjbHMtMyIgZD0iTTgyNi4zMiwyNjkuNDlsLS45OCw1LjQz"
    "Yy0zLjA2LS4yMy03LjA1LDEuMTEtOC4xNyw1Ljg5bC0yLjE4LDEyLjNoLTUuMDFsNC4wOC0yMy4yMWg1LjAxbC0uNiwzLjQ4"
    "YzItMi45Miw0Ljg3LTMuOTksNy44NC0zLjlaIi8+CiAgICAgIDwvZz4KICAgIDwvZz4KICA8L2c+CiAgPGc+CiAgICA8Zz4K"
    "ICAgICAgPHBhdGggY2xhc3M9ImNscy00IiBkPSJNMTM5LjQ2LDE0My4yNWwtMzkuNTQsMzMuNjYsMTEuMzItNjUuMzYtNTku"
    "MTctNTQuNiw2NS40LDE4Ljg2QzY4LjUsMTkuMTgsMCwzMC44MSwwLDMwLjgxYzAsMCwxNi42NCw1Ny4zMiw3OS45LDgzLjcy"
    "LTIwLjY3LDM2LjE2LTE3LjA1LDczLjUzLTIuMzIsMTEwLjRsNjAuNjYtNTQuNDhjMi42NCwzLjE3LDcuNCw3Ljg5LDE2LjQ4"
    "LDExLjU2LDguNSwzLjQ0LDIwLjMsNS4xMiwzMywuMTdsLTQ4LjI2LTM4LjkyWiIvPgogICAgICA8cGF0aCBjbGFzcz0iY2xz"
    "LTEiIGQ9Ik0xNTMuMzQsNTguODFsNi45OS01Ni4zOGMtMTUuNzgtNS41OS0zMS4wOS0xLjA2LTQxLjE4LDkuMDItMTQuMjks"
    "MTQuMjYtMTUuODYsMzguOTgsMCw1NC41Nmw3LjEtNDAuOTIsMjMuNTYsNjAuMDEsNDMuMTksMTIuNDUtMjguODgsMjQuODNj"
    "NTYuODgtNS40Nyw3OS45Ni00Ny4wMSw3OS45Ni00Ny4wMWwtOTAuNzQtMTYuNTZaIi8+CiAgICA8L2c+CiAgICA8Zz4KICAg"
    "ICAgPHBhdGggY2xhc3M9ImNscy01IiBkPSJNMjk1LjMxLDEzNi41OHY4OC44NWgtMTcuMzl2LTM2LjgxaC0zM3YzNi44MWgt"
    "MTcuNTJ2LTg4Ljg1aDE3LjUydjM1LjI5aDMzdi0zNS4yOWgxNy4zOVoiLz4KICAgICAgPHBhdGggY2xhc3M9ImNscy01IiBk"
    "PSJNMzc1LjY2LDE2MS45N3Y2My40N2gtMTYuMzd2LTcuNDljLTQuNTcsNS43MS0xMS40Miw5LjI3LTIwLjY5LDkuMjctMTYu"
    "ODgsMC0zMC44NS0xNC42LTMwLjg1LTMzLjUxczEzLjk2LTMzLjUxLDMwLjg1LTMzLjUxYzkuMjcsMCwxNi4xMiwzLjU1LDIw"
    "LjY5LDkuMjd2LTcuNDloMTYuMzdaTTM1OS4yOCwxOTMuN2MwLTEwLjY2LTcuNDktMTcuOS0xNy42NC0xNy45cy0xNy41Miw3"
    "LjIzLTE3LjUyLDE3LjksNy40OSwxNy45LDE3LjUyLDE3LjksMTcuNjQtNy4yNCwxNy42NC0xNy45WiIvPgogICAgICA8cGF0"
    "aCBjbGFzcz0iY2xzLTUiIGQ9Ik00MzcuODYsMjA2LjljMCwxMy43MS0xMS45MywyMC4zMS0yNS41MSwyMC4zMS0xMi42OSww"
    "LTIyLjA5LTUuMzMtMjYuNjYtMTUuMTFsMTQuMjItOGMxLjc4LDUuMiw2LjA5LDguMjUsMTIuNDQsOC4yNSw1LjIsMCw4Ljc2"
    "LTEuNzgsOC43Ni01LjQ2LDAtOS4yNy0zMi43NS00LjE5LTMyLjc1LTI2LjUzLDAtMTIuOTUsMTEuMDQtMjAuMTgsMjQuMTIt"
    "MjAuMTgsMTAuMjgsMCwxOS4xNyw0LjcsMjQuMTIsMTMuNDZsLTEzLjk2LDcuNjJjLTEuOS00LjA2LTUuNDYtNi40Ny0xMC4x"
    "NS02LjQ3LTQuMDYsMC03LjM2LDEuNzgtNy4zNiw1LjIsMCw5LjM5LDMyLjc1LDMuNTUsMzIuNzUsMjYuOTFaIi8+CiAgICAg"
    "IDxwYXRoIGNsYXNzPSJjbHMtNSIgZD0iTTQ4Ny44NywyMjUuNDNsLTIzLjEtMjguODF2MjguODFoLTE2LjM3di04OC44NWgx"
    "Ni4zN3Y1My4zMWwyMS44My0yNy45M2gxOS41NWwtMjUuNTEsMzEuMzUsMjYuMjgsMzIuMTFoLTE5LjA0WiIvPgogICAgICA8"
    "cGF0aCBjbGFzcz0iY2xzLTUiIGQ9Ik01MDcuMTcsMTkzLjdjMC0xOC45MSwxNC44NS0zMy41MSwzMy41MS0zMy41MXMzMy42"
    "NCwxNC42LDMzLjY0LDMzLjUxLTE0Ljk4LDMzLjUxLTMzLjY0LDMzLjUxLTMzLjUxLTE0LjYtMzMuNTEtMzMuNTFaTTU1Ny45"
    "NCwxOTMuN2MwLTEwLjI4LTcuNDktMTcuNTItMTcuMjYtMTcuNTJzLTE3LjE0LDcuMjMtMTcuMTQsMTcuNTIsNy40OSwxNy41"
    "MiwxNy4xNCwxNy41MiwxNy4yNi03LjIzLDE3LjI2LTE3LjUyWiIvPgogICAgICA8cGF0aCBjbGFzcz0iY2xzLTUiIGQ9Ik02"
    "NDUuMTUsMTg2LjQ3djM4Ljk3aC0xNi4zOHYtMzYuOTRjMC04LjYzLTUuMi0xMy4wNy0xMi41Ny0xMy4wNy04LDAtMTMuOTYs"
    "NC43LTEzLjk2LDE1Ljc0djM0LjI3aC0xNi4zN3YtNjMuNDdoMTYuMzd2Ny4xMWMzLjgxLTUuNzEsMTAuNDEtOC44OSwxOC45"
    "MS04Ljg5LDEzLjQ2LDAsMjMuOTksOS4zOSwyMy45OSwyNi4yOFoiLz4KICAgICAgPHBhdGggY2xhc3M9ImNscy01IiBkPSJN"
    "NjU3LjIxLDE0NC4zMmMwLTUuNDYsNC41Ny0xMC4xNSwxMC4wMy0xMC4xNXMxMC4xNSw0LjcsMTAuMTUsMTAuMTUtNC41Nywx"
    "MC4wMy0xMC4xNSwxMC4wMy0xMC4wMy00LjU3LTEwLjAzLTEwLjAzWk02NTkuMTEsMTYxLjk3aDE2LjM3djYzLjQ3aC0xNi4z"
    "N3YtNjMuNDdaIi8+CiAgICAgIDxwYXRoIGNsYXNzPSJjbHMtNSIgZD0iTTc0OS43NCwxODYuNDd2MzguOTdoLTE2LjM3di0z"
    "Ni45NGMwLTguNjMtNS4yLTEzLjA3LTEyLjU3LTEzLjA3LTgsMC0xMy45Niw0LjctMTMuOTYsMTUuNzR2MzQuMjdoLTE2LjM3"
    "di02My40N2gxNi4zN3Y3LjExYzMuODEtNS43MSwxMC40MS04Ljg5LDE4LjkxLTguODksMTMuNDYsMCwyMy45OSw5LjM5LDIz"
    "Ljk5LDI2LjI4WiIvPgogICAgICA8cGF0aCBjbGFzcz0iY2xzLTUiIGQ9Ik04MjguMzIsMTYxLjk3djYwLjQyYzAsMjAuODIt"
    "MTYuMzcsMzAuMjEtMzMuMTMsMzAuMjEtMTMuNTgsMC0yNC41LTUuMjEtMzAuMDgtMTUuNDlsMTMuOTYtOGMyLjY3LDQuOTUs"
    "Ni44NSw4Ljg5LDE2LjYzLDguODksMTAuMjgsMCwxNi42My01LjU5LDE2LjYzLTE1LjYxdi02Ljg2Yy00LjQ0LDUuOTctMTEu"
    "Myw5LjY1LTIwLjMxLDkuNjUtMTguMDIsMC0zMS42MS0xNC42LTMxLjYxLTMyLjVzMTMuNTgtMzIuNSwzMS42MS0zMi41Yzku"
    "MDEsMCwxNS44NywzLjY4LDIwLjMxLDkuNjV2LTcuODdoMTUuOTlaTTgxMi4zMiwxOTIuNjhjMC0xMC4wMy03LjQ5LTE3LjI2"
    "LTE3Ljc3LTE3LjI2cy0xNy43Nyw3LjI0LTE3Ljc3LDE3LjI2LDcuNDksMTcuMzksMTcuNzcsMTcuMzksMTcuNzctNy4yNCwx"
    "Ny43Ny0xNy4zOVoiLz4KICAgICAgPGc+CiAgICAgICAgPHBhdGggY2xhc3M9ImNscy0zIiBkPSJNMjM4LjAyLDI2NS43M2wt"
    "MS40OSw4LjQ1aDEyLjk5bC0uODgsNS4wMWgtMTIuOTlsLTEuNTgsOC44MmgxNC40M2wtLjkzLDUuMTFoLTE5LjczbDUuNzEt"
    "MzIuNDloMTkuNDlsLS44OCw1LjExaC0xNC4xNloiLz4KICAgICAgICA8cGF0aCBjbGFzcz0iY2xzLTMiIGQ9Ik0yNzUuNzYs"
    "Mjc4Ljg2bC0yLjUxLDE0LjI1aC01LjAxbDIuNDEtMTMuNzRjLjYtMy41Ny0xLjAyLTUuMzgtNC4yNy01LjM4cy02LjAzLDEu"
    "NzYtNi45Niw2LjA4bC0yLjI3LDEzLjA0aC01LjAxbDQuMDgtMjMuMjFoNS4wMWwtLjUxLDIuNzhjMi0yLjMyLDQuNzMtMy4z"
    "OSw3LjU3LTMuMzksNS4yLDAsOC40OSwzLjU3LDcuNDcsOS41NloiLz4KICAgICAgICA8cGF0aCBjbGFzcz0iY2xzLTMiIGQ9"
    "Ik0zMDIuMTcsMjc4Ljg2bC0yLjUxLDE0LjI1aC01LjAxbDIuNDEtMTMuNzRjLjYtMy41Ny0xLjAyLTUuMzgtNC4yNy01LjM4"
    "cy02LjA4LDEuNzYtNi45Niw2LjIybC0yLjI3LDEyLjloLTUuMDFsNS43MS0zMi40OWg1LjAxbC0yLjEzLDEyLjA3YzItMi4z"
    "Miw0LjczLTMuMzksNy41Ny0zLjM5LDUuMiwwLDguNDksMy41Nyw3LjQ3LDkuNTZaIi8+CiAgICAgICAgPHBhdGggY2xhc3M9"
    "ImNscy0zIiBkPSJNMzMyLjQ5LDI2OS45bC00LjA4LDIzLjIxaC01LjAxbC40Ni0yLjc0Yy0yLjA0LDIuMDktNC44NywzLjM0"
    "LTguNDksMy4zNC02Ljk2LDAtMTAuNzctNi4xNy05LjU2LTEyLjcyLDEuMjUtNi45MSw2LjY4LTExLjcsMTMuMTgtMTEuNywz"
    "LjU3LDAsNi4zMSwxLjU4LDcuODQsNC4zNmwuNjUtMy43Nmg1LjAxWk0zMjUuMjksMjgyLjM0bC4yMy0xLjM1Yy40Ni00LjQ2"
    "LTIuNTEtNi45MS02LjI2LTYuOTFzLTcuNjEsMi41NS04LjQ1LDcuMjljLS43NCw0LjMyLDEuODEsNy41Nyw2LjAzLDcuNTcs"
    "My45NCwwLDcuNDMtMi42NSw4LjQ1LTYuNTlaIi8+CiAgICAgICAgPHBhdGggY2xhc3M9ImNscy0zIiBkPSJNMzU3Ljg4LDI3"
    "OC44NmwtMi41MSwxNC4yNWgtNS4wMWwyLjQxLTEzLjc0Yy42LTMuNTctMS4wMi01LjM4LTQuMjctNS4zOHMtNi4wMywxLjc2"
    "LTYuOTYsNi4wOGwtMi4yNywxMy4wNGgtNS4wMWw0LjA4LTIzLjIxaDUuMDFsLS41MSwyLjc4YzItMi4zMiw0LjczLTMuMzks"
    "Ny41Ny0zLjM5LDUuMiwwLDguNDksMy41Nyw3LjQ3LDkuNTZaIi8+CiAgICAgICAgPHBhdGggY2xhc3M9ImNscy0zIiBkPSJN"
    "MzYxLjUxLDI4MWMxLjE2LTYuODIsNi45Ni0xMS43LDEzLjk3LTExLjcsNC43OCwwLDguMjYsMi40MSw5LjY1LDYuMDNsLTQu"
    "NSwyLjMyYy0uODQtMi4xMy0yLjc4LTMuNDQtNS42Mi0zLjQ0LTQuMTMsMC03Ljc1LDIuOTItOC40OSw3LjE1LS43LDQuMTgs"
    "MS43Niw3LjQzLDUuOTQsNy40MywyLjc4LDAsNS4yLTEuNDQsNi42NC0zLjYybDQuMDQsMi42Yy0yLjQxLDMuOS02LjY0LDUu"
    "OTQtMTEuMTksNS45NC03LjEsMC0xMS42LTUuNzEtMTAuNDQtMTIuNzJaIi8+CiAgICAgICAgPHBhdGggY2xhc3M9ImNscy0z"
    "IiBkPSJNMzg5Ljc4LDI2OS45aDUuMDFsLTQuMDgsMjMuMjFoLTUuMDFsNC4wOC0yMy4yMVpNMzkwLjI0LDI2My4yMmMuMjgt"
    "MS43MiwxLjktMy4yLDMuNzEtMy4yczMuMDIsMS40NCwyLjY5LDMuMmMtLjI4LDEuNzItMS44NiwzLjItMy43NiwzLjJzLTIu"
    "OTItMS40OS0yLjY0LTMuMloiLz4KICAgICAgICA8cGF0aCBjbGFzcz0iY2xzLTMiIGQ9Ik00MjAuMTMsMjc4Ljg2bC0yLjUx"
    "LDE0LjI1aC01LjAxbDIuNDEtMTMuNzRjLjYtMy41Ny0xLjAyLTUuMzgtNC4yNy01LjM4cy02LjAzLDEuNzYtNi45Niw2LjA4"
    "bC0yLjI3LDEzLjA0aC01LjAxbDQuMDgtMjMuMjFoNS4wMWwtLjUxLDIuNzhjMi0yLjMyLDQuNzMtMy4zOSw3LjU3LTMuMzks"
    "NS4yLDAsOC40OSwzLjU3LDcuNDcsOS41NloiLz4KICAgICAgICA8cGF0aCBjbGFzcz0iY2xzLTMiIGQ9Ik00NTAuNDksMjY5"
    "LjlsLTMuOSwyMi4xNGMtMS4zNSw3LjctNi44NywxMC45NS0xMy4zNywxMC45NS01LjAxLDAtOC44Ni0xLjk1LTEwLjU0LTUu"
    "NjJsNC41LTIuMzJjLjg0LDEuOSwyLjY5LDMuMzksNi4zNiwzLjM5LDQuNSwwLDcuMzgtMi4yNyw4LjEyLTYuNDFsLjQyLTIu"
    "NDFjLTIuMDQsMi4yMy00Ljg3LDMuNjItOC40LDMuNjItNy4yOSwwLTEwLjk1LTUuODktOS44OC0xMi40OCwxLjA3LTYuNTUs"
    "Ni41LTExLjQ2LDEyLjk5LTExLjQ2LDMuNjcsMCw2LjU5LDEuNjIsOC4wOCw0LjVsLjctMy45aDQuOTJaTTQ0My41MywyODEu"
    "NDJjLjg4LTQuNjktMi4zMi03LjM4LTYuMjItNy4zOHMtNy44LDIuNjktOC40OSw3LjFjLS43LDQuMjcsMS44Niw3LjM4LDYu"
    "MTcsNy4zOHM3Ljc1LTIuODMsOC41NC03LjFaIi8+CiAgICAgICAgPHBhdGggY2xhc3M9ImNscy0zIiBkPSJNNDYzLjYzLDI4"
    "NS43M2w0LjgzLTIuNTFjLjcsMy4xNiwyLjk3LDUuMzQsNy4zOCw1LjM0LDMuODUsMCw2LjE3LTEuNjcsNi42OC00LjA4Ljct"
    "My4xMS0yLjQ2LTQuMjctNi4yMi01LjUyLTQuODMtMS42Mi05LjU2LTQuMTMtOC40LTEwLjM1LDEuMDctNS45OSw2LjUtOC41"
    "OSwxMS41Ni04LjU5LDUuNDgsMCw5LjEsMi45MiwxMC41OCw3LjFsLTQuNjksMi40NmMtLjk4LTIuNTUtMi43NC00LjQxLTYu"
    "MzEtNC40MS0yLjg4LDAtNS4yNCwxLjM5LTUuNzUsMy44MS0uNjUsMy4wNiwyLjMyLDQuMjcsNi4wMyw1LjU3LDQuMzIsMS41"
    "Myw5LjkzLDMuNjIsOC42MywxMC40NC0xLjA3LDUuODUtNi4xNyw4LjczLTEyLjQ4LDguNzNzLTEwLjYzLTMuMTEtMTEuODQt"
    "Ny45OFoiLz4KICAgICAgICA8cGF0aCBjbGFzcz0iY2xzLTMiIGQ9Ik00OTEuOSwyODAuOWMxLjMtNi45Niw3LjI5LTExLjYs"
    "MTQuMTYtMTEuNnMxMS4zNyw1LjY2LDEwLjE2LDEyLjY3Yy0xLjI1LDcuMDUtNy4zMywxMS43NC0xMy44MywxMS43NC03LjMz"
    "LDAtMTEuODQtNS43MS0xMC40OS0xMi44MVpNNTExLjI2LDI4MS40MmMuODMtNC42LTIuMTQtNy4yNC01Ljg5LTcuMjRzLTcu"
    "NjEsMi42NS04LjQ1LDcuMzNjLS43OSw0LjY5LDIuMDQsNy4zMyw1Ljg1LDcuMzNzNy42Ni0yLjY1LDguNDktNy40M1oiLz4K"
    "ICAgICAgICA8cGF0aCBjbGFzcz0iY2xzLTMiIGQ9Ik01MTkuNjYsMjgxYzEuMTYtNi44Miw2Ljk2LTExLjcsMTMuOTctMTEu"
    "Nyw0Ljc4LDAsOC4yNiwyLjQxLDkuNjUsNi4wM2wtNC41LDIuMzJjLS44NC0yLjEzLTIuNzgtMy40NC01LjYyLTMuNDQtNC4x"
    "MywwLTcuNzUsMi45Mi04LjQ5LDcuMTUtLjcsNC4xOCwxLjc2LDcuNDMsNS45NCw3LjQzLDIuNzgsMCw1LjItMS40NCw2LjY0"
    "LTMuNjJsNC4wNCwyLjZjLTIuNDEsMy45LTYuNjQsNS45NC0xMS4xOSw1Ljk0LTcuMSwwLTExLjYtNS43MS0xMC40NC0xMi43"
    "MloiLz4KICAgICAgICA8cGF0aCBjbGFzcz0iY2xzLTMiIGQ9Ik01NDcuOTMsMjY5LjloNS4wMWwtNC4wOCwyMy4yMWgtNS4w"
    "MWw0LjA4LTIzLjIxWk01NDguNCwyNjMuMjJjLjI4LTEuNzIsMS45LTMuMiwzLjcxLTMuMnMzLjAyLDEuNDQsMi42OSwzLjJj"
    "LS4yOCwxLjcyLTEuODYsMy4yLTMuNzYsMy4ycy0yLjkyLTEuNDktMi42NC0zLjJaIi8+CiAgICAgICAgPHBhdGggY2xhc3M9"
    "ImNscy0zIiBkPSJNNTc5LjM2LDI4MS41NmMtLjA5LjM3LS4zMywxLjM5LS41NiwyLjA5aC0xOC40N2MuMDksMy43MSwyLjc0"
    "LDUuNDgsNi4yNyw1LjQ4LDIuNzQsMCw1LjAxLTEuMDcsNi41NC0yLjkybDMuNjcsMi43OWMtMi41MSwzLjExLTYuMzYsNC43"
    "My0xMC42Myw0LjczLTcuNjEsMC0xMS44NC01LjY2LTEwLjY3LTEyLjY3LDEuMTYtNi43OCw2Ljk2LTExLjc0LDEzLjgzLTEx"
    "Ljc0czExLjMyLDUuNDgsMTAuMDMsMTIuMjVaTTU3NC42MiwyNzkuNTFjLjA1LTMuOTktMi40MS01LjY2LTUuNjItNS42Ni0z"
    "LjY3LDAtNi42NCwyLjEzLTcuOTgsNS42NmgxMy42WiIvPgogICAgICAgIDxwYXRoIGNsYXNzPSJjbHMtMyIgZD0iTTU4OS40"
    "OCwyODUuODdjLS41MSwzLjAyLDEuNTgsMi45Nyw1LjI5LDIuNzRsLS43OSw0LjVjLTcuMjQuOTMtMTAuNTgtMS4yMS05LjUx"
    "LTcuMjRsMS45NS0xMS4xNGgtNC4yN2wuODgtNC44M2g0LjI3bC44OC01LjAxLDUuMjQtMS40OS0xLjE2LDYuNWg1LjhsLS44"
    "OCw0LjgzaC01Ljc1bC0xLjk1LDExLjE0WiIvPgogICAgICAgIDxwYXRoIGNsYXNzPSJjbHMtMyIgZD0iTTYyNC4wNiwyNjku"
    "OWwtMTMuMTMsMjMuOTVjLTMuNDgsNi40NS03Ljc1LDguODYtMTIuODEsOC41NGwuODQtNC42OWMzLjE2LjE5LDQuOTctMS4z"
    "LDYuNzMtNC40NmwuNDItLjY1LTUuNzEtMjIuN2g1LjE1bDMuOTksMTcuMDMsOC45Ni0xNy4wM2g1LjU3WiIvPgogICAgICAg"
    "IDxwYXRoIGNsYXNzPSJjbHMtMyIgZD0iTTY2MS4wMSwyNjUuNzNoLTkuMTRsLTQuODMsMjcuMzhoLTUuMzRsNC44My0yNy4z"
    "OGgtOS4xOWwuODgtNS4xMWgyMy42N2wtLjg4LDUuMTFaIi8+CiAgICAgICAgPHBhdGggY2xhc3M9ImNscy0zIiBkPSJNNjU2"
    "LjUxLDI4MC45YzEuMy02Ljk2LDcuMjktMTEuNiwxNC4xNi0xMS42czExLjM3LDUuNjYsMTAuMTYsMTIuNjdjLTEuMjUsNy4w"
    "NS03LjMzLDExLjc0LTEzLjgzLDExLjc0LTcuMzMsMC0xMS44NC01LjcxLTEwLjQ5LTEyLjgxWk02NzUuODcsMjgxLjQyYy44"
    "My00LjYtMi4xNC03LjI0LTUuOS03LjI0cy03LjYxLDIuNjUtOC40NSw3LjMzYy0uNzksNC42OSwyLjA0LDcuMzMsNS44NSw3"
    "LjMzczcuNjYtMi42NSw4LjQ5LTcuNDNaIi8+CiAgICAgICAgPHBhdGggY2xhc3M9ImNscy0zIiBkPSJNNzExLjAxLDI2OS45"
    "bC0zLjksMjIuMTRjLTEuMzUsNy43LTYuODcsMTAuOTUtMTMuMzcsMTAuOTUtNS4wMSwwLTguODYtMS45NS0xMC41NC01LjYy"
    "bDQuNS0yLjMyYy44NCwxLjksMi42OSwzLjM5LDYuMzYsMy4zOSw0LjUsMCw3LjM4LTIuMjcsOC4xMi02LjQxbC40Mi0yLjQx"
    "Yy0yLjA0LDIuMjMtNC44NywzLjYyLTguNCwzLjYyLTcuMjksMC0xMC45NS01Ljg5LTkuODgtMTIuNDgsMS4wNy02LjU1LDYu"
    "NS0xMS40NiwxMi45OS0xMS40NiwzLjY3LDAsNi41OSwxLjYyLDguMDgsNC41bC43LTMuOWg0LjkyWk03MDQuMDQsMjgxLjQy"
    "Yy44OC00LjY5LTIuMzItNy4zOC02LjIyLTcuMzhzLTcuOCwyLjY5LTguNDksNy4xYy0uNyw0LjI3LDEuODYsNy4zOCw2LjE3"
    "LDcuMzhzNy43NS0yLjgzLDguNTQtNy4xWiIvPgogICAgICAgIDxwYXRoIGNsYXNzPSJjbHMtMyIgZD0iTTczNy40NywyODEu"
    "NTZjLS4wOS4zNy0uMzMsMS4zOS0uNTYsMi4wOWgtMTguNDdjLjA5LDMuNzEsMi43NCw1LjQ4LDYuMjcsNS40OCwyLjc0LDAs"
    "NS4wMS0xLjA3LDYuNTQtMi45MmwzLjY3LDIuNzljLTIuNTEsMy4xMS02LjM2LDQuNzMtMTAuNjMsNC43My03LjYxLDAtMTEu"
    "ODQtNS42Ni0xMC42Ny0xMi42NywxLjE2LTYuNzgsNi45Ni0xMS43NCwxMy44My0xMS43NHMxMS4zMiw1LjQ4LDEwLjAzLDEy"
    "LjI1Wk03MzIuNzMsMjc5LjUxYy4wNS0zLjk5LTIuNDEtNS42Ni01LjYyLTUuNjYtMy42NywwLTYuNjQsMi4xMy03Ljk4LDUu"
    "NjZoMTMuNloiLz4KICAgICAgICA8cGF0aCBjbGFzcz0iY2xzLTMiIGQ9Ik03NDcuNTksMjg1Ljg3Yy0uNTEsMy4wMiwxLjU4"
    "LDIuOTcsNS4yOSwyLjc0bC0uNzksNC41Yy03LjI0LjkzLTEwLjU4LTEuMjEtOS41MS03LjI0bDEuOTUtMTEuMTRoLTQuMjds"
    "Ljg4LTQuODNoNC4yN2wuODgtNS4wMSw1LjI0LTEuNDktMS4xNiw2LjVoNS44bC0uODgsNC44M2gtNS43NWwtMS45NSwxMS4x"
    "NFoiLz4KICAgICAgICA8cGF0aCBjbGFzcz0iY2xzLTMiIGQ9Ik03ODAuMjcsMjc4Ljg2bC0yLjUxLDE0LjI1aC01LjAxbDIu"
    "NDEtMTMuNzRjLjYtMy41Ny0xLjAyLTUuMzgtNC4yNy01LjM4cy02LjA4LDEuNzYtNi45Niw2LjIybC0yLjI3LDEyLjloLTUu"
    "MDFsNS43MS0zMi40OWg1LjAxbC0yLjEzLDEyLjA3YzItMi4zMiw0LjczLTMuMzksNy41Ny0zLjM5LDUuMiwwLDguNDksMy41"
    "Nyw3LjQ3LDkuNTZaIi8+CiAgICAgICAgPHBhdGggY2xhc3M9ImNscy0zIiBkPSJNODA3Ljc1LDI4MS41NmMtLjA5LjM3LS4z"
    "MywxLjM5LS41NiwyLjA5aC0xOC40N2MuMDksMy43MSwyLjc0LDUuNDgsNi4yNyw1LjQ4LDIuNzQsMCw1LjAxLTEuMDcsNi41"
    "NC0yLjkybDMuNjcsMi43OWMtMi41MSwzLjExLTYuMzYsNC43My0xMC42Myw0LjczLTcuNjEsMC0xMS44NC01LjY2LTEwLjY3"
    "LTEyLjY3LDEuMTYtNi43OCw2Ljk2LTExLjc0LDEzLjgzLTExLjc0czExLjMyLDUuNDgsMTAuMDMsMTIuMjVaTTgwMy4wMiwy"
    "NzkuNTFjLjA1LTMuOTktMi40MS01LjY2LTUuNjItNS42Ni0zLjY3LDAtNi42NCwyLjEzLTcuOTgsNS42NmgxMy42WiIvPgog"
    "ICAgICAgIDxwYXRoIGNsYXNzPSJjbHMtMyIgZD0iTTgyNi4zMiwyNjkuNDlsLS45OCw1LjQzYy0zLjA2LS4yMy03LjA1LDEu"
    "MTEtOC4xNyw1Ljg5bC0yLjE4LDEyLjNoLTUuMDFsNC4wOC0yMy4yMWg1LjAxbC0uNiwzLjQ4YzItMi45Miw0Ljg3LTMuOTks"
    "Ny44NC0zLjlaIi8+CiAgICAgIDwvZz4KICAgIDwvZz4KICA8L2c+Cjwvc3ZnPg=="
)


def _load_logo_data_uri() -> str:
    """Geef het Haskoning-logo terug als data-URI (inline base64, geen los bestand nodig)."""
    return f"data:image/svg+xml;base64,{_HASKONING_LOGO_SVG_B64}"


def _branding_header_html(title: str = TOOL_TITLE, subtitle: str = "", fixed: bool = False) -> str:
    """
    Genereer de Haskoning-navigatiebalk (Ocean Blue) met logo, titel en payoff-tekst.

    fixed=True: balk over de volledige breedte, vast bovenaan de pagina (voor de
    geëxporteerde kaart-HTML). fixed=False: normale blok-layout voor de notebook.
    """
    logo_uri = _load_logo_data_uri()
    logo_img = (
        f'<img src="{logo_uri}" alt="Haskoning" style="height:32px;width:auto;display:block;">'
        if logo_uri else ""
    )
    subtitle_html = (
        f'<div style="font-size:12px;color:{HASKONING_COLORS["white"]};opacity:0.85;">{subtitle}</div>'
        if subtitle else ""
    )
    position_css = (
        f"position:fixed;top:0;left:0;right:0;z-index:10000;border-radius:0;margin-bottom:0;height:{TOPBAR_HEIGHT_PX}px;box-sizing:border-box;"
        if fixed else "border-radius:4px;margin-bottom:10px;"
    )
    return f'''
    <div style="
        display:flex;
        align-items:center;
        justify-content:space-between;
        gap:16px;
        background-color:{HASKONING_COLORS["primary"]};
        color:{HASKONING_COLORS["white"]};
        padding:10px 18px;
        font-family:Arial, sans-serif;
        {position_css}
    ">
        <div style="display:flex;align-items:center;gap:14px;">
            {logo_img}
            <div>
                <div style="font-size:16px;font-weight:700;">{title}</div>
                {subtitle_html}
            </div>
        </div>
        <div style="font-size:11px;font-style:italic;color:{ALARM_COLORS["low"]};">{TOOL_PAYOFF}</div>
    </div>
    '''


def _get_topbar_offset_css() -> str:
    """CSS die de kaart en vaste panelen onder de branded topbar plaatst (enkel voor de geëxporteerde kaart)."""
    h = TOPBAR_HEIGHT_PX
    return f'''
    <style>
        .folium-map {{
            top: {h}px !important;
            height: calc(100% - {h}px) !important;
        }}
        #control-panel {{
            top: {h + 10}px !important;
        }}
        #left-panel, #right-panel {{
            top: {h}px !important;
            height: calc(100vh - {h}px) !important;
        }}
        #close-panels-btn {{
            top: {h + 10}px !important;
        }}
    </style>
    '''


def _notebook_css() -> str:
    """
    CSS die de ipywidgets-elementen in de notebook themet naar de Haskoning Green theme.

    Naast generieke ipywidgets-selectors (die per ipywidgets-versie kunnen verschillen en dus
    niet altijd raken) krijgen widgets ook eigen classes via `add_class()` (`hsk-input`,
    `hsk-btn-secondary`, ...). Die classes worden hieronder gestyled zodat de branding
    gegarandeerd wordt toegepast, ongeacht de interne DOM-structuur van ipywidgets.
    """
    c = HASKONING_COLORS
    t = THEME_GREEN
    return f'''
    <style>
        /* Primaire knoppen (Genereer kaart, Open kaart, ...) */
        .jupyter-widgets.widget-button, .jupyter-button.widget-button {{
            background-color: {t["secondary"]} !important;
            color: {c["white"]} !important;
            border: none !important;
            border-radius: 4px !important;
            font-weight: 600 !important;
        }}
        .jupyter-widgets.widget-button:hover:enabled, .jupyter-button.widget-button:hover:enabled {{
            background-color: {t["highlight"]} !important;
            color: {c["primary"]} !important;
        }}
        .jupyter-widgets.widget-button:disabled, .jupyter-button.widget-button:disabled {{
            background-color: {c["disabled_bg"]} !important;
            color: {c["disabled_text"]} !important;
        }}
        .jupyter-widgets.widget-button.mod-danger {{
            background-color: {ALARM_COLORS["critical"]} !important;
            color: {c["white"]} !important;
            border: none !important;
        }}

        /* Secundaire knoppen (bladeren, laag toevoegen): wit met Ocean Blue rand */
        .hsk-btn-secondary, .hsk-btn-secondary.jupyter-widgets.widget-button {{
            background-color: {c["white"]} !important;
            color: {c["primary"]} !important;
            border: 1px solid {c["primary"]} !important;
            border-radius: 4px !important;
            font-weight: 600 !important;
        }}
        .hsk-btn-secondary:hover:enabled {{
            background-color: {t["highlight"]} !important;
        }}

        /* Tekstvelden: uniforme achtergrond/rand voor alle pad- en naamvelden */
        .widget-text input, .widget-text > input,
        .hsk-input input, .hsk-input.widget-text input {{
            background-color: {c["input_bg"]} !important;
            border: 1px solid rgba(0, 46, 79, 0.35) !important;
            border-radius: 4px !important;
            color: {c["primary"]} !important;
        }}
        .hsk-input input:focus {{
            border-color: {c["primary"]} !important;
            outline: none !important;
        }}

        /* Accordion-koppen */
        .p-Accordion-title, .lm-AccordionPanel-title, .jupyter-widgets.widget-accordion .widget-box {{
            background-color: {c["primary"]} !important;
            color: {c["white"]} !important;
        }}
    </style>
    '''


# ==========================
# DATA HELPERS
# ==========================

def _read_layer(path: Optional[str], fallback_crs: str = SOURCE_CRS):
    """Lees een GIS-laag en zet CRS als nodig. Geeft None terug bij leeg pad."""
    if not path or not str(path).strip():
        return None
    fp = Path(path)
    if not fp.exists():
        raise FileNotFoundError(f"Bestand niet gevonden: {path}")
    try:
        gdf = gpd.read_file(path)
    except Exception as exc:
        raise ValueError(f"Kon '{fp.name}' niet lezen: {exc}") from exc
    if gdf.empty:
        raise ValueError(f"Shapefile is leeg (geen rijen): {path}")
    if gdf.crs is None:
        gdf = gdf.set_crs(fallback_crs)
    return gdf


def _to_map_crs(gdf):
    """Converteer GeoDataFrame naar WGS84 voor weergave op kaart."""
    if gdf is None:
        return None
    return gdf.to_crs(MAP_CRS)


def _layer_to_geojson(gdf, name, style=None, tooltip_fields=None):
    """Converteer GeoDataFrame naar Folium GeoJson laag."""
    tooltip = None
    if tooltip_fields:
        tooltip = folium.GeoJsonTooltip(fields=tooltip_fields)
    return folium.GeoJson(
        data=gdf.__geo_interface__,
        name=name,
        style_function=(lambda _: style) if style else None,
        tooltip=tooltip,
    )


def _pick_tooltip_fields(gdf, max_fields=6):
    """Selecteer velden voor tooltip (exclusief geometry)."""
    fields = [c for c in gdf.columns if c != "geometry"]
    return fields[:max_fields]


# ==========================
# Legenda verschil gemeten vs berekend
# ==========================

def html_map_legend():
    """Retourneer legenda tabel voor verschil gemeten vs berekend."""
    return {
        "value": [
            (9999999.0, 10.0, 0, 0, 149, ">10 (natter)"),
            (10.0, 5.0, 0, 84, 240, "5.00 - 10.00"),
            (5.0, 2.5, 55, 125, 255, "2.50 - 5.00"),
            (2.5, 1.0, 108, 159, 255, "1.00 - 2.50"),
            (1.0, 0.6, 166, 197, 255, "0.60 - 1.00"),
            (0.6, 0.4, 206, 224, 255, "0.40 - 0.60"),
            (0.4, 0.2, 206, 239, 255, "0.20 - 0.40"),
            (0.2, 0.1, 0, 128, 85, "0.20 - 0.10"),
            (0.1, -0.1, 0, 54, 0, "-0.10 - 0.10"),
            (-0.1, -0.2, 85, 128, 0, "-0.10 - -0.20"),
            (-0.2, -0.4, 255, 230, 203, "-0.20 - -0.40"),
            (-0.4, -0.6, 255, 215, 170, "-0.40 - -0.60"),
            (-0.6, -1.0, 255, 181, 106, "-0.60 - -1.00"),
            (-1.0, -2.5, 255, 148, 40, "-1.00 - -2.50"),
            (-2.5, -5.0, 217, 108, 0, "-2.50 - -5.00"),
            (-5.0, -10.0, 176, 88, 0, "-5.00 - -10.00"),
            (-10.0, -9999999.0, 89, 47, 0, "<-10 (droger)"),
        ]
    }


def _color_from_legend(value, legend_table):
    """Bepaal kleur op basis van waarde en legenda tabel."""
    try:
        v = float(value)
    except:
        return "#6c757d"
    for lower, upper, r, g, b, _ in legend_table["value"]:
        lo = min(lower, upper)
        hi = max(lower, upper)
        if lo <= v < hi:
            return f"rgb({r},{g},{b})"
    return "#6c757d"


# Pas heir de wensen voor het uiterlijk van de legenda aan
def _get_legend_html():
    """Genereer HTML voor de legenda die getoond wordt bij Peilbuizen laag."""
    legend = html_map_legend()
    rows = []
    for _, _, r, g, b, label in legend["value"]:
        color = f"rgb({r},{g},{b})"
        rows.append(
            f'<div style="display:flex;align-items:center;margin:2px 0;">'
            f'<span style="width:20px;height:20px;background:{color};'
            f'display:inline-block;margin-right:6px;border:1px solid #333;flex-shrink:0;"></span>'
            f'<span style="font-size:14px;">{label}</span>'
            f"</div>"
        )
    
    return f"""
    <div id="legend-panel" style="
        position: fixed;
        bottom: 30px;
        right: 10px;
        z-index: 9998;
        background-color: white;
        border: 1px solid {HASKONING_COLORS["primary"]};
        border-radius: 4px;
        padding: 10px 12px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.35);
        font-family: Arial, sans-serif;
        max-height: 600px;
        overflow-y: auto;
        display: none;
    ">
        <div style="font-weight:700;font-size:20px;margin-bottom:6px;border-bottom:1px solid #ddd;padding-bottom:4px;color:{HASKONING_COLORS["primary"]};">
            Legenda: Verschil (m)
        </div>
        {''.join(rows)}
    </div>
    
    <button id="legend-toggle" onclick="toggleLegend()" style="
        position: fixed;
        bottom: 30px;
        right: 10px;
        z-index: 9997;
        padding: 8px 12px;
        background-color: white;
        border: 1px solid {HASKONING_COLORS["primary"]};
        color: {HASKONING_COLORS["primary"]};
        border-radius: 4px;
        cursor: pointer;
        font-family: Arial, sans-serif;
        font-size: 12px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.35);
    ">
        📊 Legenda
    </button>
    
    <script>
    var legendVisible = false;
    function toggleLegend() {{
        var panel = document.getElementById('legend-panel');
        var btn = document.getElementById('legend-toggle');
        legendVisible = !legendVisible;
        if (legendVisible) {{
            panel.style.display = 'block';
            btn.style.display = 'none';
        }} else {{
            panel.style.display = 'none';
            btn.style.display = 'block';
        }}
    }}
    
    // Sluit legenda door label te minimaliseren met een dropdown knop toegevoegd aan legenda
    document.addEventListener('DOMContentLoaded', function() {{
        var legendPanel = document.getElementById('legend-panel');
        if (legendPanel) {{
            var header = legendPanel.querySelector('div:first-child');
            if (header) {{
                var collapseBtn = document.createElement('button');
                collapseBtn.textContent = '▼';
                collapseBtn.style.float = 'right';
                collapseBtn.style.background = 'none';
                collapseBtn.style.border = 'none';
                collapseBtn.style.cursor = 'pointer';
                collapseBtn.style.fontSize = '16px';
                collapseBtn.title = 'Inklappen/Uitklappen';
                header.appendChild(collapseBtn);
                
                collapseBtn.addEventListener('click', function() {{
                    toggleLegend();
                }});
            }}
        }}
    }});
    </script>
    """


# ==========================
# .PNG afbeeldingen voor grafieken verwerken in de output. Hier worden de bestanden aangeroepen.
# Belangrijk: Elke map heeft het nummer van een modellaag.
# ==========================

def _encode_image_to_base64(image_path: Path) -> Optional[str]:
    """Zet een afbeeldingsbestand om naar base64 encoding."""
    try:
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        return image_data
    except:
        return None


def _find_graph_files_for_layer(png_base_path: Path, model_layer: int) -> Dict[str, str]:
    """
    Zoek alle grafiekbestanden voor een specifieke modellaag en retourneer als dict.
    
    Returns:
        Dict met {peilbuis_naam: base64_encoded_image}
    """
    result = {}
    layer_folder = png_base_path / str(model_layer)
    
    if not layer_folder.exists():
        return result
    
    for png_file in layer_folder.glob("*.png"):
        filename = png_file.stem  # bijv. "B43H0316_2"
        base64_data = _encode_image_to_base64(png_file)
        if base64_data:
            result[filename] = base64_data
    
    return result


def _collect_all_images_for_layers(png_base_path: Path, model_layers: List[int]) -> Dict[int, Dict[str, str]]:
    """
    Verzamel alle afbeeldingen voor de opgegeven modellagen.
    
    Returns:
        Dict met {layer_number: {peilbuis_naam: base64_encoded_image}}
    """
    all_images = {}
    for layer in model_layers:
        all_images[layer] = _find_graph_files_for_layer(png_base_path, layer)
    return all_images


def _discover_model_layers(png_base_path) -> List[int]:
    """
    Detecteer automatisch welke modellagen beschikbaar zijn.

    Elke submap van png_base_path waarvan de naam een geheel getal is én die minstens
    één .png-bestand bevat, wordt herkend als modellaag. Hiermee hoeft de gebruiker
    nooit handmatig een modellaag-range in te stellen.
    """
    base = Path(png_base_path)
    if not base.exists():
        return []
    layers = []
    for entry in base.iterdir():
        if entry.is_dir() and entry.name.isdigit() and next(entry.glob("*.png"), None) is not None:
            layers.append(int(entry.name))
    return sorted(layers)


# ==========================
# Inputvalidatie
# ==========================

# Verplichte kolommen voor peilbuis-shapefiles
_REQUIRED_SHAPEFILE_COLS = ["Naam", "Modellaag", "X", "Y"]
# Optionele kolommen met uitleg wat wegvalt als ze ontbreken
_OPTIONAL_SHAPEFILE_COLS = {
    "Difference": "verschilkleuren op de kaart worden niet getoond",
    "Measured":   "gemeten grondwaterstand niet zichtbaar in popup",
    "Calc":       "berekende grondwaterstand niet zichtbaar in popup",
}


def _validate_shapefile(path: str, label: str):
    """
    Valideer een shapefile: bestaan, leesbaarheid en kolommen.

    Retourneert (fouten: list[str], info: list[str]).
    Fouten blokkeren generatie; info-meldingen niet.
    """
    fouten: List[str] = []
    info:   List[str] = []
    fp = Path(str(path).strip())
    if not fp.exists():
        fouten.append(f"Bestand niet gevonden: {fp}")
        return fouten, info
    if fp.suffix.lower() != ".shp":
        fouten.append(f"Bestand is geen shapefile (.shp): {fp.name}")
        return fouten, info
    try:
        gdf = gpd.read_file(str(fp))
    except Exception as exc:
        fouten.append(f"Kon het bestand niet openen: {exc}")
        return fouten, info
    if gdf.empty:
        fouten.append("Shapefile is leeg (geen rijen).")
        return fouten, info
    cols = list(gdf.columns)
    for col in _REQUIRED_SHAPEFILE_COLS:
        if col not in cols:
            beschikbaar = ", ".join(c for c in cols if c != "geometry")
            fouten.append(
                f"Verplichte kolom '{col}' ontbreekt. "
                f"Beschikbare kolommen: {beschikbaar}"
            )
    for col, hint in _OPTIONAL_SHAPEFILE_COLS.items():
        if col not in cols:
            info.append(f"Optionele kolom '{col}' niet aanwezig \u2014 {hint}.")
    return fouten, info


def _validate_png_dir(path: str):
    """
    Valideer de grafiekenmap.

    Retourneert (fouten: list[str], info: list[str]).
    """
    fouten: List[str] = []
    info:   List[str] = []
    p = str(path).strip()
    if not p:
        fouten.append("Geen pad opgegeven.")
        return fouten, info
    fp = Path(p)
    if not fp.exists():
        fouten.append(f"Map niet gevonden: {p}")
        return fouten, info
    if not fp.is_dir():
        fouten.append(f"Opgegeven pad is geen map: {p}")
        return fouten, info
    layers = _discover_model_layers(fp)
    if not layers:
        fouten.append(
            f"Geen modellagen gevonden in '{fp.name}'. "
            "Verwacht: genummerde submappen (bijv. '1', '2', \u2026) met .png-bestanden erin."
        )
    else:
        info.append(f"{len(layers)} modellagen gevonden (laag {layers[0]} t/m {layers[-1]}).")
    return fouten, info


def _validate_output_path(path: str):
    """Valideer het HTML-uitvoerpad. Retourneert fouten: list[str]."""
    fouten: List[str] = []
    p = str(path).strip()
    if not p:
        fouten.append("Geen uitvoerpad opgegeven.")
        return fouten
    fp = Path(p)
    if fp.suffix.lower() != ".html":
        fouten.append(f"Uitvoerbestand moet eindigen op .html: {fp.name}")
    return fouten


def _render_validation_block(label: str, fouten: List[str], info: List[str]) -> str:
    """Render een HTML-blok met validatieresultaten voor één veld."""
    if not fouten and not info:
        return ""
    border_color = ALARM_COLORS["critical"] if fouten else ALARM_COLORS["medium"]
    html = (
        f'<div style="margin:4px 0;padding:6px 10px;font-family:Arial,sans-serif;'
        f'font-size:12px;background:#fafafa;border-left:3px solid {border_color};'
        f'border-radius:0 4px 4px 0;">'
        f'<b style="color:{HASKONING_COLORS["primary"]};">{label}</b><br>'
    )
    for f in fouten:
        html += f'<span style="color:{ALARM_COLORS["critical"]};">&#10007; {f}</span><br>'
    for i in info:
        html += f'<span style="color:#7a5900;">&#9888; {i}</span><br>'
    html += "</div>"
    return html


# ==========================
# Javascript
# ==========================

# Turf.js CDN script tag voor bufferberekeningen
def _get_turf_js_cdn():
    """Retourneer Turf.js CDN script tag."""
    return '<script src="https://unpkg.com/@turf/turf@6/turf.min.js"></script>'

# genereert de HTML voor het controle paneel waar gebruikers interactie mee hebben
def _get_control_panel_html(available_layers: List[int], available_types: List[Dict] = None, first_active_type: str = "stat") -> str:
    """
    Genereer HTML voor het controle paneel met:
    - Dataset toggle (Stat / GHG / GLG)
    - Modellaag selectie
    - Buffer input
    - Zoek knop
    - Inklapbaar en versleepbaar
    """
    layer_options = "\n".join([f'<option value="{l}">{l}</option>' for l in available_layers])

    if available_types is None:
        available_types = [{'key': 'stat', 'label': 'Stat', 'enabled': True}]
    _type_btns = ""
    for _t in available_types:
        _enabled = _t.get("enabled", True)
        _disabled = " disabled" if not _enabled else ""
        _active = " active" if _t["key"] == first_active_type else ""
        _lbl_txt = _t["label"]
        _title = (
            f' title="Niet opgegeven \u2014 voeg een {_lbl_txt}-shapefile toe om te activeren"'
            if not _enabled else ""
        )
        _type_btns += (
            f'<button class="dataset-type-btn{_active}" data-type="{_t["key"]}"'
            f'{_disabled}{_title} onclick="switchDataType(\'{_t["key"]}\')">{_t["label"]}</button>\n            '
        )
    
    return f'''
    <style>
        #control-panel {{
            position: fixed;
            top: 10px;
            left: 60px;
            z-index: 9999;
            background-color: white;
            border: 1px solid #777;
            border-radius: 5px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
            font-family: Arial, sans-serif;
            min-width: 220px;
            max-width: 280px;
        }}
        #control-panel-header {{
            padding: 10px 15px;
            background-color: {HASKONING_COLORS["primary"]};
            color: {HASKONING_COLORS["white"]};
            border-bottom: 1px solid {HASKONING_COLORS["primary"]};
            border-radius: 5px 5px 0 0;
            cursor: move;
            display: flex;
            justify-content: space-between;
            align-items: center;
            user-select: none;
        }}
        #control-panel-header:hover {{
            background-color: #01324f;
        }}
        #control-panel-body {{
            padding: 15px;
            display: block;
        }}
        #control-panel-body.collapsed {{
            display: none;
        }}
        #collapse-btn {{
            background: none;
            border: none;
            font-size: 16px;
            cursor: pointer;
            padding: 0 5px;
            color: {HASKONING_COLORS["white"]};
        }}
        #collapse-btn:hover {{
            color: {THEME_GREEN["highlight"]};
        }}
        .graph-card-highlight {{
            outline: 3px solid #ff6600 !important;
            transition: outline 0.2s;
        }}
        #search-btn:hover {{
            background-color: {THEME_GREEN["highlight"]} !important;
            color: {HASKONING_COLORS["primary"]} !important;
        }}
        .dataset-type-btn {{
            flex: 1;
            padding: 5px 4px;
            font-size: 11px;
            font-weight: 600;
            border: 1px solid {HASKONING_COLORS["primary"]};
            border-radius: 3px;
            cursor: pointer;
            background-color: white;
            color: {HASKONING_COLORS["primary"]};
            transition: all 0.15s;
        }}
        .dataset-type-btn.active {{
            background-color: {HASKONING_COLORS["primary"]};
            color: white;
        }}
        .dataset-type-btn:disabled {{
            background-color: {HASKONING_COLORS["disabled_bg"]};
            color: {HASKONING_COLORS["disabled_text"]};
            border-color: {HASKONING_COLORS["disabled_bg"]};
            cursor: not-allowed;
        }}
        .dataset-type-btn:not(:disabled):hover {{
            background-color: {THEME_GREEN["highlight"]};
            color: {HASKONING_COLORS["primary"]};
        }}
    </style>
    
    <div id="control-panel">
        <div id="control-panel-header">
            <span style="font-weight: 700; font-size: 14px;">GW-Grafieken Raai Tool</span>
            <button id="collapse-btn" onclick="togglePanel()" title="Inklappen/Uitklappen">▼</button>
        </div>
        
        <div id="control-panel-body">
            <div style="margin-bottom: 12px; border-bottom: 1px solid #eee; padding-bottom: 10px;">
                <label style="font-size: 12px; font-weight: 600; display: block; margin-bottom: 5px;">
                    Dataset:
                </label>
                <div style="display: flex; gap: 4px;">
                    {_type_btns}
                </div>
            </div>
            <div style="margin-bottom: 10px;">
                <label style="font-size: 12px; font-weight: 600; display: block; margin-bottom: 4px;">
                    Modellaag:
                </label>
                <select id="model-layer-select" style="width: 100%; padding: 6px; border: 1px solid #ccc; border-radius: 3px; background-color: {HASKONING_COLORS["input_bg"]};">
                    {layer_options}
                </select>
            </div>
            
            <div style="margin-bottom: 10px;">
                <label style="font-size: 12px; font-weight: 600; display: block; margin-bottom: 4px;">
                    Bufferzone (meters):
                </label>
                <input type="number" id="buffer-input" value="500" min="10" max="10000" step="50"
                    style="width: 100%; padding: 6px; border: 1px solid #ccc; border-radius: 3px; box-sizing: border-box; background-color: {HASKONING_COLORS["input_bg"]};">
            </div>
            
            <button id="search-btn" onclick="searchPointsInBuffer()" style="
                width: 100%;
                padding: 10px;
                background-color: {THEME_GREEN["secondary"]};
                color: {HASKONING_COLORS["white"]};
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-weight: 600;
                font-size: 13px;
            ">
                🔍 Zoek Punten
            </button>
            
            <div id="status-message" style="
                margin-top: 10px;
                padding: 8px;
                border-radius: 3px;
                font-size: 12px;
                display: none;
            "></div>
            
            <div style="margin-top: 12px; font-size: 13px; color: #666; border-top: 1px solid #ddd; padding-top: 8px;">
                <b>Instructies:</b><br>
                1. Selecteer dataset<br>
                2. Selecteer modellaag<br>
                3. Teken een lijn (raai) op de kaart<br>
                &nbsp;&nbsp;&nbsp;• Klik = knikpunt<br>
                &nbsp;&nbsp;&nbsp;• Dubbelklik = einde<br>
                4. Voer gewenste bufferzone in<br>
                5. Klik "Zoek Punten"<br>
                <i style="color: #999;">Sleep header om te verplaatsen</i>
            </div>
        </div>
    </div>
    
    <script>
    // Panel toggle functie
    function togglePanel() {{
        var body = document.getElementById('control-panel-body');
        var btn = document.getElementById('collapse-btn');
        if (body.classList.contains('collapsed')) {{
            body.classList.remove('collapsed');
            btn.textContent = '▼';
        }} else {{
            body.classList.add('collapsed');
            btn.textContent = '▶';
        }}
    }}
    
    // Maak panel versleepbaar
    (function makeDraggable() {{
        var panel = document.getElementById('control-panel');
        var header = document.getElementById('control-panel-header');
        if (!panel || !header) {{
            setTimeout(makeDraggable, 100);
            return;
        }}
        
        var isDragging = false;
        var offsetX, offsetY;
        
        header.addEventListener('mousedown', function(e) {{
            if (e.target.id === 'collapse-btn') return;
            isDragging = true;
            offsetX = e.clientX - panel.offsetLeft;
            offsetY = e.clientY - panel.offsetTop;
            panel.style.transition = 'none';
        }});
        
        document.addEventListener('mousemove', function(e) {{
            if (!isDragging) return;
            e.preventDefault();
            var newX = e.clientX - offsetX;
            var newY = e.clientY - offsetY;
            newX = Math.max(0, Math.min(newX, window.innerWidth - panel.offsetWidth));
            newY = Math.max(0, Math.min(newY, window.innerHeight - panel.offsetHeight));
            panel.style.left = newX + 'px';
            panel.style.top = newY + 'px';
        }});
        
        document.addEventListener('mouseup', function() {{
            isDragging = false;
            panel.style.transition = '';
        }});
    }})();
    </script>
    '''

#==========================
# Zijpanelen voor grafieken, hier kunnen de wensen daarvan makkelijk aan worden gepast
#==========================

def _get_side_panels_html() -> str:
    """Genereer HTML voor de zijpanelen waar grafieken worden getoond."""
    return '''
    <!-- Linker paneel voor grafieken -->
    <div id="left-panel" style="
        position: fixed;
        top: 0;
        left: 0;
        width: 560px;
        height: 100vh;
        background-color: #FAF2E3;
        border-right: 2px solid #002E4F;
        overflow-y: auto;
        z-index: 9990;
        display: none;
        padding: 10px;
        box-sizing: border-box;
    ">
        <div style="font-weight: 700; font-size: 13px; margin-bottom: 10px; padding-bottom: 5px; border-bottom: 1px solid #002E4F; color: #002E4F;">
            Grafieken peilbuizen 📊
        </div>
        <div id="left-graphs"></div>
    </div>
    
    <!-- Rechter paneel voor grafieken -->
    <div id="right-panel" style="
        position: fixed;
        top: 0;
        right: 0;
        width: 560px;
        height: 100vh;
        background-color: #FAF2E3;
        border-left: 2px solid #002E4F;
        overflow-y: auto;
        z-index: 9990;
        display: none;
        padding: 10px;
        box-sizing: border-box;
    ">
        <div style="font-weight: 700; font-size: 13px; margin-bottom: 10px; padding-bottom: 5px; border-bottom: 1px solid #002E4F; color: #002E4F;">
            Grafieken peilbuizen 📊
        </div>
        <div id="right-graphs"></div>
    </div>
    
    <!-- Sluit knop voor panelen -->
    <button id="close-panels-btn" onclick="closePanels()" style="
        position: fixed;
        top: 10px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 9995;
        display: none;
        padding: 8px 12px;
        background-color: #F74646;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-weight: 600;
    ">
        ✕ Sluit Grafieken
    </button>
    '''


def _get_main_javascript(points_stat_json: str, points_ghg_json: str, points_glg_json: str, images_json: str, initial_type: str = "stat") -> str:
    """
    Genereer de hoofd JavaScript code voor:
    - Buffer berekening met Turf.js
    - Punten filteren
    - Grafieken weergeven
    - Oude lijn verwijderen bij nieuwe
    - Punten highlighten
    - Afstand langs raai tonen
    """
    return f'''
    <script>
    // ==========================
    // data opzetten
    // ==========================
    
    var allPointsByType = {{
        'stat': {points_stat_json},
        'GHG':  {points_ghg_json},
        'GLG':  {points_glg_json}
    }};
    var currentDataType = '{initial_type}';
    function getCurrentPoints() {{ return allPointsByType[currentDataType]; }}
    var allImages = {images_json};
    
    // Referenties
    var drawnLine = null;
    var leafletMap = null;
    var bufferLayer = null;
    var highlightLayers = [];           // Opslaan van highlight markers
    var highlightMarkersByCardId = {{}};  // Mapping cardId → marker voor hover-highlight
    var hoveredCardId = null;           // Huidig gehighlight grafiek-card
    var lastPointsInBuffer = null;      // Laatste zoekopdracht voor auto-refresh (ongefilterd)
    var currentLine = null;             // Referentie naar de Turf.js lijn voor afstandsberekening
    var colorLayer = null;              // Dynamische gekleurde bollenkaart per modellaag
    var highlightColorsByCardId = {{}};   // Legenda-kleur per cardId voor hover-herstel
    
    // Legenda kleurdata (identiek aan html_map_legend() in Python)
    var legendColorData = [
        [9999999.0, 10.0, 0, 0, 149],
        [10.0, 5.0, 0, 84, 240],
        [5.0, 2.5, 55, 125, 255],
        [2.5, 1.0, 108, 159, 255],
        [1.0, 0.6, 166, 197, 255],
        [0.6, 0.4, 206, 224, 255],
        [0.4, 0.2, 206, 239, 255],
        [0.2, 0.1, 0, 128, 85],
        [0.1, -0.1, 0, 54, 0],
        [-0.1, -0.2, 85, 128, 0],
        [-0.2, -0.4, 255, 230, 203],
        [-0.4, -0.6, 255, 215, 170],
        [-0.6, -1.0, 255, 181, 106],
        [-1.0, -2.5, 255, 148, 40],
        [-2.5, -5.0, 217, 108, 0],
        [-5.0, -10.0, 176, 88, 0],
        [-10.0, -9999999.0, 89, 47, 0]
    ];
    
    function getLegendColor(value) {{
        if (value === null || value === undefined || value === '') return null;
        var v = parseFloat(value);
        if (isNaN(v)) return null;
        for (var i = 0; i < legendColorData.length; i++) {{
            var lo = Math.min(legendColorData[i][0], legendColorData[i][1]);
            var hi = Math.max(legendColorData[i][0], legendColorData[i][1]);
            if (v >= lo && v < hi) {{
                return 'rgb(' + legendColorData[i][2] + ',' + legendColorData[i][3] + ',' + legendColorData[i][4] + ')';
            }}
        }}
        return null;
    }}
    
    function updateAllMarkerColors(modelLayer) {{
        if (!leafletMap) return;
        if (colorLayer) {{
            leafletMap.removeLayer(colorLayer);
            colorLayer = null;
        }}
        colorLayer = L.layerGroup();
        getCurrentPoints().features.forEach(function(feature) {{
            var ml = feature.properties.Modellaag;
            if (ml === undefined || ml === null) return;
            if (parseInt(ml) !== modelLayer) return;
            var coords = feature.geometry.coordinates;
            var diff = feature.properties.Difference;
            var color = getLegendColor(diff);
            if (!color) return;
            var marker = L.circleMarker([coords[1], coords[0]], {{
                radius: 7,
                color: '#333333',
                weight: 1,
                fillColor: color,
                fillOpacity: 0.9
            }});
            var popupLines = [];
            ['Naam', 'X', 'Y', 'Difference', 'Measured', 'Calc'].forEach(function(col) {{
                if (feature.properties[col] !== undefined && feature.properties[col] !== null) {{
                    var val = feature.properties[col];
                    if (['Difference', 'Measured', 'Calc'].indexOf(col) > -1) {{
                        var num = parseFloat(val);
                        if (!isNaN(num)) val = num.toFixed(2);
                    }}
                    if (['X', 'Y'].indexOf(col) > -1) {{
                        var num = parseFloat(val);
                        if (!isNaN(num)) val = Math.round(num);
                    }}
                    popupLines.push('<b>' + col + '</b>: ' + val);
                }}
            }});
            marker.bindPopup(popupLines.join('<br>'), {{maxWidth: 250}});
            colorLayer.addLayer(marker);
        }});
        colorLayer.addTo(leafletMap);
    }}
    
    // ==========================
    // filter functie op modellaag
    // ==========================
    
    function filterPointsByLayer(points, modelLayer) {{
        return points.filter(function(feature) {{
            var ml = feature.properties.Modellaag;
            if (ml === undefined || ml === null) return true;
            return parseInt(ml) === modelLayer;
        }});
    }}
    
    // ==========================
    // dataset wissel tussen GHG, GLG en Stat
    // ==========================
    
    function switchDataType(type) {{
        currentDataType = type;
        updateDataTypeBtns(type);
        var sel = document.getElementById('model-layer-select');
        var modelLayer = sel ? parseInt(sel.value) : 1;
        updateAllMarkerColors(modelLayer);
        // Reset zoekresultaten: gebruiker moet opnieuw op "Zoek Punten" klikken
        lastPointsInBuffer = null;
        clearHighlights();
        closePanels();
        if (drawnLine) {{
            showStatus('Dataset gewijzigd naar "' + type + '". Klik op "Zoek Punten" om de grafieken te laden.', 'info');
        }}
    }}
    
    function updateDataTypeBtns(activeType) {{
        var btns = document.querySelectorAll('.dataset-type-btn');
        btns.forEach(function(btn) {{
            if (btn.dataset.type === activeType) {{
                btn.classList.add('active');
            }} else {{
                btn.classList.remove('active');
            }}
        }});
    }}
    
    // Werk de dropdown bij: toon checkmark bij lagen die grafieken hebben voor gevonden punten
    function updateLayerDropdown(pointsInBuffer) {{
        var select = document.getElementById('model-layer-select');
        if (!select) return;
        Array.from(select.options).forEach(function(option) {{
            var layerVal = parseInt(option.value);
            if (!pointsInBuffer || pointsInBuffer.length === 0) {{
                option.text = String(layerVal);
                return;
            }}
            var layerPoints = filterPointsByLayer(pointsInBuffer, layerVal);
            var layerImages = allImages[layerVal] || {{}};
            var hasGraphs = layerPoints.some(function(point) {{
                var naam = point.properties.Naam || point.properties.naam || '';
                return Object.keys(layerImages).some(function(filename) {{
                    return filename === naam || filename.indexOf(naam + '_') === 0;
                }});
            }});
            option.text = hasGraphs ? '\u2713 ' + layerVal : String(layerVal);
        }});
    }}
    
    // ==========================
    // initialiseer draw events
    // ==========================
    
    (function initDrawEvents() {{
        function tryInit() {{
            for (var key in window) {{
                if (window[key] instanceof L.Map) {{
                    leafletMap = window[key];
                    break;
                }}
            }}
            
            if (!leafletMap) {{
                setTimeout(tryInit, 500);
                return;
            }}
            
            console.log('Leaflet map gevonden, events koppelen...');
            
            // Luister naar draw:created event
            leafletMap.on('draw:created', function(e) {{
                // Verwijder oude lijn als die bestaat
                if (drawnLine && typeof drawnItems !== 'undefined') {{
                    drawnItems.removeLayer(drawnLine);
                }}
                // Verwijder ook oude buffer en highlights
                clearHighlights();
                if (bufferLayer) {{
                    leafletMap.removeLayer(bufferLayer);
                    bufferLayer = null;
                }}
                
                lastPointsInBuffer = null;
                drawnLine = e.layer;
                showStatus('Lijn getekend! Klik op "Zoek Punten" om te zoeken.', 'info');
            }});
            
            leafletMap.on('draw:deleted', function(e) {{
                drawnLine = null;
                clearHighlights();
                if (bufferLayer) {{
                    leafletMap.removeLayer(bufferLayer);
                    bufferLayer = null;
                }}
                lastPointsInBuffer = null;
                updateLayerDropdown(null);
                closePanels();
                showStatus('Lijn verwijderd.', 'info');
            }});
            
            leafletMap.on('draw:edited', function(e) {{
                e.layers.eachLayer(function(layer) {{
                    if (layer instanceof L.Polyline) {{
                        drawnLine = layer;
                    }}
                }});
                showStatus('Lijn bewerkt! Klik op "Zoek Punten" om opnieuw te zoeken.', 'info');
            }});
            
            // Kleuren markers bij initialisatie op basis van geselecteerde modellaag
            setTimeout(function() {{
                var sel = document.getElementById('model-layer-select');
                if (sel) updateAllMarkerColors(parseInt(sel.value));
            }}, 300);
            
            // Koppel colorLayer en highlights aan Peilbuizen laag-toggle
            leafletMap.on('overlayadd', function(e) {{
                if (e.name === 'Peilbuizen') {{
                    var sel = document.getElementById('model-layer-select');
                    if (sel) updateAllMarkerColors(parseInt(sel.value));
                }}
            }});
            leafletMap.on('overlayremove', function(e) {{
                if (e.name === 'Peilbuizen') {{
                    if (colorLayer && leafletMap) {{
                        leafletMap.removeLayer(colorLayer);
                        colorLayer = null;
                    }}
                    clearHighlights();
                }}
            }});
        }}
        
        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', tryInit);
        }} else {{
            tryInit();
        }}
    }})();
    
    // Registreer auto-update bij modellaag wissel
    (function initLayerChangeListener() {{
        function tryRegister() {{
            var layerSelect = document.getElementById('model-layer-select');
            if (!layerSelect) {{
                setTimeout(tryRegister, 100);
                return;
            }}
            layerSelect.addEventListener('change', function() {{
                var modelLayer = parseInt(this.value);
                updateAllMarkerColors(modelLayer);
                if (lastPointsInBuffer && lastPointsInBuffer.length > 0) {{
                    var filtered = filterPointsByLayer(lastPointsInBuffer, modelLayer);
                    highlightPoints(filtered);
                    displayGraphs(filtered, modelLayer);
                }}
            }});
        }}
        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', tryRegister);
        }} else {{
            tryRegister();
        }}
    }})();
    
    // ==========================
    // highlight functies voor gevonden punten
    // ==========================
    
    function clearHighlights() {{
        highlightLayers.forEach(function(layer) {{
            if (leafletMap) leafletMap.removeLayer(layer);
        }});
        highlightLayers = [];
        highlightMarkersByCardId = {{}};
        highlightColorsByCardId = {{}};
        hoveredCardId = null;
    }}
    
    function highlightPoints(points) {{
        clearHighlights();
        
        points.forEach(function(point) {{
            var coords = point.geometry.coordinates;
            var props = point.properties;
            var naam = props.Naam || props.naam || 'Onbekend';
            var cardId = 'graph-card-' + naam.replace(/[^a-zA-Z0-9]/g, '_');
            
            var legendFill = getLegendColor(props.Difference) || '#888888';
            var marker = L.circleMarker([coords[1], coords[0]], {{
                radius: 9,
                color: '#333333',
                weight: 3,
                fillColor: legendFill,
                fillOpacity: 0.9
            }});
            highlightMarkersByCardId[cardId] = marker;
            highlightColorsByCardId[cardId] = legendFill;
            
            // Popup opbouwen met puntinformatie
            var popupLines = [];
            ['Naam', 'X', 'Y', 'Difference', 'Measured', 'Calc'].forEach(function(col) {{
                if (props[col] !== undefined && props[col] !== null) {{
                    var val = props[col];
                    if (['Difference', 'Measured', 'Calc'].indexOf(col) > -1) {{
                        var num = parseFloat(val);
                        if (!isNaN(num)) val = num.toFixed(2);
                    }}
                    if (['X', 'Y'].indexOf(col) > -1) {{
                        var num = parseFloat(val);
                        if (!isNaN(num)) val = Math.round(num);
                    }}
                    popupLines.push('<b>' + col + '</b>: ' + val);
                }}
            }});
            marker.bindPopup(popupLines.join('<br>'), {{maxWidth: 250}});
            
            // Klik: toon popup + highlight punt geel/rood + scroll naar grafiek
            (function(n, cid) {{
                marker.on('click', function() {{
                    marker.openPopup();
                    showHoverHighlight(cid);
                    scrollToGraph(n);
                }});
            }})(naam, cardId);
            
            marker.addTo(leafletMap);
            highlightLayers.push(marker);
        }});
    }}
    
    // ==========================
    // hover highlight en grafiek koppeling
    // ==========================
    
    function showHoverHighlight(cardId) {{
        hideHoverHighlight();
        var marker = highlightMarkersByCardId[cardId];
        if (!marker) return;
        var legendFill = highlightColorsByCardId[cardId] || '#888888';
        marker.setStyle({{ color: '#FFD700', weight: 5, fillColor: legendFill, fillOpacity: 0.95 }});
        hoveredCardId = cardId;
    }}
    
    function hideHoverHighlight() {{
        if (!hoveredCardId) return;
        var marker = highlightMarkersByCardId[hoveredCardId];
        if (marker) {{
            var legendFill = highlightColorsByCardId[hoveredCardId] || '#888888';
            marker.setStyle({{ color: '#333333', weight: 3, fillColor: legendFill, fillOpacity: 0.9 }});
        }}
        hoveredCardId = null;
    }}
    
    function scrollToGraph(naam) {{
        var cardId = 'graph-card-' + naam.replace(/[^a-zA-Z0-9]/g, '_');
        var card = document.getElementById(cardId);
        if (!card) return;
        card.scrollIntoView({{behavior: 'smooth', block: 'center'}});
        card.classList.add('graph-card-highlight');
        setTimeout(function() {{
            card.classList.remove('graph-card-highlight');
        }}, 2000);
    }}
    
    // ==========================
    // buffer & zoek functie
    // ==========================
    
    function searchPointsInBuffer() {{
        var lineCoords = getDrawnLineCoordinates();
        
        if (!lineCoords || lineCoords.length < 2) {{
            showStatus('Teken eerst een lijn (raai) op de kaart! Gebruik de tekentools links.', 'error');
            return;
        }}
        
        var bufferMeters = parseFloat(document.getElementById('buffer-input').value);
        if (isNaN(bufferMeters) || bufferMeters < 10) {{
            showStatus('Voer een geldige bufferzone in (min. 10 meter)', 'error');
            return;
        }}
        
        var modelLayer = parseInt(document.getElementById('model-layer-select').value);
        
        // Maak een Turf.js lijn
        var line = turf.lineString(lineCoords);
        currentLine = line;  // Bewaar voor afstandsberekening
        
        // Maak een buffer rond de lijn
        var bufferKm = bufferMeters / 1000;
        var buffered = turf.buffer(line, bufferKm, {{units: 'kilometers'}});
        
        showBufferOnMap(buffered);
        
        // Filter punten binnen de buffer
        var pointsInBuffer = [];
        
        var lineStartPoint = turf.point(lineCoords[0]);  // Eerste punt van de raai
        getCurrentPoints().features.forEach(function(feature) {{
            var point = turf.point(feature.geometry.coordinates);
            if (turf.booleanPointInPolygon(point, buffered)) {{
                // Bereken afstand tot het eerste punt van de raai
                var distance = turf.distance(lineStartPoint, point, {{ units: 'meters' }});
                feature.properties._distanceAlongLine = distance; 
                pointsInBuffer.push(feature);
            }}
        }});
        
        console.log('Gevonden punten (alle lagen):', pointsInBuffer.length);
        
        // Sorteer punten op afstand langs de lijn
        pointsInBuffer.sort(function(a, b) {{
            return a.properties._distanceAlongLine - b.properties._distanceAlongLine;
        }});
        
        // Bewaar ongefilterd resultaat voor auto-refresh bij modellaag wissel
        lastPointsInBuffer = pointsInBuffer;
        
        // Werk dropdown bij met indicatie welke lagen grafieken hebben
        updateLayerDropdown(pointsInBuffer);
        
        // Filter op geselecteerde modellaag via Modellaag-kolom
        
        // Filter op geselecteerde modellaag via Modellaag-kolom
        var displayPoints = filterPointsByLayer(pointsInBuffer, modelLayer);
        
        if (displayPoints.length === 0) {{
            showStatus('Geen peilbuizen gevonden binnen de bufferzone voor modellaag ' + modelLayer + '.', 'warning');
            clearHighlights();
            closePanels();
            return;
        }}
        
        if (displayPoints.length > 12) {{
            showStatus('Te veel peilbuizen gevonden (' + displayPoints.length + '). Verklein de bufferzone of teken een kortere raai. Max = 12.', 'error');
            clearHighlights();
            closePanels();
            return;
        }}
        
        // Highlight de gevonden punten
        highlightPoints(displayPoints);
        
        showStatus('Gevonden: ' + displayPoints.length + ' peilbuizen voor laag ' + modelLayer + '. Grafieken worden geladen...', 'success');
        
        displayGraphs(displayPoints, modelLayer);
    }}
    
    function showBufferOnMap(bufferedPolygon) {{
        if (bufferLayer && leafletMap) {{
            leafletMap.removeLayer(bufferLayer);
        }}
        
        if (leafletMap) {{
            bufferLayer = L.geoJSON(bufferedPolygon, {{
                style: {{
                    color: '#ff7800',
                    weight: 2,
                    opacity: 0.8,
                    fillColor: '#ff7800',
                    fillOpacity: 0.15
                }}
            }}).addTo(leafletMap);
        }}
    }}
    
    function getDrawnLineCoordinates() {{
        var coords = [];
        
        if (drawnLine && drawnLine instanceof L.Polyline) {{
            var latLngs = drawnLine.getLatLngs();
            if (latLngs.length > 0 && Array.isArray(latLngs[0])) {{
                latLngs = latLngs[0];
            }}
            latLngs.forEach(function(ll) {{
                coords.push([ll.lng, ll.lat]);
            }});
        }}
        
        if (coords.length === 0 && typeof drawnItems !== 'undefined') {{
            drawnItems.eachLayer(function(layer) {{
                if (layer instanceof L.Polyline && !(layer instanceof L.Polygon)) {{
                    var latLngs = layer.getLatLngs();
                    if (latLngs.length > 0 && Array.isArray(latLngs[0])) {{
                        latLngs = latLngs[0];
                    }}
                    latLngs.forEach(function(ll) {{
                        coords.push([ll.lng, ll.lat]);
                    }});
                }}
            }});
        }}
        
        return coords.length >= 2 ? coords : null;
    }}
    
    // ==========================
    // Weergave van grafieken in zijpanelen
    // ==========================
    
    function displayGraphs(points, modelLayer) {{
        var leftGraphs = document.getElementById('left-graphs');
        var rightGraphs = document.getElementById('right-graphs');
        var leftPanel = document.getElementById('left-panel');
        var rightPanel = document.getElementById('right-panel');
        var closeBtn = document.getElementById('close-panels-btn');
        
        leftGraphs.innerHTML = '';
        rightGraphs.innerHTML = '';
        
        var layerImages = allImages[modelLayer] || {{}};
        
        // Verdeel punten: eerste helft links, tweede helft rechts
        var half = Math.ceil(points.length / 2);
        var leftPoints = points.slice(0, half);
        var rightPoints = points.slice(half);
        
        leftPoints.forEach(function(point) {{
            var graphHtml = createGraphElement(point, layerImages, modelLayer);
            leftGraphs.innerHTML += graphHtml;
        }});
        
        rightPoints.forEach(function(point) {{
            var graphHtml = createGraphElement(point, layerImages, modelLayer);
            rightGraphs.innerHTML += graphHtml;
        }});
        
        leftPanel.style.display = 'block';
        if (rightPoints.length > 0) {{
            rightPanel.style.display = 'block';
        }}
        closeBtn.style.display = 'block';
        
        adjustMapMargins(true);
    }}
    
    function createGraphElement(point, layerImages, modelLayer) {{
        var props = point.properties;
        var naam = props.Naam || props.naam || 'Onbekend';
        var distance = props._distanceAlongLine || 0;
        var distanceStr = distance.toFixed(0) + ' m';

        var cardId = 'graph-card-' + naam.replace(/[^a-zA-Z0-9]/g, '_');

    // Zoek alle grafieken waarvan de bestandsnaam bij deze peilbuis hoort.
    // Geen gedoe met filternummers: de bestandsnaam wordt exact getoond zoals die in layerImages staat.
    var matchedImages = Object.keys(layerImages)
        .filter(function(filename) {{
            return filename === naam || filename.indexOf(naam + '_') === 0;
        }})
        .sort()
        .map(function(filename) {{
            return {{
                filename: filename,
                imageData: layerImages[filename]
            }};
        }});

    var html = '';

    if (matchedImages.length === 0) {{
        html += '<div id="' + cardId + '" data-card-id="' + cardId + '" '
            + 'onmouseenter="showHoverHighlight(this.dataset.cardId)" '
            + 'onmouseleave="hideHoverHighlight()" '
            + 'style="margin-bottom: 15px; background: white; border: 1px solid #ddd; border-radius: 4px; padding: 8px; cursor: pointer;">';

        html += '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">';
        html += '<span style="font-weight: 600; font-size: 12px; color: #333;">' + naam + '</span>';
        html += '<span style="font-size: 12px; color: #0066cc; background: #e6f2ff; padding: 2px 6px; border-radius: 3px;">📍 ' + distanceStr + '</span>';
        html += '</div>';

        html += '<div style="padding: 20px; background: #f0f0f0; text-align: center; color: #666; font-size: 11px; border-radius: 3px;">';
        html += 'Geen grafiek beschikbaar<br>voor laag ' + modelLayer;
        html += '</div>';

        html += '</div>';

        return html;
    }}

    matchedImages.forEach(function(match, idx) {{
        var subCardId = idx === 0 ? cardId : cardId + '_' + idx;

        html += '<div id="' + subCardId + '" data-card-id="' + cardId + '" '
            + 'onmouseenter="showHoverHighlight(this.dataset.cardId)" '
            + 'onmouseleave="hideHoverHighlight()" '
            + 'style="margin-bottom: 15px; background: white; border: 1px solid #ddd; border-radius: 4px; padding: 8px; cursor: pointer;">';

        html += '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">';

        // Hier wordt gewoon de bestandsnaam/key getoond.
        html += '<span style="font-weight: 600; font-size: 12px; color: #333;">' + match.filename + '</span>';

        html += '<span style="font-size: 12px; color: #0066cc; background: #e6f2ff; padding: 2px 6px; border-radius: 3px;">📍 ' + distanceStr + '</span>';
        html += '</div>';

        html += '<img src="data:image/png;base64,' + match.imageData + '" style="width: 100%; height: auto; border-radius: 3px;">';

        if (props.Difference !== undefined) {{
            var diff = parseFloat(props.Difference);
            if (!isNaN(diff)) {{
                html += '<div style="font-size: 12px; color: #666; margin-top: 4px;">Verschil: ' + diff.toFixed(2) + ' m</div>';
            }}
        }}

        html += '</div>';
    }});

    return html;
    }}
  
    function closePanels() {{
        document.getElementById('left-panel').style.display = 'none';
        document.getElementById('right-panel').style.display = 'none';
        document.getElementById('close-panels-btn').style.display = 'none';
        adjustMapMargins(false);
    }}
    
    function adjustMapMargins(showPanels) {{
        var mapContainer = document.querySelector('.folium-map');
        if (mapContainer) {{
            if (showPanels) {{
                mapContainer.style.marginLeft = '340px';
                mapContainer.style.marginRight = '340px';
                mapContainer.style.width = 'calc(100% - 680px)';
            }} else {{
                mapContainer.style.marginLeft = '0';
                mapContainer.style.marginRight = '0';
                mapContainer.style.width = '100%';
            }}
            setTimeout(function() {{
                window.dispatchEvent(new Event('resize'));
            }}, 100);
        }}
    }}
    
    // ==========================
    // STATUS BERICHTEN
    // ==========================
    
    function showStatus(message, type) {{
        var statusDiv = document.getElementById('status-message');
        statusDiv.style.display = 'block';
        statusDiv.textContent = message;
        
        switch(type) {{
            case 'error':
                statusDiv.style.backgroundColor = '{ALARM_COLORS["critical"]}';
                statusDiv.style.color = '#ffffff';
                statusDiv.style.border = '1px solid {ALARM_COLORS["critical"]}';
                break;
            case 'warning':
                statusDiv.style.backgroundColor = '{ALARM_COLORS["medium"]}';
                statusDiv.style.color = '{HASKONING_COLORS["primary"]}';
                statusDiv.style.border = '1px solid {ALARM_COLORS["high"]}';
                break;
            case 'success':
                statusDiv.style.backgroundColor = '{THEME_GREEN["highlight"]}';
                statusDiv.style.color = '{HASKONING_COLORS["primary"]}';
                statusDiv.style.border = '1px solid {THEME_GREEN["secondary"]}';
                break;
            case 'info':
            default:
                statusDiv.style.backgroundColor = '{ALARM_COLORS["low_optional"]}';
                statusDiv.style.color = '{HASKONING_COLORS["primary"]}';
                statusDiv.style.border = '1px solid {ALARM_COLORS["low"]}';
                break;
        }}
    }}
    
    </script>
    '''
def _get_ui_tweaks_html() -> str:
    """CSS en JS voor grotere toolbar-knoppen, verbergen edit-knop, directe prullenbak en grotere legenda/lagenknop."""
    return '''
    <style>
        .leaflet-draw-draw-polyline {
            width: 50px !important;
            height: 50px !important;
            background-size: 350px 50px !important;
            background-position: 7px center !important;
        }

        .leaflet-draw-edit-remove {
            width: 50px !important;
            height: 50px !important;
            background-size: 350px 50px !important;
            background-position: -272px center !important;
        }
        /* Grotere zoom knoppen */
        .leaflet-control-zoom a {
            width: 50px !important;
            height: 50px !important;
            line-height: 50px !important;
            font-size: 22px !important;
        }
        /* Grotere layer control toggle (rechtsboven) */
        .leaflet-control-layers-toggle {
            width: 50px !important;
            height: 50px !important;
            line-height: 50px !important;
        }
        /* Grotere font in lagen dropdown */
        .leaflet-control-layers label,
        .leaflet-control-layers span {
            font-size: 18px !important;
        }
        /* Verberg edit layers knop */
        .leaflet-draw-edit-edit {
            display: none !important;
        }
        /* Grotere legenda-knop (rechtsonder) */
        #legend-toggle {
            padding: 12px 16px !important;
            font-size: 20px !important;
            text-align: center !important;
        }
        #legend-toggle:hover {
            background-color: #BDDECC !important;
        }
    </style>
    
    <script>
    // Prullenbak knop betekent direct verwijderen

    (function initDirectDelete() {
        function attachDeleteHandler() {
            var deleteBtn = document.querySelector('.leaflet-draw-edit-remove');
            if (!deleteBtn) {
                setTimeout(attachDeleteHandler, 300);
                return;
            }
            deleteBtn.addEventListener('click', function(e) {
                e.stopImmediatePropagation();
                e.preventDefault();
                if (typeof drawnItems !== 'undefined') {
                    drawnItems.clearLayers();
                }
                drawnLine = null;
                clearHighlights();
                if (bufferLayer && leafletMap) {
                    leafletMap.removeLayer(bufferLayer);
                    bufferLayer = null;
                }
                lastPointsInBuffer = null;
                if (typeof updateLayerDropdown === 'function') updateLayerDropdown(null);
                closePanels();
                showStatus('Lijn verwijderd.', 'info');
            }, true);
        }
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', attachDeleteHandler);
        } else {
            attachDeleteHandler();
        }
    })();
    </script>
    '''

# ==========================
# Hoofdfunctie, het genereren van de interactieve kaart met raai-selectie functionaliteit
# ==========================


# Definieren van de hoofdfunctie die de interactieve kaart maakt 
def create_raai_selection_map(
    points_path: str = None,
    png_base_path: str = None,
    model_layers: List[int] = None,
    background_layers: Optional[List[Dict]] = None,
    provinces_path: str = None,
    water_path: str = None,
    pumping_path: str = None,
    points_ghg_path: str = None,
    points_glg_path: str = None,
) -> folium.Map:
    """
    Maak een interactieve kaart met raai-selectie functionaliteit.

    Minstens één van de drie shapefiles (points_path / GHG / GLG) moet worden opgegeven.
    Ontbrekende datasets worden overgeslagen; de eerste beschikbare wordt als primaire
    basis voor kaartcentrering en markers gebruikt.

    Args:
        background_layers: Optionele lijst van achtergrondlagen, elk als dict met
            keys 'path' (str), 'name' (str) en 'color' (str, bijv. '#2c7fb8').
            Als None wordt teruggevallen op provinces_path/water_path/pumping_path.
    """
    if model_layers is None:
        model_layers = list(range(1, 25))

    png_base = Path(png_base_path) if png_base_path else Path()

    # Laad alle drie datasets; elk is optioneel maar minstens één is vereist
    _dataset_specs = [
        ("stat", points_path,     "Stat (GG)"),
        ("GHG",  points_ghg_path, "GHG"),
        ("GLG",  points_glg_path, "GLG"),
    ]
    _loaded: Dict[str, object] = {}
    for _key, _path, _lbl in _dataset_specs:
        if not _path or not str(_path).strip():
            continue
        try:
            _gdf = _to_map_crs(_read_layer(_path))
            _loaded[_key] = _gdf
            print(f"Geladen: {len(_gdf)} peilbuizen ({_lbl})")
        except Exception as _exc:
            print(f"\u26a0 {_lbl} kon niet worden geladen: {_exc}")

    if not _loaded:
        raise ValueError(
            "Geen van de opgegeven shapefiles (Stat/GHG/GLG) kon worden geladen. "
            "Controleer of minstens \u00e9\u00e9n geldig pad is ingesteld."
        )

    points_stat = _loaded.get("stat")
    points_ghg  = _loaded.get("GHG")
    points_glg  = _loaded.get("GLG")

    # Eerste beschikbare dataset als primaire basis voor kaartcentrering en markers
    primary_points = next(p for p in [points_stat, points_ghg, points_glg] if p is not None)

    # Bepaal welke dataset-knoppen ingeschakeld zijn
    available_types = [
        {'key': 'stat', 'label': 'Stat', 'enabled': points_stat is not None},
        {'key': 'GHG',  'label': 'GHG',  'enabled': points_ghg is not None},
        {'key': 'GLG',  'label': 'GLG',  'enabled': points_glg is not None},
    ]

    # Bouw achtergrondlagen op: gebruik background_layers als opgegeven, anders fallback
    if background_layers is None:
        _fallbacks = [
            (provinces_path, "Provincies",    "#1f4e79"),
            (water_path,     "Waterwegen",    "#2c7fb8"),
            (pumping_path,   "Onttrekkingen", "#8c2d04"),
        ]
        background_layers = [
            {"path": p, "name": n, "color": c}
            for p, n, c in _fallbacks if p
        ]

    print("Afbeeldingen laden...")
    all_images = _collect_all_images_for_layers(png_base, model_layers)
    total_images = sum(len(imgs) for imgs in all_images.values())
    print(f"Geladen: {total_images} afbeeldingen voor {len(model_layers)} modellagen")
    
    available_layers = [l for l in model_layers if all_images.get(l)]
    if not available_layers:
        print("Waarschuwing: Geen afbeeldingen gevonden in de opgegeven modellagen!")
        available_layers = model_layers
    
    bounds = primary_points.total_bounds
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2
    
    fmap = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=10,
        tiles="OpenStreetMap",
        width="100%",
        height="720px",
    )
    # Zet ook de hoogte van de onderliggende Figure vast: zonder dit gebruikt folium in
    # Jupyter een responsive padding-bottom-truc die de kaart (en de branded topbar/
    # panelen die er bovenop liggen) scheef of afgeknot laat renderen bij inline weergave.
    fmap.get_root().width = "100%"
    fmap.get_root().height = "720px"
    
    # Voeg achtergrondlagen toe
    for layer_def in background_layers:
        try:
            gdf = _to_map_crs(_read_layer(layer_def.get("path")))
        except Exception as _exc:
            _bg_name = layer_def.get("name") or Path(layer_def.get("path", "?")).stem
            print(f"\u26a0 Achtergrondlaag '{_bg_name}' overgeslagen: {_exc}")
            continue
        if gdf is None:
            continue
        name  = layer_def.get("name") or Path(layer_def.get("path", "onbekend")).stem
        color = layer_def.get("color", "#555555")
        weight = layer_def.get("weight", 2)
        _layer_to_geojson(
            gdf,
            name,
            style={"color": color, "weight": weight, "fillOpacity": 0.1},
            tooltip_fields=_pick_tooltip_fields(gdf),
        ).add_to(fmap)

    # Voeg peilbuispunten toe (op basis van eerste beschikbare dataset)
    fg = folium.FeatureGroup(name="Peilbuizen", show=True)

    for _, row in primary_points.iterrows():
        geom = row.geometry
        if geom is None:
            continue
        
        color = "#888888"  # Grijs; dynamisch ingekleurd per modellaag via JavaScript
           
        folium.CircleMarker(
            location=[geom.y, geom.x],
            radius=5,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
        ).add_to(fg)
    
    fg.add_to(fmap)
    
    # Voeg Draw plugin toe
    draw = Draw(
        draw_options={
            'polyline': {
                'shapeOptions': {
                    'color': '#ff0000',
                    'weight': 3,
                },
                'metric': True,
            },
            'polygon': False,
            'rectangle': False,
            'circle': False,
            'marker': False,
            'circlemarker': False,
        },
        edit_options={
            'edit': True,
            'remove': True,
        },
    )
    draw.add_to(fmap)
    
    folium.LayerControl().add_to(fmap)
    
    # Eerste beschikbare dataset als JSON-fallback voor ontbrekende datasets
    _primary_json = json.dumps(primary_points.__geo_interface__)
    points_stat_json = json.dumps(points_stat.__geo_interface__) if points_stat is not None else _primary_json
    points_ghg_json  = json.dumps(points_ghg.__geo_interface__)  if points_ghg is not None else _primary_json
    points_glg_json  = json.dumps(points_glg.__geo_interface__)  if points_glg is not None else _primary_json
    images_json = json.dumps(all_images)

    _first_active_type = next(
        (t["key"] for t in available_types if t.get("enabled", True)), "stat"
    )

    html_elements = []
    html_elements.append(_get_turf_js_cdn())
    html_elements.append(_branding_header_html(
        title=TOOL_TITLE,
        subtitle="Seppe-Schijf grondwatertool",
        fixed=True,
    ))
    html_elements.append(_get_topbar_offset_css())
    html_elements.append(_get_control_panel_html(available_layers, available_types, _first_active_type))
    html_elements.append(_get_side_panels_html())
    html_elements.append(_get_legend_html())  # Legenda toggle
    html_elements.append(_get_main_javascript(points_stat_json, points_ghg_json, points_glg_json, images_json, _first_active_type))
    html_elements.append(_get_ui_tweaks_html())
    
    for elem in html_elements:
        fmap.get_root().html.add_child(folium.Element(elem))
    
    return fmap


# ==========================
# Code voor het uitvoeren van de Jupyter notebook met widgets 
# ==========================

def setup_widgets(base_dir):
    """
    Maak en toon alle Jupyter-widgets voor de tool-configuratie.

    Roept deze functie aan vanuit de Jupyter-notebook om de widgets
    voor paden en achtergrondlagen te tonen.

    Returns:
        (shp_w, png_w, html_w, bg_rows, ghg_w, glg_w)
    """
    import ipywidgets as w
    from IPython.display import display
    import tkinter as tk
    from tkinter import filedialog

    base_dir = Path(base_dir)

    def _browse_to(widget, mode, **kw):
        def _handler(_):
            r = tk.Tk(); r.withdraw(); r.attributes("-topmost", True)
            fn = {"file": filedialog.askopenfilename,
                  "dir":  filedialog.askdirectory,
                  "save": filedialog.asksaveasfilename}[mode]
            p = fn(**kw); r.destroy()
            if p: widget.value = p
        return _handler

    # Alle pad-velden delen dezelfde breedte, label-breedte en (via de hsk-input class) dezelfde
    # Haskoning-styling (achtergrond/rand), zodat ze er overal in de tool uniform uitzien.
    _W = dict(style={"description_width": "180px"},
              layout=w.Layout(width="540px", margin="3px 0"))
    _B = dict(layout=w.Layout(width="130px", margin="3px 0"))

    shp_w  = w.Text(value=str(base_dir / "input/01_bollenkaart_shp/bollenkaart_stat.shp"),
                    description="Shapefile (GG):", **_W)
    ghg_w  = w.Text(value=str(base_dir / "input/01_bollenkaart_shp/bollenkaart_GHG.shp"),
                    description="Shapefile (GHG):", **_W)
    glg_w  = w.Text(value=str(base_dir / "input/01_bollenkaart_shp/bollenkaart_GLG.shp"),
                    description="Shapefile (GLG):", **_W)
    png_w  = w.Text(value=str(base_dir / "input/02_grafieken_png"),
                    description="Map met grafieken:", **_W)
    html_w = w.Text(value=str(base_dir / "output/Teken_raaitool.html"),
                    description="Locatie output:", **_W)

    for widget in (shp_w, ghg_w, glg_w, png_w, html_w):
        widget.add_class("hsk-input")

    for widget, mode, kw in [
        (shp_w,  "file", dict(title="Selecteer shapefile (GG)", filetypes=[("Shapefile", "*.shp")],
                              initialdir=str(base_dir / "input/01_bollenkaart_shp"))),
        (ghg_w,  "file", dict(title="Selecteer shapefile (GHG)", filetypes=[("Shapefile", "*.shp")],
                              initialdir=str(base_dir / "input/01_bollenkaart_shp"))),
        (glg_w,  "file", dict(title="Selecteer shapefile (GLG)", filetypes=[("Shapefile", "*.shp")],
                              initialdir=str(base_dir / "input/01_bollenkaart_shp"))),
        (png_w,  "dir",  dict(title="Selecteer grafiekenmap", initialdir=str(base_dir / "input"))),
        (html_w, "save", dict(title="Selecteer locatie voor HTML output", filetypes=[("HTML", "*.html")],
                              defaultextension=".html", initialdir=str(base_dir / "output"))),
    ]:
        btn = w.Button(description="📂 Bladeren...", **_B)
        btn.add_class("hsk-btn-secondary")
        btn.on_click(_browse_to(widget, mode, **kw))
        display(w.HBox([widget, btn], layout=w.Layout(margin="2px 0")))

    # --- Dynamische achtergrondlagen ---
    bg_rows = []
    layers_vbox = w.VBox([])

    def _refresh():
        layers_vbox.children = tuple(row["box"] for row in bg_rows)

    def _remove(row_dict):
        def _handler(_):
            bg_rows.remove(row_dict)
            _refresh()
        return _handler

    def _add_layer(path="", name=""):
        # Zelfde hsk-input styling als de pad-velden hierboven, voor een uniform beeld.
        path_w  = w.Text(value=path, placeholder="Pad naar shapefile...",
                         layout=w.Layout(width="370px", margin="2px 4px 2px 0"))
        name_w  = w.Text(value=name, placeholder="Laagnaam...",
                         layout=w.Layout(width="160px", margin="2px 4px 2px 0"))
        path_w.add_class("hsk-input")
        name_w.add_class("hsk-input")
        browse_btn = w.Button(description="📂", tooltip="Bladeren naar shapefile",
                              layout=w.Layout(width="50px", margin="2px 4px 2px 0"))
        browse_btn.add_class("hsk-btn-secondary")
        remove_btn = w.Button(description="✕", tooltip="Verwijder laag",
                              button_style="danger", layout=w.Layout(width="40px", margin="2px 0"))

        row_dict = {"path_w": path_w, "name_w": name_w}

        def _browse_layer(_):
            r = tk.Tk(); r.withdraw(); r.attributes("-topmost", True)
            p = filedialog.askopenfilename(
                title="Selecteer achtergrond shapefile",
                filetypes=[("Shapefile", "*.shp")],
                initialdir=str(base_dir / "input"))
            r.destroy()
            if p:
                path_w.value = p
                if not name_w.value:
                    name_w.value = Path(p).stem

        browse_btn.on_click(_browse_layer)
        remove_btn.on_click(_remove(row_dict))
        row_box = w.HBox([path_w, browse_btn, name_w, remove_btn],
                         layout=w.Layout(margin="2px 0"))
        row_dict["box"] = row_box
        bg_rows.append(row_dict)
        _refresh()

    # Standaard achtergrondlagen voorinvullen
    _add_layer(str(base_dir / "input/00_achtergrond_shp/Provincies/NL/provincie2010.shp"),
               "Provincies")
    _add_layer(str(base_dir / "input/00_achtergrond_shp/Waterlopen/waterwegen_nedeland.shp"),
               "Waterwegen")
    _add_layer(str(base_dir / "input/00_achtergrond_shp/Onttrekkingen/ontrekkingen.shp"),
               "Onttrekkingen")

    add_btn = w.Button(description="➕ Voeg achtergrondlaag toe",
                       layout=w.Layout(width="240px", margin="6px 0 0 0"))
    add_btn.add_class("hsk-btn-secondary")

    def _add_new(_):
        r = tk.Tk(); r.withdraw(); r.attributes("-topmost", True)
        p = filedialog.askopenfilename(
            title="Selecteer achtergrond shapefile",
            filetypes=[("Shapefile", "*.shp")],
            initialdir=str(base_dir / "input"))
        r.destroy()
        if p:
            _add_layer(path=p, name=Path(p).stem)

    add_btn.on_click(_add_new)

    c = HASKONING_COLORS
    display(w.HTML(f'''
    <hr style="border-color:{c["input_bg"]};">
    <b style="font-size:13px;color:{c["primary"]};">Achtergrondlagen</b>
    <p style="font-size:12px;color:#555;margin:4px 0 8px;max-width:640px;line-height:1.5;">
        Optionele extra kaartlagen (shapefiles) die als context onder de peilbuizen worden getoond,
        bijvoorbeeld provinciegrenzen, waterlopen of onttrekkingslocaties. Elke rij hieronder is één laag met een
        <b>pad</b> naar een <code>.shp</code>-bestand (via 📂 te bladeren) en een vrij te kiezen <b>naam</b>
        (deze naam verschijnt in de laag-schakelaar rechtsboven op de kaart). Standaard staan Provincies,
        Waterwegen en Onttrekkingen al klaar &mdash; pas een pad aan, voeg met <b>➕</b> een extra laag toe,
        of verwijder een laag met <b>✕</b>. Lagen zonder (geldig) pad worden genegeerd bij het genereren
        van de kaart.
    </p>
    '''))
    display(layers_vbox)
    display(add_btn)

    return shp_w, png_w, html_w, bg_rows, ghg_w, glg_w


def collect_background_layers(bg_rows):
    """Bouw de background_layers lijst op uit de widget-rijen."""
    return [
        {
            "path":  row["path_w"].value,
            "name":  (row["name_w"].value if row.get("name_w") is not None else "") or Path(row["path_w"].value).stem,
            }
        for row in bg_rows
        if row["path_w"].value.strip()
    ]


# ==========================
# Uitleg die voorheen als losse markdown-cellen in de notebook stond.
# Hier centraal bijhouden zodat code en documentatie niet uit elkaar kunnen lopen.
# ==========================

def _short_intro_html() -> str:
    """Genereer een korte, altijd zichtbare introductietekst boven de widgets in de notebook."""
    c = HASKONING_COLORS
    return f'''
    <div style="font-family:Arial, sans-serif; color:{c["primary"]}; background-color:{c["background"]};
                padding:10px 14px; border-radius:4px; margin-bottom:10px; font-size:13px;">
        Met deze tool teken je een <b>raai</b> (lijn) op de kaart met een gekozen bufferzone.
        Alle peilbuizen binnen de buffer worden getoond, samen met de bijbehorende grafieken per modellaag.
        Stel hieronder de bestandspaden in &mdash; de beschikbare modellagen worden automatisch herkend
        aan de submappen in de grafieken-map &mdash; en klik daarna op <b>"\U0001F5FA\uFE0F Genereer kaart"</b>
        om de kaart te maken en op te slaan als HTML. Klik daarna op <b>"\U0001F310 Open kaart"</b> om de kaart
        in een nieuw browsertabblad te openen.
        Open de secties hieronder voor gedetailleerde uitleg over de databestanden.
    </div>
    '''


def _instructions_accordion():
    """Bouw een inklapbare instructie-sectie als ipywidgets. Hierin staat uitleg over shapefile-opbouw en mappenstructuur."""
    import ipywidgets as w

    c = HASKONING_COLORS
    th_style = f"background-color:{c['primary']};color:{c['white']};padding:4px 8px;text-align:left;"
    td_style = "padding:4px 8px;border-bottom:1px solid #ddd;"

    shapefile_rows = [
        ("Naam", "Naam van de peilbuis"),
        ("Modellaag", "Modellaagnummer als geheel getal"),
        ("X", "X-coördinaat (RD New)"),
        ("Y", "Y-coördinaat (RD New)"),
        ("Difference", "Verschil gemeten vs berekend (m)"),
        ("Measured", "Gemeten grondwaterstand"),
        ("Calc", "Berekende grondwaterstand"),
    ]
    shapefile_table_rows = "".join(
        f"<tr><td style='{td_style}'><b>{naam}</b></td><td style='{td_style}'>{beschrijving}</td></tr>"
        for naam, beschrijving in shapefile_rows
    )
    shapefile_html = f'''
    <div style="font-family:Arial, sans-serif; font-size:13px; padding:6px 4px;">
        <p>De shapefile met peilbuisgegevens moet een pointlayer zijn in het coördinatenstelsel
        <b>RD New (EPSG:28992)</b> en de volgende kolomnamen bevatten:</p>
        <table style="border-collapse:collapse; width:100%;">
            <tr><th style="{th_style}">Kolomnaam</th><th style="{th_style}">Beschrijving</th></tr>
            {shapefile_table_rows}
        </table>
        <p style="margin-top:8px;">Van deze kolommen zijn <b>Naam</b> en <b>Modellaag</b> noodzakelijk voor de koppeling.
        Zonder RD New X/Y-coördinaten worden er geen punten geplot.</p>
        <p><b>Let op:</b> de bestandsnaam van een grafiek (<code>Naam.png</code>) moet exact overeenkomen met de
        waarde in de kolom <code>Naam</code>. Bij een filternummer werkt de koppeling ook
        (bijv. filternummer 2 &rarr; <code>Naam_2</code> &rarr; <code>B43H0316_2.png</code> bij <code>Naam = B43H0316</code>).</p>
    </div>
    '''

    folders_html = f'''
    <div style="font-family:Arial, sans-serif; font-size:13px; padding:6px 4px;">
        <p>De grafieken staan per modellaag in een genummerde submap. De mapnaam is het nummer van de
        modellaag. Ontbrekende mappen worden overgeslagen.</p>
        <pre style="background-color:{c['input_bg']}; padding:8px; border-radius:4px; font-size:12px;">grafieken_map/
├── 1/                  ← modellaag 1
│   ├── B43H0316.png    ← Naam.png (zelfde Naam als kolom Naam in shapefile pointlayer!)
│   └── B43H0317.png
├── 2/                  ← modellaag 2
│   ├── B43H0316.png
│   └── B43H0317.png
└── ...                 ← etc.</pre>
    </div>
    '''

    acc = w.Accordion(children=[
        w.HTML(shapefile_html),
        w.HTML(folders_html),
    ])
    acc.set_title(0, "\U0001F4C4 Shapefile-opbouw")
    acc.set_title(1, "\U0001F5C2\uFE0F Mappenstructuur grafieken")
    acc.selected_index = None  # standaard ingeklapt
    return acc



# ==========================
# Notebook-orchestrator: bouwt de complete layout (header, uitleg, widgets,
# modellagen-keuze, kaart en export-knop) op in één aanroep vanuit de notebook.
# ==========================

def run_tool(base_dir):
    """
    Bouw en toon de complete tool-layout in de Jupyter-notebook.

    Roep deze functie aan vanuit de notebook (zie Jupyter_setup.ipynb):

        _mod.run_tool(_here)

    Toont: Haskoning-header, korte uitleg, inklapbare instructies, instellingen-
    widgets (bestandspaden, achtergrondlagen, modellagen), en knoppen om de kaart
    te genereren (en op te slaan als HTML) en te openen in de browser.
    """
    import webbrowser
    import ipywidgets as w
    from IPython.display import display, HTML

    base_dir = Path(base_dir)

    display(HTML(_notebook_css()))
    display(HTML(_branding_header_html(
        title=TOOL_TITLE,
        subtitle="Seppe-Schijf grondwatertool \u2014 interactieve raai-selectie",
    )))
    display(HTML(_short_intro_html()))
    display(_instructions_accordion())

    display(HTML(
        f"<h4 style='color:{HASKONING_COLORS['primary']};margin:12px 0 2px;font-family:Arial, sans-serif;'>Instellingen</h4>"
    ))
    shp_w, png_w, html_w, bg_rows, ghg_w, glg_w = setup_widgets(base_dir)

    generate_btn = w.Button(description="\U0001F5FA\uFE0F Genereer kaart",
                             layout=w.Layout(width="200px", margin="12px 8px 0 0"))
    open_btn = w.Button(description="\U0001F310 Open kaart", disabled=True,
                         layout=w.Layout(width="200px", margin="12px 0 0 0"))
    display(w.HBox([generate_btn, open_btn]))

    status_out = w.Output()
    display(status_out)

    state = {"kaart_path": None}

    def _on_generate(_):
        from IPython.display import display as _display, HTML as _HTML
        status_out.clear_output()
        open_btn.disabled = True
        state["kaart_path"] = None

        with status_out:
            # ── Pre-flight validatie ──────────────────────────────────────
            fouten_totaal: List[str] = []
            rapport_delen: List[str] = []

            stat_pad = shp_w.value.strip()
            ghg_pad  = ghg_w.value.strip()
            glg_pad  = glg_w.value.strip()

            # Minstens één shapefile is vereist
            if not stat_pad and not ghg_pad and not glg_pad:
                fouten_totaal.append(
                    "Geen shapefile opgegeven \u2014 voer minstens \u00e9\u00e9n shapefile in (Stat, GHG of GLG)."
                )

            for _pad, _lbl in [
                (stat_pad, "Shapefile Stat (GG)"),
                (ghg_pad,  "Shapefile GHG"),
                (glg_pad,  "Shapefile GLG"),
            ]:
                if _pad:
                    _f, _i = _validate_shapefile(_pad, _lbl)
                    fouten_totaal.extend(_f)
                    rapport_delen.append(_render_validation_block(_lbl, _f, _i))
                else:
                    rapport_delen.append(
                        _render_validation_block(_lbl, [], ["Niet opgegeven \u2014 wordt overgeslagen."])
                    )

            _f_png, _i_png = _validate_png_dir(png_w.value)
            fouten_totaal.extend(_f_png)
            rapport_delen.append(_render_validation_block("Grafiekenmap", _f_png, _i_png))

            _f_out = _validate_output_path(html_w.value)
            fouten_totaal.extend(_f_out)
            rapport_delen.append(_render_validation_block("Uitvoerpad", _f_out, []))

            rapport_html = "".join(rapport_delen)

            if fouten_totaal:
                _display(_HTML(
                    f'<div style="border:1px solid {ALARM_COLORS["critical"]};border-radius:4px;'
                    f'margin:6px 0;font-family:Arial,sans-serif;">'
                    f'<div style="background:{ALARM_COLORS["critical"]};color:white;padding:8px 10px;'
                    f'font-weight:700;font-size:13px;border-radius:4px 4px 0 0;">'
                    f'&#10007; Kan kaart niet genereren \u2014 los de fouten hieronder op</div>'
                    f'<div style="padding:10px;">{rapport_html}</div></div>'
                ))
                return

            if rapport_html.strip():
                _display(_HTML(
                    f'<div style="border:1px solid {ALARM_COLORS["medium"]};border-radius:4px;'
                    f'margin:6px 0;background:#fffde7;font-family:Arial,sans-serif;">'
                    f'<div style="background:{ALARM_COLORS["medium"]};color:{HASKONING_COLORS["primary"]};'
                    f'padding:6px 10px;font-weight:700;font-size:12px;border-radius:4px 4px 0 0;">'
                    f'&#9432; Opmerkingen (generatie gaat door)</div>'
                    f'<div style="padding:10px;">{rapport_html}</div></div>'
                ))

            # ── Modellagen ontdekken ──────────────────────────────────────
            model_layers = _discover_model_layers(png_w.value)
            _display(_HTML(
                f'<div style="font-family:Arial,sans-serif;font-size:12px;'
                f'color:{HASKONING_COLORS["primary"]};margin:4px 0;">'
                f'Kaart genereren voor modellagen '
                f'{", ".join(str(l) for l in model_layers)} \u2026</div>'
            ))

            # ── Genereer kaart ────────────────────────────────────────────
            try:
                kaart = create_raai_selection_map(
                    points_path=stat_pad or None,
                    png_base_path=png_w.value,
                    model_layers=model_layers,
                    background_layers=collect_background_layers(bg_rows),
                    points_ghg_path=ghg_pad or None,
                    points_glg_path=glg_pad or None,
                )
            except Exception as exc:
                _display(_HTML(
                    f'<div style="color:{ALARM_COLORS["critical"]};font-family:Arial,sans-serif;'
                    f'font-size:13px;padding:8px;border:1px solid {ALARM_COLORS["critical"]};'
                    f'border-radius:4px;margin:4px 0;">&#10007; Fout tijdens genereren van de kaart:'
                    f'<br><code style="font-size:11px;">{exc}</code></div>'
                ))
                return

            # ── Opslaan ───────────────────────────────────────────────────
            out_path = Path(html_w.value)
            try:
                out_path.parent.mkdir(parents=True, exist_ok=True)
                kaart.save(str(out_path))
            except Exception as exc:
                _display(_HTML(
                    f'<div style="color:{ALARM_COLORS["critical"]};font-family:Arial,sans-serif;'
                    f'font-size:13px;padding:8px;border:1px solid {ALARM_COLORS["critical"]};'
                    f'border-radius:4px;margin:4px 0;">&#10007; Kon de kaart niet opslaan naar '
                    f'<code>{out_path}</code>:<br><code style="font-size:11px;">{exc}</code></div>'
                ))
                return

            state["kaart_path"] = out_path
            open_btn.disabled = False
            _display(_HTML(
                f'<div style="font-family:Arial,sans-serif;font-size:13px;padding:8px;'
                f'border:1px solid {THEME_GREEN["secondary"]};border-radius:4px;'
                f'background:{THEME_GREEN["highlight"]};color:{HASKONING_COLORS["primary"]};margin:4px 0;">'
                f'&#10003; Kaart opgeslagen: <code>{out_path}</code><br>'
                f'Klik op "\U0001f310 Open kaart" om deze te bekijken.</div>'
            ))

    def _on_open(_):
        if state["kaart_path"] is None:
            return
        webbrowser.open(state["kaart_path"].resolve().as_uri())

    generate_btn.on_click(_on_generate)
    open_btn.on_click(_on_open)


# ==========================
# Hieronder staat de code die wordt uitgevoerd als dit script direct wordt gerund (niet geïmporteerd als module).
# ==========================

if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parents[0]

    print("=" * 50)
    print("GW-Grafieken Raai Tool - Genereer interactieve kaart")
    print("=" * 50)

    _png_base = base_dir / "input" / "02_grafieken_png"
    _model_layers = _discover_model_layers(_png_base)
    if not _model_layers:
        raise SystemExit(f"Geen modellagen gevonden in: {_png_base}")

    kaart = create_raai_selection_map(
        points_path=str(base_dir / "input" / "01_bollenkaart_shp" / "bollenkaart_stat.shp"),
        png_base_path=str(_png_base),
        model_layers=_model_layers,
        background_layers=[
            {"path": str(base_dir / "input" / "00_achtergrond_shp" / "Provincies" / "NL" / "provincie2010.shp"),
             "name": "Provincies"},
            {"path": str(base_dir / "input" / "00_achtergrond_shp" / "Waterlopen" / "waterwegen_nedeland.shp"),
             "name": "Waterwegen"},
            {"path": str(base_dir / "input" / "00_achtergrond_shp" / "Onttrekkingen" / "ontrekkingen.shp"),
             "name": "Onttrekkingen"},
        ],
        points_ghg_path=str(base_dir / "input" / "01_bollenkaart_shp" / "bollenkaart_GHG.shp"),
        points_glg_path=str(base_dir / "input" / "01_bollenkaart_shp" / "bollenkaart_GLG.shp"),
    )

    output_path = base_dir / "output" / "GW-Grafieken_Raai.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    kaart.save(str(output_path))

    print("=" * 50)
    print(f"Kaart opgeslagen: {output_path}")
    print("=" * 50)