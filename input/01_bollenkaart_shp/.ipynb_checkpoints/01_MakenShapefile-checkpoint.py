import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# Bestanden
chi_file = r"c:\Users\929498\Haskoning\P-BK4363-Seppe-Schijf-grondwatermodel - Team\WIP\6. Tool\99_data\01_peilbuisdata\chi_file\calib.chi"
cho_file = r"c:\Users\929498\Haskoning\P-BK4363-Seppe-Schijf-grondwatermodel - Team\WIP\6. Tool\99_data\02_modelresultaat\01_cho_files\calib_stat.cho"
output_shp = r"c:\Users\929498\Haskoning\P-BK4363-Seppe-Schijf-grondwatermodel - Team\WIP\6. Tool\01_Tool\Shapefile_bollenkaart\bollenkaart_stat.shp"

# -----------------
# CHI inlezen
# -----------------
chi = pd.read_csv(
    chi_file,
    sep=r'\s+',
    skiprows=1,
    usecols=[0,1,2,3,4],
    names=["Naam","X","Y","Cluster","Modellaag"]
)

# -----------------
# CHO inlezen
# -----------------
cho = pd.read_csv(
    cho_file,
    sep=r"\s+",
    engine="python",
    skiprows=17,
    names=["Naam","Aquifer","Clus","Calc","Measured","Difference","Weight (DIF^2)"],
    usecols=range(7),
    on_bad_lines="skip"
)

# Kolommen hernoemen (pas aan indien nodig)
cho = cho.rename(columns={
    "NAME": "Naam",
    "Clus": "Cluster",
    "Aquifer": "Modellaag",
    "Calc": "Calc",
    "Measured": "Measured"
})

# Zorg dat types gelijk zijn

# Strings voor NAAM
chi["Naam"] = chi["Naam"].astype(str)
cho["Naam"] = cho["Naam"].astype(str)

# Integers maken voor de rest
chi["Cluster"] = chi["Cluster"].astype(int)
chi["Modellaag"] = chi["Modellaag"].astype(int)

cho["Calc"] = pd.to_numeric(cho["Calc"], errors="coerce")
cho["Measured"] = pd.to_numeric(cho["Measured"], errors="coerce")
cho["Modellaag"] = pd.to_numeric(cho["Modellaag"], errors="coerce")
cho["Cluster"] = pd.to_numeric(cho["Cluster"], errors="coerce")
cho["Difference"] = pd.to_numeric(cho["Difference"], errors="coerce")
cho["Weight (DIF^2)"] = pd.to_numeric(cho["Weight (DIF^2)"], errors="coerce")

cho = cho.dropna(subset=["Cluster","Modellaag", "Calc","Measured","Difference","Weight (DIF^2)"])

# -----------------
# Joinen
# -----------------
df = pd.merge(
    chi,
    cho,
    on=["Naam","Cluster","Modellaag"],
    how="inner"
)

# Drop duplicates based on the specified subset of columns, doet die dit nu voor alle rijen of alleen voor de rijen die gejoined zijn?
# dit doet die nu voor alle rijen in df, dus ook voor de rijen die gejoined zijn. Als er meerdere rijen met dezelfde combinatie van Naam, Cluster, Modellaag, Calc, Measured, Difference en Weight (DIF^2) zijn, dan worden alleen de eerste unieke rij behouden en de rest verwijderd.
df = df.drop_duplicates(subset=["Naam","Cluster","Modellaag", "Calc","Measured", "Difference","Weight (DIF^2)"])

# -----------------
# GeoDataFrame maken
# -----------------
geometry = [Point(xy) for xy in zip(df["X"], df["Y"])]
gdf = gpd.GeoDataFrame(df, geometry=geometry)

# -----------------
# Opslaan als shapefile
# -----------------
gdf = gdf[["Naam","X","Y","Modellaag","Cluster","Calc","Measured","Difference","Weight (DIF^2)","geometry"]]

gdf.to_file(output_shp)

print(cho.head())
print(cho.columns)

print("aantal rijen in output shapefile:", len(gdf))
print("Shapefile is opgeslagen als:", output_shp)