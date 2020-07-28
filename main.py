import re
import sys
import time
from copy import deepcopy


def tokenize(line):
    if re.match("b|e\d", line):
        return {"operation": line[0],
                "transaction": int(re.findall("\d", line)[0])}
    elif re.match("r|w\d\s*\([A-Z a-z]?\)", line):
        return {"operation": line[0],
                "transaction": int(re.findall("\d+", line)[0]),
                "item": re.findall("[A-Z a-z]?", line.split("(")[1])[0]}


def parse(line):
    if re.match("b|e\d", line):
        return Record(op=line[0], tid=int(re.findall("\d", line)[0]))
    elif re.match("r|w\d\s*\([A-Z a-z]?\)", line):
        return Record(op=line[0],
                      tid=int(re.findall("\d+", line)[0]),
                      item=re.findall("[A-Z a-z]?", line.split("(")[1])[0])


class Transaction:
    def __init__(self, tid, timestamp):
        self.tid = tid
        self.timestamp = timestamp
        self.items = []
        self.operations = []
        self.status = "active"

    def add_item(self, item):
        self.items.append(item)

    def add_operation(self, operation):
        self.operations.append(operation)


class LockTable:
    def __init__(self, item):
        self.item = item
        self.holding = []
        self.waiting = []
        self.current_state = None
        self.locklookup = {"r": "read", "w": "write"}

    def state(self):
        return self.locklookup[self.current_state]


class Record:

    def __init__(self, op, tid, item=None):
        self.__locklookup__ = {"r": "read", "w": "write"}
        self.op = op
        self.tid = tid
        self.item = None
        if op == "r" or op == "w":
            self.item = item

    def __str__(self):
        if self.item is None:
            return f"{self.op}{self.tid}"
        return f"{self.op}{self.tid}({self.item})"

    def lock(self):
        return self.__locklookup__[self.op]


