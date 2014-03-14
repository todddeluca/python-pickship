#!/usr/bin/env python3


import argparse
import collections
import re
import sys


class Item:
    def __init__(self, code, name, weight):
        self.code = code
        self.name = name
        self.weight = weight

    def __repr__(self):
        return "Item(%r, %r, %r)" % (self.code, self.name, self.weight)


class LineItem:
    def __init__(self, code, qty):
        '''
        code: str.  an Item code
        qty: int.  the quantity of items.
        '''
        self.code = code
        self.qty = qty

    def __repr__(self):
        return 'LineItem(%r, %r)' % (self.code, self.qty)


class Order:
    def __init__(self, number, customer_code, line_items):
        self.number = number
        self.customer_code = customer_code
        self.line_items = line_items

    def __repr__(self):
        return 'Order(%r, %r, %r)' % (self.number, self.customer_code,
                                      self.line_items)

class Box:
    def __init__(self, number, line_items, inventory):
        self.number = number
        self.line_items = line_items
        self.weight = 0
        for li in line_items:
            self.weight += inventory[li.code].weight * li.qty

    def __repr__(self):
        return 'Box: %r, %r' % (self.number, self.line_items)


class PickShip:
    def __init__(self, order_number, boxes):
        self.order_number = order_number
        self.boxes = boxes
        self.weight = sum(box.weight for box in boxes)
    
    def __repr__(self):
        return 'PickShip(%r, %r)' % (self.order_number, self.boxes)


def read_inventory(filename):
    '''
    Parse an inventory file.
    Return a dict mapping item code to an Item.
    '''
    inventory = {}
    # states
    START, INVENTORY, ITEM, CODE, NAME, WEIGHT, END = range(1, 8)
    state = START
    with open(filename) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue # skip blank lines

            if state == START:
                if line == 'INVENTORY START':
                    state = INVENTORY
                else:
                    raise Exception("Missing INVENTORY START line.")
            elif state == INVENTORY:
                if line == 'INVENTORY END':
                    state = END
                elif line == 'ITEM START':
                    state = ITEM
                else:
                    raise Exception("Missing ITEM START or INVENTORY END line.")
            elif state == ITEM:
                if line.startswith('CODE: '):
                    state = CODE
                    code = line.split(None, 1)[1]
                else:
                    raise Exception("Missing CODE line.")
            elif state == CODE:
                if line.startswith('NAME: '):
                    state = NAME
                    name = line.split(None, 1)[1]
                else:
                    raise Exception("Missing NAME line.")
            elif state == NAME:
                if line.startswith('WEIGHT: '):
                    state = WEIGHT
                    weight = float(line.split(None, 1)[1])
                else:
                    raise Exception("Missing WEIGHT line.")
            elif state == WEIGHT:
                if line == 'ITEM END':
                    state = INVENTORY
                    inventory[code] = Item(code, name, weight)
                else:
                    raise Exception("Missing ITEM END line.")
            elif state == END:
                raise Exception("Found a line after INVENTORY END line.")
            else:
                raise Exception("Unrecognized parsing state.")

    return inventory


def read_order(filename):

    START, ORDER, NUMBER, CODE, ITEM, END = range(1, 7)
    state = START
    line_items = []
    lineitem_regex = re.compile(r'^ITEM:\s+(.+?),\s+(.+)$')

    with open(filename) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue # skip blank lines

            if state == START:
                if line == 'ORDER START':
                    state = ORDER
                else:
                    raise Exception("Missing ORDER START line.")
            elif state == ORDER:
                if line.startswith('ORDER NUMBER: '):
                    state = CODE
                    number = int(line.split(': ', 1)[1])
                else:
                    raise Exception("Missing ORDER NUMBER line.")
            elif state == CODE:
                if line.startswith('CUSTOMER CODE: '):
                    state = ITEM
                    customer_code = line.split(': ', 1)[1]
                else:
                    raise Exception("Missing CUSTOMER CODE line.")
            elif state == ITEM:
                if line.startswith('ITEM: '):
                    # Stay in ITEM state.
                    match = lineitem_regex.search(line)
                    item_code = match.group(1)
                    qty = int(match.group(2))
                    line_items.append(LineItem(item_code, qty))
                elif line == 'ORDER END':
                    state = END
                else:
                    raise Exception("Expected ITEM or ORDER END line.")
            elif state == END:
                raise Exception("Found a line after ORDER END line.")
            else:
                raise Exception("Unrecognized parsing state.")

    return Order(number, customer_code, line_items)


class Bin:
    '''
    A bin contains items and a sum of their weights.
    This class is used by the bin packing algorithm.
    '''
    def __init__(self):
        self.items = []
        self.weight = 0

    def add(self, item):
        self.items.append(item)
        self.weight += item.weight

    def __repr__(self):
        return 'Bin: %r, %r' % (self.weight, self.items)


def first_fit_descending_pack(items, capacity):
    sorted_items = sorted(items, key=lambda i: i.weight, reverse=True)
    print('sorted items:', sorted_items)
    bins = []

    for item in sorted_items:
        if item.weight > capacity:
            raise Exception("Error: Item size greater than bin capacity.")

        # find first bin (if any) that can fit item
        the_bin = None
        for bin_ in bins:
            if item.weight <= capacity - bin_.weight:
                the_bin = bin_
                break

        # create a new bin if item fits in no current bin
        if the_bin is None:
            the_bin = Bin()
            bins.append(the_bin)

        # assign item to the bin
        the_bin.add(item)

    return bins


def make_pickship(order, inventory, capacity):
    # Unroll order into a list of items
    items = []
    for li in order.line_items:
        item = inventory[li.code]
        for i in range(li.qty):
            items.append(item)

    # pack items into bins
    bins = first_fit_descending_pack(items, capacity)
    
    # reroll binned items into a pick ship
    boxes = []
    for i, bin_ in enumerate(bins):
        c = collections.Counter(item.code for item in bin_.items)
        line_items = [LineItem(code, qty) for code, qty in c.items()]
        boxes.append(Box(i, line_items, inventory))

    return PickShip(order.number, boxes)


def write_pickship(pickship, handle=sys.stdout):
    handle.write("PICK SHIP START\n")
    handle.write("ORDER NUMBER: %s\n" % pickship.order_number)
    handle.write("TOTAL SHIP WEIGHT: %s\n" % pickship.weight)
    for box in pickship.boxes:
        handle.write('BOXSTART: %s\n' % (box.number + 1))
        handle.write('SHIP WEIGHT: %s\n' % box.weight)
        for li in box.line_items:
            handle.write('ITEM: %s, %s\n' % (li.code, li.qty))
        handle.write('BOX END\n')
    handle.write("PICK SHIP END\n")


def main():

    parser = argparse.ArgumentParser(description='Create a pick-and-ship list for a given order and inventory.')
    parser.add_argument('inventory', help='A pickship-format inventory text file')
    parser.add_argument('order', help='A pickship-format order text file.')
    parser.add_argument('--capacity', type=int, default=10,
                        help='The maximum weight capacity of each box.')
    args = parser.parse_args()

    print('Box capacity:', args.capacity)
    # read inventory
    print('Parsing inventory:', args.inventory)
    inventory = read_inventory(args.inventory)
    print(inventory)
    # read order
    print('Parsing order:', args.order)
    order = read_order(args.order)
    print(order)
    # make pickship
    print('Making pick-and-ship list.')
    pickship = make_pickship(order, inventory, args.capacity)
    print(pickship)
    # write pickship
    print('Writing pick-and-ship list.')
    write_pickship(pickship)



if __name__ == '__main__':
    main()
