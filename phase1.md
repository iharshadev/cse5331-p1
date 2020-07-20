# CSE 5331 - Project 1 - Phase 1

|Student Id | Student Name|
---|---
|1001767678| Harshavardhan Ramamurthy|
|1001767676| Karan Rajpal|

# Pseudocode to simulate a rigorous two phase locking protocol with wound wait method to deal with deadlocks and concurrency control

```python
main():
    READ input_file
    FOR each line in input_file:
        Retreive contents of transaction table into current_transaction
        IF current_transaction is blocked THEN
            Add operation to list of waiting operations for current_transaction in transaction table
        ELSE
            IF current_transaction is aborted THEN
                Disregard the operation
            ELSE
                execute_operation()

execute_operation(operation):
    split the letters and numbers from the transaction

    IF operation = 'b' THEN
        Increment counter
        begin_transaction()
    IF operation = 'r' THEN
        Get the item to be read from the variable/data structure storing it
        Apply read_lock on the variable using readlock(variable)
    IF operation = 'w' THEN
        apply write lock using writelock()
    IF operation = 'e' THEN
        COMMIT transaction using commit()

readlock():
    retreive the item's record from lock table
    
```
