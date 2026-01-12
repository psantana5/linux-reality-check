# Linux Reality Check - Top-level Makefile
# Unified build system for all components

.PHONY: all clean test install help core scenarios tests plots plots-advanced

# Default target
all: core scenarios

# Build core library
core:
	@echo "Building core library..."
	$(MAKE) -C core

# Build scenarios (experiments)
scenarios: core
	@echo "Building scenarios..."
	$(MAKE) -C scenarios

# Build and run tests
test: all
	@echo "Running tests..."
	$(MAKE) -C tests test

# Run individual test categories
test-unit: all
	@echo "Running unit tests..."
	$(MAKE) -C tests test_numa_impl
	cd tests && ./test_numa_impl

test-integration: all
	@echo "Running integration tests..."
	cd tests && ./test_lrc.sh

test-analysis: all
	@echo "Running analysis tool tests..."
	cd tests && ./test_quick_wins.sh

# Run quick test suite
quick: all
	@echo "Running quick test..."
	./lrc quick

# Generate plots from experiment data
plots:
	@echo "Generating plots from experiment data..."
	@if command -v python3 >/dev/null 2>&1; then \
		if python3 -c "import matplotlib" 2>/dev/null; then \
			python3 analyze/plot_all.py; \
		else \
			echo "⚠ matplotlib not installed. Install with:"; \
			echo "  sudo apt-get install python3-matplotlib python3-numpy"; \
			exit 1; \
		fi; \
	else \
		echo "⚠ Python 3 not found"; \
		exit 1; \
	fi

# Generate advanced statistical plots
plots-advanced:
	@echo "Generating advanced statistical plots..."
	@if command -v python3 >/dev/null 2>&1; then \
		if python3 -c "import matplotlib; import scipy" 2>/dev/null; then \
			python3 analyze/plot_advanced.py --all --compare; \
		else \
			echo "⚠ Required packages not installed. Install with:"; \
			echo "  sudo apt-get install python3-matplotlib python3-numpy python3-scipy"; \
			exit 1; \
		fi; \
	else \
		echo "⚠ Python 3 not found"; \
		exit 1; \
	fi

# Clean all build artifacts
clean:
	@echo "Cleaning build artifacts..."
	$(MAKE) -C core clean
	$(MAKE) -C scenarios clean
	$(MAKE) -C tests clean

# Install headers and library (optional)
install: core lrc.pc
	@echo "Installing to /usr/local..."
	@mkdir -p /usr/local/include/lrc
	@mkdir -p /usr/local/lib
	@mkdir -p /usr/local/lib/pkgconfig
	@cp core/*.h /usr/local/include/lrc/
	@cp core/liblrc.a /usr/local/lib/
	@cp lrc.pc /usr/local/lib/pkgconfig/
	@echo "Installation complete!"
	@echo "Use 'pkg-config --cflags --libs lrc' to get compile flags"

# Help message
help:
	@echo "Linux Reality Check - Build System"
	@echo ""
	@echo "Targets:"
	@echo "  all       - Build everything (default)"
	@echo "  core      - Build core library only"
	@echo "  scenarios - Build experiment scenarios"
	@echo "  test      - Run full test suite"
	@echo "  test-unit - Run unit tests only"
	@echo "  test-integration - Run integration tests"
	@echo "  test-analysis - Run analysis tool tests"
	@echo "  quick     - Run quick validation"
	@echo "  plots     - Generate basic plots from CSV data"
	@echo "  plots-advanced - Generate advanced statistical plots"
	@echo "  clean     - Remove all build artifacts"
	@echo "  install   - Install headers and library to /usr/local"
	@echo "  help      - Show this message"
	@echo ""
	@echo "Quick Start:"
	@echo "  make          # Build everything"
	@echo "  make test     # Run tests"
	@echo "  ./lrc quick   # Run quick experiments"
	@echo "  make plots    # Generate visualizations"
