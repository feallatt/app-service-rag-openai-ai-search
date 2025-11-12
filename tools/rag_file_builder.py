import pandas as pd
import numpy as np
import os

def extract_base_model(artikel_name, color=None):
    """
    Extract the base model name by removing the color from the article name.
    
    Parameters:
    artikel_name : str
        The full article name including color
    color : str, optional
        The color to remove. If not provided, attempts to detect the color.
        
    Returns:
    str
        The base model name without the color
    """
    # Handle None or empty inputs
    if not artikel_name or pd.isna(artikel_name):
        return ""
    
    # If color is provided, simply remove it from the artikel_name
    if color and color in artikel_name:
        # Remove the color and trim any trailing spaces
        return artikel_name.replace(color, "").strip()
    
    # If no color is provided, try to identify it
    # CUBE bikes often use the format where color is at the end after the model number
    # Common pattern: model numbers followed by color
    parts = artikel_name.split()
    
    # Look for common color indicators like 'n' or color names
    for i in range(len(parts)-1, 0, -1):
        potential_color = parts[i]
        if ('´n´' in potential_color or 
            any(c in potential_color.lower() for c in ['black', 'white', 'blue', 'red', 'grey', 'green', 'chrome'])):
            # Found a likely color part, reconstruct the base model without it
            return ' '.join(parts[:i]).strip()
    
    # If no clear color indicator is found and we have a number followed by text
    # (common pattern in CUBE bikes where model number is followed by color)
    for i in range(len(parts)-1, 0, -1):
        # If we find a part that contains digits (likely a model number)
        if any(c.isdigit() for c in parts[i]) and i < len(parts)-1:
            # Assume everything after the model number is color
            return ' '.join(parts[:i+1]).strip()
    
    # If we can't identify a color pattern, return the original name
    return artikel_name

def agg_func(x):
    unique_vals = x.dropna().unique()
    if len(unique_vals) == 0:
        return np.nan
    elif len(unique_vals) == 1:
        return unique_vals[0]
    else:
        return list(unique_vals)

def create_text_documents_from_df(df):
    """
    Convert DataFrame rows to text documents for RAG system.
    Excludes specified technical columns and focuses on descriptive content.
    """
    text_documents = []
    
    for index, row in df.iterrows():
        # Create a text document for each bike
        doc_parts = []
        
        # Skip completely empty columns and only include non-empty values
        for col in df.columns:
               # Check if there's actually something meaningful inside
            value = row[col]
            if (
                value is None                       # None
                or (isinstance(value, float) and pd.isna(value))  # NaN
                or (isinstance(value, (list, str)) and len(value) == 0)  # empty list or empty string
            ):
                continue  # skip this row
            if isinstance(value, list):
                # Handle lists by joining elements with commas
                formatted_value = ", ".join(str(item) for item in value if pd.notna(item) and str(item).strip())
                if formatted_value:  # Only add if there's content
                    doc_parts.append(f"{col}: {formatted_value}")
            elif str(value).strip():  # For scalar values, check if not empty
                doc_parts.append(f"{col}: {value}")
        
        # Join all parts into a single document
        document = "\n".join(doc_parts)
        text_documents.append(document)
    
    return text_documents

import numpy as np
import pandas as pd

