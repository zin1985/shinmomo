#ifndef SHINMOMO_TYPES_H
#define SHINMOMO_TYPES_H

#include <stdint.h>
#include <stddef.h>

typedef struct {
    uint16_t w0;
    uint16_t w1;
    uint16_t w2;
    uint16_t w3;
    uint8_t  b8;
    uint8_t  b9;
    uint8_t  b10;
    uint32_t rom_offset;
} ShinItemRecord;

typedef struct {
    uint16_t w0;
    uint16_t w1;
    uint16_t w2;
    uint16_t w3;
    uint8_t  b8;
    uint8_t  b9;
    uint8_t  b10;
    uint8_t  b11;
    uint8_t  b12;
    uint8_t  b13;
    uint8_t  equip_slot;
    uint8_t  power_delta;
    uint32_t rom_offset;
} ShinEquipmentRecord;

typedef struct {
    uint8_t key;
    uint8_t c1;
    uint8_t c2;
    uint8_t c3;
    uint8_t c4;
    uint8_t c5;
    uint16_t target;
    uint32_t target_rom_offset;
    uint32_t rom_offset;
} ShinBranch8Record;

typedef struct {
    uint8_t op0;
    uint8_t p1;
    uint8_t p2;
    uint8_t p3;
    uint8_t p4;
    uint8_t p5;
    uint8_t p6;
    uint16_t label_word;
    uint32_t label_rom_offset;
    uint32_t rom_offset;
} ShinMacro9Row;

typedef enum {
    SHINVM_BEHAVIOR_UNKNOWN = 0,
    SHINVM_BEHAVIOR_IDLE,
    SHINVM_BEHAVIOR_MOVE,
    SHINVM_BEHAVIOR_TURN,
    SHINVM_BEHAVIOR_WAIT,
    SHINVM_BEHAVIOR_TALK,
    SHINVM_BEHAVIOR_EVENT,
    SHINVM_BEHAVIOR_STATE_CHANGE,
    SHINVM_BEHAVIOR_BRANCH
} ShinVmBehavior;

typedef struct {
    uint8_t state;          /* $0619 equivalent in the working model */
    uint8_t x_or_work;      /* $0719 equivalent */
    uint8_t y_or_ptr_lo;    /* $0759 equivalent */
    uint8_t wait_or_ptr_hi; /* $0799 equivalent */
    uint16_t pc;
    uint16_t script_base;
    uint8_t active;
} ShinVmObject;

#endif
