# Design Patterns: Elements of Reusable Object-Oriented Software
Authors: Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides (Gang of Four)
Publisher: Addison-Wesley / Pearson Education, 1994.

## Core Classification of Patterns
Design patterns are categorized into three fundamental families:
1. Creational Patterns: Abstract the instantiation process (Factory Method, Abstract Factory, Singleton, Builder).
2. Structural Patterns: Compose classes or objects into larger structures (Adapter, Decorator, Facade, Composite, Proxy).
3. Behavioral Patterns: Characterize the ways in which classes or objects interact and distribute responsibility.

## Strategy Pattern
Intent: Define a family of algorithms, encapsulate each one, and make them interchangeable. Strategy lets the algorithm vary independently from clients that use it.
Application: Used in e-commerce systems for interchangeable payment gateways (VNPAY, MoMo, COD) and dynamic import/export formats (Excel, CSV).

## Template Method Pattern
Intent: Define the skeleton of an algorithm in an operation, deferring some steps to subclasses. Template Method lets subclasses redefine certain steps of an algorithm without changing the algorithm's structure.
Application: Multi-step report generation and inventory spreadsheet batch parsing.
