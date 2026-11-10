# Permite analizar expresiones regulares en texto crudo: r''
# El texto crudo significa que toma en cuenta saltos de linea y espacios.
import re
import sys


class errorHandler:

    def __init__(self):
        self.errors = []                 # Lista de errores reportados
        self.has_lexical_error = False   # [CAMBIO] Bandera para errores lexicos
        self.has_parsing_error = False   # Banderas de error en el manejador de errores
        self.has_sdt_error = False

    # Para reportar errores lexicos/parsing/sdt muestra el mensaje, la linea y columna en la que ocurrio
    def add_error_report(self, message, line, column, error_type):
        self.errors.append(f"{error_type} Error [Line {line}, Column {column}]: {message}")

        if error_type == "Lexical":      # Activa las banderas si hay un error de este tipo
            self.has_lexical_error = True
        elif error_type == "Parsing":
            self.has_parsing_error = True
        elif error_type == "SDT":
            self.has_sdt_error = True

    # Indica si hay errores en la lista
    def has_errors(self):
        return len(self.errors) > 0

    # Estructura de como quedan los errores dependiendo de las banderas activas
    def print_final_status(self):
        if self.has_lexical_error:
            print("Lexical error...")
        elif self.has_parsing_error:
            print("Parsing error...")
            print("SDT error...")
        elif self.has_sdt_error:
            print("Parsing Success!")
            print("SDT error...")
        else:
            print("Parsing Success!")
            print("SDT Verified!")

        if self.has_errors():  # Imprime los detalles de lineas y columnas
            print("\n--- Error Details ---")
            for err in self.errors:
                print(err)


# Caracteristicas de un Token: Su tipo, el valor, y posicion en linea y columna
class Token:
    def __init__(self, type_, value, line, column):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column


""" #################
ANALIZADOR LEXICO
##################"""

class Lexer:
    def __init__(self, source_code, error_handler):
        self.source_code = source_code      # El codigo a analizar.
        self.error_handler = error_handler  # El objeto de manejo de errores.
        self.tokens = []                    # Donde se van a almacenar la lista de tokens

        # Rastreo de posición
        self.line_number = 1  # Rastrea el numero de linea del codigo analizado
        self.line_start = 0   # Posicion donde inicia la linea actual

        self.tokens_type = [
            # \bPATRON\b Encuentra un PATRON en especifico de caracteres de palabra
            # ?: Indica que solo busca una coincidencia pero no la guarda.
            ('KEYWORD', r'\b(?:int|print|float|string|if|elif|else|while|for|return)\b'),
            # [a-zA-Z_] -> Obliga a empezar con una letra o guion bajo
            # \w* -> Los siguientes caracteres pueden ser cualquier numero, letra o guion bajo
            ('IDENTIFIER', r'[a-zA-Z_]\w*'),
            # [CAMBIO] Antes el '-' solo se reconocia con espacios (' - ') y '//' nunca se alcanzaba.
            # Ahora cada operador es un solo caracter: = + - * / %
            ('OPERATOR', r'[=+\-*/%]'),
            ('DECIMAL', r'\d*\.\d+'),      # Numeros con punto decimal: 8.6, .5
            ('CONSTANT', r'\b\d+\b'),      # Numeros enteros
            ('PUNCTUATION', r'[;(){},\[\]]'),
            ('LITERAL', r'"[^"\n]*"'),     # Texto dentro de comillas "" (en una sola linea)
            ('NEWLINE', r'\n'),
            # [CAMBIO] Se agrega \r para que los archivos guardados en Windows (\r\n) no den error
            ('BLANK_SPACE', r'[ \t\r]+'),
            ('ERROR', r'.')                # Cualquier otro caracter es un error
        ]

        # regex = '(?P<TIPO_DE_TOKEN> patron_del_token) | ...'
        self.regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in self.tokens_type)

    def tokenize(self):
        for match in re.finditer(self.regex, self.source_code):
            kind = match.lastgroup   # Tipo del token
            value = match.group()    # Texto que coincidio
            # [CAMBIO] Columnas empiezan en 1 (antes empezaban en 0)
            column = match.start() - self.line_start + 1

            if kind == 'NEWLINE':
                self.line_number += 1
                self.line_start = match.end()
                continue
            elif kind == 'BLANK_SPACE':
                continue
            elif kind == 'ERROR':
                self.error_handler.add_error_report(f"Character not recognized '{value}'",
                                                    self.line_number, column, "Lexical")
                continue

            self.tokens.append(Token(kind, value, self.line_number, column))

    # Para imprimir el reporte de los tokens identificados
    def print_report(self):
        print('-----Tokens List-----')
        for token in self.tokens:
            print(f'{token.type.lower()} {token.value}')
        print(f'\n*Total of tokens: {len(self.tokens)}')


