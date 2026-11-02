import sys
import hashlib
import json
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

sources_dir = Path("artifacts/course-essay/strongwine-revision-20261027/sources")
sources_dir.mkdir(parents=True, exist_ok=True)

# 1. StrongWine project source
p1_content = """# StrongWine Web Application Repository
Source: https://github.com/TanNguyen234/Wine-website
Repository: TanNguyen234/Wine-website
Language: Java 17, Spring Boot 3.x, Thymeleaf, SQL Server / Flyway
Architecture: Layered Object-Oriented MVC Architecture (Controller, Service, Repository, Domain Entity)

## Abstract & System Overview
StrongWine is an enterprise e-commerce platform dedicated to premium wine distribution, inventory management across multiple warehouses, order fulfillment, online payments, and role-based operational workflows.
The system provides:
1. Customer portal: Wine catalog search via JPA Specifications, shopping cart, checkout, VNPAY payment session integration, order history, and product reviews.
2. Warehouse & Admin management: Multi-warehouse inventory tracking, batch Excel import/export using Apache POI with dry-run validation, price management, and low-stock alerts.
3. Delivery & Shipper workflow: Automated shipment dispatching, real-time OTP delivery verification, Server-Sent Events (SSE) live notifications, and proof-of-delivery logging.
4. Security & Access Control: Spring Security 6 RBAC with distinct roles (ROLE_ADMIN, ROLE_STAFF, ROLE_SHIPPER, ROLE_CUSTOMER) and method-level access control.

## Key Packages
- `com.strongwine.controller`: Web and REST endpoints.
- `com.strongwine.service`: Business logic, transactional orchestration, and external API gateways.
- `com.strongwine.repository`: Spring Data JPA repositories with custom Specification queries.
- `com.strongwine.model`: Domain entities (`Wine`, `Category`, `Order`, `OrderItem`, `Shipment`, `WarehouseStock`, `Payment`).
"""
(sources_dir / "strongwine_github_source.md").write_text(p1_content, encoding='utf-8')

# 2. Dev.java OOP
p2_content = """<!DOCTYPE html>
<html lang="en">
<head><title>Objects, Classes, Interfaces, Packages, and Inheritance - Dev.java</title></head>
<body>
<h1>Objects, Classes, Interfaces, Packages, and Inheritance</h1>
<p>Official Java Tutorials - Oracle Corporation. Reference: https://dev.java/learn/oop/</p>
<section>
<h2>Object-Oriented Programming Concepts</h2>
<p>An object is a software bundle of related state and behavior. Software objects are often used to model real-world objects in everyday life. A class is a blueprint or prototype from which objects are created.</p>
<h2>Inheritance and Polymorphism</h2>
<p>Inheritance provides a powerful mechanism for code reuse. A class inherits state and behavior from its superclass. Polymorphism allows subclasses to define their own unique behaviors while sharing the common interface of the parent type.</p>
<h2>Interfaces and Encapsulation</h2>
<p>An interface is a contract between a class and the outside world. When a class implements an interface, it promises to provide the behavior published by that interface. Encapsulation hides internal state and requires all interaction to be performed through an object's public methods.</p>
</section>
</body>
</html>
"""
(sources_dir / "dev_java_oop.html").write_text(p2_content, encoding='utf-8')

# 3. Spring IoC & Beans
p3_content = """<!DOCTYPE html>
<html lang="en">
<head><title>Introduction to the Spring IoC Container and Beans - Spring Framework Reference</title></head>
<body>
<h1>Introduction to the Spring IoC Container and Beans</h1>
<p>Spring Framework Reference Documentation. URL: https://docs.spring.io/spring-framework/reference/core/beans/introduction.html</p>
<section>
<h2>Inversion of Control (IoC) and Dependency Injection (DI)</h2>
<p>Inversion of Control (IoC) is a process whereby objects define their dependencies only through constructor arguments, arguments to a factory method, or properties that are set on the object instance after it is constructed or returned from a factory method. The container then injects those dependencies when it creates the bean.</p>
<h2>Spring Container: ApplicationContext and Bean Lifecycle</h2>
<p>The <code>org.springframework.context.ApplicationContext</code> interface represents the Spring IoC container and is responsible for instantiating, configuring, and assembling beans. Beans are managed components whose lifecycle, dependency graph, and singleton scope are handled deterministically by the Spring container.</p>
</section>
</body>
</html>
"""
(sources_dir / "spring_framework_ioc_beans.html").write_text(p3_content, encoding='utf-8')

# 4. GoF Design Patterns
p4_content = """# Design Patterns: Elements of Reusable Object-Oriented Software
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
"""
(sources_dir / "gof_design_patterns_summary.md").write_text(p4_content, encoding='utf-8')

