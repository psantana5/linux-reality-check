/*
 * Quick test to verify NUMA implementation
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern int numa_get_node_count(void);
extern int numa_is_available(void);
extern void* numa_alloc_on_node(size_t size, int node);
extern int numa_free(void *ptr, size_t size);
extern void numa_print_topology(void);

int main(void) {
    printf("=== NUMA Implementation Test ===\n\n");
    
    numa_print_topology();
    printf("\n");
    
    int node_count = numa_get_node_count();
    printf("Detected %d NUMA node(s)\n", node_count);
    
    if (!numa_is_available()) {
        printf("NUMA not available (single node system)\n");
        printf("Testing fallback to malloc...\n\n");
    } else {
        printf("NUMA is available\n\n");
    }
    
    // Test allocation on node 0
    size_t test_size = 1024 * 1024; // 1 MB
    printf("Allocating %zu bytes on node 0...\n", test_size);
    void *ptr0 = numa_alloc_on_node(test_size, 0);
    
    if (!ptr0) {
        printf("ERROR: Allocation failed\n");
        return 1;
    }
    printf("SUCCESS: Allocated at %p\n", ptr0);
    
    // Write to memory to ensure it's accessible
    memset(ptr0, 0xAA, test_size);
    printf("Memory is accessible (written 0xAA pattern)\n");
    
    // Test allocation on node 1 (if available)
    if (node_count >= 2) {
        printf("\nAllocating %zu bytes on node 1...\n", test_size);
        void *ptr1 = numa_alloc_on_node(test_size, 1);
        
        if (!ptr1) {
            printf("ERROR: Allocation failed\n");
            numa_free(ptr0, test_size);
            return 1;
        }
        printf("SUCCESS: Allocated at %p\n", ptr1);
        
        memset(ptr1, 0xBB, test_size);
        printf("Memory is accessible (written 0xBB pattern)\n");
        
        numa_free(ptr1, test_size);
        printf("Freed node 1 allocation\n");
    }
    
    // Clean up
    numa_free(ptr0, test_size);
    printf("\nFreed node 0 allocation\n");
    printf("\nAll tests passed!\n");
    
    return 0;
}