""" #################
PARSER TOP-DOWN (Descenso recursivo LL(1))

[CAMBIO] Se unificaron ExpresionI y ExpresionF en una sola Expresion.
La gramatica solo revisa la FORMA; los tipos (int, float, string) los revisa el SDT.

Gramatica (forma iterativa, sin recursion por la izquierda):

    Program        -> Statement { Statement }
    Statement      -> Declaration | PrintStatement
    Declaration    -> Type Var '=' Expresion ';'
    Type           -> int | float | string
    Var            -> id
    PrintStatement -> print '(' Expresion ')' ';'
    Expresion      -> Termino { ( '+' | '-' ) Termino }
    Termino        -> Factor { ( '*' | '/' | '%' ) Factor }
    Factor         -> constant | decimal | literal | '(' Expresion ')'

Es LL(1): en cada no terminal, el token actual decide la produccion sin ambiguedad.
##################"""

# Creacion del Nodo del arbol
class Node:
    pass

# Nodo raiz: el programa completo
class ProgramNode(Node):
    def __init__(self, statements):
        self.statements = statements

# Nodo de declaracion: Type Var = Expresion ;
class DeclarationNode(Node):
    def __init__(self, type_value, var_value, exp_node, line, column):
        self.type_val = type_value   # 'int', 'float' o 'string'
        self.var_val = var_value     # Nombre de la variable (ej. 'x')
        self.exp_node = exp_node     # Sub-arbol de la expresion
        self.line = line             # Linea para el reporte de error
        self.column = column         # Columna para el reporte de error

# Nodo de print: print ( Expresion ) ;
class PrintStatementNode(Node):
    def __init__(self, print_value_node):
        self.print_value_node = print_value_node

# Nodo de operacion binaria (Expresion o Termino)
class BinaryOpNode(Node):
    def __init__(self, rule_name, left, op, right, line, column):
        self.rule_name = rule_name  # 'Expresion' o 'Termino'
        self.left = left
        self.op = op
        self.right = right
        self.line = line
        self.column = column

# Nodo hoja (Factor): un valor o una expresion entre parentesis
class ValueNode(Node):
    def __init__(self, rule_name, value):
        self.rule_name = rule_name  # 'Factor'
        self.value = value          # int, float, str u otro Node (parentesis)


