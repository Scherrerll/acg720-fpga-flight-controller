import unittest,argparse
from xy_pi_cli import gain,encode_request,decode_response,exchange,ResponseStream
class HostTests(unittest.TestCase):
 def test_gain_grid(self):
  for text,wire in [('0',0),('.05',500),('.1',1000),('1',10000),('.0001',1)]:self.assertEqual(gain(text),wire)
  for text in ['-.1','1.0001','.00001','nan','inf','abc']:
   with self.assertRaises(argparse.ArgumentTypeError):gain(text)
 def test_golden_request(self):
  # This request is accepted by the independent CRC implementation in RTL.
  self.assertEqual(encode_request(2,10,1500,1000).hex(),'a590010210000000000a05dc03e870c2')
 def test_timeout_never_retransmits(self):
  class Port:
   def __init__(self):self.writes=[]
   def write(self,b):self.writes.append(b)
   def flush(self):pass
  p=Port()
  with self.assertRaises(TimeoutError):exchange(p,ResponseStream(),2,4,500,0,timeout=0)
  self.assertEqual(p.writes,[encode_request(2,4,500,0)])
 def test_status_and_identity(self):
  p=bytes.fromhex('a591010218050000000a05dc03e8000000010000b0b3271b')
  row=decode_response(p);self.assertEqual(row['status_name'],'STALE_SEQUENCE');self.assertEqual(row['generation'],1)
  for n in range(len(p)):
   broken=bytearray(p);broken[n]^=1
   with self.assertRaises(ValueError):decode_response(broken)
if __name__=='__main__':unittest.main()
