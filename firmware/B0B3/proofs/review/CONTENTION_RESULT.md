# Shared arithmetic contention check

PASS. The real `mtf_xyz_hold_control` controller runs as client3 of the real `nav_math_service` with CLIENTS=4. Clients0–2 independently keep both multiply and divide services busy by issuing the next request as soon as their own busy deasserts. Their operands remain stable and legal through request, pending, grant, completion, and reissue. Every dummy result is checked; no dummy zero-divisor or protocol overflow is used to manufacture a controller error.

The exact same controller and inputs also run against CLIENTS=1. At public P=0.125/I=0.25, twelve completed XY callbacks (zero, signed velocity error, reversed error, return to zero) match the isolated controller exactly in both angle targets and both integral states. Twenty completed height callbacks match exactly in collective, delta, climb speed, and height target. Both axes accumulate nonzero I during the run. No controller blocked state, service error, or overlapping uncompleted callback occurs.

| Measurement | Clocks at 50 MHz | Time |
|---|---:|---:|
| Maximum XY accepted request → output publication, including queue/stick wait | 17,792 | 355.84 µs |
| Maximum XY work-pair capture → output publication | 13,737 | 274.74 µs |
| Maximum height accepted request → output publication | 12,554 | 251.08 µs |

Dummy clients0/1/2 complete 5812/5812/5811 multiplications and 2614/2614/2614 divisions, respectively. All numerical results match their independent integer constants. The run therefore exercises ongoing fair arbitration rather than a brief startup burst.

The clock is genuinely 50 MHz in the RTL simulation. Input arrivals are accelerated 10×: a nominal 1ms stick/acceleration tuple arrives every 5000 clocks (100µs), Z every 11 tuples, and XY every 20 tuples. Arithmetic dt values remain the original 1ms/11ms/20ms. Thus the fixture increases scheduling pressure while preserving the equations' dt contract; it does not claim a physical closed-loop flight replay or replace post-route timing analysis. The first height sample merely establishes the origin and is excluded from accepted Z calculation latency, matching the controller's actual tracking behavior.

Reproduce from the task root with `python -B review/verify_contention.py`. The script reads only the parent port-contract literal, current product sources and installed Icarus binaries; it writes only `review/contention/`. Evidence is in `review/contention/simulation.log`, `compile.log`, `contention_tb.v` and `results.json`. `results.json` binds all real arithmetic/controller source hashes plus the executed script, fixture, compile and simulation logs. No product source, existing main verification artifact, original log, hardware, serial port, receiver, or reference source was modified.
