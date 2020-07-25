import re
import sys
import time
from collections import OrderedDict
from pprint import pprint


def tokenize(line):
    if re.match("b|e\d", line):
        return {"operation": line[0],
                "transaction": int(re.findall("\d", line)[0])}
    elif re.match("r|w\d\s*\([A-Z a-z]?\)", line):
        return {"operation": line[0],
                "transaction": int(re.findall("\d+", line)[0]),
                "item": re.findall("[A-Z a-z]?", line.split("(")[1])[0]}


# todo: Implement
def wound_wait(operations):
    transaction_table = {}
    lock_table = {}
    ts = int(time.time() * 1000)
    counter = 0
    for index, rec in enumerate(operations):
        # pprint(rec)
        operation = rec["operation"]
        transaction = rec["transaction"]
        if operation == "b":
            counter += 1
            # todo: Check if transaction has already ended and throw error
            transaction_table[rec["transaction"]] = {"id": rec["transaction"],
                                                     "timestamp": ts + counter,
                                                     "items": set(),
                                                     "status": "active",
                                                     "operations": []
                                                     }
            print("Transaction {} started".format(transaction))
        elif operation == "r":
            item = rec["item"]
            if item not in lock_table:
                print("T{} applied read-lock on {}".format(transaction, item))
                holding = OrderedDict()
                holding["tid"] = transaction
                holding["op"] = "r"
                lock_table[item] = {"item": item,
                                    "holding": holding,
                                    "status": "r",
                                    "waiting": OrderedDict()
                                    }
                transaction_table[transaction]["items"].add(item)
            else:
                status = lock_table[item]["holding"][0]["op"]
                tid = lock_table[item]["holding"][0]["tid"]
                if status == "w":
                    print("{} already write-locked by {}. Adding read-operation to wait-list".format(item, tid))
                    lock_table[item]["waiting"].append({"tid": transaction, "op": operation})
                    transaction_table[transaction]["items"].add(item)
                else:
                    print("T{} has applied read-lock on {}".format(transaction, item))
                    transaction_table[transaction]["items"].add(item)
                    lock_table[item]["holding"].append({"tid": transaction, "op": "r"})
        elif operation == "w":
            item = rec["item"]
            if item in lock_table:
                current_rec = lock_table[item]["holding"][0]
                current_tid = current_rec["tid"]
                current_op = current_rec["op"]
                if current_op == "w":
                    print("{} is already write-locked by T{}. Adding read operation to wait-list".format(
                        item,current_tid))
                    lock_table[item]["waiting"].append({"tid": transaction, "op": operation})
                elif current_op == "r" and current_tid == transaction:
                    print("T{} upgraded lock from read to write on {}".format(transaction, item))
                    lock_table[item]["holding"][0]["op"] = "w"
            else:
                print("T{} applied write-lock on {}".format(transaction, item))
                lock_table[item]["holding"].append({"tid": transaction, "op": operation})
                lock_table[item]["status"] = "w"
                transaction_table[transaction]["items"].add(item)

        elif operation == "e":
            items = ",".join(transaction_table[transaction]["items"])
            print("T{} ended. Releasing locks on [{}]".format(transaction, items))
            for i, item in enumerate(items):
                lock_table[item]["holding"].pop()
                record = lock_table[item]["waiting"][0]

        else:
            print("Unknown operation. Ignoring instruction")


if len(sys.argv) < 3:
    print("Usage: python main.py <control-method> <input-file>"
          "\ncontrol-methods:\n1.wound-wait\n2.wait-die3.something-else")
    exit(1)

operations = []

with open(sys.argv[2], 'rt') as file:
    lines = file.readlines()
    for line in lines:
        operations.append(tokenize(line))
# pprint(operations)
wound_wait(operations)
