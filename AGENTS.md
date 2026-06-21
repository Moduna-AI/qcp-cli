----
Name: QCP
Description: Is a Query Companion for non developers. Simply install the cli and start querying your database in natural language.
----

# AGENTS.md

Query companion is a user friendly cli tool that allows any one to easily make any query to their database. Use LLMs to generate SQL queries and execute it on the database. CLI tool is a query companion agent.

## Supported Database:

- Postgres

## Supported LLM

- gemini-2.5-flash

## Features

- **read**: Does read operations on the database.

## Memory

- Stores all the schema info in the memory.

## Configuration

**~/.qcp/config.json**

## Python OOP Development Guide

Welcome to the team! This guide ensures our Python codebase remains clean, maintainable, and scalable. Follow these object-oriented programming (OOP) guidelines, principles, and styling standards for all contributions.

---

### 1. Code Style and Formatting

*   **PEP 8 Compliance**: Adhere strictly to PEP 8 standards for all Python code.
*   **Explicit Naming**: 
    *   Use `PascalCase` for class names (e.g., `UserManager`).
    *   Use `snake_case` for methods, functions, and attributes (e.g., `calculate_total`).
    *   Use `CAPITAL_SNAKE_CASE` for constants (e.g., `MAX_RETRY_ATTEMPTS`).
*   **Type Hinting**: Provide explicit type hints for all method arguments and return types.
*   **Docstrings**: Include PEP 257 compliant docstrings for every class and public method.

---

### 2. Core OOP Design Principles

### SOLID Principles
*   **Single Responsibility (SRP)**: A class must have only one reason to change.
*   **Open/Closed (OCP)**: Design classes open for extension but closed for modification.
*   **Liskov Substitution (LSP)**: Subclasses must be completely substitutable for their base classes.
*   **Interface Segregation (ISP)**: Create small, specific interfaces rather than large, bloated ones.
*   **Dependency Inversion (DIP)**: Depend on abstractions (abstract base classes), not on concrete implementations.

#### Encapsulation and Access Control
*   **Public Attributes**: Use for data safely modified directly without validation.
*   **Protected Attributes (`_single_leading_underscore`)**: Use for internal class/subclass properties.
*   **Private Attributes (`__double_leading_underscore`)**: Use to trigger name mangling and prevent accidental overrides.
*   **Properties**: Use `@property` getters and setters instead of writing manual `get_x()` and `set_x()` methods.

---

### 3. Abstract Classes and Interfaces

*   **Enforce Contracts**: Use Python’s `abc` module to define interfaces and abstract base classes.
*   **Decorators**: Mark abstract methods with the `@abstractmethod` decorator.

---

### 4. Project Management and Tooling

*   **Package Management**: Always use `uv` for dependency management and environment isolation.
*   **Build Backend**: Use `hatchling` as the build system backend inside `pyproject.toml`.
*   **Virtual Environments**: Initialize environments using `uv venv` and sync dependencies with `uv pip sync`.
*   **Linting and Formatting**: Use `ruff check` for linting and `ruff format` for code formatting.
*   **Pre-commit Hook**: Ensure `ruff` checks and formatting run automatically before every commit.