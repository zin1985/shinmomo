#include "vm_runtime.h"

void shinvm_decoder_init(ShinVmDecoder *decoder) {
    for (int i = 0; i < 256; i++) {
        decoder->opcode_behavior[i] = SHINVM_BEHAVIOR_UNKNOWN;
    }

    /* Working hypotheses. Update after Table A / command_table are verified. */
    decoder->opcode_behavior[0x00] = SHINVM_BEHAVIOR_IDLE;
    decoder->opcode_behavior[0x07] = SHINVM_BEHAVIOR_EVENT;
    decoder->opcode_behavior[0x80] = SHINVM_BEHAVIOR_BRANCH;
    decoder->opcode_behavior[0xFF] = SHINVM_BEHAVIOR_BRANCH;
}

const char *shinvm_behavior_name(ShinVmBehavior b) {
    switch (b) {
    case SHINVM_BEHAVIOR_IDLE: return "IDLE";
    case SHINVM_BEHAVIOR_MOVE: return "MOVE";
    case SHINVM_BEHAVIOR_TURN: return "TURN";
    case SHINVM_BEHAVIOR_WAIT: return "WAIT";
    case SHINVM_BEHAVIOR_TALK: return "TALK";
    case SHINVM_BEHAVIOR_EVENT: return "EVENT";
    case SHINVM_BEHAVIOR_STATE_CHANGE: return "STATE_CHANGE";
    case SHINVM_BEHAVIOR_BRANCH: return "BRANCH";
    default: return "UNKNOWN";
    }
}

int shinvm_step(ShinVmObject *obj, const uint8_t *script, size_t script_len, const ShinVmDecoder *decoder) {
    if (!obj || !script || !decoder || !obj->active) {
        return 0;
    }

    if (obj->wait_or_ptr_hi > 0) {
        obj->wait_or_ptr_hi--;
        return 1;
    }

    if (obj->pc >= script_len) {
        obj->active = 0;
        return 0;
    }

    uint8_t opcode = script[obj->pc++];
    ShinVmBehavior behavior = decoder->opcode_behavior[opcode];

    switch (behavior) {
    case SHINVM_BEHAVIOR_IDLE:
        obj->wait_or_ptr_hi = 1;
        break;
    case SHINVM_BEHAVIOR_EVENT:
        /*
         * Placeholder for opcode 0x07 style dispatch.
         * The real command mapping is unresolved, so this only models the
         * scheduler side: command execution sets a short wait.
         */
        if (obj->pc < script_len) {
            uint8_t param = script[obj->pc++];
            obj->state = param;
        }
        obj->wait_or_ptr_hi = 2;
        break;
    case SHINVM_BEHAVIOR_BRANCH:
        /*
         * Conservative branch model: consume one byte offset if present.
         * This keeps the host executable deterministic without pretending
         * opcode semantics are fully known.
         */
        if (obj->pc < script_len) {
            uint8_t off = script[obj->pc++];
            if (off < script_len) obj->pc = off;
        }
        obj->wait_or_ptr_hi = 1;
        break;
    default:
        obj->wait_or_ptr_hi = 1;
        break;
    }
    return 1;
}