class ParserTreeBuilder:
    def __init__(self, tokens, error_handler):
        self.error_handler = error_handler
        self.tokens = tokens
        self.position = 0
        self.last_token = None  # Ultimo token que ya se reviso
        self.current_token = self.tokens[0] if self.tokens else None

    # Avanza al siguiente token
    def look_ahead(self):
        self.last_token = self.current_token
        self.position += 1
        if self.position < len(self.tokens):
            self.current_token = self.tokens[self.position]
        else:
            self.current_token = None

    # Compara el token actual con el esperado; si coincide, avanza
    def match(self, expected_type, expected_value=None):
        tok = self.current_token
        if tok and tok.type == expected_type and (expected_value is None or tok.value == expected_value):
            self.look_ahead()
            return tok

        # Si falta un ';' o ')', el error se reporta en la palabra anterior
        if expected_value in [';', ')'] and self.last_token:
            self.report_error(f"Expected '{expected_value}' after '{self.last_token.value}'", self.last_token)
        else:
            esperado = f"'{expected_value}'" if expected_value else expected_type
            encontrado = f"'{tok.value}'" if tok else "end of input"
            self.report_error(f"Expected {esperado}, found {encontrado}")
        return None

    # Revisa si el token actual es uno de los operadores indicados
    def is_operator(self, *ops):
        tok = self.current_token
        return tok is not None and tok.type == 'OPERATOR' and tok.value in ops

    # Reporta solo el primer error de parsing
    def report_error(self, message, token=None):
        if not self.error_handler.has_parsing_error:
            if token is None:
                token = self.current_token if self.current_token else self.last_token
            line = token.line if token else "n"
            column = token.column if token else "n"
            self.error_handler.add_error_report(message, line, column, "Parsing")

    # Program -> Statement { Statement }
    def parse(self):
        # [CAMBIO] Un programa necesita al menos un Statement
        if not self.tokens:
            self.report_error("Empty input: expected at least one statement")
            return ProgramNode([])

        statements = []
        while self.current_token is not None and not self.error_handler.has_parsing_error:
            actual_statement = self.statement()
            if actual_statement:
                statements.append(actual_statement)
        return ProgramNode(statements)

    # Statement -> Declaration | PrintStatement
    def statement(self):
        tok = self.current_token
        if tok.type == 'KEYWORD' and tok.value in ('int', 'float', 'string'):
            return self.declaration()
        elif tok.type == 'KEYWORD' and tok.value == 'print':
            return self.print_statement()
        else:
            self.report_error(f"Expected statement (int, float, string or print), found '{tok.value}'")
            return None

    # [CAMBIO] Una sola funcion para int, float y string
    # Declaration -> Type Var '=' Expresion ';'
    def declaration(self):
        t = self.type_()
        if not t:
            return None

        v = self.var(t)
        if not v:
            return None

        if not self.match('OPERATOR', '='):
            return None

        e = self.expresion()
        if e is None or self.error_handler.has_parsing_error:
            return None

        if not self.match('PUNCTUATION', ';'):
            return None

        return DeclarationNode(t.value, v.value, e, t.line, t.column)

    # Type -> int | float | string
    def type_(self):
        return self.match('KEYWORD')

    # Var -> id
    def var(self, type_token):
        tok = self.current_token
        if tok is None or tok.type != 'IDENTIFIER':
            encontrado = f"'{tok.value}'" if tok else "end of input"
            self.report_error(f"Expected an identifier after '{type_token.value}', found {encontrado}")
            return None
        return self.match('IDENTIFIER')

    # PrintStatement -> print '(' Expresion ')' ';'
    def print_statement(self):
        if not self.match('KEYWORD', 'print'):
            return None
        if not self.match('PUNCTUATION', '('):
            return None

        e = self.expresion()
        if e is None or self.error_handler.has_parsing_error:
            return None

        if not self.match('PUNCTUATION', ')'):
            return None
        if not self.match('PUNCTUATION', ';'):
            return None

        return PrintStatementNode(e)

    # Expresion -> Termino { ( '+' | '-' ) Termino }
    def expresion(self):
        node = self.termino()
        while node is not None and self.is_operator('+', '-'):
            op = self.match('OPERATOR')
            right = self.termino()
            if right is None:
                return None
            node = BinaryOpNode('Expresion', node, op.value, right, op.line, op.column)
        return node

    # Termino -> Factor { ( '*' | '/' | '%' ) Factor }
    def termino(self):
        node = self.factor()
        while node is not None and self.is_operator('*', '/', '%'):
            op = self.match('OPERATOR')
            right = self.factor()
            if right is None:
                return None
            node = BinaryOpNode('Termino', node, op.value, right, op.line, op.column)
        return node

    # Factor -> constant | decimal | literal | '(' Expresion ')'
    def factor(self):
        tok = self.current_token

        if tok is None:
            self.report_error("Expected a value but the input ended")
            return None

        if tok.type == 'CONSTANT':
            return ValueNode('Factor', int(self.match('CONSTANT').value))
        elif tok.type == 'DECIMAL':
            return ValueNode('Factor', float(self.match('DECIMAL').value))
        elif tok.type == 'LITERAL':
            return ValueNode('Factor', self.match('LITERAL').value)
        elif tok.type == 'PUNCTUATION' and tok.value == '(':
            self.match('PUNCTUATION', '(')
            node = self.expresion()
            if node is None:
                return None
            if not self.match('PUNCTUATION', ')'):
                return None
            return ValueNode('Factor', node)
        else:
            self.report_error(f"Expected a value (CONSTANT, DECIMAL, LITERAL or '('), found '{tok.value}'")
            return None


""" #################
ANALISIS SEMANTICO (SDT)

Cada valor sube por el arbol con dos atributos sintetizados: .value y .type
Reglas:
  - Declaration: si Expresion.type != Type.type -> SDT error (Type Mismatch)
  - Operaciones con un string -> SDT error
  - Division o modulo entre cero -> SDT error
  - int op int -> int (division entera); si alguno es float -> float
##################"""

# Convierte el tipo de Python al nombre del tipo en el lenguaje
def type_name(val):
    if isinstance(val, int):
        return 'int'
    if isinstance(val, float):
        return 'float'
    return 'string'


