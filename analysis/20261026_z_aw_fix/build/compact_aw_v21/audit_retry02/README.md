# v21 audit-only retry preparation

Original vendor SYN returned0. Original audit and runner returned1; those
receipts and all original scripts/artifacts remain unchanged.

The actual VG wrapper input declaration is line350184. SP0 CE uses it at350212.
The actual parent instance at661773 connects it explicitly at661775 using a
legal escaped named port followed by its required terminating whitespace.
The protected Graph regex requires the port immediately followed by `(` and
therefore omitted this connection, leaving a false unconnected child-prefix
CE net. The actual DO escaped named port at661796 was omitted by the same rule.

The local adapter parses only this explicit wrapper instance and its complete
declaration/connection set. It checks escaped-name whitespace termination,
directions, exact widths, parent declarations/slice membership, duplicate or
missing ports, consistency with all old parsed ports and driver conflicts.
Only the two genuinely omitted escaped connections acquire explicit aliases:
one CE bit and888 DO bits. No suffix-based guessed renaming is allowed.

The read-only investigation confirms that after these explicit aliases all28
SP CE pins and627 core snapshot FF CE pins resolve to the same actual root
net. An exact BDD built from the actual LUT INIT values and39 shared actual
CLK50 FF-Q roots confirms the same Boolean function for every root assignment.
The structural same-net check remains mandatory and is not replaced by the BDD.

`run_audit_retry02.py`, when separately approved, reruns the original Python
mapped/clock/radio/gain/18-port audits into results_01, applies the local lexical
adapter, invokes the *unchanged original SP auditor* including its original
CE identity assertion, adds the actual-LUT Boolean evidence and recomputes the
resource comparison. It rehashes original source55/VG/artifacts before and after.
No synthesis, vendor process, PNR or hardware operation exists in the retry.
The hidden supervisor records the real retry child wait separately. Original
SYN0/audit1/root1 are never relabeled as successful original audit/root exits.

Completion has two real Python process boundaries: successful_audit_exit.json
records the audit child return to complete_audit_retry02.py; the outer hidden
supervisor writes completion_runner_exit.json for the completion coordinator's
actual return. completion_result.json names original_runner_actual_wait1,
original_audit_actual_wait1 and original_vendor_actual_wait0 separately from
successful_audit_wait0, completion_runner_actual_wait0 and
actual_completion_root_wait0. It carries exact original/new receipt and log
paths/hashes. completion_manifest.json binds the final result and all new
directory artifacts. No original SYNTHESIS_RESULT or original receipt is edited.

All original attempt/source/verification files and original metadata artifacts
(excluding prior compiler scratch and this new directory) are hash-bound and
checked unchanged before and after the retry. Both new completion phases write
only in this new directory.

Only the read-only investigation has run. `REVIEW_REQUIREMENTS.json` is not an
approval. Main and an independent reviewer must review the frozen preparation
and scripts, then main creates `REVIEW_APPROVAL.json` before the retry launcher
can run. The original source and all protected scripts are left intact.
