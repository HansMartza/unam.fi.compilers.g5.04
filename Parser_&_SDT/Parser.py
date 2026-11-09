# Permite analizar expresiones regulares en texto crudo: r''
# El texto crudo significa que toma en cuenta saltos de linea y espacios.
import re

# Clase que identifica los errores
class errorHandler:
    # Dentro de la lista se agregan todos los errores
    def __init__(self):
        self.errors = []
    
    # Para reportar errores lexicos/parsing/std muesta el mensaje, la linea y columna en la que ocurrio 
    def add_error_report(self, message, line, column, type):
        self.errors.append(f"{type} Error [Line {line}, Column {column}]: {message}")
        
    # Devuelve el numero de errores que hay en la lista
    def has_errors(self):
        return len(self.errors) > 0
    
    #def parsing_report(self, message, line, column):
    #    self.errors.append(f"Parsing Error [Line {line}, Column {column}]: {message}")
    
    #def sdt_report(self, message, line, column):
    #        self.errors.append(f"Lexical Error [Line {line}, Column {column}]: {message}")
    
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
            ('DECIMAL', r'\d*\.\d+'),  # Encuentra los puntos decimales, \d+ obliga a que existan numeros. Permite 8, 8.6, .5
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
                self.error_handler.add_error_report(f"Character not recognized '{value}'", self.line_number, column, "Lexical")
                continue
            
            # Agrega un objeto de Token a la lista de tokens, incluye sus caracteristicas.
            self.tokens.append(Token(kind, value, self.line_number, column))
    
    # Para imprimir el reporte de los tokens identificados
    def print_report(self):
        print('-----Tokens List-----')
        for token in self.tokens:
            print(f'{token.type.lower()} {token.value}')
        
        print(f'\n*Total of tokens: {len(self.tokens)}')      
        

""" #################
INICIO DEL ANALIZADOR SEMANTICO
##################"""

