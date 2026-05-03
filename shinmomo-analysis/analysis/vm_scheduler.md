# VM scheduler

Cランタイムでは `$0799` 相当を `wait_or_ptr_hi` とし、VM対象objectでは wait counter として扱う。

```c
if (obj->wait_or_ptr_hi > 0) {
    obj->wait_or_ptr_hi--;
    return;
}
shinvm_step(...);
```

ただし実ROMでは同じslotが別object typeでは座標/速度/pointer部品になるため、type別解釈が必要。
