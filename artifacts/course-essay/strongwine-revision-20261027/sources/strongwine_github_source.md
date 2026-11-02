# StrongWine Web Application Repository
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
