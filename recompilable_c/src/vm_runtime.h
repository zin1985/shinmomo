#ifndef SHINMOMO_VM_RUNTIME_H
#define SHINMOMO_VM_RUNTIME_H

#include "shinmomo_types.h"

typedef struct {
    ShinVmBehavior opcode_behavior[256];
} ShinVmDecoder;

void shinvm_decoder_init(ShinVmDecoder *decoder);
int shinvm_step(ShinVmObject *obj, const uint8_t *script, size_t script_len, const ShinVmDecoder *decoder);
const char *shinvm_behavior_name(ShinVmBehavior b);

#endif