class SemanticAnalyzer:

    def __init__(self, error_handler):
        self.error_handler = error_handler
        self.trace_log = []  # El proceso de cada regla se guarda aqui

    def print_sdt_trace(self):
        if not self.trace_log:
            print("There is not SDT available.")
            return
        print("\n--- Trace of SDT ---")
        for trace in self.trace_log:
            print(trace)

    # Recorre el arbol y aplica las reglas semanticas de cada nodo
    def visit(self, node):

        if isinstance(node, ProgramNode):
            # Revisa TODAS las sentencias, aunque alguna tenga error
            for actual_statement in node.statements:
                self.visit(actual_statement)

        elif isinstance(node, DeclarationNode):
            val = self.visit(node.exp_node)
            if val is None:
                return None  # Hubo un error dentro de la expresion

            # Type Checking
            if type_name(val) != node.type_val:
                mensaje = (f"Type Mismatch: variable '{node.var_val}' is {node.type_val}, "
                           f"assigned value is {type_name(val)}")
                self.error_handler.add_error_report(mensaje, node.line, node.column, "SDT")
                return None

            sdt_string = f"{node.type_val} {node.var_val} '=' {val} ';'"
            self.trace_log.append(f"Declaration{{D.exp = {sdt_string}}}")
            self.trace_log.append(f"Statement{{Statement = {sdt_string}}}")
            self.trace_log.append(f"Program{{Program = {sdt_string}}}")

        elif isinstance(node, BinaryOpNode):
            left_val = self.visit(node.left)
            right_val = self.visit(node.right)
            if left_val is None or right_val is None:
                return None

            # No se pueden hacer operaciones con texto
            if isinstance(left_val, str) or isinstance(right_val, str):
                self.error_handler.add_error_report(
                    f"Operator '{node.op}' cannot be used with a string", node.line, node.column, "SDT")
                return None

            if node.op == '/':
                if right_val == 0:
                    self.error_handler.add_error_report("Division by zero", node.line, node.column, "SDT")
                    return None
                if isinstance(left_val, int) and isinstance(right_val, int):
                    result = left_val // right_val   # Division entera
                else:
                    result = left_val / right_val
            elif node.op == '%':
                if right_val == 0:
                    self.error_handler.add_error_report("Modulo by zero", node.line, node.column, "SDT")
                    return None
                result = left_val % right_val
            elif node.op == '+':
                result = left_val + right_val
            elif node.op == '-':
                result = left_val - right_val
            else:  # '*'
                result = left_val * right_val

            letra = node.rule_name[0]  # 'E' de Expresion o 'T' de Termino
            self.trace_log.append(f"{node.rule_name}{{{letra}.value = {result}, {letra}.type = {type_name(result)}}}")
            return result

        elif isinstance(node, ValueNode):
            val = self.visit(node.value) if isinstance(node.value, Node) else node.value
            if val is None:
                return None
            self.trace_log.append(f"Factor{{F.value = {val}, F.type = {type_name(val)}}}")
            return val

        elif isinstance(node, PrintStatementNode):
            val = self.visit(node.print_value_node)
            if val is not None:
                self.trace_log.append(f"PrintStatement{{P.val = print ({val}) ';'}}")


""" #################
PROGRAMA PRINCIPAL
##################"""

# [CAMBIO] Todo el proceso en una funcion para poder analizar varios codigos
def analizar(codigo, mostrar_tokens=False, mostrar_traza=False):
    err_handler = errorHandler()

    lexer = Lexer(codigo, err_handler)
    lexer.tokenize()
    if mostrar_tokens:
        lexer.print_report()
        print()

    # Solo se parsea si el lexer no encontro errores
    if not err_handler.has_lexical_error:
        parser = ParserTreeBuilder(lexer.tokens, err_handler)
        ast_root = parser.parse()

        # Solo se hace el analisis semantico si el parsing fue exitoso
        if not err_handler.has_parsing_error:
            semantic = SemanticAnalyzer(err_handler)
            semantic.visit(ast_root)
            if mostrar_traza:
                semantic.print_sdt_trace()
                print()

    err_handler.print_final_status()


if __name__ == '__main__':

    # [CAMBIO] Si se pasa un archivo: python Parser_SDT.py programa.txt
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding='utf-8') as archivo:
            analizar(archivo.read(), mostrar_tokens=True, mostrar_traza=True)

    # Si no, se corren los casos de prueba
    else:
        casos = [
            ("Correcto (ejemplo del PDF)", 'int x = 10;'),
            ("Correcto (varias lineas)", 'int x = (10 + 3) * 2 - 8 / 4;\n'
                                         'float y = 2.5 * 4.0;\n'
                                         'string s = "Hola";\n'
                                         'print("Hola mundo");'),
            ("Error de parsing (keyword como variable)", 'int float = 2323.32;'),
            ("Error de parsing (falta ';' en linea 2)", 'int a = 5;\nint b = 6\nprint(a);'),
            ("Error SDT (type mismatch)", 'int a = 7.8;\nprint("Hellooo");\nstring answer = "Correct";'),
            ("Error SDT (division entre cero)", 'int a = 10 / (5 - 5);'),
            ("Error SDT (string en operacion)", 'string s = "a" + 3;'),
            ("Error lexico", 'int x = 10 $ 2;'),
        ]

        for nombre, codigo in casos:
            print(f"========== {nombre} ==========")
            print(codigo)
            print("----------")
            analizar(codigo)
            print()