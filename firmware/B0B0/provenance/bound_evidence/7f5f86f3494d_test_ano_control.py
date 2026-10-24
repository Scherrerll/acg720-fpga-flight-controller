import binascii,struct,unittest
from nav_protocol import FORMAT_V3,decode_nav,display_values,identity_matches
from protocol import decode_info

def framed(header,body):
 p=header+b'\0\x01'+body
 return p+binascii.crc_hqx(p[2:],0xffff).to_bytes(2,'big')
def nav(shadow,roll=0,collective=0,target=0,flags=0xbf):
 body=struct.pack(FORMAT_V3,5,flags,1,0,1234,1,10,10000,1<<19,
  234,0,0,0,0,0,0,234,0,0,0,roll,0,0,shadow,0,0,collective,0,target)
 return framed(b'\xa5\x82',body)
class ANOControlTests(unittest.TestCase):
 def test_altitude_continues_without_xy(self):
  row=decode_nav(nav(0x15,collective=1400,target=600))
  self.assertTrue(row['vertical_active']);self.assertFalse(row['xyz_requested']);self.assertFalse(row['xyz_active'])
  self.assertEqual(display_values(row)['nav_target_height_mm'],600)
  self.assertTrue(identity_matches({'build_id':0xb0ae},row))
  self.assertFalse(identity_matches({'build_id':0xb0ad},row))
 def test_mode_selected_before_armed(self):
  r=decode_nav(nav(0x0f));self.assertTrue(r['xyz_requested']);self.assertTrue(r['xyz_ready']);self.assertFalse(r['xyz_active'])
 def test_joint_run(self):
  r=decode_nav(nav(0x3f,roll=-123,collective=1400,target=600));self.assertTrue(r['xyz_active']);self.assertTrue(r['ano_control'])
 def test_position_display_is_not_control_authority(self):
  r=decode_nav(nav(0x3f,roll=-123,collective=1400,target=600,flags=0x9f))
  self.assertFalse(r['position_accumulator_ready']);self.assertTrue(r['xyz_active'])
  self.assertEqual(display_values(r)['nav_shadow_roll_deg'],-1.23)
 def test_bad_state_rejected(self):
  for packet in [nav(0x2f,roll=3),nav(0x14,collective=1400,target=600),nav(0x0f,collective=1400),nav(0x0f,roll=20)]:
   with self.assertRaises(ValueError):decode_nav(packet)
 def test_flight_state_v3(self):
  packet=b'\xa5\x80'+struct.pack('>HBBIQHQBBBBIBB',1,3,15,0xb0ae,123,0,0,0,0,0,0,0,0,4)
  packet+=binascii.crc_hqx(packet[2:],0xffff).to_bytes(2,'big')
  r=decode_info(packet)
  self.assertTrue(r['taking_off']);self.assertTrue(r['motor_prepared']);self.assertTrue(r['flying']);self.assertTrue(r['auto_takeoff'])
  self.assertFalse(r['throttle_takeover_active']);self.assertEqual(r['sticky_yaw_fault'],4)
if __name__=='__main__':unittest.main()
