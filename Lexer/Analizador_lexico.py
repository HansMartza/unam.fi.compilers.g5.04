# Permite analizar expresiones regulares en texto crudo: r''
# El texto crudo significa que toma en cuenta saltos de linea y espacios.
import re

# Clase que identifica los errores
class errorHandler:
    # Dentro de la lista se agregan todos los errores
    def __init__(self):
        self.errors = []
    
    # Para reportar errores lexicos muesta el mensaje, la linea y columna en la que ocurrio 
    def lexical_report(self, message, line, column):
        self.errors.append(f"Lexical Error [Line {line}, Column {column}]: {message}")
        
    # Devuelve el numero de errores que hay en la lista
    def has_errors(self):
        return len(self.errors) > 0
    
    # Imprime error por error detectado 
    def print_errors(self):
        print("\n--- Report of errors ---")
        for err in self.errors:  # Recorre la lista para imprimirlos
            print(err)
    


# Caracteristicas de un Token: Su tipo, el valor, y posicion en linea y columna
class Token:
    def __init__(self, type_, value, line, column):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column

# Clase donde se ejecuta el analizador lexico
class Lexer:
    def __init__(self, source_code, error_handler):
        self.source_code = source_code  # El codigo a analizar.
        self.error_handler = error_handler  # El objeto de manejo de errores.
        self.tokens = [] # Donde se van a almacenar la lista de tokens
        
        # Rastreo de posición
        self.line_number = 1  # Rastrea el numero de linea del codigo analizado
        self.line_start = 0   # Indica la "columna" de la fila actual
        
        self.tokens_type = [
            
            # De acuerdo a las expresiones regulares, podemos:
            # \bPATRON\b Encuentra un PATRON en especifico de caracteres de palabra
            # ?: Indica que solo busca una coincidencia pero no la guarda.
            # (Patron1|Patron2) permite buscar diferentes patrones
            
            ('KEYWORD', r'\b(?:int|print|float|string|if|elif|else|while|for|return)\b'),   # Palabras clave: print, int, etc.
            
            # [a-zA-Z_] -> Obliga a empezar con una letra o guion bajo
            # \w* -> Los siguientes caracteres pueden ser cualquier numero, letra o guion bajo
            ('IDENTIFIER', r'[a-zA-Z_]\w*'),    # Identificador como variables
            ('OPERATOR', r'(?:=|\+| - |/|//|\*|%)'),  # Encuentra el operador de asignacion y los numericos
            # \d+ Encuentra uno o mas digitos del 0 al 9.
            ('CONSTANT', r'\b\d+\b'),    # Encuentra los numeros del 0-9
            ('PUNCTUATION', r'[;(){},\[\]]'),  # Encuentra puntuaciones
            ('LITERAL', r'"[^"]*"'),   # Encuentra cualquier texto dentro de las comillas ""
            ('NEWLINE', r'\n'),   # Busca saltos de linea
            # Busca un espacio, una tabulacion o mas
            ('BLANK_SPACE', r'[ \t]+'),
            # . Cualquier caracter que no es salto de linea
            ('ERROR', r'.')  # Un error puede provenir de cualquier caracter
        ]
        
        # Genera una expresion regular donde inluye la siguiente forma:
        # regex = '(?P<TIPO_DE_TOKEN> patron_del_token) | ...'
        self.regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in self.tokens_type)
        
    
    def tokenize(self):
        
        # Utiliza finditer para encontrar todos los patrones del texto finditer(patron, texto)
        # Obtenemos con match el objeto obtenido por cada coincidencia
        for match in re.finditer(self.regex, self.source_code):
            kind = match.lastgroup  # Obtiene el tipo del token
            value = match.group()   # Obtiene el patron que coincidio
            column = match.start() - self.line_start  # Obtiene la columna en la que se obtuvo el token actual
            
            # Si identifica un salto de linea suma 
            if kind == 'NEWLINE':
                self.line_number += 1
                # Actualiza la posicion de inicio de la linea con la ultima posicion de esta linea
                self.line_start = match.end()  
                continue
            
            # Si es una tabulacion o espacio en blanco lo ignora
            elif kind == 'BLANK_SPACE':
                continue
            
            # Si no coincide con ningun token anterior entonces es un error
            elif kind == 'ERROR':
            # Se reporta este error en el manejador
                self.error_handler.lexical_report(f"Character not recognized '{value}'", self.line_number, column)
                continue
            
            # Agrega un objeto de Token a la lista de tokens, incluye sus caracteristicas.
            self.tokens.append(Token(kind, value, self.line_number, column))
    
    # Para imprimir el reporte de los tokens identificados
    def print_report(self):
        print('-----Tokens List-----')
        for token in self.tokens:
            print(f'{token.type.lower()} {token.value}')
        
        print(f'\n*Total of tokens: {len(self.tokens)}')       

# Main del programa
if __name__ == '__main__':
    
    # Ejemplos con los que probar
    example1 = 'print("This is an example");'
    example2 = 'int a=10;'
    example3 = """int a = 10;
print("This is an example!!!!");
int b = 20;
float c = (500 * 4) / 20 + 1 - 10;
print(c);
print(!!!"hello"); 
string answer_5 = c;
"""
    # Se crea el objeto del manejador de errores
    err_handler = errorHandler()
    lexer = Lexer(example3, err_handler) # Se crea el lexer con el string insertado
    
    # Convierte a tokens el analizador lexico
    lexer.tokenize()
    lexer.print_report()  # Imprime el reporte
    
    # Si es que tiene errores lexicos los imprime
    if err_handler.has_errors():
        err_handler.print_errors()

