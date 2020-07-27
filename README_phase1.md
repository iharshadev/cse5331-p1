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

#### main()

Reads statements from input file and drives the program

```python
timestamp := 0 # To track the transaction's timestamp
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
#### begin_transaction(transaction_number, transation_timestamp)

Starts a transaction by adding an new entry in the transaction table with status as 'active'

```python
def begin_transaction(transaction_id, transation_timestamp):
    transaction_id := timestamp + transaction_number
    INSERT (tid:transaction_id,timestamp: transaction_timestamp, status: 'active', items:{}) for this transaction in the transaction_table 
    
```


#### execute_operation(operation)

Executes operation sent as an argument

```python
def execute_operation(operation):
    TOKENIZE line into operation and item

    IF operation = 'b' THEN
        INCREMENT timestamp
        begin_transaction()
    IF operation = 'r' THEN
        Get item to be read from the variable/data structure storing it
        Apply read_lock on the variable using readlock(variable)
    IF operation = 'w' THEN
        APPLY write lock using writelock()
    IF operation = 'e' THEN
        COMMIT transaction using commit()
```

#### readlock()

Retrieves all records present in the lock_table for an item. If no records are present, then records are inserted to lock_table with appropriate status and the transaction table is updated as well. If the item is locked by a non-conflicting transaction, then it is unlocked. If the transcation is write-locked by another transcation then wound_wait() is executed.

```python
def readlock():
    record := entry for the item in transaction_table
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

#### writelock()

Retrieves all records present in the lock_table for an item. If item is read-locked by the same transaction, then the lock status is updated to a write-lock. If the item is unlocked beforehand, then the status is updated to write-locked directly. If the item is locked by another transaction, then wound_wait() is executed. 

```python
def writelock():
    item := record for the item from lock_table
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

#### commit()

Unlocks all present locks for a transaction and updates the status to committed in the transaction table.

```python
def commit():
    items := {items_locked_by_transaction}
    FOR EACH item in items:
        unlock(item) # to unlock items
    UPDATE status OF transaction in transaction_table to "committed"
    DISPLAY that the transaction has been committed
```

#### abort()

Unlocks all present locks for a transaction and updates the status to aborted in the transaction table.

```python
def abort():
    items := {items_locked_by_transaction}
    FOR EACH item in items:
        unlock(item) # to unlock items
    UPDATE status OF transaction in transaction_table to "aborted"
```

#### unlock()

Unlocks item in the transaction table by updating the status accordingly. If any transactions are waiting for this item the the lock is granted to them. 

```python
def unlock():
    FOR EACH transaction in lock_table
        IF transaction is waiting THEN
            resumed_transaction := {transaction}
            DISPLAY resumed_transaction has resumed operation
            GET tid of resumed_transaction from lock_table
            REMOVE tid of resumed_transaction from transaction_waiting in lock_table
            APPEND tid of resumed_transaction to transaction_holding in lock_table
            UPDATE status of resumed_transaction in transaction_table to "active"
            # Execute waiting operations from transaction table
            operations_list := {operations from transaction_table}
            FOR EACH operation in operations_list
                execute_operation()
        ELSE
            REMOVE tid of transaction from transaction_holding in lock_table
            UPDATE state of transaction in lock_table to "unlocked"
            REMOVE tid of transaction from items in transaction_table
```

#### wound_wait()

Used to decide which transaction will wait and which will abort when a deadlock occurs based on the timestamp stored in the transaction table.

```python
def wound_wait():
    request_timestamp := timestamp_of_requesting_transaction
    hold_timestamp := timestamp_holding_transaction_lock
    IF request_timestamp < hold_timestamp THEN
        DISPLAY requesting_transaction will abort
        abort(requesting_transaction) # Will be restarted later with same timestamp
    ELSE
        # requesting_transaction will wait
        APPEND tid of requesting_transaction to transaction_waiting in lock_table
        UPDATE status of requesting_transaction in transaction_table to "blocked"
        DISPLAY requesting_transaction is blocked
```

### Data Structures Proposed

#### Transaction Table
Attribute|Description|Data type
---|---|---
tid | Transaction ID | `int`
timestamp | Transaction Timestamp | `int`
items | Items the current transaction holds | `list` 
status | State of current transaction(active, committed, aborted) | `string`
operations | Operations in the waiting transaction| `list`

#### Lock Table
Attribute|Description|Data type
---|---|---
item | The item locked or unlocked by the transaction | `int`
tid_holding | List of transactions currently holding the item| `list`
tid_waiting | List of transactions currently waiting to hold the item | `list`
state | Current state of the item (r/w)| `str` 