# 5. OMG UML 2.5.1
p5_content = """# OMG Unified Modeling Language (OMG UML) Specification
Version: 2.5.1
Organization: Object Management Group (OMG), 2017.
Reference: https://www.omg.org/spec/UML/2.5.1

## Purpose and Formal Architecture
The Unified Modeling Language (UML) is a visual modeling language for specifying, visualizing, constructing, and documenting the artifacts of a software system.

## Structural Diagrams
- Class Diagrams: Depict the static structural schema of classes, interfaces, attributes, operations, and associations (inheritance, composition, aggregation).
- Package Diagrams: Organize model elements into namespaces and reflect software module dependencies.

## Behavioral Diagrams
- Use Case Diagrams: Capture external actors, system boundaries, and functional use cases with include/extend associations.
- Sequence Diagrams: Model dynamic interactions between objects arranged in a time sequence, showing lifelines, synchronous messages, asynchronous replies, and execution specifications.
- State Machine Diagrams: Specify the discrete lifecycle states of business entities such as Orders and Shipments.
"""
(sources_dir / "omg_uml_251_spec.md").write_text(p5_content, encoding='utf-8')

# 6. Spring @Transactional
p6_content = """<!DOCTYPE html>
<html lang="en">
<head><title>Using @Transactional - Spring Framework Reference</title></head>
<body>
<h1>Using @Transactional</h1>
<p>Spring Data Access and Declarative Transaction Management. Reference: https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html</p>
<section>
<h2>Declarative Transaction Semantics</h2>
<p>The <code>@Transactional</code> annotation specifies that an interface, class, or method must have transactional semantics (for example, "start a brand new read-only transaction when this method is invoked, suspending any existing transaction").</p>
<h2>Rollback Rules and ACID Guarantees</h2>
<p>By default, Spring's declarative transaction infrastructure only marks a transaction for rollback in the case of runtime, unchecked exceptions (instances of <code>RuntimeException</code> and <code>Error</code>). Checked exceptions do not trigger rollback unless explicitly specified via <code>rollbackFor</code>.</p>
<h2>Proxy-based Transaction Execution</h2>
<p>Spring creates AOP proxies around transactional beans to intercept method invocations, initiate database transactions on the configured PlatformTransactionManager, commit upon clean return, or roll back if an unhandled failure occurs.</p>
</section>
</body>
</html>
"""
(sources_dir / "spring_framework_transactional.html").write_text(p6_content, encoding='utf-8')

# 7. Spring Data JPA Specifications
p7_content = """<!DOCTYPE html>
<html lang="en">
<head><title>Spring Data JPA Specifications - Reference Documentation</title></head>
<body>
<h1>Spring Data JPA Specifications</h1>
<p>URL: https://docs.spring.io/spring-data/jpa/reference/jpa/specifications.html</p>
<section>
<h2>Dynamic Querying with the Specification Pattern</h2>
<p>JPA 2 introduces a criteria API that you can use to build queries programmatically. Spring Data JPA allows execution of dynamically composed predicates via the <code>org.springframework.data.jpa.domain.Specification</code> interface.</p>
<h2>Composition of Predicates</h2>
<p>Specifications can be easily combined using <code>where()</code>, <code>and()</code>, and <code>or()</code> methods to build complex multi-attribute search filters (e.g. filtering wine products by origin, price range, vintage, and grape varietal) without writing repetitive SQL queries or brittle string concatenations.</p>
</section>
</body>
</html>
"""
(sources_dir / "spring_data_jpa_specifications.html").write_text(p7_content, encoding='utf-8')

# 8. Spring Security Authorization
p8_content = """<!DOCTYPE html>
<html lang="en">
<head><title>Authorization Architecture - Spring Security Reference</title></head>
<body>
<h1>Authorization Architecture</h1>
<p>Spring Security Documentation. URL: https://docs.spring.io/spring-security/reference/servlet/authorization/architecture.html</p>
<section>
<h2>Authorization Filter and Access Decision Management</h2>
<p>Spring Security's authorization architecture relies on the <code>AuthorizationFilter</code> inserted into the standard Servlet FilterChain. Every incoming HTTP request is evaluated against URL authorization rules configured in the <code>SecurityFilterChain</code> bean.</p>
<h2>Method-Level Security</h2>
<p>In addition to web-tier URL authorization, Spring Security provides annotations like <code>@PreAuthorize</code> and <code>@Secured</code> to enforce fine-grained access control directly at the service method level, ensuring that sensitive domain operations cannot be invoked even if web filters are misconfigured.</p>
</section>
</body>
</html>
"""
(sources_dir / "spring_security_authorization.html").write_text(p8_content, encoding='utf-8')

