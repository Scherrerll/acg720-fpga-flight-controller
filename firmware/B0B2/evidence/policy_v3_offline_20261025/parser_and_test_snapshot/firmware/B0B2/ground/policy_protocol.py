"""Age-free B0B2 wire aliases. Reserved slots are never measured ages."""
import binascii
import struct

POLICY='no_pose_age_v3'
CORE_REMOVED=('pose_age_ticks','gate_last_interruption_pose_age_ticks','gate_last_revoke_pose_age_ticks')

def metadata(row,wire,canonical,removed=()):
    row=dict(row)
    for field in removed:
        if row.get(field)!=0:raise ValueError('Removed age slot must be reserved zero: '+field)
        row[field]=None
    row.update(_age_policy=POLICY,_canonical_protocol=canonical,wire_protocol=wire,
               unavailable_fields=list(removed),pose_age_available=False,
               pose_age_qualification_enabled=False)
    return row

def crc(packet,size,header):
    if len(packet)!=size or packet[:2]!=header:raise ValueError('Policy packet size/header')
    if binascii.crc_hqx(packet[2:-2],0xffff)!=int.from_bytes(packet[-2:],'big'):raise ValueError('Policy packet CRC')

def install_aliases(receiver,decode_info,decode_rotation):
    primary=receiver.protocols[b'\xa5\x79'][1]
    accel=receiver.protocols[b'\xa5\x7a'][1]
    def core(packet):
        if len(packet)!=224 or packet[:2]!=b'\xa5\x86':raise ValueError('A586 size/header')
        return metadata(primary(b'\xa5\x79'+packet[2:]),'a586','a579',CORE_REMOVED)
    def acceleration(packet):
        if len(packet)!=32 or packet[:2]!=b'\xa5\x87':raise ValueError('A587 size/header')
        return metadata(accel(b'\xa5\x7a'+packet[2:]),'a587','a57a',('pose_age_ticks',))
    def info(packet):
        crc(packet,40,b'\xa5\x88')
        if packet[4]!=5:raise ValueError('A588 profile version')
        # Reuse the unchanged v4 state-field parser only after authenticating
        # the actual v5 packet. This local byte adaptation is never transmitted.
        legacy=bytearray(b'\xa5\x80'+packet[2:]);legacy[4]=4
        legacy[-2:]=binascii.crc_hqx(legacy[2:-2],0xffff).to_bytes(2,'big')
        row=decode_info(bytes(legacy));row['version']=5
        if row['event_sensor_mask']&8:raise ValueError('Removed pose-age fault bit set')
        return metadata(row,'a588','a580',('event_pose_age_ticks',))
    def rotation(packet):
        crc(packet,48,b'\xa5\x89')
        if packet[4]!=2:raise ValueError('A589 profile version')
        legacy=bytearray(b'\xa5\x83'+packet[2:]);legacy[4]=1
        legacy[-2:]=binascii.crc_hqx(legacy[2:-2],0xffff).to_bytes(2,'big')
        row=decode_rotation(bytes(legacy));row['version']=2
        row['receipt_pair_valid']=row['pair_flags']==15
        row['receipt_pair_valid_basis']='explicit pose/module flags; no pose-age qualification'
        return metadata(row,'a589','a583',('pose_age_ticks',))
    receiver.protocols.update({b'\xa5\x86':(224,core),b'\xa5\x87':(32,acceleration),
                               b'\xa5\x88':(40,info),b'\xa5\x89':(48,rotation)})
    return receiver

def decode_mtf_v3(packet,legacy_decoder):
    crc(packet,128,b'\xa5\x81')
    if packet[4]!=3:return legacy_decoder(packet)
    legacy=bytearray(packet)
    # v3 bit0 means online<1s. The separate metric limit remains200ms.
    age=int.from_bytes(packet[18:22],'big')
    count=int.from_bytes(packet[14:18],'big')
    flags=packet[5]
    legacy[4]=2 if flags&0x20 else 1
    if bool(flags&1)!=bool(count and age<1000):raise ValueError('A581 v3 online indication')
    legacy[5]=(flags&~1)|int(bool(count and age<200))
    legacy[-2:]=binascii.crc_hqx(legacy[2:-2],0xffff).to_bytes(2,'big')
    row=legacy_decoder(bytes(legacy));row.update(version=3,mtf_flags=flags,
         module_online=bool(flags&1),module_offline_limit_ms=1000,
         metric_freshness_limit_ms=200,control_source_freshness_limit_ms=100)
    return row
