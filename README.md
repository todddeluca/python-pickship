

This is a python implementation of the Pick-and-Ship Programming Exercise from [OpenTempo](http://opentempo.com).  For the original Java implementation and more details, see [https://github.com/todddeluca/opentempo-pickship](https://github.com/todddeluca/opentempo-pickship).

In this implementation, I directly packed items into bins, instead of
manipulating sorted weight indexes.  This made for a much cleaner algorithm
while tying the implementation to the implementation of an item.  The Java
version packs a list of numbers, which I feel more closely relates to the
abstract notion of bin packing.

I also chose to make a LineItem have an item code and quantity, instead of
embedding the Item object itself in the LineItem.  I think I might prefer the
latter approach, which I used in the Java implementation.


## Usage

    python3 pickship.py data/pick-ship/inventory.txt  data/pick-ship/order3.txt


