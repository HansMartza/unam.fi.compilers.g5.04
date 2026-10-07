# Compilers Course - Lexer Project (1st Submission)

This folder contains the **Lexical Analyzer (Lexer)** module implemented in Python as part of the Compilers course project at the UNAM Faculty of Engineering.

## Team 04 - Group 5
* **Blancas Díaz Isaías**
* **Hernández Flores Alan Uziel**
* **Martínez Sánchez Hans**
* **Ramírez Terán Emily**
* **Valdez Subirachs Sebastián**

---

## Project Overview

The lexer uses Python's native regular expressions library (`re`) to scan raw input text, tokenize it according to a defined grammar, and handle lexical errors (such as unrecognized characters) with precise line and column tracking.

### Supported Token Categories
* **`KEYWORD`**: Reserved words (`int`, `print`, `float`, `string`, `if`, `elif`, `else`, `while`, `for`, `return`).
* **`IDENTIFIER`**: Variable names and identifiers (starting with a letter or underscore).
* **`OPERATOR`**: Mathematical and assignment operators (`=`, `+`, `-`, `/`, `//`, `*`, `%`).
* **`CONSTANT`**: Numeric integer values.
* **`Punctuation`**: Delimiters and punctuation marks (`;`, `()`, `{}`, `[]`).
* **`LITERAL`**: Text strings enclosed in double quotes (`"..."`).

---

## File Structure

* `Analizador_lexico.py`: Main Python script containing the `Token`, `errorHandler`, and `Lexer` classes, along with test execution cases.
* `Grammar.pdf` / `04-Compilers-Lexer-2.pdf`: Official project report and theoretical grammar documentation.

---

## How to Run

Make sure you have **Python 3** installed, then execute the script directly from your terminal:

```bash
python Analizador_lexico.py
```

### Example Test Case
The script includes built-in test strings demonstrating successful tokenization as well as lexical error catching (e.g., reporting unexpected characters with exact line and column numbers).