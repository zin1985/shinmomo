#include <stdio.h>
#include "shinmomo_types.h"
#include "item_records.h"
#include "equipment_records.h"
#include "branch_records.h"
#include "macro_rows.h"
#include "vm_blob_catalog.h"
#include "vm_runtime.h"

int main(void) {
    printf("Shinmomo recompilable decomp scaffold\n");
    printf("item records:      %zu\n", SHIN_ITEM_RECORD_COUNT);
    printf("equipment records: %zu\n", SHIN_EQUIPMENT_RECORD_COUNT);
    printf("branch records:    %zu\n", SHIN_BRANCH_41A10_COUNT);
    printf("macro A rows:      %zu\n", SHIN_MACRO_A_COUNT);
    printf("macro B rows:      %zu\n", SHIN_MACRO_B_COUNT);
    printf("vm blob previews:  %zu\n", SHIN_VM_BLOB_PREVIEW_COUNT);

    if (SHIN_BRANCH_41A10_COUNT > 68) {
        const ShinBranch8Record *r = &SHIN_BRANCH_41A10_RECORDS[68];
        printf("branch[68]: key=%02X target=%06X rom=%06X\n", r->key, r->target_rom_offset, r->rom_offset);
    }

    ShinVmDecoder decoder;
    shinvm_decoder_init(&decoder);
    const unsigned char tiny_script[] = {0x07, 0x03, 0x00};
    ShinVmObject obj = {0};
    obj.active = 1;
    for (int i = 0; i < 5; i++) {
        shinvm_step(&obj, tiny_script, sizeof(tiny_script), &decoder);
        printf("vm frame %d: pc=%u state=%u wait=%u active=%u\n", i, obj.pc, obj.state, obj.wait_or_ptr_hi, obj.active);
    }

    return 0;
}
