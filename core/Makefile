CC = gcc
CFLAGS = -O2 -march=native -Wall -Wextra -Werror -std=c11
LDFLAGS = -lrt

# Header files
HEADERS = lrc.h numa_api.h workloads_api.h sched_api.h metrics.h perf_counters.h

OBJS = cpu_spin.o memory_stream.o memory_random.o sched_utils.o metrics.o perf_counters.o numa_utils.o lock_contention.o mixed_workload.o
LIB = liblrc.a

all: $(LIB)

$(LIB): $(OBJS)
	ar rcs $@ $^

# Compile with header dependencies
cpu_spin.o: cpu_spin.c workloads_api.h
	$(CC) $(CFLAGS) -c $<

memory_stream.o: memory_stream.c workloads_api.h
	$(CC) $(CFLAGS) -c $<

memory_random.o: memory_random.c workloads_api.h
	$(CC) $(CFLAGS) -c $<

perf_counters.o: perf_counters.c perf_counters.h
	$(CC) $(CFLAGS) -c $<

numa_utils.o: numa_utils.c numa_api.h
	$(CC) $(CFLAGS) -c $<

sched_utils.o: sched_utils.c sched_api.h
	$(CC) $(CFLAGS) -c $<

metrics.o: metrics.c metrics.h
	$(CC) $(CFLAGS) -c $<

lock_contention.o: lock_contention.c workloads_api.h
	$(CC) $(CFLAGS) -c $<

mixed_workload.o: mixed_workload.c workloads_api.h
	$(CC) $(CFLAGS) -c $<

clean:
	rm -f $(OBJS) $(LIB)

.PHONY: all clean
