<h1 align="center"> 
    CSE 5331 | Project 1
</h1>

<h2 align="center">
    Phase 1 - Pseudocode to simulate a rigorous two phase locking protocol (2PL) with wound wait method to deal with deadlocks and concurrency control
</h2>

### Contributors

|Student Id | Student Name|
|---|---|
|1001767678| Harshavardhan Ramamurthy|
|1001767676| Karan Rajpal|

### Pseudo Code

```python
def main():
    READ input_file
    FOR each line in input_file:
        current_transaction := contents_of_transaction_table
        IF current_transaction is blocked THEN
            ADD operation to list of waiting operations for current_transaction in transaction table
        ELSE
            IF current_transaction is aborted THEN
                Disregard operation
            ELSE
                execute_operation()
```

```python
def execute_operation(operation):
    TOKENIZE line into operation and item

    IF operation = 'b' THEN
        INCREMENT counter
        begin_transaction()
    IF operation = 'r' THEN
        Get item to be read from the variable/data structure storing it
        Apply read_lock on the variable using readlock(variable)
    IF operation = 'w' THEN
        APPLY write lock using writelock()
    IF operation = 'e' THEN
        COMMIT transaction using commit()
```

```python
def readlock():
    RETREIVE record for item from transaction_table
    IF record for item NOT IN lock_table THEN
        INSERT item into the lock_table with 'read' as state of lock
        DISPLAY the reansaction that has readlocked the item
    ELSE
        IF item is writelocked THEN
            # Conflict in transaction
            # Use wound wait to make a resolution
            wound_wait()
        ELSE
            UPDATE item in lock_table
            APPEND tid to transaction_holding
            UPDATE items OF transaction IN transaction_table
            DISPLAY the transaction that has readlocked the item
```

```python
def writelock():
    RETREIVE record for item from lock_table
    IF item is already locked THEN
        GET type of lock from transaction that has currently locked the item
    IF item locked by same transaction THEN
        UPDATE lock table entry for the item from readlock to writelock
        DISPLAY the transaction that has upgraded the lock
    ELSE
        IF item IS NOT locked THEN
            UPDATE status OF item TO writelocked
            APPEND tid to the transaction_holding
            DISPLAY the transaction that has held the lock
        ELSE
            IF item locked by another transaction THEN
                call wound_wait() to resolve conflict
            ELSE
                INSERT entry to lock_table
                DISPLAY the transaction that has writelocked the item
```

```python
def commit():
    items := {items_locked_by_transaction}
    FOR EACH item in items:
        unlock(item) # to unlock items
    UPDATE status OF transaction in transaction_table to "committed"
    DISPLAY that the transaction has been committed
```

```python
def abort():
    items := {items_locked_by_transaction}
    FOR EACH item in items:
        unlock(item) # to unlock items
    UPDATE status OF transaction in transaction_table to "aborted"
```

```python
def unlock():
    CHECK any previous waiting transactions from lock_table
    IF transaction is waiting THEN
        DISPLAY that the transaction has resumed its operation
```

```python
def wound_wait():
    request_timestamp := timestamp_of_requesting_transaction
    hold_timestamp := timestamp_holding_transaction_lock
    IF request_timestamp < hold_timestamp
        DISPLAY requesting_transaction will abort
        abort(requesting_transaction) # Will be restarted later with same timestamp
    ELSE
        # requesting_transaction will wait
        APPEND requesting_transaction to waiting_list
        UPDATE status of requesting_transaction in transaction_table to "blocked"
        DISPLAY requesting_transaction is blocked
```
