# Tests Makefile
CC = gcc
CFLAGS = -O2 -Wall -Wextra -std=c11
LDFLAGS = -L../core -llrc -lrt

.PHONY: all clean test

all: test_numa_impl

test_numa_impl: test_numa_impl.c
	$(CC) $(CFLAGS) $< $(LDFLAGS) -o $@

test: test_numa_impl
	@echo "Running NUMA test..."
	./test_numa_impl
	@echo ""
	@echo "Running main test suite..."
	./test_lrc.sh
	@echo ""
	@echo "Running quick wins tests..."
	./test_quick_wins.sh

clean:
	rm -f test_numa_impl