class TwoPhaseLocking:
    def __init__(self):
        self.timestamp = time.time() * 1000
        self.TRANSACTION_TABLE = {}
        self.LOCK_TABLE = {}
        self.counter = 0
        self.print_ts = 1
    
    def print_log(self, message, record=None):
        print(f"{self.print_ts} - {message} {'- ' + str(record) if record else ''}")
        self.print_ts += 1
        return

    def begin_transaction(self, record, counter):
        if record.tid in self.TRANSACTION_TABLE:
            print("Malformed Input. Transaction T{} started more than once".format(record.tid))
        else:
            self.TRANSACTION_TABLE[record.tid] = Transaction(record.tid, self.timestamp + counter)
            message = f"Transaction T{record.tid} started"
            self.print_log(message, record)

    def prevent_deadlock(self, line, holding, lock="write"):
        if control_method == ALLOWED_CONTROL_METHODS[0]:
            self.wound_wait(line, holding, lock)
        elif control_method == ALLOWED_CONTROL_METHODS[1]:
            self.wait_die(line, holding, lock)
        else:
            self.caution_wait(line, holding, lock)

    def wound_wait(self, line, holding, lock):
        if self.TRANSACTION_TABLE[line.tid].timestamp < self.TRANSACTION_TABLE[holding].timestamp:
            abort_message = f"T{holding} aborted since an older transaction T{line.tid} applied write-lock on item {line.item}"
            self.print_log(abort_message, line)
            self.terminate_transaction(holding, term_type="abort", reason=abort_message, line=line)
            self.LOCK_TABLE[line.item].holding.append(line.tid)
            self.LOCK_TABLE[line.item].current_state = lock
            print("T{} applied write-lock on item {}".format(line.tid, line.item))
        else:
            waitlist_message = f"T{line.tid} blocked for {line.lock()}-lock on item {line.item}. REASON: Older transaction T{holding} has applied {self.LOCK_TABLE[line.item].state()} lock on it."
            self.print_log(waitlist_message, line)
            self.TRANSACTION_TABLE[line.tid].operations.append((line.op, line.item))
            if line.item not in self.TRANSACTION_TABLE[line.tid].items:
                self.TRANSACTION_TABLE[line.tid].items.append(line.item)
            self.TRANSACTION_TABLE[line.tid].status = "blocked"
            if line.tid not in self.LOCK_TABLE[line.item].waiting:
                self.LOCK_TABLE[line.item].waiting.append(line.tid)

    def wait_die(self, line, holding, lock):
        if self.TRANSACTION_TABLE[line.tid].timestamp < self.TRANSACTION_TABLE[holding].timestamp:
            waitlist_message = f"T{line.tid} blocked for {line.lock()}-lock on item {line.item}. REASON: Older transaction T{holding} has applied {self.LOCK_TABLE[line.item].state()} lock on it."
            self.print_log(waitlist_message, line)
            self.TRANSACTION_TABLE[line.tid].operations.append((line.op, line.item))
            if line.item not in self.TRANSACTION_TABLE[line.tid].items:
                self.TRANSACTION_TABLE[line.tid].items.append(line.item)
            self.TRANSACTION_TABLE[line.tid].status = "blocked"
            if line.tid not in self.LOCK_TABLE[line.item].waiting:
                self.LOCK_TABLE[line.item].waiting.append(line.tid)
        else:
            abort_message = f"T{holding} aborted since a younger transaction T{line.tid} applied write-lock on item {line.item}"
            self.print_log(abort_message, line)
            self.terminate_transaction(holding, term_type="abort", reason=abort_message, line=line)
            self.LOCK_TABLE[line.item].holding.append(line.tid)
            self.LOCK_TABLE[line.item].current_state = lock
            self.print_log("T{} applied write-lock on item {}".format(line.tid, line.item), line)

    def cautious_wait(self, line, holding, lock):
        pass

    def get_younger_than(self, tid, item):
        return [key for (key, value) in self.TRANSACTION_TABLE.items()
                if value.timestamp > self.TRANSACTION_TABLE[tid].timestamp
                and (key in self.LOCK_TABLE[item].holding or key in self.LOCK_TABLE[item].waiting)]

    def terminate_transaction(self, tid, term_type="committ", **kwargs):
        reason = kwargs.get("reason")
        line = kwargs.get("line")

        if term_type == "abort":
            abort_message = f"Aborting transaction T{tid}. REASON: {reason}"
            self.print_log(abort_message, line)
        else:
            release_message = f"Transaction T{tid} {term_type}ed. Releasing all locks held"
            self.print_log(release_message, line)

        items_to_be_freed = deepcopy(self.TRANSACTION_TABLE[tid].items)

        for i in items_to_be_freed:
            self.TRANSACTION_TABLE[tid].items.remove(i)
            if tid in self.LOCK_TABLE[i].holding:
                self.unlock(i, tid)

        for i in items_to_be_freed:
            if self.LOCK_TABLE[i].waiting:
                tid_waiting = self.LOCK_TABLE[i].waiting.pop(0)
                resume_message = f"T{tid_waiting} resumed operation from wait-list for item {i}."
                self.print_log(resume_message, line)
                waiting_ops = deepcopy(self.TRANSACTION_TABLE[tid_waiting].operations)
                for exec_op in waiting_ops:
                    self.TRANSACTION_TABLE[tid_waiting].operations.remove(exec_op)
                    self.execute_operation(Record(exec_op[0],
                                                  tid_waiting,
                                                  exec_op[1]), resume=True, op=exec_op)

        self.TRANSACTION_TABLE[tid].items = []
        self.TRANSACTION_TABLE[tid].operations = []
        self.TRANSACTION_TABLE[tid].status = "{}ed".format(term_type)

    def unlock(self, item, tid):
        for index, tpl in enumerate(self.TRANSACTION_TABLE[tid].operations):
            if tpl[1] == item:
                del self.TRANSACTION_TABLE[tid].operations[index]
        self.LOCK_TABLE[item].holding.remove(tid)
        self.LOCK_TABLE[item].current_state = None
        release_message = f"\tT{tid} released lock on item {item}"
        print(release_message)

    def simulate(self, schedule):
        [self.execute_operation(line) for line in schedule]

    def execute_operation(self, line, resume=False, op=None):
        if line.op == 'b':
            self.counter += 1
            self.begin_transaction(line, self.counter)
        elif line.op == "r":
            if self.TRANSACTION_TABLE[line.tid].status in ["aborted", "ended"]:
                pass
            elif line.item in self.LOCK_TABLE:
                if self.LOCK_TABLE[line.item].current_state == "w":
                    message = f"Item {line.item} already write-locked by T{self.LOCK_TABLE[line.item].holding[0]}. Using {control_method} to resolve conflict"
                    self.print_log(message, line)
                    self.prevent_deadlock(line, self.LOCK_TABLE[line.item].holding[0], "read")
                else:
                    message = f"T{line.tid} applied read-lock on item {line.item}"
                    self.print_log(message, line)
                    if self.TRANSACTION_TABLE[line.tid].status == "active":
                        if line.item not in self.TRANSACTION_TABLE[line.tid].items:
                            self.TRANSACTION_TABLE[line.tid].items.append(line.item)
                    elif self.TRANSACTION_TABLE[line.tid].status == "blocked":
                        self.TRANSACTION_TABLE[line.tid].status = "active"
                    self.LOCK_TABLE[line.item].holding.append(line.tid)
                    self.LOCK_TABLE[line.item].current_state = "r"
                    if op and op in self.TRANSACTION_TABLE[line.tid].operations:
                        self.TRANSACTION_TABLE[line.tid].operations.remove(op)
            else:
                message = f"T{line.tid} applied read-lock on item {line.item}"
                self.print_log(message, line)
                # self.TRANSACTION_TABLE[line.tid].operations.append((line.op, line.item))
                if line.item not in self.TRANSACTION_TABLE[line.tid].items:
                    self.TRANSACTION_TABLE[line.tid].items.append(line.item)
                self.LOCK_TABLE[line.item] = LockTable(line.item)
                self.LOCK_TABLE[line.item].holding.append(line.tid)
                self.LOCK_TABLE[line.item].current_state = "r"

        elif line.op == "w":
            if self.TRANSACTION_TABLE[line.tid].status in ["aborted", "ended"]:
                pass
            else:
                for younger_tid in self.get_younger_than(line.tid, line.item):
                    # self.abort(younger_tid, line.tid)
                    abort_reason = f"Older transaction T{line.tid} applied write-lock on {line.item}"
                    self.print_log(abort_reason, line)
                    self.terminate_transaction(younger_tid, term_type="abort", reason=abort_reason, line=line)

                # if item is locked by a transaction
                if line.item in self.LOCK_TABLE:
                    if not self.LOCK_TABLE[line.item].holding:
                        wlock_message = f"T{line.tid} applied write-lock on item {line.item}"
                        self.print_log(wlock_message, line)
                        self.LOCK_TABLE[line.item].current_state = "w"
                        self.LOCK_TABLE[line.item].holding.append(line.tid)
                        if op and op in self.TRANSACTION_TABLE[line.tid].operations:
                            self.TRANSACTION_TABLE[line.tid].operations.remove(op)
                    else:
                        tid_holding = self.LOCK_TABLE[line.item].holding[-1]
                        if tid_holding == line.tid:
                            upgrade_message = f"T{line.tid} upgraded the lock on item {line.item} to write"
                            self.print_log(upgrade_message)
                            self.LOCK_TABLE[line.item].current_state = "w"
                            if ("r", line.item) in self.TRANSACTION_TABLE[line.tid].operations:
                                index = self.TRANSACTION_TABLE[line.tid].operations.index(("r", line.item))
                                self.TRANSACTION_TABLE[line.tid].operations[index] = ("w", line.item)
                            if op and op in self.TRANSACTION_TABLE[line.tid].operations:
                                self.TRANSACTION_TABLE[line.tid].operations.remove(op)
                        else:
                            state = self.LOCK_TABLE[line.item].current_state
                            holding_item = self.LOCK_TABLE[line.item].holding[-1]
                            conflict_message = f"Conflict: Already {state}-locked by T{holding_item}. Using {control_method} to resolve conflict."
                            self.print_log(conflict_message, line)
                            self.prevent_deadlock(line, tid_holding)
                else:
                    wlock_message = f"T{line.tid} applied write-lock on item {line.item}"
                    self.print_log(wlock_message, line)
                    self.LOCK_TABLE[line.item].current_state = "w"
                    self.LOCK_TABLE[line.item].holding.append(line.tid)

        elif line.op == "e":
            if self.TRANSACTION_TABLE[line.tid].status != "aborted":
                self.terminate_transaction(line.tid, line=line)


operations = []

ALLOWED_CONTROL_METHODS = ["wound-wait", "wait-die", "caution-wait"]

if len(sys.argv) < 3:
    print(f"""Usage: python main.py <control-method> <input-file-path>
                control-methods:
                    1. {ALLOWED_CONTROL_METHODS[0]}
                    2. {ALLOWED_CONTROL_METHODS[1]}
                    3. {ALLOWED_CONTROL_METHODS[2]}""")
    exit(1)

control_method = sys.argv[1].lower()

if control_method in ALLOWED_CONTROL_METHODS:
    print(f"Using {control_method} for deadlock prevention\n")
else:
    print(f"Unsupported control method: {control_method}. Allowed methods are: {ALLOWED_CONTROL_METHODS}")
    exit(1)

with open(sys.argv[2], 'rt') as file:
    lines = file.readlines()
    for row in lines:
        operations.append(parse(row))

TwoPhaseLocking().simulate(operations)
