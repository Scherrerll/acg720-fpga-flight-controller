# Failed copy99 PNR evidence: p2/r2/rep0

This directory records a completed, rejected physical attempt. Vendor exit code is 1 and the physical report records 176 unrouted nets. No timing report or FS bitstream was produced. It is not an accepted candidate or installation package.

All copied files retain their original bytes. `index.json` uses archive-relative file names and binds their SHA256 values. Original absolute paths inside raw receipts/reports are historical references only; no local out path is needed to inspect these archived files. The 53 logical source hashes are bound to the repository's frozen `firmware/B0B2/source` files; only the derived GPRJ, CST and PNR Tcl differ physically.

`donor_inputs.json`, `donor_synthesis_result.json` and `donor_synthesis.log` bind the completed synthesis-only donor and copied VG identity. The donor runner is identical to `build_runner.py`. Large VG, DB, protected post-place, HTML duplicates and other large/generated products are deliberately excluded; omitted artifacts remain hash references, not included evidence. Therefore this archive alone cannot re-run or independently re-hash the omitted VG/DB.

The archived runner is retained as provenance and was not executed during archiving. No vendor process, new build, GUI, programmer, serial port or hardware operation was started. The B0B0 release and B0B2 source/helpers were unchanged.