def generate_bike_stats_text(df: pd.DataFrame, out_path: str = "data/bike_stats.txt") -> str:
    """
    Erstellt Statistik-Report für das Bike-DataFrame und schreibt ihn als Textdatei.
    Nutzt 'Produktklasse' für E-Bike-Erkennung, nimmt 'UVP DE' direkt als Zahl
    und ergänzt Fahrräder mit höchstem Fahrergewicht.
    """

    # ----------------- Hilfsfunktionen -----------------
    def _is_empty(x):
        if x is None:
            return True
        if isinstance(x, str):
            return len(x.strip()) == 0 or x.strip().lower() == "nan"
        if isinstance(x, (list, tuple, set, dict)):
            return len(x) == 0
        try:
            return pd.isna(x)
        except Exception:
            return False

    def _fmt_eur(x):
        return f"{float(x):,.2f} EUR".replace(",", "X").replace(".", ",").replace("X", ".")

    def _dedup(strings):
        seen = set()
        out = []
        for s in strings:
            s = str(s).strip()
            if s and s.lower() not in seen:
                seen.add(s.lower())
                out.append(s)
        return out

    # ----------------- Vorbereitung -----------------
    total = len(df)
    # einfache E-Bike-Erkennung
    is_ebike = df["Produktklasse"].astype(str).str.lower().str.contains("e-bike")
    ebikes = int(is_ebike.sum())

    prices = df["UVP DE"].astype(float)
    price_ok = prices.notna().any()

    price_min, price_max, price_mean, price_median = None, None, None, None
    if price_ok:
        price_min = float(prices.min())
        price_max = float(prices.max())
        price_mean = float(prices.mean())
        price_median = float(prices.median())

    idx_min = prices.idxmin() if price_ok else None
    idx_max = prices.idxmax() if price_ok else None

    def pick_row(i):
        if i is None or i not in df.index:
            return None
        return {
            "artikel": df.at[i, "Artikel"] if "Artikel" in df.columns else None,
            "beschreibung": df.at[i, "Beschreibung"] if "Beschreibung" in df.columns else None,
            "preis": df.at[i, "UVP DE"],
        }

    cheapest = pick_row(idx_min)
    most_expensive = pick_row(idx_max)

    # Kategorien zählen
    cat_counts = (
        df["Produktklasse"].astype(str).str.strip().value_counts().to_dict()
        if "Produktklasse" in df.columns
        else {}
    )

    # unterschiedliche Modelle
    distinct_models = df["Artikel"].nunique() if "Artikel" in df.columns else None

    # Preisbuckets + Modelle
    bins = [-np.inf,1000,2000,3000,4000,5000,6000,7000,np.inf]
    labels = ['<1k','1k-2k','2k-3k','3k-4k','4k-5k','5k-6k','6k-7k','>7k']
    human_label = {
        '<1k': 'Unter 1.000 EUR','1k-2k':'1.000 - 2.000 EUR','2k-3k':'2.000 - 3.000 EUR',
        '3k-4k':'3.000 - 4.000 EUR','4k-5k':'4.000 - 5.000 EUR','5k-6k':'5.000 - 6.000 EUR',
        '6k-7k':'6.000 - 7.000 EUR','>7k':'Über 7.000 EUR'
    }
    bucket = pd.cut(prices, bins=bins, labels=labels)

    # Farben
    colors = []
    for i, color in enumerate(df.Farbe):
        if isinstance(color, list):
            colors = colors + color
        else:
            colors.append(color)

    colors = set(colors)
    colors
                
    color_count = len(colors)

    # Fahrräder mit höchstem Fahrergewicht
    max_weight_bikes = []
    if "FahrergewichtMax" in df.columns:
        # Convert to string first to ensure we can apply string operations
        fw_str = df["FahrergewichtMax"].astype(str)
        
        # Extract numeric part (remove "kg" and strip spaces)
        fw = fw_str.str.replace("kg", "").str.strip().astype(float)
        
        if fw.notna().any():
            max_fw = fw.max()
            max_idxs = fw[fw == max_fw].index
            for i in max_idxs:
                name = df.at[i, "Artikel"]
                max_weight_bikes.append((name, max_fw))

    # ----------------- Text aufbauen -----------------
    lines = []
    lines.append(f"Gesamtanzahl Fahrräder: {total}")
    lines.append(f"Anzahl E-Bikes: {ebikes}")
    if cat_counts:
        lines.append("Fahrräder pro Kategorie:")
        for k, v in cat_counts.items():
            lines.append(f"  - {k}: {v}")
    if distinct_models is not None:
        lines.append(f"Anzahl unterschiedlicher Modelle: {distinct_models}")
    if most_expensive:
        lines.append(
            f"Teuerstes Fahrrad: {most_expensive['artikel']} - {_fmt_eur(most_expensive['preis'])}"
        )
    if cheapest:
        lines.append(
            f"Günstigstes Fahrrad: {cheapest['artikel']} - {_fmt_eur(cheapest['preis'])}"
        )
    if price_mean is not None:
        lines.append(f"Durchschnittlicher Preis: {_fmt_eur(price_mean)}")
    if price_median is not None:
        lines.append(f"Median Preis: {_fmt_eur(price_median)}")

    # Preisverteilung mit Modellen
    lines.append("Preisverteilung (UVP DE):")
    for lab in labels:
        mask = bucket == lab
        subset = df[mask]
        lines.append(f"{human_label[lab]} ({len(subset)} Fahrräder):")
        for _, r in subset.sort_values("UVP DE").iterrows():
            art = r["Artikel"]
            lines.append(f"  - {art} - {_fmt_eur(r['UVP DE'])}")

    # Farben
    lines.append(f"Anzahl unterschiedlicher Farben: {color_count}")
    if color_count:
        lines.append("Verfügbare Farben:")
        lines.append("  - " + ", ".join(colors))

    # Fahrergewicht
    if max_weight_bikes:
        lines.append(f"Fahrräder mit höchstem Fahrergewicht ({max_weight_bikes[0][1]} kg):")
        for name, w in max_weight_bikes:
            lines.append(f"  - {name} - {w} kg")

    # Datei schreiben
    text = "\n".join(lines)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)

    return out_path


