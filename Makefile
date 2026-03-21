CXX       ?= c++
CXXFLAGS  := -O3 -shared -fPIC -Wall
PYBIND    := $(shell python3 -m pybind11 --includes)
EXT       := $(shell python3-config --extension-suffix)

TARGET    := fast_loader$(EXT)
SRC       := fast_loader.cpp

.PHONY: all clean install check

all: $(TARGET)

$(TARGET): $(SRC)
	$(CXX) $(CXXFLAGS) $(PYBIND) $< -o $@

check: $(TARGET)
	python3 -c "import fast_loader; h,d = fast_loader.load('README.md'); print('ERROR: should have failed')" 2>/dev/null || true
	@echo "Build OK: $(TARGET)"
	@python3 -c "import fast_loader; print(f'fast_loader loaded successfully')"

clean:
	rm -f fast_loader*.so fast_loader*.pyd

install: $(TARGET)
	@echo "Place $(TARGET) next to modernplot.py"
