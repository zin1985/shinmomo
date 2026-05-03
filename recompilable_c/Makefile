CC ?= gcc
CFLAGS ?= -std=c99 -Wall -Wextra -O2
INCLUDES = -Iinclude -Igenerated -Isrc
BUILD = build
OBJS = \
  $(BUILD)/main.o \
  $(BUILD)/vm_runtime.o \
  $(BUILD)/item_records.o \
  $(BUILD)/equipment_records.o \
  $(BUILD)/branch_records.o \
  $(BUILD)/macro_rows.o \
  $(BUILD)/vm_blob_catalog.o

all: $(BUILD)/shinmomo_decomp_demo

$(BUILD):
	mkdir -p $(BUILD)

$(BUILD)/%.o: src/%.c | $(BUILD)
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

$(BUILD)/%.o: generated/%.c | $(BUILD)
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

$(BUILD)/shinmomo_decomp_demo: $(OBJS)
	$(CC) $(CFLAGS) $(OBJS) -o $@

clean:
	rm -rf $(BUILD)

.PHONY: all clean
