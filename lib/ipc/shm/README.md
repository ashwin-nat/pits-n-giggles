
# PNG Shared Memory IPC

High-performance **single-writer → multi-reader shared memory IPC** for real-time telemetry, HUDs, and overlays.

Design goals:

- Zero-copy memory transport
- Lock-free atomic publishing
- CRC-protected frames
- Crash-safe restart & reattach
- Latest-state broadcast (not a queue)
- Slow readers never block the writer
- Broadcast IPC

---

# Layer Model

```

+------------------------------------------------+
| PRESENTATION LAYER (L2)                        |
| ---------------------------------------------- |
| - Topic-based JSON batching                    |
| - JSON serialization / deserialization         |
| - Handler dispatch per topic                   |
| +--------------------------------------------+ |

                │
                ▼

+------------------------------------------------+
|        TRANSPORT LAYER - SHARED MEMORY         |
|                                                |
| (L1)                                           |
| ---------------------------------------------- |
| - Atomic double buffering                      |
| - CRC32 integrity protection                   |
| - Latest-frame-wins semantics                  |
| - Crash-safe reattach                          |
| +--------------------------------------------+ |

```

The presentation layer never touches shared memory directly.
It only sees `bytes`.
The transport layer never understands JSON or topics.

---

# Supported Topology


```
     Writer (only one allowed)
             │
             ▼
    +-------------------+
    |   SHARED MEMORY   |
    |   Double Buffer   |
    +-------------------+
       ▲        ▲
       │        │
    Reader 1  Reader N
```

Single writer
Unlimited readers
Readers may be slow
Frames may be skipped

---

# Transport Layer (L1)

## Atomic Memory Layout

```

|==================== SHARED MEMORY ====================|
+-------------------------------------------------------+
|                GLOBAL HEADER                          |
+----------------------+--------------------------------+
| uint64 seq           | uint8 active_index (0 or 1)    |
+----------------------+--------------------------------+

+-------------------------------------------------------+
|                    BUFFER 0                           |
+----------------------+--------------------------------+
| uint32 size          | uint32 crc32                   |
+----------------------+--------------------------------+
| payload bytes... (max 512 KB)                         |
+-------------------------------------------------------+

+-------------------------------------------------------+
|                    BUFFER 1                           |
+----------------------+--------------------------------+
| uint32 size          | uint32 crc32                   |
+----------------------+--------------------------------+
| payload bytes... (max 512 KB)                         |
+-------------------------------------------------------+

```

### Publish Algorithm (Writer)

```

1. seq += 1
2. active_index = seq & 1
3. Write → [size][crc][payload] into inactive buffer
4. Commit → write [seq][active_index] into global header

```

This guarantees:
- No torn reads
- No locks
- Atomic visibility

---

### Read Algorithm (Reader)

```

1. Read [seq][active_index]
2. If seq == last_seq → skip
3. Read [size][crc][payload] from active buffer
4. Validate CRC
5. If OK → deliver
6. last_seq = seq

```

If CRC fails, frame is dropped

### Crash & Restart Behavior

| Event | Result |
|--------|--------|
| Writer crashes | Readers detach & wait |
| Writer restarts | Readers auto-reattach |
| Corrupt frame | Dropped |
| Reader crashes | Writer unaffected |

---

# Presentation Layer (L2)

The presentation layer batches **topic-keyed JSON payloads** into a single frame.

### Write Flow

```

writer.add("speed", {...})
writer.add("gear", {...})
await writer.write()

```

Internally:

```

{ "speed": {...}, "gear": {...} }
│
▼
compact JSON → bytes → transport.write()

```

---

### Read Flow

```

@reader.on("speed")
def on_speed(data): ...

@reader.on("gear")
def on_gear(data): ...

reader.read()

```

Internally:

```

transport → bytes → JSON → dispatch per topic

```

---

# Memory Size

Default buffer size:

```

512 KB per buffer × 2 buffers ≈ ~1 MB total

```

---
