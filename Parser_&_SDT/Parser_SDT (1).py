# Permite analizar expresiones regulares en texto crudo: r''
# El texto crudo significa que toma en cuenta saltos de linea y espacios.
import re

class errorHandler:
    
    def __init__(self):
        self.errors = []  # Lista de errores reportados
        self.has_parsing_error = False  # Banderas de error en el manejador de errores
        self.has_sdt_error = False
    
    # Para reportar errores lexicos/parsing/sdt muestra el mensaje, la linea y columna en la que ocurrio 
    def add_error_report(self, message, line, column, error_type):
        self.errors.append(f"{error_type} Error [Line {line}, Column {column}]: {message}")
        
        if error_type == "Parsing":  # Activa las banderas si hay un error de este tipo
            self.has_parsing_error = True
        elif error_type == "SDT":
            self.has_sdt_error = True
        
    # Devuelve el numero de errores que hay en la lista
    def has_errors(self):
        return len(self.errors) > 0

    # Imprime error por error detectado 
    def print_errors(self):
        print("\n--- Report of errors ---")
        for err in self.errors:  # Recorre la lista para imprimirlos
            print(err)
    
    # Estructura de como quedan los errores dependiendo de las banderas activas
    def print_final_status(self):
        if self.has_parsing_error:
            print("Parsing error...")
            print("SDT error...")
        elif self.has_sdt_error:
            print("Parsing Success!")
            print("SDT error...")
        elif not self.has_parsing_error and not self.has_sdt_error:
            print("Parsing Success!")
            print("SDT Verified!")
        else:
            print()

        if self.has_errors(): # Imprime los detalles de lineas y columnas
            print("\n--- Error Details ---")
            for err in self.errors:
                print(err)
    


# Caracteristicas de un Token: Su tipo, el valueor, y posicion en linea y columna
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
INICIO DEL PARSER
##################"""

# Creacion del Nodo del arbol, el cual cambia caracteristicas dependiendo 
# de como se divide la gramatica
class Node:
    pass

# Inicia con el nodo del programa completo
class ProgramNode(Node):
    def __init__(self, statements):
        self.statements = statements  # Se divide por sus statment, como si fuera el nodo raiz

# Si es un nodo de declaracion debe contener lo siguiente: 
class DeclarationNode(Node):
    def __init__(self, d_type, type_value, var_value, exp_node, line, column):
        self.d_type = d_type       # 'Int', 'Float', 'String'  para identificar el tipo dentro del codigo
        self.type_val = type_value   # 'int', 'float', 'string' asignado al token
        self.var_val = var_value     # Nombre de la variable (ej. 'x')
        self.exp_node = exp_node   # El sub-árbol de la expresión matemática/literal
        self.line = line           # Línea para el reporte de error
        self.column = column       # Columna para el reporte de error

# Si es un nodo para usar el print
class PrintStatementNode(Node):
    # Almacena el tipo que se quiere imprimir
    def __init__(self, print_value_node): 
        self.print_value_node = print_value_node

# Si es un nodo para operaciones binarias
class BinaryOpNode(Node):
    def __init__(self, rule_name, left, op, right, line, column):
        self.rule_name = rule_name  # Ingresa el nombre de la regla
        self.left = left  # Termino izquierdo
        self.op = op  # Operador
        self.right = right  # Termino derecho
        self.line = line  # Linea y columna de este operador
        self.column = column

# Identifica el valor con el que se esta trabajando
class ValueNode(Node):
    def __init__(self, rule_name, value):
        self.rule_name = rule_name  # El nombre de la regla gramatical (ValorF, ValorO, ValorS)
        self.value = value  # El valor de la variable que guarda (numeros, literal, otro nodo Value)

