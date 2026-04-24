import pandas as pd


def saludar(name):
    """
    Función que imprime un saludo personalizado.

    Parameters:
    name (str): El nombre de la persona a saludar.

    Returns:
    None
    """
    print(f"Hola, {name}! Bienvenido de")


def contarRegistrosConmayusculas(columna: pd.Series) -> int:
    """
    Count how many entries in a pandas Series contain uppercase letters.

    Args:
        columna (pd.Series): Column of strings.

    Returns:
        int: Number of entries containing uppercase letters.
    """
    return int(columna.str.contains(r"[A-Z]", na=False).sum())
