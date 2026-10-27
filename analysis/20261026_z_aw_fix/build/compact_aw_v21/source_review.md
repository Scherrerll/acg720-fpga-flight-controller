# v21: extension-only same-edge SP snapshot

The exact frozen v18 source55 is copied. Only one top region changes:
extension_q[887:0] becomes a WIDTH888 gw5_snapshot_bram instance with the exact
original enable !telemetry_snapshot_hold. Other assignments in the original
posedge block remain on that edge. There is no added reset, phase, clock,
latency, mask, gain, SDC/CST, build option or public interface change.

The unchanged wrapper selects28 SP BIT_WIDTH32 banks, READ_MODE0 bypass output,
WRITE_MODE01 write-through, all-byte AD000f, RESET0, zero default INIT. The
unmodified complete vendor functional model has independently passed WIDTH888
against initialized enabled FF semantics, including pre-clock0, same-edge,
hold, enable X/Z and payload X/Z. The Icarus default FF branch is not evidence
for hardware SP behavior: new integration and original-top13 runs explicitly
select GW5_USE_VENDOR_BRAM, add a fixture-only GSR root and inspect elaborated
SP count. Source/proof/vendor qualification are separate gates.

New actual-top integration may force only the extension source payload and
the serializer's transport-busy acknowledgment boundary. It must leave boot,
reset, snapshot hold, serializer state/ticks/index/cache and storage untouched.
Natural short/long-period scheduling, same-edge snapshot888, all public ports,
start/data/hold and complete protocol sequence/XOR/CRC are compared. This is
payload-boundary and byte-ack integration, not a physical UART/whole-flight
qualification. Original top13 stimulus is reused byte-for-byte; its existing
internal safety/RX forces remain explicitly part of that separate test scope.

Historical47-SP core/info/rotation experiments passed functional models but
failed routing. Extension was not moved in those trials. No timing benefit
is inferred; synthesis-only preparation must retain strict mapped SP CLK50
checks, and vendor execution waits for independent review.
