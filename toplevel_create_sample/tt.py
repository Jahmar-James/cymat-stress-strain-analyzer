import pandas as pd
import re
from typing import List, Tuple, Optional

def _parse_unit_from_df_column(dataframe: pd.DataFrame) -> list[tuple[str, Optional[str]]]:
        import re
        # Regex pattern to extract units within parentheses or square brackets
        pattern = re.compile(r'(.+?)\s*(?:\(|\[)([a-zA-Z%°]{1,3})(?:\)|\])?$')
        
        # Flatten the list of known units into a set for faster membership testing
        known_units = {
            'time': ['s', 'ms', 'min', 'hr'],
            'force': ['N', 'kN', 'lbf'],
            'displacement': ['mm', 'cm', 'm'],
            'stress': ['Pa', 'kPa', 'MPa', 'GPa'],
            'strain': ['%', 'mm/mm', 'in/in']
        }
        flat_known_units = set(unit for sublist in known_units.values() for unit in sublist)
        
        result = []
        for column in dataframe.columns:
            match = pattern.match(column)
            if match:
                name, unit = match.groups()
                result.append((name.strip(), unit))
            else:
                parts = column.split()
                if parts[-1] in flat_known_units:
                    name = ' '.join(parts[:-1])
                    unit = parts[-1]
                    result.append((name, unit))
                else:
                    result.append((column, None))
        return result

if __name__ == '__main__':
    # Example DataFrame
    data = {
        'Temperature (°C)': [20, 22, 21],
        'Pressure [kPa]': [101, 99, 102],  # This will be ignored due to square brackets
        'Humidity (%)': [30, 45, 50],
        'Wind Speed': [5, 10, 7], # No units present
        'blade speed rpm': [100, 200, 150],  # unit in name
        'Time (s)': [20, 22, 21],
        'Force N': [101, 99, 102],
        'Displacement [mm]': [1, 2, 1.5],
        'Stress MPa': [300, 450, 500],
        'Strain %': [10, 15, 12],
    }

    df = pd.DataFrame(data)

    # Extract units from column names
    extracted_info = _parse_unit_from_df_column(df)
    print(extracted_info)

