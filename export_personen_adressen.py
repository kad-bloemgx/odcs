#!/usr/bin/env python3
"""
Script to export person and address data to CSV files based on the ERD specification.
"""

import csv

# Voorbeeldgegevens uit het document
personen_data = [
    {"id": "123456", "naam": "Jan Jansen", "adres_id": "ADDR001"},
    {"id": "123458", "naam": "Pietje Puk", "adres_id": "ADDR001"},
    {"id": "123457", "naam": "Maria Pieterse", "adres_id": "ADDR002"}
]

adressen_data = [
    {"id": "ADDR001", "straat": "Koppejan", "huisnummer": "1", "postcode": "7461 DB", "woonplaats": "Rijssen"},
    {"id": "ADDR002", "straat": "Kerkweg", "huisnummer": "42", "postcode": "7411 CX", "woonplaats": "Deventer"}
]

def export_personen_to_csv():
    """Export personen data to CSV file"""
    with open('personen.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'naam', 'adres_id']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for persoon in personen_data:
            writer.writerow(persoon)
    
    print("Personen data geëxporteerd naar personen.csv")

def export_adressen_to_csv():
    """Export adressen data to CSV file"""
    with open('adressen.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'straat', 'huisnummer', 'postcode', 'woonplaats']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for adres in adressen_data:
            writer.writerow(adres)
    
    print("Adressen data geëxporteerd naar adressen.csv")

def main():
    """Main function to run the export"""
    print("Exporteren van personen en adressen data naar CSV-bestanden...")
    export_personen_to_csv()
    export_adressen_to_csv()
    print("Export voltooid!")

if __name__ == "__main__":
    main()