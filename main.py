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
        self.op = op
        self.tid = tid
        self.item = None
        if op == "r" or op == "w":
            self.item = item

    def __str__(self):
        return "[Transaction: {}, Operation: {}, item: {}]".format(self.tid, self.op, self.item)


class TwoPhaseLocking:
    def __init__(self):
        self.timestamp = time.time() * 1000
        self.TRANSACTION_TABLE = {}
        self.LOCK_TABLE = {}
        self.counter = 0

    def begin_transaction(self, record, counter):
        if record.tid in self.TRANSACTION_TABLE:
            print("Malformed Input. Transaction T{} started more than once".format(record.tid))
        else:
            self.TRANSACTION_TABLE[record.tid] = Transaction(record.tid, self.timestamp + counter)
            print("Transaction T{} started".format(record.tid))

    def woundwait(self, line, holding, lock="write"):
        if self.TRANSACTION_TABLE[line.tid].timestamp < self.TRANSACTION_TABLE[holding].timestamp:
            abort_reason = "T{} Aborted since an older transaction T{} applied write-lock on item {}.".format(
                holding, line.tid, line.item)
            self.terminate_transaction(holding, term_type="abort", reason=abort_reason)
            self.LOCK_TABLE[line.item].holding.append(line.tid)
            self.LOCK_TABLE[line.item].current_state = lock
            print("T{} applied write-lock on item {}".format(line.tid, line.item))
        else:
            print("T{} added to wait-list for {}-lock on item {}.\
            REASON: Older transaction T{} has applied {} lock on it".format(
                line.tid, line.op, line.item, holding, self.LOCK_TABLE[line.item].state()))
            self.TRANSACTION_TABLE[line.tid].operations.append((line.op, line.item))
            if line.item not in self.TRANSACTION_TABLE[line.tid].items:
                self.TRANSACTION_TABLE[line.tid].items.append(line.item)
            self.TRANSACTION_TABLE[line.tid].status = "wait"
            if line.tid not in self.LOCK_TABLE[line.item].waiting:
                self.LOCK_TABLE[line.item].waiting.append(line.tid)

    def get_younger_than(self, tid, item):
        return [key for (key, value) in self.TRANSACTION_TABLE.items()
                if value.timestamp > self.TRANSACTION_TABLE[tid].timestamp
                and (key in self.LOCK_TABLE[item].holding or key in self.LOCK_TABLE[item].waiting)]

    def terminate_transaction(self, tid, term_type="end", **kwargs):
        if term_type == "abort":
            print("Aborting transaction T{}. REASON: {}".format(tid, kwargs["reason"]))
        else:
            print("Transaction T{} {}ed. Releasing all locks held".format(tid, term_type))

        items_to_be_freed = deepcopy(self.TRANSACTION_TABLE[tid].items)

        for i in items_to_be_freed:
            self.TRANSACTION_TABLE[tid].items.remove(i)
            if tid in self.LOCK_TABLE[i].holding:
                self.unlock(i, tid)

        for i in items_to_be_freed:
            if self.LOCK_TABLE[i].waiting:
                tid_waiting = self.LOCK_TABLE[i].waiting.pop(0)
                print("T{} resumed operation from wait-list.".format(tid_waiting))
                waiting_ops = deepcopy(self.TRANSACTION_TABLE[tid_waiting].operations)
                for exec_op in waiting_ops:
                    # exec_op = self.TRANSACTION_TABLE[tid_waiting].operations[0]
                    self.TRANSACTION_TABLE[tid_waiting].operations.remove(exec_op)
                    print("T{} resumed operation from wait-list.".format(tid_waiting))
                    self.execute_operation(Record(exec_op[0],
                                                  tid_waiting,
                                                  exec_op[1]), resume=True, op=exec_op)


        self.TRANSACTION_TABLE[tid].items = []
        self.TRANSACTION_TABLE[tid].operations = []
        self.TRANSACTION_TABLE[tid].status = "{}ed".format(term_type)

    def unlock(self, item, tid):
        # item_index = self.TRANSACTION_TABLE[tid].items.index(item)

        for index, tpl in enumerate(self.TRANSACTION_TABLE[tid].operations):
            if tpl[1] == item:
                del self.TRANSACTION_TABLE[tid].operations[index]
        self.LOCK_TABLE[item].holding.remove(tid)
        self.LOCK_TABLE[item].current_state = None
        print("\tT{} released lock on item {}".format(tid, item))

        # if self.LOCK_TABLE[item].waiting:
        #     tid_waiting = self.LOCK_TABLE[item].waiting.pop(0)
        #     print("T{} resumed operation from wait-list.".format(tid_waiting))
            #
            # for i, exec_op in enumerate(self.TRANSACTION_TABLE[tid_waiting].operations):
            #     # exec_op = self.TRANSACTION_TABLE[tid_waiting].operations[0]
            #     del self.TRANSACTION_TABLE[tid_waiting].operations[i]
            #     self.execute_operation(Record(exec_op[0],
            #                                   tid_waiting,
            #                                   exec_op[1]))

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
                    print("Item {} already write-locked by T{}. Using wound-wait to resolve conflict".format(
                        line.item, self.LOCK_TABLE[line.item].holding[0]
                    ))
                    self.woundwait(line, self.LOCK_TABLE[line.item].holding[0], "read")
                else:
                    print("T{} applied read-lock on item {}".format(line.tid, line.item))
                    if self.TRANSACTION_TABLE[line.tid].status == "active":
                        # self.TRANSACTION_TABLE[line.tid].operations.append((line.op, line.item))
                        if line.item not in self.TRANSACTION_TABLE[line.tid].items:
                            self.TRANSACTION_TABLE[line.tid].items.append(line.item)
                    elif self.TRANSACTION_TABLE[line.tid].status == "wait":
                        self.TRANSACTION_TABLE[line.tid].status = "active"
                    self.LOCK_TABLE[line.item].holding.append(line.tid)
                    self.LOCK_TABLE[line.item].current_state = "r"
                    if op and op in self.TRANSACTION_TABLE[line.tid].operations:
                        self.TRANSACTION_TABLE[line.tid].operations.remove(op)
            else:
                print("T{} applied read-lock on item {}".format(line.tid, line.item))
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
                    abort_reason = "Older transaction T{} applied write-lock on {}".format(line.tid, line.item)
                    self.terminate_transaction(younger_tid, term_type="abort", reason=abort_reason)

                # if item is locked by a transaction
                if line.item in self.LOCK_TABLE:
                    if not self.LOCK_TABLE[line.item].holding:
                        print("T{} applied write-lock on item {}".format(line.tid, line.item))
                        self.LOCK_TABLE[line.item].current_state = "w"
                        self.LOCK_TABLE[line.item].holding.append(line.tid)
                        if op and op in self.TRANSACTION_TABLE[line.tid].operations:
                            self.TRANSACTION_TABLE[line.tid].operations.remove(op)
                    else:
                        tid_holding = self.LOCK_TABLE[line.item].holding[-1]
                        if tid_holding == line.tid:
                            print("T{} upgraded the lock on item{} from to write".format(line.tid, line.item))
                            self.LOCK_TABLE[line.item].current_state = "w"
                            if ("r", line.item) in self.TRANSACTION_TABLE[line.tid].operations:
                                index = self.TRANSACTION_TABLE[line.tid].operations.index(("r", line.item))
                                self.TRANSACTION_TABLE[line.tid].operations[index] = ("w", line.item)
                            if op and op in self.TRANSACTION_TABLE[line.tid].operations:
                                self.TRANSACTION_TABLE[line.tid].operations.remove(op)
                        else:
                            print(
                                "Conflict: Already {}-locked by T{}. Using wound-wait to resolve conflict".format(
                                    self.LOCK_TABLE[line.item].current_state, self.LOCK_TABLE[line.item].holding[-1]))
                            self.woundwait(line, tid_holding)
                else:
                    print("T{} applied write-lock on item {}".format(line.tid, line.item))
                    self.LOCK_TABLE[line.item].current_state = "w"
                    self.LOCK_TABLE[line.item].holding.append(line.tid)

        elif line.op == "e":
            if self.TRANSACTION_TABLE[line.tid].status != "aborted":
                self.terminate_transaction(line.tid)


if len(sys.argv) < 3:
    print("Usage: python main.py <control-method> <input-file>"
          "\ncontrol-methods:\n1.wound-wait\n2.wait-die3.something-else")
    exit(1)

operations = []

with open(sys.argv[2], 'rt') as file:
    lines = file.readlines()
    for row in lines:
        operations.append(parse(row))
TwoPhaseLocking().simulate(operations)
