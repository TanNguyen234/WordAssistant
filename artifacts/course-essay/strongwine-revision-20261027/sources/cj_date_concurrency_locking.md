# An Introduction to Database Systems: Concurrency Control and Locking Mechanisms
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
