# Host tests: make -C test/host
CXX ?= g++
CXXFLAGS ?= -std=c++17 -O1 -g -Wall -Wextra -Werror -fsanitize=address,undefined
CORE := ../../lib/relay6_core
SRC := test_main.cpp $(wildcard $(CORE)/*.cpp)
run: relay6_tests
	./relay6_tests
relay6_tests: $(SRC) $(wildcard $(CORE)/*.h)
	$(CXX) $(CXXFLAGS) -I$(CORE) $(SRC) -o $@
clean:
	rm -f relay6_tests
.PHONY: run clean
