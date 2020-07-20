# CSE 5331 - Project 1 - Phase 1

|Student Id | Student Name|
---|---
|1001767678| Harshavardhan Ramamurthy|
|1001767676| Karan Rajpal|

# Pseudocode to simulate a rigorous two phase locking protocol with wound wait method to deal with deadlocks and concurrency control

```python
def main():
    READ input_file
    FOR each line in input_file:
        RETREIVE contents of transaction table into current_transaction
        IF current_transaction is blocked THEN
            ADD operation to list of waiting operations for current_transaction in transaction table
        ELSE
            IF current_transaction is aborted THEN
                Disregard the operation
            ELSE
                execute_operation()

def execute_operation(operation):
    TOKENIZE the line into operation and item

    IF operation = 'b' THEN
        INCREMENT counter
        begin_transaction()
    IF operation = 'r' THEN
        Get the item to be read from the variable/data structure storing it
        Apply read_lock on the variable using readlock(variable)
    IF operation = 'w' THEN
        APPLY write lock using writelock()
    IF operation = 'e' THEN
        COMMIT transaction using commit()

def readlock():
    RETREIVE record for the item from transaction_table
    IF record for item NOT IN lock_table THEN
        INSERT item into the lock_table with 'read' as state of lock
        DISPLAY the reansaction that has readlocked the item
    ELSE
        IF item is writelocked THEN
            # Conflict in transaction; use wound wait to take an appropriate decision to resolve the situation
            wound_wait()
        ELSE
            UPDATE item in the lock_table
            APPEND Tid to transaction_holding
            UPDATE items field of the transaction_table for the transaction
            DISPLAY the transaction that has readlocked the item


def writelock():
    RETREIVE the record for the item from lock_table
    IF the item is already locked THEN
        GET type of lock from transaction that has currently locked the item
    IF item locked by same transaction THEN
        UPDATE lock table entry for the item from readlock to writelock
        DISPLAY the transaction that has upgraded the lock
    ELSE
        IF item IS NOT locked THEN
            UPDATE status of the item to writelocked
            APPEND Tid to the transaction_holding
            DISPLAY the transaction that has held the lock
        ELSE
            IF item locked by another transaction THEN
                call wound_wait() to resolve conflict
            ELSE
                INSERT entry to lock_table
                DISPLAY the transaction that has writelocked the item

def commit():
    items := {items locked by transaction}
    RETREIVE items locked by transaction
    FOR EACH item in items:
        unlock(item)
    UPDATE status of the transaction in transaction_table to committed
    DISPLAY that the transaction has been committed

def abort():
    items := { items locked by the transaction}
    RETREIVE items locked by the transaction
    FOR EACH item in items:
        unlock() to unlock items
    UPDATE status of transaction in transaction_table to aborted

def unlock():
    CHECK any previous waiting transactions from lock_table
    IF transaction is waiting THEN
        DISPLAY that the transaction has resumed its operation
        
```