# Inicio de la construccion del arbol Parser TOP-DOWN
class ParserTreeBuilder:
    # Almacena la lista de tokens y el manejador de errores
    def __init__(self, tokens, error_handler):
        self.error_handler = error_handler  # El objeto de manejo de errores.
        self.tokens = tokens  # Obtenemos la lista de tokens
        self.position = 0  # Contador para la posicion del token
        self.last_token = None  # [CORRECCION 6] Ultimo token que ya se reviso
        
        # Si no esta vacia la lista de tokens
        if self.tokens:
            # Se guarda el token de esta posicion
            self.current_token = self.tokens[self.position]
        else:
            # De lo contrario no hay ningun token seleccionado
            self.current_token = None

    # Definimos el metodo de "look_ahead" para revisar el siguiente token
    def look_ahead(self):
        self.last_token = self.current_token  # [CORRECCION 6] Antes de avanzar, recuerda el token actual
        self.position += 1 # Aumenta la posicion
        if self.position < len(self.tokens): # Mientras exista la posicion del token
            self.current_token = self.tokens[self.position] # Actualiza el token actual
        # Si ya no existen mas tokens
        else:
            self.current_token = None # Almacena en el token actual None

    # Sirve para comparar si el token esperado concuerda con el token revisado
    # Ingresa el tipo esperado y valueor esperado si es que es el caso
    def match(self, expected_type, expected_valueue = None):
        # Si existe un token actual, y su tipo concuerda con el tipo esperado
        if self.current_token and self.current_token.type == expected_type:
            # Si es que no tiene el valueor esperado
            if expected_valueue and self.current_token.value != expected_valueue:
                # [CORRECCION 6] Si falta un ';' o ')', el error es de la palabra anterior
                if expected_valueue in [';', ')'] and self.last_token:
                    self.report_error(f"Expected '{expected_valueue}' after '{self.last_token.value}'", self.last_token)
                else:
                    self.report_error(f"Expected {expected_valueue}")  # [CORRECCION 7] Usa report_error para no repetir errores
                return None  # Y regresa None
            
            # Obtiene el token actual
            token = self.current_token  
            self.look_ahead() #Y usa el look_ahead para actualizar el current_token
            return token  # Regresa el token del match revisado
        
        else:
            # [CORRECCION 6] Si falta un ';' o ')', el error es de la palabra anterior
            if expected_valueue in [';', ')'] and self.last_token:
                self.report_error(f"Expected '{expected_valueue}' after '{self.last_token.value}'", self.last_token)
            # Si no coincide con el tipo, genera un error de parsing
            else:
                self.report_error(f"Expected Type: {expected_type}")  # [CORRECCION 7] Usa report_error para no repetir errores
            return None  # regresa None

    # Reportar errores esecificamente del parsing
    # [CORRECCION 6] Puede recibir el token exacto del error para reportar la linea correcta
    def report_error(self, message, token=None):
        # Si es que no existen errores de parsing antes
        if not self.error_handler.has_parsing_error:
            # Si no se indica el token, usa el actual (o el ultimo, si ya se acabaron)
            if token is None:
                token = self.current_token if self.current_token else self.last_token
            # Si es posible, almacena la linea o columna, si no solo usa n
            line = token.line if token else "n"
            column = token.column if token else "n"
            # Manda el reporte del error 
            self.error_handler.add_error_report(message, line, column, "Parsing")

    # Realiza el proceso de parse
    def parse(self):
        # Almacena una lista de statments
        statements = []
        
        # Parsea sentencias mientras haya tokens y no haya errores de parsing
        while self.current_token is not None and not self.error_handler.has_parsing_error:  
            actual_statement = self.statement()  # Almacena la linea del codigo actual
            if actual_statement:  # Si es que existe
                statements.append(actual_statement)  # Lo guarda en la lista
        return ProgramNode(statements)  # Genera el arbol con la lista de statements

    # Como se define un statement
    def statement(self):
        # Si no existe un token actual, regresa un None
        if not self.current_token:
            return None
        
        # Almacena lo que contiene el token 
        token_value = self.current_token.value
        
        # Mapeo a Statement -> DeclarationFloat | DeclarationInt | DeclarationString | PrintStatement
        # Cada funcion regresa un statement al final
        if token_value == 'int': 
            return self.declaration_int()
        elif token_value == 'float': 
            return self.declaration_float()
        elif token_value == 'string': 
            return self.declaration_string()
        elif token_value == 'print': 
            return self.print_statement()
        else:
            # Si no coincide estas KEYWORD, entonces es un error
            # [CORRECCION 7] Un solo reporte (antes se reportaba dos veces con match('ERROR'))
            self.report_error(f"Expected Statement (int, float, string or print), found '{token_value}'")
            return None  # No regresa nada. El error detiene el ciclo de parse()

    # Revisa si es correcta la declaracion de variable de int
    # int IDENTIFIER = EXPRESSION; 
    def declaration_int(self):
        
        # Realiza match para verificar este nivel
        t = self.match('KEYWORD', 'int')  # Inicia con KEYWORD int
        if not t: 
            return None  # Retorna inmediatamente si falla
        
        v = self.match('IDENTIFIER')  # Si sigue un IDENTIFIER
        if not v: 
            return None
        
        if not self.match('OPERATOR', '='): # Sigue un = 
            return None
        
        # Baja un nivel al nodo de expression
        e = self.expresion_i()   # Al ser numerico primero empieza con su ultima prioridad (+ o -)
        if e is None or self.error_handler.has_parsing_error:  # [CORRECCION 2] Si la expresion estaba mal, se detiene
            return None
        
        if not self.match('PUNCTUATION', ';'):  # Finaliza con ;
            return None 
        
        # Termina el nodo de declaracion con los valores obtenidos
        return DeclarationNode('Int', t.value, v.value, e, t.line, t.column) 

    # Analiza la expresion ingresada si debe hacer una operacion de + o -
    def expresion_i(self):
        
        # Revisa un nivel mas bajo al arbol para ver si tiene que hacer *, / o %
        node = self.valor_t()
        
        # Mientras exista un token y encuentre un operador de + o -
        while self.current_token and self.current_token.value in ['+', '-']:
            operator = self.current_token  # Guarda este operador
            self.match('OPERATOR')  # Y comprueba con match
            
            # Obtiene un nuevo nodo, enviando un nivel mas abajo la operacion binaria a realizar
            node = BinaryOpNode('ExpresionI', node, operator.value, self.valor_t(), operator.line, operator.column)
        return node  # Regresa el nodo como la expresion esperada
    
    # Analiza si hay que realizar una operacion con prioridad (*, /, %)
    def valor_t(self):
        # Baja un nivel para obtener el valor numerico 
        node = self.valor_o()
        
        # Mientras existan tokens y operadores de prioridad de * / %
        while self.current_token and self.current_token.value in ['*', '/', '%']:
            operator_token = self.current_token  # Obtiene el token del operador
            self.match('OPERATOR')  # Realiza el match
            # Hace la operacion binaria
            node = BinaryOpNode('ValorT', node, operator_token.value, self.valor_o(), operator_token.line, operator_token.column)
        return node # Regresa el nodo
    
    # Paso intermedio para obtener el valor
    def valor_o(self):
        return ValueNode('ValorO', self.valor_i())   # Con valor_i() obtiene el tipo de dato con el que se trabaja

    # Permite que valor_i() acepte flotantes y strings sin lanzar error de parsing
    def valor_i(self):
        tok = self.current_token   # Obtiene el token actual
        
        # [CORRECCION 3] Si ya no hay tokens, el codigo termino antes de tiempo (ej: "int x =")
        if tok is None:
            self.report_error("Expected a value but the input ended")
            return None
        
        # Dependiendo de su tipo lo almacena con diferentes valores
        if tok.type == 'CONSTANT':          
            return ValueNode('ValorI', int(self.match('CONSTANT').value))  # Hace match y de su value lo vuelve int. (Se guarda como ValorI)
        elif tok.type == 'DECIMAL':
            return ValueNode('ValorF', float(self.match('DECIMAL').value)) # Hace match y de su value lo vuelve float (Se guarda como ValorF)
        elif tok.type == 'LITERAL':
            return ValueNode('ValorS', self.match('LITERAL').value) # Hace match y se queda como string (Se guarda como ValorS)
        
        # Si es un parentesis entonces revisa si cumple la estructura (expression_i)
        elif tok.value == '(':
            self.match('PUNCTUATION', '(')
            node = self.expresion_i()
            self.match('PUNCTUATION', ')')
            return node
        
        # [CORRECCION 2] Cualquier otra cosa (;, =, una variable...) no es un valor valido
        else:
            self.report_error(f"Expected a value (CONSTANT, DECIMAL, LITERAL or '('), found '{tok.value}'")
            return None
        
    # GRAMÁTICA FLOAT: De forma similar a int, revisa que cumpla: float IDENTIFIER = EXPRESSION;
    def declaration_float(self):
        
        t = self.match('KEYWORD', 'float') # Comprueba con match
        if not t: 
            return None # Y si no cumple, se regresa
        
        v = self.match('IDENTIFIER')  # Sigue un IDENTIFIER
        if not v: 
            return None
        
        if not self.match('OPERATOR', '='): # Sigue un =
            return None
        
        e = self.expresion_f()  # Baja un nivel a la gramatica de expression_f 
        if e is None or self.error_handler.has_parsing_error:  # [CORRECCION 2] Si la expresion estaba mal, se detiene
            return None
        
        if not self.match('PUNCTUATION', ';'):  # Comprueba que termine con ;
            return None
        
        # Termina el nodo de declaracion
        return DeclarationNode('Float', t.value, v.value, e, t.line, t.column)

    # Expression f para comprobar si se hace una operacion de + o -
    def expresion_f(self):
        node = self.valor_q()  # Baja de nivel para ver si existe otra operacion de pprioridad
        
        while self.current_token and self.current_token.value in ['+', '-']: # Si no entonces lo hace con BinaryOpNode
            operator_token = self.current_token
            self.match('OPERATOR')
            node = BinaryOpNode('ExpresionF', node, operator_token.value, self.valor_q(), operator_token.line, operator_token.column)
        return node  # Regresa el resultado

    # Observa si hace operaciones de prioridad de *, / o %
    def valor_q(self):
        node = self.valor_h()  # Baja un nivel para obtener el valor numerico
        while self.current_token and self.current_token.value in ['*', '/', '%']:  # Realiza las operaciones con BinaryOpNode
            operator_token = self.current_token
            self.match('OPERATOR')
            node = BinaryOpNode('ValorQ', node, operator_token.value, self.valor_h(), operator_token.line, operator_token.column)  # [CORRECCION 8] antes decia .value
        return node  # Regresa resultado

    # Paso intermedio para obtener numeros
    def valor_h(self):
        return ValueNode('ValorH', self.valor_f())

    # Has lo mismo para valor_f(), identifica tipo de dato para almacenarlo en su nodo
    def valor_f(self):
        tok = self.current_token
        
        # [CORRECCION 3] Si ya no hay tokens, el codigo termino antes de tiempo (ej: "float x =")
        if tok is None:
            self.report_error("Expected a value but the input ended")
            return None
        
        if tok.type == 'DECIMAL':
            return ValueNode('ValorF', float(self.match('DECIMAL').value))  # ValorF para float
        elif tok.type == 'CONSTANT':
            return ValueNode('ValorI', int(self.match('CONSTANT').value))  #ValorI para int
        elif tok.type == 'LITERAL':
            return ValueNode('ValorS', self.match('LITERAL').value)  # ValorS para string
        
        # Si hay parentesis revisa si hay expresiones adentro
        elif tok.value == '(':  
            self.match('PUNCTUATION', '(')
            node = self.expresion_f()
            self.match('PUNCTUATION', ')')
            return node  # Regresa este resultado
        
        # [CORRECCION 2] Cualquier otra cosa (;, =, una variable...) no es un valor valido
        else:
            self.report_error(f"Expected a value (CONSTANT, DECIMAL, LITERAL or '('), found '{tok.value}'")
            return None

    # GRAMÁTICA STRING: De forma similar, revisa que cumpla: string IDENTIFIER = EXPRESSION;
    def declaration_string(self):
        t = self.match('KEYWORD', 'string')  # Revisa con match
        if not t: 
            return None  # Si no cumple se regresa
        
        v = self.match('IDENTIFIER')
        if not v: 
            return None
        
        if not self.match('OPERATOR', '='): 
            return None
        
        # En lugar de forzar un LITERAL, leemos el token actual (sea el que sea)
        token = self.current_token 
        if not token:
            self.report_error("Expected a value but the input ended")  # [CORRECCION 3] Antes regresaba sin reportar nada
            return None
        
        # Identificamos su tipo y lo guardamos en su nodo
        if token.type == 'LITERAL':
            val_node = ValueNode('ValorS', token.value)
        elif token.type == 'CONSTANT':
            val_node = ValueNode('ValorI', int(token.value))
        elif token.type == 'DECIMAL':
            val_node = ValueNode('ValorF', float(token.value))
        else:
            # [CORRECCION 2] Antes creaba un nodo 'Error' pero nunca lo reportaba
            self.report_error(f"Expected a value (LITERAL, CONSTANT or DECIMAL), found '{token.value}'")
            return None
        
        self.look_ahead() # Avanzamos con un look_ahead()
        
        if not self.match('PUNCTUATION', ';'):  # Revisamos si termina con ;
            return None
        
        # Termina el nodo de declaracion
        return DeclarationNode('String', t.value, v.value, val_node, t.line, t.column)
    
    # Revisa si es correcta la funcion print. Cumple con la gramatica: 
    # 'print' '(' (LITERAL | IDENTIFIER | CONSTANT | DECIMAL) ')' ';'
    def print_statement(self):
        
        # Revisa que el token es un print_statement
        if not self.match('KEYWORD', 'print'): 
            return None
        
        # Realiza match comprobando que continua con PUNCTUATION con valor (
        if not self.match('PUNCTUATION', '('):
            return None
        
        # [CORRECCION 3] Si ya no hay tokens, el codigo termino antes de tiempo (ej: "print(")
        if self.current_token is None:
            self.report_error("Expected a value but the input ended")
            return None
        
        # Pequeño lookahead semántico para enrutar el valor
        if self.current_token.type == 'LITERAL':  # Si se trata de una literal
            token_value = ValueNode('ValorS', self.match('LITERAL').value) # Simplemente guarda su valor S
        elif self.current_token.type == 'CONSTANT':  # Si es constante revisa sus posibles hijos en su expresion
            token_value = self.expresion_i()
        elif self.current_token.type == 'DECIMAL':# Si es decimal revisa sus posibles hijos en su expresion
            token_value = self.expresion_f()
        else:
            # [CORRECCION 2] Antes creaba un nodo 'Error' pero nunca lo reportaba
            self.report_error(f"Expected a value in print (LITERAL, CONSTANT or DECIMAL), found '{self.current_token.value}'")
            return None
        
        # [CORRECCION 2] Si la expresion dentro del print estaba mal, se detiene
        if token_value is None or self.error_handler.has_parsing_error:
            return None
        
        # Revisa que el siguiente match sea un ) y ;
        if not self.match('PUNCTUATION', ')'):
            return None
        if not self.match('PUNCTUATION', ';'):
            return None
        
        return PrintStatementNode(token_value) # Regresa el Statement creado