# Crea la clase del Parser
class ParserSDT:
    
    # Situacion actual del parser, se van a ingresar tokens
    def __init__(self, tokens, error_handler):
        
        self.error_handler = error_handler  # El objeto de manejo de errores.
        self.tokens = tokens  # Obtenemos la lista de tokens
        self.position = 0  # Contador para la posicion del token
        
        # Si no esta vacia la lista de tokens
        if self.tokens:
            # Se guarda el token de esta posicion
            self.current_token = self.tokens[self.position]
        else:
            # De lo contrario no hay ningun token seleccionado
            self.current_token = None
        
        # Banderas de estado.
        self.parsing_success = True  # Si el Parser es correcto
        self.sdt_success = True  # Si es posible realizar la instruccion en el sdt
        self.error_reported = False  # Si surge algun error que reportar

    # Definimos el metodo de "look_ahead" para revisar el siguiente token
    def look_ahead(self):
        self.position += 1 # Aumenta la posicion
        if self.position < len(self.tokens): # Mientras exista la posiciion del token
            self.current_token = self.tokens[self.position] # Actualiza el token actual
        # Si ya no existen mas tokens
        else:
            self.current_token = None # Almacena en el token actual None

    # Sirve para comparar si el token esperado concuerda con el token revisado
    # Ingresa el tipo esperado y valor esperado si es que es el caso
    def match(self, expected_type, expected_value = None):
        # Si existe un token actual, y su tipo concuerda con el tipo esperado
        if self.current_token and self.current_token.type == expected_type:
            # Si es que no tiene el valor esperado
            if expected_value and self.current_token.value != expected_value:
                self.report_error('parsing', f"Expected Value: {expected_value}")  # Genera el reporte de error de parsing
                return None
            
            # Obtiene el token actual
            token = self.current_token  
            self.look_ahead() #Y usa el look_ahead para actualizar el current_token
            return token
        else:
            # Si no coincide con el tipo, genera un error de parsing
            self.report_error('parsing', f"Expected Type: {expected_type}") 
            return None

    # Actualiza las banderas si ocurre un error
    def report_error(self, error_type, message):
        if self.error_reported:
            return  # Evita múltiples reportes de error en cascada
        
        # Se vuelve True el error reportado
        self.error_reported = True
        # Si existe, almacena la linea o columna, si no solo usa n
        line = self.current_token.line if self.current_token else "n"
        column = self.current_token.column if self.current_token else "n"
        
        # Si el error es del parseo
        if error_type == 'parsing':
            self.parsing_success = False
            self.sdt_success = False
            self.error_handler.add_error_report(message, line, column, "Parsing")
            self.error_handler.print_errors()
            print("SDT error...")
        
        # Si el error es logico
        elif error_type == 'sdt':
            self.sdt_success = False
            print("Parsing Success!")
            self.error_handler.add_error_report(message, line, column, "SDT")
            self.error_handler.print_errors()
            #print("SDT error...")

    # Realiza el proceso de parsear
    def parse(self):
        # Parsea sentencias mientras haya tokens, este activa la bandera del parseo y no haya errores
        while self.current_token is not None and self.parsing_success and not self.error_reported:
            self.statement()  # Inicia revisando la declaracion
        
        # Si termina sin reportar errores, imprime que funciono correctamente
        if not self.error_reported:
            print("Parsing Success!")
            print("SDT Verified!")

    # Metodo que define si inicia con la declaracion
    def statement(self):
        # Si no existe un token actual, regresa
        if not self.current_token:
            return

        # El tipo del token debe ser una palabra clave
        if self.current_token.type == 'KEYWORD':
            
            # Si su valor es un int, float o string significa que es una declaracion de variable
            if self.current_token.value in ['int', 'float', 'string']:
                self.declaration()
            
            # Si su valor es un print, indica que debe iniciar un proceso de print
            elif self.current_token.value == 'print':
                self.print_statement()
            
            # De otra forma usa look_ahead  -------
            else:
                self.look_ahead()
        
        # Al no iniciar con una palabra clave, reporta un error de parsing
        else:
            self.report_error('parsing', f"Expected Type in the start of the statement: KEYWORD")  

    # Revisa si es correcta la declaracion de variables. Sigue la gramatica:
    # KEYWORD IDENTIFIER '=' EXPRESSION ';'
    def declaration(self):
        
        # Revisa si inicia con una palabra clave con match 
        keyword_token = self.match('KEYWORD')
        if not keyword_token: 
            return  # Si no coincide un match termina la declaracion
        
        # Se guarda el valor declarado (int, string, float) para el SDT
        declared_type = keyword_token.value  
        
        # Revisa si el siguiente match es un identificador de la variable
        if not self.match('IDENTIFIER'): 
            return
        # Revisa si el siguiente match es un operador con el valor de =
        if not self.match('OPERATOR', '='): 
            return
        
        # Almacena la expresion que tomara el identificador (10, "hello")
        expr_token = self.current_token
        
        # Si la expresion es de tipo constante, decimal o literal
        if self.current_token.type in ['CONSTANT', 'LITERAL', 'DECIMAL']:
            self.look_ahead()  # Usa look_ahead para pasar a la puntuacion
        else:
            self.report_error('parsing', f"Expected Types in the Expression: CONSTANT. DECIMAL or LITERAL")  # De lo contrario es un error en parsing
            return

        # Revisa con match si el ultimo termino es un token de puntuacion con valor de ;
        if not self.match('PUNCTUATION', ';'): 
            return
        
        # --- REGLAS SDT (Análisis Semántico) ---
        # Verificamos que el tipo de variable coincida con el valor asignado
        
        # Primero observa si el parsing fue un exito y no existen errores reportados
        if self.parsing_success and not self.error_reported:
            
            # Primera regla: si el tipo es int, su expresion debe ser una constante
            if declared_type == 'int' and expr_token.type != 'CONSTANT':
                # De lo contrario, reporta un error en sdt
                self.report_error('sdt', "Expression Expected with int: CONSTANT")  
            
            # Segunda regla: Si el tipo es un string, su expresion debe ser una literal
            elif declared_type == 'float' and expr_token.type != 'DECIMAL':
                self.report_error('sdt', "Expression Expected with float: DECIMAL")
            
            # Tercera regla: Si el tipo es un string, su expresion debe ser una literal
            elif declared_type == 'string' and expr_token.type != 'LITERAL':
                self.report_error('sdt', "Expression Expected in string: LITERAL")

    # Revisa si es correcta la funcion print. Cumple con la gramatica: 
    # 'print' '(' (LITERAL | IDENTIFIER | CONSTANT | DECIMAL) ')' ';'
    
    def print_statement(self):
        
        # Realiza match comprobando que inicia con un token KEYWORD con valor print
        if not self.match('KEYWORD', 'print'): 
            return
        # Realiza match comprobando que continua con PUNCTUATION con valor (
        if not self.match('PUNCTUATION', '('): 
            return
        
        # Si sigue con una literal, identificador o constante
        if self.current_token.type in ['LITERAL', 'IDENTIFIER', 'CONSTANT', 'DECIMAL']:
            self.look_ahead() # Realiza un look_ahead para pasar a la puntuacion
        else:
            self.report_error('parsing', f"Expected Types in the print statement: \nCONSTANT, DECIMAL, LITERAL or IDENTIFIER")  # Si es de otro tipo es un error
            return
            
        # Revisa que el siguiente match sea un )
        if not self.match('PUNCTUATION', ')'): 
            return
        
        # Revisa que el siguiente match sea un ;
        if not self.match('PUNCTUATION', ';'): 
            return

# ---------------------------------------
# Probando su funcionamiento
if __name__ == '__main__':
    
    # Codigo a probar
    codigo_correcto = """float a = 7.8;
print("Hellooo");
string answer = "Correct";
"""

    codigo_error_parsing = """float int = 7.8;
print("Hellooo");
string answer = "Correct";
"""
    codigo_error_sdt = """string a = 7.8;
    print("Hellooo");
    string answer = "Correct";
    """
    
    # Inicia con el analizador lexico
    err_handler = errorHandler()  # Inicializa el manejador de errores
    lexer = Lexer(codigo_correcto, err_handler) # Ejecuta el lexer
    lexer.tokenize() # Obtiene toda la lista de tokens en el lexer
    
    #lexer.print_report()
    
    # Si hay errores léxicos, se detiene. 
    if err_handler.has_errors():
        err_handler.print_errors()
    else:  # Si no, pasamos al Parser.
        
        # Ejecutar el Parser & SDT
        print("\n--- Executing Parser & SDT ---")
        parser = ParserSDT(lexer.tokens, err_handler)  # Genera el objeto del parser introduciendo los tokens
        parser.parse()  # Realiza el parseo 