### insert your path here ###
stammdaten_path = '/Users/Q607721/Downloads/2026_Bike_Stammdaten_02.09.2026.xlsx'
################################

stammdaten = pd.read_excel(stammdaten_path)
stammdaten.rename(columns={'Unnamed: 0': 'NewProductLasse'},inplace=True)
stammdaten.drop(columns=['BezeichnungKurz', 'Marke', 'Modellfamilie', 'Größe', 'Lenkerband', 'Griffe', 'Bremshebel', 'Kette', 
                         'Riemen', 'Pedale', 'Sattelklemme', 'Schutzblech', 'Kettenschutz', 
                         'Glocke', 'GewichtMax', 'Körpergröße', 'Schrittlänge', 
                         'HEK Euro', 'UVP AT', 'UVP IT',
                        'UVP CHF', 'UVP ES', 'UVP DKK', 'UVP SEK', 'UVP NOK', 'EAN',
                        'Bestellnummer', 'Box-Label-Code', 'LengthInMeter', 'WidthInMeter',
                        'HeightInMeter', 'Gewicht_netto', 'Gewicht_brutto', 'Herkunftsland',
                        'Zolltarifnummer', 'SecurityInformation', 'ManufacturerInformation',
                        'kommentare',
                         ],inplace=True)

stammdaten['newProductIch'] = stammdaten['newProductIch'].apply(lambda x: bool(x) if x == 'true' else np.nan)

# stammdaten['NewProductLasse'] = stammdaten['NewProductLasse'].apply(lambda x: bool(x))
stammdaten['newProduct'] = (stammdaten['NewProductLasse'].fillna(False) | stammdaten['newProductIch'].fillna(False))
stammdaten['newIndex'] = stammdaten.newProduct.cumsum()
stammdaten['Artikel_base'] = stammdaten.apply(lambda row: extract_base_model(row['Artikel'], row['Farbe']), axis=1)
stammdaten['Laufräder'] = stammdaten['Laufradsatz'] + stammdaten['Felgen'] + stammdaten['Nabe vorn'] + stammdaten['Nabe hinten']
stammdaten.drop(columns=['NewProductLasse', 'newProductIch', 'newProduct', 'Felgen', 'Laufradsatz', 'Nabe vorn', 'Nabe hinten'], inplace=True)
grouped = stammdaten.groupby('newIndex').agg(agg_func)

grouped['Ständer'] = grouped['Ständer'].apply(lambda x: 'Ja' if not 
                                              pd.isna(x) else 'Nein')
grouped['Gepäckträger'] = grouped['Gepäckträger'].apply(lambda x: 'Ja' if not 
                                              pd.isna(x) else 'Nein')

grouped['Artikel'] = grouped['Artikel_base']
grouped.drop(columns=['Artikel_base'], inplace=True)


# Create text documents from the DataFrame
bike_documents = create_text_documents_from_df(grouped)

# Display first few documents as example
print(f"Created {len(bike_documents)} text documents")
print("\nFirst document example:")
print(bike_documents[0])

# Create a directory to store individual files if it doesn't exist
output_dir = 'data/bike_catalog_files'
os.makedirs(output_dir, exist_ok=True)

# Save each document to its own file
for i, doc in enumerate(bike_documents):
    # Extract bike model name from the first line for filename
    # (typically starts with "Artikel: ")
    first_line = doc.split('\n')[0] if '\n' in doc else doc
    if first_line.startswith('Artikel: '):
        bike_name = first_line[9:].strip()
        # Clean filename by replacing invalid characters
        filename = ''.join(c if c.isalnum() or c in [' ', '-', '_'] else '_' for c in bike_name)
    else:
        # Fallback if no model name found
        filename = f"bike_{i+1}"
    
    filename = filename.replace(' ', '_')
    # Ensure filename isn't too long
    if len(filename) > 100:
        filename = filename[:100]
    
    # Save to file
    output_file = os.path.join(output_dir, f"{filename}.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(doc)

print(f"Created {len(bike_documents)} individual text files in: {output_dir}")

generate_bike_stats_text(grouped)


