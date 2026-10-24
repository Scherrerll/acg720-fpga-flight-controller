"""Current-source binding of independently reviewed actual INFO272 mapped proof."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def verify(vg,sources):
 binding=json.loads((ROOT/'hardware/info_mapped_binding.json').read_text());report_path=ROOT/'hardware/info_mapped_review.json'
 report=json.loads(report_path.read_text());assert binding['passed'] is True and report['passed'] is True
 assert binding['sources_sha256']==sources and binding['netlist_sha256']==sha(Path(vg))=='aa2de0222dc404ae2326da2d068fc079833296dece1b726f1af0b10f5bb9f941'
 assert binding['logical_bits_verified']==272 and binding['independent_review_accepted'] is True
 assert report['logical_info_bits']==272 and report['physical_upstream_ff']==225 and report['physical_own_flight_info_ff']==219 and report['physical_shared_core_ff']==6
 assert report['reference_local_snapshot_ff']==225 and report['candidate_local_snapshot_ff']==0
 assert report['candidate_vg_sha256']==binding['netlist_sha256'] and report['reference_vg_sha256']=='a27dca89aa11e49bab4a370e5617bcac73c62db3ce5a9a5a4c8961cf31d207d8'
 for key in ['upstream_ff_init_all_zero','upstream_pin_cones_boolean_equal','old_local_snapshot_init_zero','old_local_snapshot_ce_equals_sequence_capture_ce','logical_payload_after_capture_boolean_equal']:assert report[key] is True
 assert report['inactive_initial_packet_differing_logical_bits']==[]
 assert len(report['upstream_mapping'])==219 and len(report['shared_upstream_mapping'])==6
 assert len(report['upstream_mapping'])+len(report['shared_upstream_mapping'])==report['physical_upstream_ff']
 assert sha(Path(report['reference_vg']))==report['reference_vg_sha256'] and sha(Path(report['candidate_vg']))==report['candidate_vg_sha256']

 assert binding['report_sha256']==sha(report_path)==sha(Path(binding['original_report']))
 assert binding['evidence_sha256']
 for name,h in binding['evidence_sha256'].items():assert sha(Path(name))==h,('INFO mapped evidence changed',name)
 return binding
