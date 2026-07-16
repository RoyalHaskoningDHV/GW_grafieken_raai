[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/RoyalHaskoningDHV/GW_grafieken_raai/HEAD?urlpath=%2Fdoc%2Ftree%2FGW_grafieken_raai.ipynb)

TEKEN RAAI TOOL
===============
Seppe-Schijf Geohydrologische Tool

Met deze tool teken je een raai (lijn) op een interactieve kaart met een gekozen
bufferzone. Alle peilbuizen binnen die buffer worden getoond, samen met de
bijbehorende grafieken per modellaag.

De tool bestaat uit:
- Jupyter Notebook gebruikersinterface (Jupyter_setup.ipynb)
- Python-module met de kaart-/rekencode (Teken_raai_tool.py)
- Shapefile met peilbuisgegevens (input/01_bollenkaart_shp)
- Grafieken van metingen en modelresultaten, per modellaag (input/02_grafieken_png)
- Optionele achtergrond-shapefiles (input/00_achtergrond_shp)
- Interactieve kaart met kaartlagen, raai-tekentool en export naar HTML


1. VEREISTEN
-------------
- Python 3.9 of hoger.
- Een conda- of virtualenv-omgeving (aanbevolen) met Jupyter Lab/Notebook.
- Tkinter (voor de "Bladeren..."-knoppen). Dit zit standaard in de Python-installatie
  van python.org, maar ontbreekt soms in conda(-forge)-omgevingen; installeer dan
  apart met: conda install tk
- De packages uit requirements.txt:
    jupyterlab   - Jupyter-omgeving om de notebook te draaien
    ipython      - basis voor widgets/weergave in de notebook
    folium       - interactieve kaart genereren (HTML-output)
    geopandas    - shapefiles inlezen en verwerken
    matplotlib   - ondersteunende functionaliteit voor ruimtelijke eenheden
    ipywidgets   - knoppen, tekstvelden en instellingen-UI in de notebook


2. INSTALLATIE
---------------
1) Open een Anaconda- of Miniforge-prompt.
2) Activeer een bestaande omgeving, bijvoorbeeld:
       conda activate base
   of maak een nieuwe omgeving aan en activeer die:
       conda create -n raai-tool python=3.11
       conda activate raai-tool
3) Ga naar de projectmap (04_Tool_Concept_V3) en installeer de benodigde packages:
       pip install -r requirements.txt
4) Start Jupyter Lab vanuit dezelfde map:
       jupyter lab
5) Herstart na de installatie eenmalig de kernel (Kernel > Restart) voordat je
   cellen uitvoert, zodat alle packages correct geladen worden.


3. GEBRUIK
-----------
1) Open Jupyter_setup.ipynb in Jupyter Lab.
2) Run de ene code-cel. Dit laadt de volledige tool: Haskoning-huisstijl, een
   korte uitleg, inklapbare detail-uitleg (shapefile-opbouw en mappenstructuur
   van de grafieken), instellingen en knoppen.
3) Controleer/pas de bestandspaden aan (shapefile peilbuizen, map met grafieken,
   HTML-exportpad) en de lijst met achtergrondlagen indien gewenst.
4) Klik op "Genereer kaart". De beschikbare modellagen worden automatisch herkend
   aan de genummerde submappen in de grafieken-map; de kaart wordt gegenereerd en
   direct opgeslagen als HTML-bestand op het opgegeven pad (standaard:
   output/Teken_raaitool.html).
5) Klik op "Open kaart" om het zojuist opgeslagen HTML-bestand in een nieuw
   browsertabblad te openen.
6) Teken op de kaart een raai (lijn), kies een bufferzone en klik op
   "Zoek Punten" om de peilbuizen en bijbehorende grafieken te tonen.
7) Pas je iets aan (bestandspaden, achtergrondlagen)? Klik opnieuw op "Genereer
   kaart" en daarna op "Open kaart" om de bijgewerkte versie te bekijken.


4. DATA-VEREISTEN
-------------------
Gedetailleerde uitleg over de verplichte kolomnamen in de shapefile en de
mappenstructuur van de grafieken staat inklapbaar in de notebook zelf (onder
"Shapefile-opbouw" en "Mappenstructuur grafieken"). Kort samengevat:
- De shapefile voor GG, GLG en GHG moeten pointlayers zijn in RD New (EPSG:28992) met minimaal de
  kolommen Naam en Modellaag, X en Y (optioneel aangevuld met Difference, Measured, Calc). 
      Let op: gebruiker blijft verantwoordelijk voor invoerbestanden, 
      De gemiddelde grondwaterstand GG kan tijdsafhankelijk of stationair worden aangeleverd maar de knop blijft GG weergeven. 
      Wees altijd bewust van uw invoer, waar kijk ik naar en wat verwacht ik te zien.
- De grafieken staan per modellaag in een genummerde submap
  (input/02_grafieken_png/<modellaag>/), met bestandsnamen die exact overeenkomen
  met de kolom Naam (eventueel met filternummer, bijv. B43H0316_2.png).


5. PROJECTSTRUCTUUR
---------------------
04_Tool_Concept/
|-- Jupyter_setup.ipynb        - notebook, start hier
|-- Teken_raai_tool.py         - module met alle kaart-/rekencode en UI
|-- requirements.txt           - benodigde Python-packages
|-- haskoning_branding_1.md    - Haskoning huisstijl-referentie
|-- img/haskoning-logo.svg     - logo, gebruikt in de kaart en notebook-header
|-- input/
|   |-- 00_achtergrond_shp/    - optionele achtergrondlagen (provincies, waterlopen, onttrekkingen)
|   |-- 01_bollenkaart_shp/    - shapefile met peilbuisgegevens
|   `-- 02_grafieken_png/<modellaag>/ - grafieken per modellaag
`-- output/
    `-- Teken_raaitool.html    - ge\u00ebxporteerde interactieve kaart (via de exportknop)


6. CONTACT
-----------
Voor bugs, feedback of vragen:
- https://github.com/......


