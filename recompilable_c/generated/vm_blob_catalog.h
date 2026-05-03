#ifndef SHINMOMO_VM_BLOB_CATALOG_H
#define SHINMOMO_VM_BLOB_CATALOG_H
#include <stdint.h>
#include <stddef.h>
typedef struct {
    const char *name;
    uint32_t file_offset;
    uint8_t preview[16];
} ShinVmBlobPreview;
extern const ShinVmBlobPreview SHIN_VM_BLOB_PREVIEWS[];
extern const size_t SHIN_VM_BLOB_PREVIEW_COUNT;
#endif