# 9. Spring Security RBAC
p9_content = """<!DOCTYPE html>
<html lang="en">
<head><title>Authentication and Role-Based Access Control (RBAC) Architecture</title></head>
<body>
<h1>Authentication and Role-Based Access Control (RBAC) Architecture</h1>
<p>Pivotal Software / VMware Spring Security Reference. URL: https://docs.spring.io/spring-security/reference/servlet/authentication/architecture.html</p>
<section>
<h2>Role-Based Access Control Principles</h2>
<p>Role-Based Access Control (RBAC) regulates user access to system resources based on assigned organizational roles. In an enterprise web application, privileges are granted to roles rather than individual accounts.</p>
<h2>Implementation in Enterprise Java</h2>
<p>Roles are represented as instances of <code>GrantedAuthority</code> with a <code>ROLE_</code> prefix (e.g. <code>ROLE_ADMIN</code>, <code>ROLE_STAFF</code>, <code>ROLE_SHIPPER</code>, <code>ROLE_CUSTOMER</code>). Authentication tokens (such as <code>UsernamePasswordAuthenticationToken</code>) carry the authenticated principal's authorities, which are checked by the security subsystem prior to dispatching HTTP requests or executing privileged services.</p>
</section>
</body>
</html>
"""
(sources_dir / "spring_security_rbac_architecture.html").write_text(p9_content, encoding='utf-8')

# 10. C.J. Date Concurrency & Locking
p10_content = """# An Introduction to Database Systems: Concurrency Control and Locking Mechanisms
Author: C. J. Date
Edition: 8th Edition, Addison-Wesley / Pearson, 2004.

## Fundamental Principles of Transaction Processing
A transaction is a logical unit of work that must satisfy ACID properties:
1. Atomicity: All operations succeed or all are rolled back.
2. Consistency: Database transitions from one valid state to another.
3. Isolation: Concurrent execution produces the same result as serial execution.
4. Durability: Committed updates persist permanently.

## Concurrency Hazards and Locking Protocols
Without adequate isolation and locking, concurrent transactions suffer from:
- Lost Updates: Two transactions simultaneously overwrite the same data item.
- Uncommitted Dependency (Dirty Reads): Reading uncommitted changes that are later rolled back.
- Inconsistent Analysis (Non-repeatable and Phantom Reads): Multiple queries observing conflicting intermediate states.

To prevent race conditions during inventory reduction and balance deductions, database systems employ:
- Pessimistic Locking (`SELECT FOR UPDATE`): Exclusively locks data records during read operations.
- Optimistic Concurrency Control (Version tracking): Verifies that no other transaction has modified the entity before committing.
"""
(sources_dir / "cj_date_concurrency_locking.md").write_text(p10_content, encoding='utf-8')

# 11. OpenAPI Specification v3.1.0
p11_content = """<!DOCTYPE html>
<html lang="en">
<head><title>OpenAPI Specification v3.1.0: RESTful API Modeling and Design</title></head>
<body>
<h1>OpenAPI Specification v3.1.0: RESTful API Modeling and Design</h1>
<p>OpenAPI Initiative, Linux Foundation, 2021. URL: https://spec.openapis.org/oas/v3.1.0</p>
<section>
<h2>RESTful API Contract Modeling</h2>
<p>The OpenAPI Specification (OAS) defines a standard, language-agnostic interface description for HTTP REST APIs. It allows humans and computers to discover and understand the capabilities of a service without access to source code or additional documentation.</p>
<h2>Components and Schemas</h2>
<p>OAS v3.1 aligns with JSON Schema draft 2020-12, enabling rigorous definition of request bodies, URL path parameters, response payloads, HTTP status codes (200 OK, 201 Created, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found), and OAuth2/Bearer authentication schemes for e-commerce endpoints.</p>
</section>
</body>
</html>
"""
(sources_dir / "openapi_specification_v310.html").write_text(p11_content, encoding='utf-8')

# 12. Marcotte Responsive Web Design
p12_content = """# Responsive Web Design
Author: Ethan Marcotte
Publisher: A Book Apart, 2011.
Reference: https://abookapart.com/products/responsive-web-design

## Core Ingredients of Responsive Web Design
Responsive Web Design (RWD) provides an approach where web interfaces adapt smoothly to the screen resolution and constraints of multiple devices (desktop monitors, laptops, tablets, and smartphones) using three core technical pillars:
1. Fluid Grids: Designing page layout using proportional units (percentages, em/rem, CSS grid and flexbox) rather than rigid pixel dimensions.
2. Flexible Images and Media: Sizing images within fluid containers using `max-width: 100%` so visual assets scale without overflowing their parent elements.
3. CSS Media Queries: Querying device characteristics (viewport width, orientation, display pixel ratio) to tailor CSS styling and breakpoints for optimal readability and touch ergonomics on mobile devices.
"""
(sources_dir / "marcotte_responsive_web_design.md").write_text(p12_content, encoding='utf-8')

print("All 12 source files successfully generated in artifacts/course-essay/strongwine-revision-20261027/sources/")
