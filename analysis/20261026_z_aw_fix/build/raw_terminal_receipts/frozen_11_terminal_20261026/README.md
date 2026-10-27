# Frozen physical terminal receipts

This archive preserves original raw bytes for eleven closed physical attempts: nine route failures, one XML startup failure, and one full-route timing failure. Every attempt remains unqualified. A normal process return of 0 is not qualification.

The ten historical attempts are bound by the existing ATTEMPTS.json index. V4 P3R0 is bound by its owner's sealed p3r0_final FINAL_STATUS.json and MANIFEST.json; it completed routing at actual p.wait=0 but failed 20 ns timing (49.456 MHz, setup -0.220 ns, 32 setup-violated endpoints). The XML startup failure did not reach placement and its unrouted count is null.

| Attempt | Classification | Actual p.wait | Archived raw files |
|---|---|---:|---:|
| `first_p3r0` | `routefail` | 1 | 3 |
| `first_p2r0` | `routefail` | 1 | 3 |
| `first_p3r1` | `routefail` | 1 | 3 |
| `compact_v1_project01` | `xml_startupfail` | 1 | 2 |
| `compact_v1_p3r0` | `routefail` | 1 | 3 |
| `compact_v2_map2_p2r0` | `routefail` | 1 | 3 |
| `compact_v2_map1_p3r0` | `routefail` | 1 | 3 |
| `compact_v3_p3r0` | `routefail` | 1 | 3 |
| `compact_v3_p2r0_nt0` | `routefail` | 1 | 3 |
| `compact_v3_p1r2` | `routefail` | 1 | 3 |
| `compact_v4_p3r0` | `fullroute_timingfail` | 0 | 5 |

Each historical attempt includes its exact physical_exit.json and physical.log, plus gzip-compressed RPT text when present. The XML startup failure has no RPT. V4 P3R0 additionally includes its exact physical_audit.json and gzip-compressed raw TR. Compression uses Python gzip.compress(bytes, mtime=0); decompression reproduces the original bytes without text conversion. MANIFEST.json records original absolute and repository-relative paths, original and archived SHA-256 values, compression, byte counts, classification, and each verified hash binding. Every selected source was re-read after copying and again before sealing to verify its bytes and size/mtime were unchanged.

This is a compact evidence receipt archive, not a complete build fixture or a selected release. No FS, VG, PR, other binary, or whole out tree is included. In particular, V4 P3R0's timing-failing FS is excluded and must not be inferred to be an accepted image. No pending or later profile is included. Running jobs and toolfailed receipts were left untouched. No source, canonical index, earlier manifest, proof, old B0B3/R/H evidence, process, hardware, or serial state was changed.

Original absolute paths and hash-binding document paths describe this workstation at archive time and are not portable links. The archived relative paths remain usable after checkout, but some provenance documents and large omitted vendor artifacts remain outside this subtree and may be untracked; this archive alone cannot reproduce or fully re-audit a build. Historical receipt JSON may itself contain machine-specific paths. SHA-256 checks establish byte identity, not timing qualification, hardware validation, or acceptance for delivery.
