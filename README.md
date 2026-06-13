# Build Your Own JavaScript (Python)

A lightweight JavaScript runtime implemented entirely in Python.

This project tokenizes JavaScript source code, parses it into an Abstract Syntax Tree (AST), and executes it using a custom interpreter written from scratch. The implementation focuses on clean architecture, extensibility, and readability while supporting a practical subset of JavaScript required for common programming tasks and hackathon test cases.

---

# Overview

This interpreter was built as part of the **Build Your Own JavaScript** challenge.

The runtime supports:

* Variable declarations (`let`, `const`)
* Functions and closures
* Arrays and objects
* Conditional statements
* Loops
* Common array and string methods
* Built-in runtime APIs such as `console`, `Math`, and `Date`

The project is implemented entirely in Python and does not embed any external JavaScript engine.

---

# Architecture

```text
┌─────────────────────────┐
│ JavaScript Source Code  │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│         Lexer           │
│-------------------------│
│ Converts source code    │
│ into a stream of tokens │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│         Tokens          │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│         Parser          │
│-------------------------│
│ Pratt Parser builds     │
│ an Abstract Syntax Tree │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│           AST           │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│      Interpreter        │
│-------------------------│
│ Evaluates AST nodes     │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Lexical Environment    │
│-------------------------│
│ Scopes & Closures       │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│   Runtime Libraries     │
│-------------------------│
│ console, Math, Date     │
│ Arrays, Strings         │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│         Output          │
└─────────────────────────┘
```

---

# Repository Structure

```text
JsInterpreter/
├── jsrunner/
│   ├── lexer.py
│   ├── tokens.py
│   ├── parser.py
│   ├── ast_nodes.py
│   ├── interpreter.py
│   ├── environment.py
│   ├── stdlib.py
│   ├── runtime.py
│   └── errors.py
│
├── tests/
│   ├── test_cases.py
│   ├── samples/
│   │   ├── tc1_odd_even.js
│   │   ├── tc2_triangle.js
│   │   ├── tc3_armstrong.js
│   │   ├── tc4_array_reverse.js
│   │   └── tc5_palindrome.js
│   │
│   └── OtherTestCases/
│       ├── tc6.js
│       ├── tc7.js
│       ├── tc8.js
│       └── tc9.js
│
├── cli.py
├── pyproject.toml
├── README.md
└── image.png
```


# Installation

## Requirements

* Python 3.9+

## Clone Repository

```bash
git clone https://github.com/ishikabatra20/thunder_hackathon2.git
cd JsInterpreter
```

## Install Dependencies


```bash
# No external dependencies required
```

---

# Usage

Run a JavaScript file:

```bash
python cli.py tests/samples/tc1_odd_even.js 
python cli.py tests/samples/tc2_triangle.js 
python cli.py tests/samples/tc3_armstrong.js 
python cli.py tests/samples/tc4_array_reverse.j 
python cli.py tests/samples/tc5_palindrome.js
```

Run tests:

```bash
python -m pytest
```

---

# Example

Input:

```javascript
let arr = [1, 2, 3];

arr.push(4);

console.log(arr.join(", "));
```

Output:

```text
1,2,3,4
```

---

# Supported Language Features

## Variables

* let
* const

## Primitive Types

* number
* string
* boolean
* null
* undefined

## Control Flow

* if
* else
* switch
* break
* continue

## Loops

* for
* while
* do...while

## Functions

* Function declarations
* Function expressions
* Arrow functions
* Closures
* Return statements

## Operators

* Arithmetic operators
* Comparison operators
* Logical operators
* Assignment operators
* Increment / decrement (`++`, `--`)
* Exponentiation (`**`)

## Arrays

Supported methods:

* push()
* pop()
* shift()
* unshift()
* slice()
* splice()
* concat()
* includes()
* indexOf()
* reverse()
* sort()
* map()
* filter()
* reduce()
* find()
* some()
* every()
* join()

Properties:

* length

## Strings

Supported methods:

* replace()
* replaceAll()
* substring()
* slice()
* split()
* trim()
* toUpperCase()
* toLowerCase()
* includes()
* startsWith()
* endsWith()
* indexOf()

Properties:

* length

## Math

Supported APIs:

* Math.PI
* Math.random()
* Math.floor()
* Math.ceil()
* Math.round()
* Math.abs()
* Math.max()
* Math.min()
* Math.pow()
* Math.sqrt()

## Date

Supported APIs:

* new Date(...)
* getFullYear()
* toString()

## Spread / Rest

* Array spread syntax
* Rest parameters

## Console

```javascript
console.log(...)
```

---

# Test Results

| Test Case          | Status   |
| ------------------ | -------- |
| Odd / Even Checker | ✅ Passed |
| Triangle Pattern   | ✅ Passed |
| Armstrong Number   | ✅ Passed |
| Array Reverse      | ✅ Passed |
| Palindrome Check   | ✅ Passed |

```text
5 passed in 0.12s
```

---

# Design Decisions

### Pratt Parser

A Pratt parser is used to implement operator precedence while keeping the parser compact and extensible.

### Lexical Environments

Nested environments provide:

* Variable scope resolution
* Function scope
* Closures

### First-Class Functions

Functions are runtime values that can:

* Be assigned to variables
* Be passed as arguments
* Be returned from other functions

### Pure Python Runtime

The interpreter is implemented entirely in Python without embedding Node.js, V8, or any external JavaScript engine.

---

# Performance

* Linear-time tokenization
* Pratt-parser expression handling
* Lightweight AST evaluation
* No external runtime dependencies

---

# Limitations

This is not a complete ECMAScript implementation.

Current limitations include:

* No DOM APIs
* No module system
* No async/await
* No browser APIs
* Simplified Date implementation
* Simplified JavaScript coercion rules

---

# Future Improvements

* Template literal interpolation
* Improved JavaScript coercion behavior
* Async/await support
* ES Modules
* Class syntax
* for...of loops
* Additional Date APIs
* Better error diagnostics

---

# Acknowledgements

Built for the **Build Your Own JavaScript** challenge.

The project was created to better understand the internals of programming language execution by implementing:

* Lexer
* Parser
* Abstract Syntax Tree (AST)
* Interpreter
* Runtime Environment
* Standard Library
