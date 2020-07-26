import re
import sys
import time


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


class Record:
    def __init__(self, op, tid, item=None):
        self.op = op
        self.tid = tid
        self.item = None
        if op == "r" or op == "w":
            self.item = item

    def __str__(self):
        return "[Transaction: {}, Operation: {}, item: {}]".format(self.tid, self.op, self.item)


class WoundWait:
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

    def woundwait(self, line, holding):
        if self.TRANSACTION_TABLE[line.tid].timestamp < self.TRANSACTION_TABLE[holding].timestamp:
            print("T{} Aborted since an older transaction T{} applied write-lock on item {}.".format(
                holding, line.tid, line.item))
            self.abort(holding, line.tid)
            self.LOCK_TABLE[line.item].holding.append(line.tid)
            self.LOCK_TABLE[line.item].current_state = "write"
            print("T{} applied write-lock on item {}".format(line.tid, line.item))
        else:
            print("T{} added to wait-list for {}-lock on item {}".format(line.tid, line.op, line.item))
            self.TRANSACTION_TABLE[line.tid].operations.append(line.op)
            self.TRANSACTION_TABLE[line.tid].items.append(line.item)

    def abort(self, tid, older_tid=None):
        for item in self.TRANSACTION_TABLE[tid].items:
            if tid in self.LOCK_TABLE[item].holding:
                self.LOCK_TABLE[item].holding.remove(tid)

            if tid in self.LOCK_TABLE[item].waiting:
                self.LOCK_TABLE[item].waiting.remove(tid)

            self.TRANSACTION_TABLE[tid].status = "aborted"
            self.TRANSACTION_TABLE[tid].items = []
            self.TRANSACTION_TABLE[tid].operations = []
        print("Transaction T{} aborted because an older transaction T{} applied write-lock on a shared item".format(
            tid, older_tid))

    def get_younger_than(self, tid, item):
        return [key for (key, value) in self.TRANSACTION_TABLE.items()
                if value.timestamp > self.TRANSACTION_TABLE[tid].timestamp
                and (key in self.LOCK_TABLE[item].holding or key in self.LOCK_TABLE[item].waiting)]

    def end_transaction(self, tid):
        print("Transaction T{} ended. Releasing all locks".format(tid))
        for i in self.TRANSACTION_TABLE[tid].items:
            if tid in self.LOCK_TABLE[i].holding:
                self.unlock(i, tid)
        # TODO: Execute next oldest transaction recursively
        self.TRANSACTION_TABLE[tid].items = []
        self.TRANSACTION_TABLE[tid].operations = []
        self.TRANSACTION_TABLE[tid].status = "ended"

    def unlock(self, item, tid):
        self.TRANSACTION_TABLE[tid].items.remove(item)
        self.LOCK_TABLE[item].holding.remove(tid)
        print("\tT{} released lock on item {}".format(tid, item))

        if self.LOCK_TABLE[item].waiting:
            tid_waiting = self.LOCK_TABLE[item].waiting.pop()
            op_waiting = self.TRANSACTION_TABLE[tid_waiting].operations[-1]
            self.LOCK_TABLE[item].holding.append(tid_waiting)
            self.LOCK_TABLE[item].current_state = op_waiting
            print("T{} resumed operation from wait-list.".format(tid_waiting, op_waiting, item))
            while self.TRANSACTION_TABLE[tid_waiting].operations and self.TRANSACTION_TABLE[tid_waiting].items:
                self.execute_operation(Record(self.TRANSACTION_TABLE[tid_waiting].operations.pop(0),
                                              tid_waiting,
                                              self.TRANSACTION_TABLE[tid_waiting].items.pop(0)))

    def simulate(self, schedule):
        [self.execute_operation(line) for line in schedule]

    def execute_operation(self, line):
        if line.op == 'b':
            self.counter += 1
            self.begin_transaction(line, self.counter)
        elif line.op == "r":
            if self.TRANSACTION_TABLE[line.tid].status in ["aborted", "ended"]:
                pass
            elif line.item in self.LOCK_TABLE:
                if self.LOCK_TABLE[line.item].current_state == "write":
                    print("Item {} already write-locked by T{}. Adding read-operation to wait-list".format(
                        line.item, self.LOCK_TABLE[line.item].holding[0]
                    ))
                    self.LOCK_TABLE[line.item].waiting.append(line.tid)
                    self.TRANSACTION_TABLE[line.tid].operations.append(line.op)
                    self.TRANSACTION_TABLE[line.tid].items.append(line.item)
                else:
                    print("T{} applied read-lock on item {}".format(line.tid, line.item))
                    # self.TRANSACTION_TABLE[line.tid].operations.append(line.op)
                    # self.TRANSACTION_TABLE[line.tid].items.append(line.item)
                    self.LOCK_TABLE[line.item].holding.append(line.tid)
                    self.LOCK_TABLE[line.item].current_state = "read"
            else:
                print("T{} applied read-lock on item {}".format(line.tid, line.item))
                # self.TRANSACTION_TABLE[line.tid].operations.append(line.op)
                # self.TRANSACTION_TABLE[line.tid].items.append(line.item)
                self.LOCK_TABLE[line.item] = LockTable(line.item)
                self.LOCK_TABLE[line.item].holding.append(line.tid)
                self.LOCK_TABLE[line.item].current_state = "read"

        elif line.op == "w":
            if self.TRANSACTION_TABLE[line.tid].status in ["aborted", "ended"]:
                pass
            else:
                # print("T{} attempting to write-lock item {}".format(line.tid, line.item))
                [self.abort(younger_tid, line.tid) for younger_tid in self.get_younger_than(line.tid, line.item)]

                if line.item in self.LOCK_TABLE:
                    if not self.LOCK_TABLE[line.item].holding:
                        print("T{} applied write-lock on item {}".format(line.tid, line.item))
                    else:
                        tid_holding = self.LOCK_TABLE[line.item].holding[-1]
                        if tid_holding == line.tid:
                            print("T{} upgraded the lock on item{} from to write".format(line.tid, line.item))
                            self.LOCK_TABLE[line.item].current_state = "write"
                        else:
                            print(
                                "Conflict: Already {}-locked by T{}. Using wound-wait to resolve conflict".format(
                                    self.LOCK_TABLE[line.item].current_state, self.LOCK_TABLE[line.item].holding[-1]))
                            self.woundwait(line, tid_holding)
        elif line.op == "e":
            if self.TRANSACTION_TABLE[line.tid].status != "aborted":
                self.end_transaction(line.tid)


if len(sys.argv) < 3:
    print("Usage: python main.py <control-method> <input-file>"
          "\ncontrol-methods:\n1.wound-wait\n2.wait-die3.something-else")
    exit(1)

operations = []

with open(sys.argv[2], 'rt') as file:
    lines = file.readlines()
    for row in lines:
        operations.append(parse(row))
WoundWait().simulate(operations)
