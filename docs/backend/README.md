# Backend API Overview

## Introduction

The Backend API serves as the gateway to the accounting system database. It provides a structured interface for managing financial data including transactions, accounts, journal entries, and related metadata.

## Project guidelines

This is a provisional version of the guidelines for this project. So far this has been developed by a single person so the guidelines so far have been my personal style.

Since it is not that big of a project, the impact of having a lot of stric rules probably would be minimal, at least at the beginning. Nonetheless, for anyone who ends up working in this project, it is important to keep some things in mind so the project remains understandable, easy to navigate and easy to refactor.

### Coding guidelines

1. The fisrt guideline is having some "code etiquette". By this I mean that code should be well documented, use type hints and have comments if necessary, using clear naming as specific as reasonable. Althoug this is technically a guideline, in practical terms is a necessity. It is important to watch out for some functions in external libraries since in many cases the types returned might not be clear for the static type-checker. In those cases its absolutely necessary to include type hints for the return type of the function to catch bugs early.

2. Hexagonal architecture: Hexagonal architecture is a bit of a complex topic to dive in, but it allows to implement a domain driven development. This means that if we define propperly what an accounting construct is, which constructs will we use, what construct data we want to work with and what data we want retrieve, then we can build the rest of the backend around those core concepts. The trade offs are added complexity and expensive domain refactor, but on the other hand we will gain order and easier refactorings in the application and ports layers.

3. Composition over inheritance: Inheritance is not completely discouraged, in fact, this project uses it a lot already, specially for abstract base classes and some mixins. The problem with inheritance is the over use. For instance, if you take the (`backend/ledger_data/domain/entities/attachments.py`) module, you will notice that mixins could have been used to build the attachment classes instead of composition, but the classes would have been difficult to read, way more verbose and combining that with the use of generics would have been an eye sore.


### Style guidelines

1. module order: Code is not art (generally), but the order of the functions, classes and variables affects readability. Ideally there should be a bit of story telling in the ordering of modules, Python even offers features like the quoting of classes to allow using type hints of classes that are defined later in the file. In the case of classes,It is usefull to order them by importance and put utility functions at the end. 

2. Formatting: max 80 character length lines, 72 for docstrings. This projec uses Ruff as formatting tool and the configuration that it offers is robust, so even if it's not mandatory, using the formatting configuration is highly reccomended. 

> **Note**: This documentation currently covers the **Domain Entities Module**, which represents the most stable and complete part of the backend. Other backend components are still under development.

> **Note2**: The rest of this readme file was generated using AI, so it stills need to be rewritten and revised by a human.

---

## Architecture Overview

The backend follows a hexagonal architecture pattern (ports and adapters) with a clear separation of concerns.

- **Domain Layer**: Core business logic and data structures (`backend/ledger_data/domain/`)
- **Adapters Layer**: Database adapters and external integrations (`backend/ledger_data/adapters/`)
- **Ports Layer**: Interface definitions for repositories and services (`backend/ledger_data/ports.py`)

---


## Design Principles

### Immutability-First
All data classes leverage Python dataclasses to ensure immutability and consistency across domain boundaries, providing type-safe interfaces for domain services and repositories.

### Generic Type System
Resources use Python generics to separate concerns while maintaining type safety:
- **Data** (D): Pure business logic
- **Persistence** (P): Storage layer metadata
- **Attachments** (A): Optional related resources

### Hierarchical Organization
Entities support hierarchical relationships through:
- Parent/child IDs in data classes
- HierarchyAttachment structures in resources
- Enables flexible organizational structures for accounts, transaction types, and recipients

### Domain-Driven Design
The domain layer remains agnostic of database implementations while providing a consistent interface for handling identified resources throughout the application lifecycle.

---

## Module Organization

```
backend/ledger_data/domain/entities/
├── __init__.py              # Public exports of all entity types
├── data_classes.py          # Pure domain data entities
├── persistence.py           # Database metadata classes
├── resources.py             # Complete domain resources with metadata
└── attachments.py           # Optional attachment structures
```

---

## Current Status

✅ **Domain Entities Module**: Fully implemented and documented
⏳ **Other Backend Components**: Under development (adapters, ports, use cases, and routing)



