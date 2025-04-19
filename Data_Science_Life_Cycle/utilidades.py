def saludar(name):
    """
    Función que imprime un saludo personalizado.
    
    Parameters:
    name (str): El nombre de la persona a saludar.
    
    Returns:
    None
    """
    print(f"Hola, {name}! Bienvenido de")

def contarRegistrosConmayusculas(columna):
    return sum(columna.str.contains(r'[A-Z]', na=False))