# RECORRIDO TOP-DOWN Y ANÁLISIS SEMÁNTICO (SDT)
class SemanticAnalyzer:
    
    # Se le envia el manejador de errores
    def __init__(self, error_handler):
        self.error_handler = error_handler
        self.trace_log = []  # El proceso de cada regla se guarda aquí.
    
    # Imprime el proceso de las reglas
    def print_sdt_trace(self):
        
        if not self.trace_log: # Si la lista esta vacia, no envia nada
            print("There is not SDT available.")
            return
            
        print("\n--- Trace of SDT ---")  # Imprime todas las reglas usadas
        for trace in self.trace_log:
            print(trace)

    # Por cada statement del nodo, identifica que tipo de nodo se trata
    def visit(self, node):
        # [CORRECCION 9] Ya no se detiene en el primer error SDT: revisa TODAS las sentencias.
        # Si una sentencia tiene error, sus funciones regresan None y solo esa sentencia se detiene.

        # Revisa un objeto para ver si pertenece a una clase. Ejemplo: isinstance(edad=25, int) -> True
        # En este caso revisa si es la raiz
        if isinstance(node, ProgramNode):
            for actual_statement in node.statements:  # Revisa toda su lista de statements 
                self.visit(actual_statement)  # Los visita en recursion
            
        # Si es un nodo de declaracion
        elif isinstance(node, DeclarationNode):
            # 1. Obtenemos el valor real de la expresión (ej. 5, 5.5, o "Hola")
            val = self.visit(node.exp_node)
            if val is None: 
                return None # Si hubo error matemático interno, subimos el error
            
            # 2. VALIDACIÓN DE TIPOS (Type Checking)
            is_valid = False  # Bandera para saber si es valido
            if node.d_type == 'Int' and isinstance(val, int):  # Comprobamos su tipo de dato junto con el valor almacenado 
                is_valid = True  # Si lo cumple cambia la bandera a True
            elif node.d_type == 'Float' and isinstance(val, float):
                is_valid = True
            elif node.d_type == 'String' and isinstance(val, str):
                is_valid = True
                
            # 3. LANZAR EL MENSAJE DE ERROR ÚNICO SI NO COINCIDEN
            if not is_valid:
                # Si hubo un error, significa que no estuvo bien asignado el tipo de la variable junto con su valor guardado
                mensaje = (f"Type Mismatch: Variable type: {node.type_val}, Assigned Type: {type(val).__name__}")
                self.error_handler.add_error_report(mensaje, node.line, node.column, "SDT")  # Se reporta el error
                return None # Y regresa
            
            # Si todo está bien, generamos la traza (SDT Rule) para imprimirlo opcionalmente
            letra = node.d_type[0]  # Obtenemos de que tipo es
            sdt_string = f"{node.type_val} {node.var_val} '=' {val} ';'"  # Guardamos el string con la forma del resultado de la regla
            
            # Agregamos a la lista del historial del reporte de las declaraciones, Statement y Program
            self.trace_log.append(f"Declaration{node.d_type}{{{letra}.exp = {sdt_string}}}")
            self.trace_log.append(f"Statement{{Statement = {sdt_string}}}")
            self.trace_log.append(f"Program{{Program = {sdt_string}}}")
        
        # Si es un nodo de operacion binaria
        elif isinstance(node, BinaryOpNode):
            # Obtenemos los valores del lado izquierdo y derecho
            left_val = self.visit(node.left)
            right_val = self.visit(node.right)
            
            if left_val is None or right_val is None: # Y si alguno es None se regresa
                return None
            
            # [CORRECCION 4] No se pueden hacer operaciones con texto (ej: "a" + 3). Antes el programa tronaba
            if isinstance(left_val, str) or isinstance(right_val, str):
                self.error_handler.add_error_report(f"Semantic Error: Operator '{node.op}' cannot be used with a string", node.line, node.column, "SDT")
                return None
            
            # --- DETECCIÓN DE ERROR SDT ---
            if node.op == '/':  # Otro error semantico es dividir por cero
                if right_val == 0:
                    # Reporte de error semántico exacto (la sintaxis es correcta, la matemática no)
                    self.error_handler.add_error_report("Semantic Error: Division by zero", node.line, node.column, "SDT")
                    return None  # No regresa nada
                # [CORRECCION 1] Si los dos son enteros, la division es entera (10 / 2 = 5, no 5.0)
                if isinstance(left_val, int) and isinstance(right_val, int):
                    result = left_val // right_val
                else:
                    result = left_val / right_val  # Si alguno es decimal, el resultado es decimal
                
            elif node.op == '%':  # Lo mismo aplica para el modulo
                if right_val == 0:
                    self.error_handler.add_error_report("Semantic Error: Modulo by zero", node.line, node.column, "SDT")
                    return None 
                result = left_val % right_val  # Cualquier otro numero hace su modulo
            
            # Dependiendo del operador, realiza su operacion correspondiente
            elif node.op == '+': 
                result = left_val + right_val
            elif node.op == '-': 
                result = left_val - right_val
            elif node.op == '*': 
                result = left_val * right_val
            
            # Almacena el proceso realizado por las reglas
            letra = node.rule_name[-1] if node.rule_name[-1].isupper() else 'exp'
            self.trace_log.append(f"{node.rule_name}{{{letra} = {result}}}")  # Y lo agrega al historial
            return result  # Al final resuelve el resultado de la operacion
            
        # Si es un ValueNode obtiene su valor minimo
        elif isinstance(node, ValueNode):
            # Si tiene un hijo lo visita, si no es asi entonces obtiene el valor de este nodo
            val = self.visit(node.value) if isinstance(node.value, Node) else node.value
            
            # Almaccena en el historial el proceso de las reglas
            letra = node.rule_name[-1] if node.rule_name[-1].isupper() else 'val'
            self.trace_log.append(f"{node.rule_name}{{{letra}.value = {val}}}")
            return val  # Regresa el valor minimo
            
        #Si es un nodo de PrintStatement
        elif isinstance(node, PrintStatementNode):
            val = self.visit(node.print_value_node) # Solo se visita a si mismo
            # Y si es valido,entonces guarda el historial de esta regla
            if val is not None:
                self.trace_log.append(f"ValorPrint{{Print.value = {val}}}")
                self.trace_log.append(f"PrintStatement{{P.val = print ({val}) ';'}} ")


# Principal
if __name__ == '__main__':
    
    # Codigo a probar
    codigo_correcto = """int x = 10 + 3 ;
"""
    # Error al construir el arbol
    codigo_error_parsing = """int float = 2323.32;
"""
    # Error mismatch
    codigo_error_sdt = """int a = 7.8;
    print("Hellooo");
    string answer = "Correct";
    """
    
    err_handler = errorHandler()  # Crea objeto de manejador de errores
    lexer = Lexer(codigo_correcto, err_handler)
    lexer.tokenize()  # Lista de tokens
    
    # Si tiene errores se detiene
    if err_handler.has_errors():
        err_handler.print_errors()
    
    else:
        # Crea el objeto del parser
        parser = ParserTreeBuilder(lexer.tokens, err_handler)
        ast_root = parser.parse()  # Construye el arbol, empieza desde la raiz
        
        if not err_handler.has_parsing_error:  # Si no tiene errores de parseo sigue
            
            semantic = SemanticAnalyzer(err_handler)  # Realiza objeto del analizador semantico
            semantic.visit(ast_root)  # Visita desde el raiz
            #semantic.print_sdt_trace()   # Opcional si se ve el proceso de sus reglas
            
        err_handler.print_final_status()   # Imprime los errores finales