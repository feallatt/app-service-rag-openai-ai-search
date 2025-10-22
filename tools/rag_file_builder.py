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
