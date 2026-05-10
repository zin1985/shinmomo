# Runtime bridge CSV semantics

## Primary CSVs

### g13_mask_minimal.csv

Purpose:

```text
execution-frame exact branch-window isolation
```

Fields:

```text
execution_frame,cutoff_index,rank,termination_flag,note
```

### g13_cutoff.csv

Purpose:

```text
visible/skip partition and cutoff boundary preservation
```

Fields:

```text
frame,execution_frame,cutoff_index,visible_count,append_count_proxy,skip_start_rank
```

### g13_contrib.csv

Purpose:

```text
contribution estimate and cumulative S(i) reconstruction
```

Fields:

```text
frame,rank,cluster_track_id,contribution_est,S_i,cutoff_slope,note
```

### g13_pretrigger.csv

Purpose:

```text
threshold buildup / plateau / decay observation
```

Fields:

```text
frame,execution_frame,density_acceleration,accumulated_acceleration,pretrigger_state,note
```

## Supporting CSVs

```text
frame.csv
visible.csv
cluster_track.csv
oam_attr.csv
dma.csv
chr_atlas.csv
tilemap_world.csv
metatile.csv
```

## Compression rule

Raw runtime dumps are not included. Keep summaries only.

