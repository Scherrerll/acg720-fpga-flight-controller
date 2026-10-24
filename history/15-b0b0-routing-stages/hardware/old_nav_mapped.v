module mtf_xyz_navigation_control (
  clk50_d,
  n13_16,
  observer_reset,
  n16969_6,
  acceleration_update,
  \staged_telemetry.core_q_453_16 ,
  source_loc_selected,
  n316_14,
  flight_state_flags_0_2,
  ready,
  converted_acc_valid,
  n774_8,
  link_fresh_7,
  mtf_range_ok,
  extension_113_5,
  core_body_860_6,
  core_body_860_8,
  stick_4_14,
  stick_4_16,
  body_yaw_range_ok,
  z_handoff_active,
  core_body_856_3,
  core_body_856_9,
  previous_pose_valid,
  pose_valid,
  n13_13,
  n13_14,
  n3216_8,
  saturated_Z,
  mtf_integrated,
  flow_ok,
  mtf_sample,
  n3649_6,
  n3649_7,
  n3648_6,
  n3648_12,
  pitch_Z_6_13,
  pitch_Z_2_13,
  link_fresh,
  sample_valid_Z,
  mtf_range_ok_3,
  core_body_784,
  core_body_785,
  core_body_786,
  core_body_787,
  core_body_788,
  core_body_789,
  core_body_790,
  core_body_791,
  core_body_792,
  core_body_793,
  core_body_794,
  core_body_795,
  core_body_800,
  core_body_801,
  core_body_802,
  core_body_803,
  core_body_804,
  core_body_805,
  core_body_806,
  core_body_807,
  core_body_808,
  core_body_809,
  core_body_810,
  core_body_811,
  core_body_816,
  core_body_817,
  core_body_818,
  core_body_819,
  core_body_820,
  core_body_821,
  core_body_822,
  core_body_823,
  core_body_824,
  core_body_825,
  core_body_826,
  core_body_827,
  core_body_856,
  converted_ax,
  converted_ay,
  body_yaw,
  sensor_yaw,
  channels,
  ch7_Z,
  converted_dt_us,
  base_throttle_us_Z_0,
  base_throttle_us_Z_1,
  base_throttle_us_Z_2,
  base_throttle_us_Z_3,
  base_throttle_us_Z_4,
  base_throttle_us_Z_5,
  base_throttle_us_Z_6,
  base_throttle_us_Z_7,
  base_throttle_us_Z_8,
  base_throttle_us_Z_9,
  base_throttle_us_Z_10,
  base_throttle_us_Z_11,
  base_throttle_us_Z_15,
  uptime_ms,
  mtf_age_ms,
  sensor_failure_mask,
  time_adapter_fault,
  converted_az,
  entry_stick,
  handoff_collective_3,
  handoff_collective_4,
  handoff_collective_11,
  fresh_ticks,
  pitch_Z,
  sensor_pitch_0,
  sensor_pitch_2,
  sensor_pitch_3,
  sensor_pitch_4,
  sensor_pitch_5,
  sensor_pitch_6,
  sensor_pitch_7,
  sensor_pitch_8,
  sensor_pitch_9,
  sensor_pitch_10,
  sensor_pitch_11,
  sensor_pitch_12,
  mtf_distance_mm,
  mtf_vy_x100_0,
  mtf_vy_x100_1,
  mtf_vy_x100_2,
  mtf_vy_x100_3,
  mtf_vy_x100_4,
  mtf_vy_x100_5,
  mtf_vy_x100_6,
  mtf_vy_x100_7,
  mtf_vy_x100_8,
  mtf_vy_x100_9,
  mtf_vy_x100_10,
  mtf_vy_x100_11,
  mtf_vy_x100_12,
  mtf_vy_x100_13,
  mtf_vy_x100_14,
  mtf_vy_x100_15,
  mtf_vy_x100_16,
  mtf_vy_x100_17,
  mtf_vy_x100_18,
  mtf_vy_x100_19,
  mtf_vy_x100_20,
  mtf_vy_x100_21,
  mtf_vy_x100_22,
  mtf_vy_x100_23,
  mtf_vy_x100_24,
  mtf_vy_x100_25,
  mtf_vy_x100_26,
  mtf_vy_x100_27,
  mtf_vy_x100_28,
  mtf_vy_x100_29,
  mtf_vy_x100_31,
  mtf_vx_x100_0,
  mtf_vx_x100_1,
  mtf_vx_x100_2,
  mtf_vx_x100_3,
  mtf_vx_x100_4,
  mtf_vx_x100_5,
  mtf_vx_x100_6,
  mtf_vx_x100_7,
  mtf_vx_x100_8,
  mtf_vx_x100_9,
  mtf_vx_x100_10,
  mtf_vx_x100_11,
  mtf_vx_x100_12,
  mtf_vx_x100_13,
  mtf_vx_x100_14,
  mtf_vx_x100_15,
  mtf_vx_x100_16,
  mtf_vx_x100_17,
  mtf_vx_x100_18,
  mtf_vx_x100_19,
  mtf_vx_x100_20,
  mtf_vx_x100_21,
  mtf_vx_x100_22,
  mtf_vx_x100_23,
  mtf_vx_x100_24,
  mtf_vx_x100_25,
  mtf_vx_x100_26,
  mtf_vx_x100_27,
  mtf_vx_x100_28,
  mtf_vx_x100_29,
  mtf_vx_x100_31,
  mtf_dt_ms,
  roll,
  flight_state_flags,
  nav_vertical_ready,
  nav_xy_active,
  nav_vertical_ready_3,
  nav_vertical_ready_4,
  nav_xy_ready,
  nav_z_active,
  nav_xy_reason_0_7,
  nav_vertical_ready_47,
  geometry_reason_1_7,
  geometry_reason_1_8,
  n164_9,
  pilot_norm_update,
  seen,
  xy_stick_fault,
  navigation_body_0,
  navigation_body_1,
  navigation_body_2,
  navigation_body_3,
  navigation_body_4,
  navigation_body_5,
  navigation_body_6,
  navigation_body_7,
  navigation_body_8,
  navigation_body_9,
  navigation_body_10,
  navigation_body_11,
  navigation_body_12,
  navigation_body_13,
  navigation_body_14,
  navigation_body_31,
  navigation_body_32,
  navigation_body_33,
  navigation_body_35,
  navigation_body_38,
  navigation_body_39,
  navigation_body_40,
  navigation_body_41,
  navigation_body_42,
  navigation_body_48,
  navigation_body_49,
  navigation_body_50,
  navigation_body_51,
  navigation_body_52,
  navigation_body_53,
  navigation_body_54,
  navigation_body_55,
  navigation_body_56,
  navigation_body_57,
  navigation_body_58,
  navigation_body_59,
  navigation_body_63,
  navigation_body_80,
  navigation_body_81,
  navigation_body_82,
  navigation_body_83,
  navigation_body_84,
  navigation_body_85,
  navigation_body_86,
  navigation_body_87,
  navigation_body_88,
  navigation_body_89,
  navigation_body_91,
  navigation_body_92,
  navigation_body_93,
  navigation_body_94,
  navigation_body_95,
  navigation_body_96,
  navigation_body_97,
  navigation_body_98,
  navigation_body_99,
  navigation_body_100,
  navigation_body_101,
  navigation_body_102,
  navigation_body_103,
  navigation_body_104,
  navigation_body_105,
  navigation_body_106,
  navigation_body_107,
  navigation_body_108,
  navigation_body_109,
  navigation_body_110,
  navigation_body_111,
  navigation_body_144,
  navigation_body_145,
  navigation_body_146,
  navigation_body_147,
  navigation_body_148,
  navigation_body_149,
  navigation_body_150,
  navigation_body_151,
  navigation_body_152,
  navigation_body_153,
  navigation_body_154,
  navigation_body_155,
  navigation_body_156,
  navigation_body_157,
  navigation_body_158,
  navigation_body_159,
  navigation_body_160,
  navigation_body_161,
  navigation_body_162,
  navigation_body_163,
  navigation_body_164,
  navigation_body_165,
  navigation_body_166,
  navigation_body_167,
  navigation_body_168,
  navigation_body_169,
  navigation_body_170,
  navigation_body_171,
  navigation_body_172,
  navigation_body_175,
  navigation_body_176,
  navigation_body_177,
  navigation_body_178,
  navigation_body_179,
  navigation_body_180,
  navigation_body_181,
  navigation_body_182,
  navigation_body_183,
  navigation_body_184,
  navigation_body_185,
  navigation_body_186,
  navigation_body_187,
  navigation_body_188,
  navigation_body_189,
  navigation_body_190,
  navigation_body_191,
  navigation_body_192,
  navigation_body_193,
  navigation_body_194,
  navigation_body_195,
  navigation_body_196,
  navigation_body_197,
  navigation_body_198,
  navigation_body_199,
  navigation_body_200,
  navigation_body_201,
  navigation_body_202,
  navigation_body_203,
  navigation_body_207,
  navigation_body_208,
  navigation_body_209,
  navigation_body_210,
  navigation_body_211,
  navigation_body_212,
  navigation_body_213,
  navigation_body_214,
  navigation_body_215,
  navigation_body_216,
  navigation_body_217,
  navigation_body_218,
  navigation_body_219,
  navigation_body_220,
  navigation_body_221,
  navigation_body_222,
  navigation_body_223,
  navigation_body_224,
  navigation_body_225,
  navigation_body_226,
  navigation_body_227,
  navigation_body_228,
  navigation_body_229,
  navigation_body_230,
  navigation_body_231,
  navigation_body_232,
  navigation_body_233,
  navigation_body_234,
  navigation_body_235,
  navigation_body_236,
  navigation_body_237,
  navigation_body_238,
  navigation_body_239,
  navigation_body_240,
  navigation_body_241,
  navigation_body_242,
  navigation_body_243,
  navigation_body_244,
  navigation_body_245,
  navigation_body_246,
  navigation_body_247,
  navigation_body_248,
  navigation_body_249,
  navigation_body_250,
  navigation_body_251,
  navigation_body_252,
  navigation_body_253,
  navigation_body_254,
  navigation_body_255,
  navigation_body_256,
  navigation_body_257,
  navigation_body_258,
  navigation_body_259,
  navigation_body_260,
  navigation_body_261,
  navigation_body_262,
  navigation_body_263,
  navigation_body_264,
  navigation_body_265,
  navigation_body_266,
  navigation_body_267,
  navigation_body_268,
  navigation_body_269,
  navigation_body_270,
  navigation_body_271,
  navigation_body_272,
  navigation_body_273,
  navigation_body_274,
  navigation_body_275,
  navigation_body_276,
  navigation_body_277,
  navigation_body_278,
  navigation_body_279,
  navigation_body_280,
  navigation_body_281,
  navigation_body_282,
  navigation_body_283,
  navigation_body_284,
  navigation_body_285,
  navigation_body_286,
  navigation_body_287,
  navigation_body_288,
  navigation_body_289,
  navigation_body_290,
  navigation_body_291,
  navigation_body_292,
  navigation_body_293,
  navigation_body_294,
  navigation_body_295,
  navigation_body_296,
  navigation_body_297,
  navigation_body_298,
  navigation_body_299,
  navigation_body_300,
  navigation_body_301,
  navigation_body_303,
  navigation_body_304,
  navigation_body_305,
  navigation_body_306,
  navigation_body_307,
  navigation_body_308,
  navigation_body_309,
  navigation_body_310,
  navigation_body_311,
  navigation_body_312,
  navigation_body_313,
  navigation_body_314,
  navigation_body_315,
  navigation_body_316,
  navigation_body_317,
  navigation_body_318,
  navigation_body_319,
  navigation_body_320,
  navigation_body_321,
  navigation_body_322,
  navigation_body_323,
  navigation_body_324,
  navigation_body_325,
  navigation_body_326,
  navigation_body_327,
  navigation_body_328,
  navigation_body_329,
  navigation_body_330,
  navigation_body_331,
  navigation_body_332,
  navigation_body_333,
  navigation_body_335,
  navigation_body_336,
  navigation_body_337,
  navigation_body_338,
  navigation_body_339,
  navigation_body_340,
  navigation_body_341,
  navigation_body_342,
  navigation_body_343,
  navigation_body_344,
  navigation_body_345,
  navigation_body_346,
  navigation_body_347,
  navigation_body_348,
  navigation_body_349,
  navigation_body_350,
  navigation_body_351,
  navigation_body_352,
  navigation_body_353,
  navigation_body_354,
  navigation_body_355,
  navigation_body_356,
  navigation_body_357,
  navigation_body_358,
  navigation_body_359,
  navigation_body_360,
  navigation_body_361,
  navigation_body_362,
  navigation_body_363,
  navigation_body_364,
  navigation_body_365,
  navigation_body_367,
  navigation_body_368,
  navigation_body_369,
  navigation_body_370,
  navigation_body_371,
  navigation_body_372,
  navigation_body_373,
  navigation_body_374,
  navigation_body_375,
  navigation_body_376,
  navigation_body_377,
  navigation_body_378,
  navigation_body_379,
  navigation_body_380,
  navigation_body_381,
  navigation_body_382,
  navigation_body_383,
  navigation_body_384,
  navigation_body_385,
  navigation_body_386,
  navigation_body_387,
  navigation_body_388,
  navigation_body_389,
  navigation_body_390,
  navigation_body_391,
  navigation_body_392,
  navigation_body_393,
  navigation_body_394,
  navigation_body_395,
  navigation_body_396,
  navigation_body_397,
  navigation_body_399,
  navigation_body_400,
  navigation_body_401,
  navigation_body_402,
  navigation_body_403,
  navigation_body_404,
  navigation_body_405,
  navigation_body_406,
  navigation_body_407,
  navigation_body_408,
  navigation_body_409,
  navigation_body_410,
  navigation_body_411,
  navigation_body_412,
  navigation_body_413,
  navigation_body_414,
  navigation_body_415,
  navigation_body_416,
  navigation_body_417,
  navigation_body_418,
  navigation_body_419,
  navigation_body_420,
  navigation_body_421,
  navigation_body_422,
  navigation_body_423,
  navigation_body_424,
  navigation_body_425,
  navigation_body_426,
  navigation_body_427,
  navigation_body_428,
  navigation_body_429,
  navigation_body_431,
  navigation_body_432,
  navigation_body_433,
  navigation_body_434,
  navigation_body_435,
  navigation_body_436,
  navigation_body_437,
  navigation_body_438,
  navigation_body_439,
  navigation_body_440,
  navigation_body_441,
  navigation_body_442,
  navigation_body_443,
  navigation_body_444,
  navigation_body_445,
  navigation_body_446,
  navigation_body_447,
  navigation_body_448,
  navigation_body_449,
  navigation_body_450,
  navigation_body_451,
  navigation_body_452,
  navigation_body_453,
  navigation_body_454,
  navigation_body_455,
  navigation_body_456,
  navigation_body_457,
  navigation_body_458,
  navigation_body_459,
  navigation_body_460,
  navigation_body_461,
  navigation_body_463,
  navigation_body_464,
  navigation_body_465,
  navigation_body_466,
  navigation_body_467,
  navigation_body_468,
  navigation_body_469,
  navigation_body_470,
  navigation_body_471,
  navigation_body_472,
  navigation_body_473,
  navigation_body_474,
  navigation_body_475,
  navigation_body_476,
  navigation_body_495,
  navigation_body_496,
  navigation_body_497,
  navigation_body_498,
  navigation_body_499,
  navigation_body_500,
  navigation_body_501,
  navigation_body_502,
  navigation_body_503,
  navigation_body_505,
  navigation_body_506,
  navigation_body_507,
  navigation_body_512,
  navigation_body_514,
  navigation_body_516,
  navigation_body_517,
  navigation_body_518,
  navigation_body_522,
  navigation_body_523,
  navigation_body_524,
  navigation_body_525,
  navigation_body_526,
  navigation_body_528,
  navigation_body_529,
  navigation_body_530,
  navigation_body_531,
  navigation_body_532,
  navigation_body_533,
  navigation_body_534,
  navigation_body_535,
  navigation_body_536,
  navigation_body_537,
  navigation_body_538,
  navigation_body_539,
  navigation_body_540,
  navigation_body_541,
  navigation_body_542,
  navigation_body_543,
  navigation_body_560,
  navigation_body_561,
  navigation_body_562,
  navigation_body_563,
  navigation_body_564,
  navigation_body_565,
  navigation_body_566,
  navigation_body_567,
  navigation_body_568,
  navigation_body_569,
  navigation_body_570,
  navigation_body_571,
  navigation_body_572,
  navigation_body_573,
  navigation_body_574,
  navigation_body_575,
  navigation_body_576,
  navigation_body_577,
  navigation_body_578,
  navigation_body_579,
  navigation_body_580,
  navigation_body_581,
  navigation_body_582,
  navigation_body_583,
  navigation_body_584,
  navigation_body_585,
  navigation_body_586,
  navigation_body_587,
  navigation_body_588,
  navigation_body_589,
  navigation_body_590,
  navigation_body_591,
  navigation_body_592,
  navigation_body_593,
  navigation_body_594,
  navigation_body_595,
  navigation_body_596,
  navigation_body_597,
  navigation_body_598,
  navigation_body_599,
  navigation_body_600,
  navigation_body_601,
  navigation_body_602,
  navigation_body_603,
  navigation_body_604,
  navigation_body_605,
  navigation_body_606,
  navigation_body_607,
  navigation_body_608,
  navigation_body_609,
  navigation_body_610,
  navigation_body_611,
  navigation_body_612,
  navigation_body_613,
  navigation_body_614,
  navigation_body_615,
  navigation_body_616,
  navigation_body_617,
  navigation_body_618,
  navigation_body_619,
  navigation_body_620,
  navigation_body_621,
  navigation_body_622,
  navigation_body_623,
  navigation_body_624,
  navigation_body_625,
  navigation_body_626,
  navigation_body_627,
  navigation_body_628,
  navigation_body_629,
  navigation_body_630,
  navigation_body_631,
  navigation_body_632,
  navigation_body_633,
  navigation_body_634,
  navigation_body_635,
  navigation_body_636,
  navigation_body_637,
  navigation_body_638,
  navigation_body_639,
  navigation_body_640,
  navigation_body_641,
  navigation_body_642,
  navigation_body_643,
  navigation_body_644,
  navigation_body_645,
  navigation_body_646,
  navigation_body_647,
  navigation_body_648,
  navigation_body_649,
  navigation_body_650,
  navigation_body_651,
  navigation_body_652,
  navigation_body_653,
  navigation_body_654,
  navigation_body_655,
  navigation_body_656,
  navigation_body_657,
  navigation_body_658,
  navigation_body_659,
  navigation_body_660,
  navigation_body_661,
  navigation_body_662,
  navigation_body_663,
  navigation_body_664,
  navigation_body_665,
  navigation_body_666,
  navigation_body_667,
  navigation_body_668,
  navigation_body_669,
  navigation_body_670,
  navigation_body_671,
  navigation_body_672,
  navigation_body_673,
  navigation_body_674,
  navigation_body_675,
  navigation_body_676,
  navigation_body_677,
  navigation_body_678,
  navigation_body_679,
  navigation_body_680,
  navigation_body_681,
  navigation_body_682,
  navigation_body_683,
  navigation_body_684,
  navigation_body_685,
  navigation_body_686,
  navigation_body_687,
  navigation_body_704,
  navigation_body_705,
  navigation_body_706,
  navigation_body_707,
  navigation_body_708,
  navigation_body_709,
  diagnostic_q_112,
  diagnostic_q_113,
  diagnostic_q_114,
  diagnostic_q_115,
  diagnostic_q_116,
  diagnostic_q_117,
  diagnostic_q_118,
  diagnostic_q_119,
  diagnostic_q_120,
  diagnostic_q_121,
  diagnostic_q_122,
  diagnostic_q_123,
  diagnostic_q_124,
  diagnostic_q_128,
  diagnostic_q_129,
  diagnostic_q_130,
  diagnostic_q_131,
  diagnostic_q_132,
  diagnostic_q_133,
  diagnostic_q_134,
  diagnostic_q_135,
  diagnostic_q_136,
  diagnostic_q_137,
  diagnostic_q_138,
  diagnostic_q_139,
  diagnostic_q_143,
  nav_z_reason_0,
  nav_z_reason_1,
  nav_z_reason_3,
  nav_z_reason_6,
  nav_z_reason_7,
  nav_z_reason_9,
  nav_z_reason_10,
  nav_z_collective,
  nav_xy_reason_1,
  nav_xy_reason_2,
  nav_xy_reason_6,
  nav_xy_reason_7,
  nav_xy_reason_8,
  nav_xy_reason_9,
  nav_xy_reason_10,
  nav_xy_payload_roll_0,
  nav_xy_payload_roll_1,
  nav_xy_payload_roll_2,
  nav_xy_payload_roll_3,
  nav_xy_payload_roll_4,
  nav_xy_payload_roll_5,
  nav_xy_payload_roll_6,
  nav_xy_payload_roll_7,
  nav_xy_payload_roll_8,
  nav_xy_payload_roll_9,
  nav_xy_payload_roll_10,
  nav_xy_payload_roll_11,
  nav_xy_payload_roll_15,
  nav_xy_payload_pitch_0,
  nav_xy_payload_pitch_1,
  nav_xy_payload_pitch_2,
  nav_xy_payload_pitch_3,
  nav_xy_payload_pitch_4,
  nav_xy_payload_pitch_5,
  nav_xy_payload_pitch_6,
  nav_xy_payload_pitch_7,
  nav_xy_payload_pitch_8,
  nav_xy_payload_pitch_9,
  nav_xy_payload_pitch_10,
  nav_xy_payload_pitch_11,
  nav_xy_payload_pitch_15,
  auto_phase,
  flight_state_flags_51,
  pilot_norm_x,
  pilot_norm_y,
  pilot_norm_dt_us
)
;
input clk50_d;
input n13_16;
input observer_reset;
input n16969_6;
input acceleration_update;
input \staged_telemetry.core_q_453_16 ;
input source_loc_selected;
input n316_14;
input flight_state_flags_0_2;
input ready;
input converted_acc_valid;
input n774_8;
input link_fresh_7;
input mtf_range_ok;
input extension_113_5;
input core_body_860_6;
input core_body_860_8;
input stick_4_14;
input stick_4_16;
input body_yaw_range_ok;
input z_handoff_active;
input core_body_856_3;
input core_body_856_9;
input previous_pose_valid;
input pose_valid;
input n13_13;
input n13_14;
input n3216_8;
input saturated_Z;
input mtf_integrated;
input flow_ok;
input mtf_sample;
input n3649_6;
input n3649_7;
input n3648_6;
input n3648_12;
input pitch_Z_6_13;
input pitch_Z_2_13;
input link_fresh;
input sample_valid_Z;
input mtf_range_ok_3;
input core_body_784;
input core_body_785;
input core_body_786;
input core_body_787;
input core_body_788;
input core_body_789;
input core_body_790;
input core_body_791;
input core_body_792;
input core_body_793;
input core_body_794;
input core_body_795;
input core_body_800;
input core_body_801;
input core_body_802;
input core_body_803;
input core_body_804;
input core_body_805;
input core_body_806;
input core_body_807;
input core_body_808;
input core_body_809;
input core_body_810;
input core_body_811;
input core_body_816;
input core_body_817;
input core_body_818;
input core_body_819;
input core_body_820;
input core_body_821;
input core_body_822;
input core_body_823;
input core_body_824;
input core_body_825;
input core_body_826;
input core_body_827;
input core_body_856;
input [31:0] converted_ax;
input [31:0] converted_ay;
input [15:1] body_yaw;
input [0:0] sensor_yaw;
input [3:0] channels;
input [11:0] ch7_Z;
input [31:0] converted_dt_us;
input base_throttle_us_Z_0;
input base_throttle_us_Z_1;
input base_throttle_us_Z_2;
input base_throttle_us_Z_3;
input base_throttle_us_Z_4;
input base_throttle_us_Z_5;
input base_throttle_us_Z_6;
input base_throttle_us_Z_7;
input base_throttle_us_Z_8;
input base_throttle_us_Z_9;
input base_throttle_us_Z_10;
input base_throttle_us_Z_11;
input base_throttle_us_Z_15;
input [63:0] uptime_ms;
input [31:0] mtf_age_ms;
input [3:3] sensor_failure_mask;
input [0:0] time_adapter_fault;
input [31:0] converted_az;
input [10:10] entry_stick;
input handoff_collective_3;
input handoff_collective_4;
input handoff_collective_11;
input [31:31] fresh_ticks;
input [15:1] pitch_Z;
input sensor_pitch_0;
input sensor_pitch_2;
input sensor_pitch_3;
input sensor_pitch_4;
input sensor_pitch_5;
input sensor_pitch_6;
input sensor_pitch_7;
input sensor_pitch_8;
input sensor_pitch_9;
input sensor_pitch_10;
input sensor_pitch_11;
input sensor_pitch_12;
input [13:0] mtf_distance_mm;
input mtf_vy_x100_0;
input mtf_vy_x100_1;
input mtf_vy_x100_2;
input mtf_vy_x100_3;
input mtf_vy_x100_4;
input mtf_vy_x100_5;
input mtf_vy_x100_6;
input mtf_vy_x100_7;
input mtf_vy_x100_8;
input mtf_vy_x100_9;
input mtf_vy_x100_10;
input mtf_vy_x100_11;
input mtf_vy_x100_12;
input mtf_vy_x100_13;
input mtf_vy_x100_14;
input mtf_vy_x100_15;
input mtf_vy_x100_16;
input mtf_vy_x100_17;
input mtf_vy_x100_18;
input mtf_vy_x100_19;
input mtf_vy_x100_20;
input mtf_vy_x100_21;
input mtf_vy_x100_22;
input mtf_vy_x100_23;
input mtf_vy_x100_24;
input mtf_vy_x100_25;
input mtf_vy_x100_26;
input mtf_vy_x100_27;
input mtf_vy_x100_28;
input mtf_vy_x100_29;
input mtf_vy_x100_31;
input mtf_vx_x100_0;
input mtf_vx_x100_1;
input mtf_vx_x100_2;
input mtf_vx_x100_3;
input mtf_vx_x100_4;
input mtf_vx_x100_5;
input mtf_vx_x100_6;
input mtf_vx_x100_7;
input mtf_vx_x100_8;
input mtf_vx_x100_9;
input mtf_vx_x100_10;
input mtf_vx_x100_11;
input mtf_vx_x100_12;
input mtf_vx_x100_13;
input mtf_vx_x100_14;
input mtf_vx_x100_15;
input mtf_vx_x100_16;
input mtf_vx_x100_17;
input mtf_vx_x100_18;
input mtf_vx_x100_19;
input mtf_vx_x100_20;
input mtf_vx_x100_21;
input mtf_vx_x100_22;
input mtf_vx_x100_23;
input mtf_vx_x100_24;
input mtf_vx_x100_25;
input mtf_vx_x100_26;
input mtf_vx_x100_27;
input mtf_vx_x100_28;
input mtf_vx_x100_29;
input mtf_vx_x100_31;
input [30:0] mtf_dt_ms;
input [15:0] roll;
input [0:0] flight_state_flags;
output nav_vertical_ready;
output nav_xy_active;
output nav_vertical_ready_3;
output nav_vertical_ready_4;
output nav_xy_ready;
output nav_z_active;
output nav_xy_reason_0_7;
output nav_vertical_ready_47;
output geometry_reason_1_7;
output geometry_reason_1_8;
output n164_9;
output pilot_norm_update;
output seen;
output xy_stick_fault;
output navigation_body_0;
output navigation_body_1;
output navigation_body_2;
output navigation_body_3;
output navigation_body_4;
output navigation_body_5;
output navigation_body_6;
output navigation_body_7;
output navigation_body_8;
output navigation_body_9;
output navigation_body_10;
output navigation_body_11;
output navigation_body_12;
output navigation_body_13;
output navigation_body_14;
output navigation_body_31;
output navigation_body_32;
output navigation_body_33;
output navigation_body_35;
output navigation_body_38;
output navigation_body_39;
output navigation_body_40;
output navigation_body_41;
output navigation_body_42;
output navigation_body_48;
output navigation_body_49;
output navigation_body_50;
output navigation_body_51;
output navigation_body_52;
output navigation_body_53;
output navigation_body_54;
output navigation_body_55;
output navigation_body_56;
output navigation_body_57;
output navigation_body_58;
output navigation_body_59;
output navigation_body_63;
output navigation_body_80;
output navigation_body_81;
output navigation_body_82;
output navigation_body_83;
output navigation_body_84;
output navigation_body_85;
output navigation_body_86;
output navigation_body_87;
output navigation_body_88;
output navigation_body_89;
output navigation_body_91;
output navigation_body_92;
output navigation_body_93;
output navigation_body_94;
output navigation_body_95;
output navigation_body_96;
output navigation_body_97;
output navigation_body_98;
output navigation_body_99;
output navigation_body_100;
output navigation_body_101;
output navigation_body_102;
output navigation_body_103;
output navigation_body_104;
output navigation_body_105;
output navigation_body_106;
output navigation_body_107;
output navigation_body_108;
output navigation_body_109;
output navigation_body_110;
output navigation_body_111;
output navigation_body_144;
output navigation_body_145;
output navigation_body_146;
output navigation_body_147;
output navigation_body_148;
output navigation_body_149;
output navigation_body_150;
output navigation_body_151;
output navigation_body_152;
output navigation_body_153;
output navigation_body_154;
output navigation_body_155;
output navigation_body_156;
output navigation_body_157;
output navigation_body_158;
output navigation_body_159;
output navigation_body_160;
output navigation_body_161;
output navigation_body_162;
output navigation_body_163;
output navigation_body_164;
output navigation_body_165;
output navigation_body_166;
output navigation_body_167;
output navigation_body_168;
output navigation_body_169;
output navigation_body_170;
output navigation_body_171;
output navigation_body_172;
output navigation_body_175;
output navigation_body_176;
output navigation_body_177;
output navigation_body_178;
output navigation_body_179;
output navigation_body_180;
output navigation_body_181;
output navigation_body_182;
output navigation_body_183;
output navigation_body_184;
output navigation_body_185;
output navigation_body_186;
output navigation_body_187;
output navigation_body_188;
output navigation_body_189;
output navigation_body_190;
output navigation_body_191;
output navigation_body_192;
output navigation_body_193;
output navigation_body_194;
output navigation_body_195;
output navigation_body_196;
output navigation_body_197;
output navigation_body_198;
output navigation_body_199;
output navigation_body_200;
output navigation_body_201;
output navigation_body_202;
output navigation_body_203;
output navigation_body_207;
output navigation_body_208;
output navigation_body_209;
output navigation_body_210;
output navigation_body_211;
output navigation_body_212;
output navigation_body_213;
output navigation_body_214;
output navigation_body_215;
output navigation_body_216;
output navigation_body_217;
output navigation_body_218;
output navigation_body_219;
output navigation_body_220;
output navigation_body_221;
output navigation_body_222;
output navigation_body_223;
output navigation_body_224;
output navigation_body_225;
output navigation_body_226;
output navigation_body_227;
output navigation_body_228;
output navigation_body_229;
output navigation_body_230;
output navigation_body_231;
output navigation_body_232;
output navigation_body_233;
output navigation_body_234;
output navigation_body_235;
output navigation_body_236;
output navigation_body_237;
output navigation_body_238;
output navigation_body_239;
output navigation_body_240;
output navigation_body_241;
output navigation_body_242;
output navigation_body_243;
output navigation_body_244;
output navigation_body_245;
output navigation_body_246;
output navigation_body_247;
output navigation_body_248;
output navigation_body_249;
output navigation_body_250;
output navigation_body_251;
output navigation_body_252;
output navigation_body_253;
output navigation_body_254;
output navigation_body_255;
output navigation_body_256;
output navigation_body_257;
output navigation_body_258;
output navigation_body_259;
output navigation_body_260;
output navigation_body_261;
output navigation_body_262;
output navigation_body_263;
output navigation_body_264;
output navigation_body_265;
output navigation_body_266;
output navigation_body_267;
output navigation_body_268;
output navigation_body_269;
output navigation_body_270;
output navigation_body_271;
output navigation_body_272;
output navigation_body_273;
output navigation_body_274;
output navigation_body_275;
output navigation_body_276;
output navigation_body_277;
output navigation_body_278;
output navigation_body_279;
output navigation_body_280;
output navigation_body_281;
output navigation_body_282;
output navigation_body_283;
output navigation_body_284;
output navigation_body_285;
output navigation_body_286;
output navigation_body_287;
output navigation_body_288;
output navigation_body_289;
output navigation_body_290;
output navigation_body_291;
output navigation_body_292;
output navigation_body_293;
output navigation_body_294;
output navigation_body_295;
output navigation_body_296;
output navigation_body_297;
output navigation_body_298;
output navigation_body_299;
output navigation_body_300;
output navigation_body_301;
output navigation_body_303;
output navigation_body_304;
output navigation_body_305;
output navigation_body_306;
output navigation_body_307;
output navigation_body_308;
output navigation_body_309;
output navigation_body_310;
output navigation_body_311;
output navigation_body_312;
output navigation_body_313;
output navigation_body_314;
output navigation_body_315;
output navigation_body_316;
output navigation_body_317;
output navigation_body_318;
output navigation_body_319;
output navigation_body_320;
output navigation_body_321;
output navigation_body_322;
output navigation_body_323;
output navigation_body_324;
output navigation_body_325;
output navigation_body_326;
output navigation_body_327;
output navigation_body_328;
output navigation_body_329;
output navigation_body_330;
output navigation_body_331;
output navigation_body_332;
output navigation_body_333;
output navigation_body_335;
output navigation_body_336;
output navigation_body_337;
output navigation_body_338;
output navigation_body_339;
output navigation_body_340;
output navigation_body_341;
output navigation_body_342;
output navigation_body_343;
output navigation_body_344;
output navigation_body_345;
output navigation_body_346;
output navigation_body_347;
output navigation_body_348;
output navigation_body_349;
output navigation_body_350;
output navigation_body_351;
output navigation_body_352;
output navigation_body_353;
output navigation_body_354;
output navigation_body_355;
output navigation_body_356;
output navigation_body_357;
output navigation_body_358;
output navigation_body_359;
output navigation_body_360;
output navigation_body_361;
output navigation_body_362;
output navigation_body_363;
output navigation_body_364;
output navigation_body_365;
output navigation_body_367;
output navigation_body_368;
output navigation_body_369;
output navigation_body_370;
output navigation_body_371;
output navigation_body_372;
output navigation_body_373;
output navigation_body_374;
output navigation_body_375;
output navigation_body_376;
output navigation_body_377;
output navigation_body_378;
output navigation_body_379;
output navigation_body_380;
output navigation_body_381;
output navigation_body_382;
output navigation_body_383;
output navigation_body_384;
output navigation_body_385;
output navigation_body_386;
output navigation_body_387;
output navigation_body_388;
output navigation_body_389;
output navigation_body_390;
output navigation_body_391;
output navigation_body_392;
output navigation_body_393;
output navigation_body_394;
output navigation_body_395;
output navigation_body_396;
output navigation_body_397;
output navigation_body_399;
output navigation_body_400;
output navigation_body_401;
output navigation_body_402;
output navigation_body_403;
output navigation_body_404;
output navigation_body_405;
output navigation_body_406;
output navigation_body_407;
output navigation_body_408;
output navigation_body_409;
output navigation_body_410;
output navigation_body_411;
output navigation_body_412;
output navigation_body_413;
output navigation_body_414;
output navigation_body_415;
output navigation_body_416;
output navigation_body_417;
output navigation_body_418;
output navigation_body_419;
output navigation_body_420;
output navigation_body_421;
output navigation_body_422;
output navigation_body_423;
output navigation_body_424;
output navigation_body_425;
output navigation_body_426;
output navigation_body_427;
output navigation_body_428;
output navigation_body_429;
output navigation_body_431;
output navigation_body_432;
output navigation_body_433;
output navigation_body_434;
output navigation_body_435;
output navigation_body_436;
output navigation_body_437;
output navigation_body_438;
output navigation_body_439;
output navigation_body_440;
output navigation_body_441;
output navigation_body_442;
output navigation_body_443;
output navigation_body_444;
output navigation_body_445;
output navigation_body_446;
output navigation_body_447;
output navigation_body_448;
output navigation_body_449;
output navigation_body_450;
output navigation_body_451;
output navigation_body_452;
output navigation_body_453;
output navigation_body_454;
output navigation_body_455;
output navigation_body_456;
output navigation_body_457;
output navigation_body_458;
output navigation_body_459;
output navigation_body_460;
output navigation_body_461;
output navigation_body_463;
output navigation_body_464;
output navigation_body_465;
output navigation_body_466;
output navigation_body_467;
output navigation_body_468;
output navigation_body_469;
output navigation_body_470;
output navigation_body_471;
output navigation_body_472;
output navigation_body_473;
output navigation_body_474;
output navigation_body_475;
output navigation_body_476;
output navigation_body_495;
output navigation_body_496;
output navigation_body_497;
output navigation_body_498;
output navigation_body_499;
output navigation_body_500;
output navigation_body_501;
output navigation_body_502;
output navigation_body_503;
output navigation_body_505;
output navigation_body_506;
output navigation_body_507;
output navigation_body_512;
output navigation_body_514;
output navigation_body_516;
output navigation_body_517;
output navigation_body_518;
output navigation_body_522;
output navigation_body_523;
output navigation_body_524;
output navigation_body_525;
output navigation_body_526;
output navigation_body_528;
output navigation_body_529;
output navigation_body_530;
output navigation_body_531;
output navigation_body_532;
output navigation_body_533;
output navigation_body_534;
output navigation_body_535;
output navigation_body_536;
output navigation_body_537;
output navigation_body_538;
output navigation_body_539;
output navigation_body_540;
output navigation_body_541;
output navigation_body_542;
output navigation_body_543;
output navigation_body_560;
output navigation_body_561;
output navigation_body_562;
output navigation_body_563;
output navigation_body_564;
output navigation_body_565;
output navigation_body_566;
output navigation_body_567;
output navigation_body_568;
output navigation_body_569;
output navigation_body_570;
output navigation_body_571;
output navigation_body_572;
output navigation_body_573;
output navigation_body_574;
output navigation_body_575;
output navigation_body_576;
output navigation_body_577;
output navigation_body_578;
output navigation_body_579;
output navigation_body_580;
output navigation_body_581;
output navigation_body_582;
output navigation_body_583;
output navigation_body_584;
output navigation_body_585;
output navigation_body_586;
output navigation_body_587;
output navigation_body_588;
output navigation_body_589;
output navigation_body_590;
output navigation_body_591;
output navigation_body_592;
output navigation_body_593;
output navigation_body_594;
output navigation_body_595;
output navigation_body_596;
output navigation_body_597;
output navigation_body_598;
output navigation_body_599;
output navigation_body_600;
output navigation_body_601;
output navigation_body_602;
output navigation_body_603;
output navigation_body_604;
output navigation_body_605;
output navigation_body_606;
output navigation_body_607;
output navigation_body_608;
output navigation_body_609;
output navigation_body_610;
output navigation_body_611;
output navigation_body_612;
output navigation_body_613;
output navigation_body_614;
output navigation_body_615;
output navigation_body_616;
output navigation_body_617;
output navigation_body_618;
output navigation_body_619;
output navigation_body_620;
output navigation_body_621;
output navigation_body_622;
output navigation_body_623;
output navigation_body_624;
output navigation_body_625;
output navigation_body_626;
output navigation_body_627;
output navigation_body_628;
output navigation_body_629;
output navigation_body_630;
output navigation_body_631;
output navigation_body_632;
output navigation_body_633;
output navigation_body_634;
output navigation_body_635;
output navigation_body_636;
output navigation_body_637;
output navigation_body_638;
output navigation_body_639;
output navigation_body_640;
output navigation_body_641;
output navigation_body_642;
output navigation_body_643;
output navigation_body_644;
output navigation_body_645;
output navigation_body_646;
output navigation_body_647;
output navigation_body_648;
output navigation_body_649;
output navigation_body_650;
output navigation_body_651;
output navigation_body_652;
output navigation_body_653;
output navigation_body_654;
output navigation_body_655;
output navigation_body_656;
output navigation_body_657;
output navigation_body_658;
output navigation_body_659;
output navigation_body_660;
output navigation_body_661;
output navigation_body_662;
output navigation_body_663;
output navigation_body_664;
output navigation_body_665;
output navigation_body_666;
output navigation_body_667;
output navigation_body_668;
output navigation_body_669;
output navigation_body_670;
output navigation_body_671;
output navigation_body_672;
output navigation_body_673;
output navigation_body_674;
output navigation_body_675;
output navigation_body_676;
output navigation_body_677;
output navigation_body_678;
output navigation_body_679;
output navigation_body_680;
output navigation_body_681;
output navigation_body_682;
output navigation_body_683;
output navigation_body_684;
output navigation_body_685;
output navigation_body_686;
output navigation_body_687;
output navigation_body_704;
output navigation_body_705;
output navigation_body_706;
output navigation_body_707;
output navigation_body_708;
output navigation_body_709;
output diagnostic_q_112;
output diagnostic_q_113;
output diagnostic_q_114;
output diagnostic_q_115;
output diagnostic_q_116;
output diagnostic_q_117;
output diagnostic_q_118;
output diagnostic_q_119;
output diagnostic_q_120;
output diagnostic_q_121;
output diagnostic_q_122;
output diagnostic_q_123;
output diagnostic_q_124;
output diagnostic_q_128;
output diagnostic_q_129;
output diagnostic_q_130;
output diagnostic_q_131;
output diagnostic_q_132;
output diagnostic_q_133;
output diagnostic_q_134;
output diagnostic_q_135;
output diagnostic_q_136;
output diagnostic_q_137;
output diagnostic_q_138;
output diagnostic_q_139;
output diagnostic_q_143;
output nav_z_reason_0;
output nav_z_reason_1;
output nav_z_reason_3;
output nav_z_reason_6;
output nav_z_reason_7;
output nav_z_reason_9;
output nav_z_reason_10;
output [12:0] nav_z_collective;
output nav_xy_reason_1;
output nav_xy_reason_2;
output nav_xy_reason_6;
output nav_xy_reason_7;
output nav_xy_reason_8;
output nav_xy_reason_9;
output nav_xy_reason_10;
output nav_xy_payload_roll_0;
output nav_xy_payload_roll_1;
output nav_xy_payload_roll_2;
output nav_xy_payload_roll_3;
output nav_xy_payload_roll_4;
output nav_xy_payload_roll_5;
output nav_xy_payload_roll_6;
output nav_xy_payload_roll_7;
output nav_xy_payload_roll_8;
output nav_xy_payload_roll_9;
output nav_xy_payload_roll_10;
output nav_xy_payload_roll_11;
output nav_xy_payload_roll_15;
output nav_xy_payload_pitch_0;
output nav_xy_payload_pitch_1;
output nav_xy_payload_pitch_2;
output nav_xy_payload_pitch_3;
output nav_xy_payload_pitch_4;
output nav_xy_payload_pitch_5;
output nav_xy_payload_pitch_6;
output nav_xy_payload_pitch_7;
output nav_xy_payload_pitch_8;
output nav_xy_payload_pitch_9;
output nav_xy_payload_pitch_10;
output nav_xy_payload_pitch_11;
output nav_xy_payload_pitch_15;
output [1:0] auto_phase;
output [3:3] flight_state_flags_51;
output [17:0] pilot_norm_x;
output [17:0] pilot_norm_y;
output [15:0] pilot_norm_dt_us;
wire live_acc;
wire live_velocity;
wire control_bad;
wire observation_event;
wire n2750_3;
wire position_ready;
wire n3022_3;
wire live_acc_5;
wire module_fresh_4;
wire n2750_4;
wire n2750_5;
wire n2750_6;
wire nav_xy_ready_4;
wire nav_xy_active_3;
wire nav_z_active_3;
wire reasons_18_4;
wire reasons_18_5;
wire nav_z_reason_0_5;
wire nav_xy_reason_1_5;
wire nav_z_reason_10_5;
wire nav_xy_reason_10_5;
wire nav_vertical_ready_6;
wire nav_vertical_ready_7;
wire nav_vertical_ready_8;
wire n2750_7;
wire n2750_8;
wire n2750_9;
wire nav_xy_ready_5;
wire nav_xy_ready_6;
wire nav_xy_ready_7;
wire nav_xy_ready_8;
wire nav_xy_ready_9;
wire nav_vertical_ready_9;
wire nav_vertical_ready_10;
wire nav_vertical_ready_11;
wire nav_vertical_ready_12;
wire nav_vertical_ready_13;
wire nav_vertical_ready_14;
wire nav_xy_ready_10;
wire nav_xy_ready_11;
wire nav_xy_ready_12;
wire nav_xy_ready_13;
wire nav_xy_ready_14;
wire nav_xy_ready_15;
wire nav_xy_ready_16;
wire nav_xy_ready_17;
wire nav_xy_ready_18;
wire nav_xy_ready_19;
wire nav_xy_ready_20;
wire nav_xy_ready_21;
wire nav_xy_ready_22;
wire nav_vertical_ready_15;
wire nav_vertical_ready_16;
wire nav_vertical_ready_17;
wire nav_vertical_ready_18;
wire nav_vertical_ready_19;
wire nav_vertical_ready_20;
wire nav_vertical_ready_21;
wire nav_vertical_ready_22;
wire nav_vertical_ready_23;
wire nav_vertical_ready_24;
wire nav_vertical_ready_25;
wire nav_vertical_ready_26;
wire nav_vertical_ready_27;
wire nav_vertical_ready_28;
wire nav_vertical_ready_29;
wire nav_xy_ready_23;
wire nav_xy_ready_24;
wire nav_xy_ready_25;
wire nav_xy_ready_26;
wire nav_xy_ready_27;
wire nav_xy_ready_28;
wire nav_xy_ready_29;
wire nav_xy_ready_30;
wire nav_xy_ready_31;
wire nav_xy_ready_32;
wire nav_xy_ready_33;
wire nav_xy_ready_34;
wire nav_xy_ready_35;
wire nav_xy_ready_36;
wire nav_xy_ready_37;
wire nav_xy_ready_38;
wire nav_xy_ready_39;
wire nav_xy_ready_40;
wire nav_xy_ready_41;
wire nav_xy_ready_42;
wire nav_xy_ready_43;
wire nav_xy_ready_44;
wire nav_xy_ready_45;
wire nav_xy_ready_46;
wire nav_xy_ready_47;
wire nav_vertical_ready_30;
wire nav_vertical_ready_31;
wire nav_vertical_ready_32;
wire nav_vertical_ready_33;
wire nav_vertical_ready_34;
wire nav_vertical_ready_35;
wire nav_vertical_ready_36;
wire nav_vertical_ready_37;
wire nav_vertical_ready_38;
wire nav_xy_ready_48;
wire nav_xy_ready_49;
wire nav_xy_ready_50;
wire nav_xy_ready_51;
wire nav_xy_ready_52;
wire nav_xy_ready_53;
wire nav_xy_ready_54;
wire nav_xy_ready_55;
wire nav_xy_ready_56;
wire nav_xy_ready_57;
wire nav_xy_ready_58;
wire nav_xy_ready_59;
wire nav_xy_ready_60;
wire nav_xy_ready_61;
wire nav_xy_ready_62;
wire nav_xy_ready_63;
wire nav_xy_ready_64;
wire nav_xy_ready_65;
wire nav_xy_ready_66;
wire nav_xy_ready_67;
wire nav_xy_ready_68;
wire nav_xy_ready_69;
wire nav_vertical_ready_42;
wire nav_vertical_ready_43;
wire nav_vertical_ready_44;
wire nav_xy_ready_70;
wire nav_xy_ready_71;
wire nav_xy_ready_72;
wire nav_xy_ready_73;
wire nav_xy_ready_74;
wire nav_xy_ready_77;
wire nav_xy_ready_78;
wire nav_xy_ready_80;
wire nav_xy_ready_81;
wire nav_xy_ready_82;
wire nav_xy_ready_83;
wire nav_xy_ready_84;
wire nav_xy_ready_85;
wire nav_xy_ready_86;
wire nav_vertical_ready_45;
wire nav_xy_ready_87;
wire nav_xy_ready_88;
wire nav_xy_ready_89;
wire nav_xy_ready_90;
wire nav_xy_ready_91;
wire nav_xy_ready_92;
wire nav_xy_ready_93;
wire nav_xy_ready_94;
wire nav_xy_ready_95;
wire nav_xy_ready_96;
wire nav_xy_ready_97;
wire nav_xy_ready_98;
wire nav_xy_ready_99;
wire nav_xy_ready_100;
wire nav_xy_ready_101;
wire nav_xy_ready_102;
wire nav_xy_ready_103;
wire nav_xy_ready_104;
wire nav_xy_ready_105;
wire nav_xy_ready_106;
wire nav_xy_ready_107;
wire nav_xy_ready_108;
wire nav_xy_ready_109;
wire nav_xy_ready_110;
wire nav_xy_ready_111;
wire nav_xy_ready_112;
wire nav_xy_ready_113;
wire nav_xy_ready_114;
wire nav_xy_ready_115;
wire nav_xy_ready_116;
wire nav_xy_ready_117;
wire nav_xy_ready_118;
wire nav_xy_ready_120;
wire n10579_5;
wire nav_xy_ready_124;
wire nav_xy_ready_126;
wire live_velocity_6;
wire n3190_6;
wire module_fresh;
wire n1933_5;
wire nav_z_reason_1_7;
wire control_bad_7;
wire nav_xy_reason_1_8;
wire nav_z_active_9;
wire position_ready_7;
wire n2737_7;
wire control_event;
wire nav_z_reason_6_9;
wire nav_xy_reason_2_9;
wire observation_bad;
wire nav_z_active_11;
wire observation_bad_d;
wire control_bad_d;
wire origin_d;
wire p_live;
wire p_height_valid;
wire p_acc_valid;
wire p_rc_valid;
wire p_enabled;
wire p_height_update;
wire p_sample_update;
wire position_tick;
wire c_position_valid;
wire c_position_update;
wire c_height_valid;
wire c_acc_valid;
wire controller_z_requested;
wire c_enabled;
wire c_height_update;
wire c_sample_update;
wire n759_2;
wire n760_2;
wire n761_2;
wire n762_2;
wire n763_2;
wire n764_2;
wire n765_2;
wire n766_2;
wire n767_2;
wire n768_2;
wire n769_2;
wire n770_2;
wire n771_2;
wire n772_2;
wire n773_2;
wire n774_2;
wire n775_2;
wire n776_2;
wire n777_2;
wire n778_2;
wire n779_2;
wire n780_2;
wire n781_2;
wire n782_2;
wire n783_2;
wire n784_2;
wire next_observation_epoch_0_2;
wire next_observation_epoch_1_2;
wire next_observation_epoch_2_2;
wire next_observation_epoch_3_2;
wire next_observation_epoch_4_2;
wire next_observation_epoch_5_2;
wire next_observation_epoch_6_2;
wire next_observation_epoch_7_0_COUT;
wire next_control_epoch_0_2;
wire next_control_epoch_1_2;
wire next_control_epoch_2_2;
wire next_control_epoch_3_2;
wire next_control_epoch_4_2;
wire next_control_epoch_5_2;
wire next_control_epoch_6_2;
wire next_control_epoch_7_0_COUT;
wire n2770_1;
wire n2770_2;
wire n2769_1;
wire n2769_2;
wire n2768_1;
wire n2768_2;
wire n2767_1;
wire n2767_2;
wire n2766_1;
wire n2766_2;
wire n2765_1;
wire n2765_2;
wire n2764_1;
wire n2764_2;
wire n2763_1;
wire n2763_2;
wire n2762_1;
wire n2762_2;
wire n2761_1;
wire n2761_2;
wire n2760_1;
wire n2760_2;
wire n2759_1;
wire n2759_2;
wire n2758_1;
wire n2758_2;
wire n2757_1;
wire n2757_2;
wire n2756_1;
wire n2756_2;
wire n2755_1;
wire n2755_2;
wire n2754_1;
wire n2754_2;
wire n2753_1;
wire n2753_2;
wire n2752_1;
wire n2752_0_COUT;
wire n5100_1;
wire n5100_2;
wire n5099_1;
wire n5099_2;
wire n5098_1;
wire n5098_2;
wire n5097_1;
wire n5097_2;
wire n5096_1;
wire n5096_2;
wire n5095_1;
wire n5095_2;
wire n5094_1;
wire n5094_2;
wire n5093_1;
wire n5093_2;
wire n5092_1;
wire n5092_2;
wire n5091_1;
wire n5091_2;
wire n5090_1;
wire n5090_2;
wire n5089_1;
wire n5089_2;
wire n5088_1;
wire n5088_2;
wire n5087_1;
wire n5087_2;
wire n5086_1;
wire n5086_2;
wire n5085_1;
wire n5085_2;
wire n5084_1;
wire n5084_2;
wire n5083_1;
wire n5083_2;
wire n5082_1;
wire n5082_2;
wire n5081_1;
wire n5081_2;
wire n5080_1;
wire n5080_2;
wire n5079_1;
wire n5079_2;
wire n5078_1;
wire n5078_2;
wire n5077_1;
wire n5077_2;
wire n5076_1;
wire n5076_2;
wire n5075_1;
wire n5075_2;
wire n5074_1;
wire n5074_2;
wire n5073_1;
wire n5073_2;
wire n5072_1;
wire n5072_2;
wire n5071_1;
wire n5071_2;
wire n5070_1;
wire n5070_0_COUT;
wire n4152_1_SUM;
wire n4152_3;
wire n4153_1_SUM;
wire n4153_3;
wire n4154_1_SUM;
wire n4154_3;
wire n4155_1_SUM;
wire n4155_3;
wire n4156_1_SUM;
wire n4156_3;
wire n4157_1_SUM;
wire n4157_3;
wire n4158_1_SUM;
wire n4158_3;
wire n4159_1_SUM;
wire n4159_3;
wire n4161_1_SUM;
wire n4161_3;
wire n4162_1_SUM;
wire n4162_3;
wire n4163_1_SUM;
wire n4163_3;
wire n4164_1_SUM;
wire n4164_3;
wire n4165_1_SUM;
wire n4165_3;
wire n4166_1_SUM;
wire n4166_3;
wire n4167_1_SUM;
wire n4167_3;
wire n4168_1_SUM;
wire n4168_3;
wire n2771_6;
wire n5101_6;
wire n107_3;
wire n128_3;
wire n149_3;
wire m_done_1_3;
wire m_done_3_3;
wire n2322_5;
wire n2330_5;
wire n2338_5;
wire n128_3_52;
wire n149_3_53;
wire n172_3;
wire geometry_update;
wire geometry_height_ready;
wire geometry_height_ready_3;
wire n1126_5;
wire geometry_flow_ready;
wire m_cancel_0_7;
wire geometry_reason_7_4;
wire flow_fusion_qualified;
wire pending_acc_epoch_ok_9;
wire pending_acc_epoch_ok_10;
wire pending_acc_epoch_ok_11;
wire flow_fusion_valid;
wire height_qualified_ready;
wire height_fusion_update;
wire v_q16_range;
wire n6360_5;
wire n6370_4;
wire height_estimate_ready_6;
wire n6355_9;
wire n6363_6;
wire height_estimate_ready_20;
wire have_epoch;
wire n845_7;
wire tracking;
wire command_seen;
wire height_command_seen;
wire blocked;
wire cancel_now_4;
wire n22634_5;
wire n22642_6;
wire controller_z_ready;
wire xy_cancel_now_17;
wire [18:16] reasons;
wire [8:8] nav_z_reason_2;
wire [31:0] z_target_height;
wire [15:0] nav_z_throttle;
wire [0:0] nav_xy_reason_0;
wire [28:0] position_x_q8;
wire [29:0] position_y_q8;
wire [6:0] observation_epoch;
wire [7:0] control_epoch;
wire [7:7] p_observation_epoch;
wire [31:0] p_vx;
wire [31:0] p_vy;
wire [31:0] p_height;
wire [31:0] p_ax;
wire [31:0] p_ay;
wire [31:0] p_az;
wire [15:0] p_yaw;
wire [3:0] p_channel_count;
wire [11:0] p_ch1;
wire [11:0] p_ch2;
wire [11:0] p_ch3;
wire [11:0] p_ch7;
wire [31:0] p_sample_dt;
wire [31:0] p_vz;
wire [15:0] p_collective;
wire [19:0] position_timer;
wire [7:0] c_observation_epoch;
wire [7:0] c_control_epoch;
wire [31:6] c_position_age;
wire [31:0] c_vx;
wire [31:0] c_vy;
wire [31:0] c_height;
wire [31:0] c_ax;
wire [31:0] c_ay;
wire [31:0] c_az;
wire [15:0] c_yaw;
wire [3:0] c_channel_count;
wire [11:0] c_ch1;
wire [11:0] c_ch2;
wire [11:0] c_ch3;
wire [11:0] c_ch7;
wire [31:0] c_sample_dt;
wire [31:0] c_vz;
wire [15:0] c_collective;
wire [31:0] navigation_sequence;
wire [7:0] next_observation_epoch;
wire [7:0] next_control_epoch;
wire [2:0] done_q;
wire [63:0] m_result;
wire [1:0] response_owner;
wire [0:0] previous_cancel;
wire [3:1] m_done;
wire [0:0] \generation[1] ;
wire [0:0] \generation[2] ;
wire [0:0] \generation[3] ;
wire [3:1] done_q_0;
wire [3:1] error_q;
wire [63:0] d_result;
wire [1:0] response_owner_0;
wire [0:0] m_request;
wire [31:0] bvx;
wire [31:0] bvy;
wire [31:0] wvx;
wire [31:0] wvy;
wire [15:0] geometry_dt_us;
wire [11:0] geometry_reason;
wire [47:0] m_a;
wire [24:0] m_b;
wire [31:0] height_mm_Z;
wire [0:0] m_cancel;
wire [1:1] m_request_0;
wire [1:1] d_request;
wire [30:0] fused_vx_q16_Z;
wire [30:0] fused_vy_q16_Z;
wire [3:0] flow_reason;
wire [96:64] m_a_0;
wire [81:64] m_b_0;
wire [113:64] d_a;
wire [95:64] d_b;
wire [1:1] d_cancel;
wire [2:2] m_request_1;
wire [2:2] d_request_0;
wire [31:0] height_sample_az;
wire [31:0] fused_vz_q16;
wire [191:128] m_a_1;
wire [151:128] m_b_1;
wire [191:128] d_a_0;
wire [152:128] d_b_0;
wire [2:2] d_cancel_0;
wire [22:22] publication_age;
wire [31:0] fused_height;
wire [9:0] position_reason;
wire [31:0] position_raw_x;
wire [31:0] position_raw_y;
wire [3:3] m_request_2;
wire [3:3] d_request_1;
wire [15:0] controller_delta;
wire [15:0] controller_collective;
wire [241:192] m_a_2;
wire [225:192] m_b_2;
wire [255:192] d_a_1;
wire [223:192] d_b_1;
wire [10:0] controller_reason;
wire [10:0] controller_z_reason;
wire [31:0] controller_target_height;
wire [3:3] d_cancel_1;
wire [62:0] DOUT;
wire VCC;
wire GND;
  LUT2 live_acc_s1 (
    .F(live_acc),
    .I0(sensor_failure_mask[3]),
    .I1(live_acc_5) 
);
defparam live_acc_s1.INIT=4'h4;
  LUT3 nav_vertical_ready_s (
    .F(nav_vertical_ready),
    .I0(nav_vertical_ready_3),
    .I1(nav_vertical_ready_4),
    .I2(nav_vertical_ready_47) 
);
defparam nav_vertical_ready_s.INIT=8'h80;
  LUT3 live_velocity_s0 (
    .F(live_velocity),
    .I0(flow_fusion_qualified),
    .I1(live_velocity_6),
    .I2(flow_fusion_valid) 
);
defparam live_velocity_s0.INIT=8'h80;
  LUT2 control_bad_s1 (
    .F(control_bad),
    .I0(control_bad_7),
    .I1(n1933_5) 
);
defparam control_bad_s1.INIT=4'h7;
  LUT4 observation_event_s0 (
    .F(observation_event),
    .I0(origin_d),
    .I1(observer_reset),
    .I2(observation_bad_d),
    .I3(n1933_5) 
);
defparam observation_event_s0.INIT=16'h444F;
  LUT3 n2750_s0 (
    .F(n2750_3),
    .I0(n2750_4),
    .I1(n2750_5),
    .I2(n2750_6) 
);
defparam n2750_s0.INIT=8'h80;
  LUT3 position_ready_s1 (
    .F(position_ready),
    .I0(have_epoch),
    .I1(live_velocity),
    .I2(position_ready_7) 
);
defparam position_ready_s1.INIT=8'h80;
  LUT2 n3022_s0 (
    .F(n3022_3),
    .I0(p_live),
    .I1(position_tick) 
);
defparam n3022_s0.INIT=4'h8;
  LUT2 nav_xy_active_s (
    .F(nav_xy_active),
    .I0(nav_xy_ready),
    .I1(nav_xy_active_3) 
);
defparam nav_xy_active_s.INIT=4'h8;
  LUT3 reasons_18_s0 (
    .F(reasons[18]),
    .I0(position_reason[9]),
    .I1(reasons_18_4),
    .I2(reasons_18_5) 
);
defparam reasons_18_s0.INIT=8'hBF;
  LUT3 reasons_16_s0 (
    .F(reasons[16]),
    .I0(flow_reason[0]),
    .I1(flow_reason[2]),
    .I2(flow_reason[3]) 
);
defparam reasons_16_s0.INIT=8'hFE;
  LUT4 nav_z_reason_0_s (
    .F(nav_z_reason_0),
    .I0(n16969_6),
    .I1(nav_z_reason_0_5),
    .I2(core_body_856),
    .I3(observer_reset) 
);
defparam nav_z_reason_0_s.INIT=16'h008F;
  LUT4 nav_z_reason_1_s (
    .F(nav_z_reason_1),
    .I0(n316_14),
    .I1(controller_z_reason[1]),
    .I2(n16969_6),
    .I3(nav_z_reason_1_7) 
);
defparam nav_z_reason_1_s.INIT=16'h8F00;
  LUT4 nav_z_reason_3_s (
    .F(nav_z_reason_3),
    .I0(controller_z_reason[3]),
    .I1(flight_state_flags_0_2),
    .I2(nav_vertical_ready),
    .I3(nav_z_active_9) 
);
defparam nav_z_reason_3_s.INIT=16'h8F00;
  LUT2 nav_z_reason_6_s (
    .F(nav_z_reason_6),
    .I0(controller_z_reason[6]),
    .I1(nav_z_reason_6_9) 
);
defparam nav_z_reason_6_s.INIT=4'h8;
  LUT2 nav_z_reason_7_s (
    .F(nav_z_reason_7),
    .I0(controller_z_reason[7]),
    .I1(nav_z_reason_6_9) 
);
defparam nav_z_reason_7_s.INIT=4'h8;
  LUT3 nav_z_reason_8_s (
    .F(nav_z_reason_2[8]),
    .I0(flight_state_flags_0_2),
    .I1(nav_vertical_ready),
    .I2(nav_z_active_9) 
);
defparam nav_z_reason_8_s.INIT=8'h40;
  LUT2 nav_z_reason_9_s (
    .F(nav_z_reason_9),
    .I0(controller_z_reason[9]),
    .I1(nav_z_reason_6_9) 
);
defparam nav_z_reason_9_s.INIT=4'h8;
  LUT2 z_target_height_0_s1 (
    .F(z_target_height[0]),
    .I0(controller_target_height[0]),
    .I1(nav_z_active) 
);
defparam z_target_height_0_s1.INIT=4'h8;
  LUT2 z_target_height_1_s1 (
    .F(z_target_height[1]),
    .I0(controller_target_height[1]),
    .I1(nav_z_active) 
);
defparam z_target_height_1_s1.INIT=4'h8;
  LUT2 z_target_height_2_s1 (
    .F(z_target_height[2]),
    .I0(controller_target_height[2]),
    .I1(nav_z_active) 
);
defparam z_target_height_2_s1.INIT=4'h8;
  LUT2 z_target_height_3_s1 (
    .F(z_target_height[3]),
    .I0(controller_target_height[3]),
    .I1(nav_z_active) 
);
defparam z_target_height_3_s1.INIT=4'h8;
  LUT2 z_target_height_4_s1 (
    .F(z_target_height[4]),
    .I0(controller_target_height[4]),
    .I1(nav_z_active) 
);
defparam z_target_height_4_s1.INIT=4'h8;
  LUT2 z_target_height_5_s1 (
    .F(z_target_height[5]),
    .I0(controller_target_height[5]),
    .I1(nav_z_active) 
);
defparam z_target_height_5_s1.INIT=4'h8;
  LUT2 z_target_height_6_s1 (
    .F(z_target_height[6]),
    .I0(controller_target_height[6]),
    .I1(nav_z_active) 
);
defparam z_target_height_6_s1.INIT=4'h8;
  LUT2 z_target_height_7_s1 (
    .F(z_target_height[7]),
    .I0(controller_target_height[7]),
    .I1(nav_z_active) 
);
defparam z_target_height_7_s1.INIT=4'h8;
  LUT2 z_target_height_8_s1 (
    .F(z_target_height[8]),
    .I0(controller_target_height[8]),
    .I1(nav_z_active) 
);
defparam z_target_height_8_s1.INIT=4'h8;
  LUT2 z_target_height_9_s1 (
    .F(z_target_height[9]),
    .I0(controller_target_height[9]),
    .I1(nav_z_active) 
);
defparam z_target_height_9_s1.INIT=4'h8;
  LUT2 z_target_height_10_s1 (
    .F(z_target_height[10]),
    .I0(controller_target_height[10]),
    .I1(nav_z_active) 
);
defparam z_target_height_10_s1.INIT=4'h8;
  LUT2 z_target_height_11_s1 (
    .F(z_target_height[11]),
    .I0(controller_target_height[11]),
    .I1(nav_z_active) 
);
defparam z_target_height_11_s1.INIT=4'h8;
  LUT2 z_target_height_12_s1 (
    .F(z_target_height[12]),
    .I0(controller_target_height[12]),
    .I1(nav_z_active) 
);
defparam z_target_height_12_s1.INIT=4'h8;
  LUT2 z_target_height_13_s1 (
    .F(z_target_height[13]),
    .I0(controller_target_height[13]),
    .I1(nav_z_active) 
);
defparam z_target_height_13_s1.INIT=4'h8;
  LUT2 z_target_height_14_s1 (
    .F(z_target_height[14]),
    .I0(controller_target_height[14]),
    .I1(nav_z_active) 
);
defparam z_target_height_14_s1.INIT=4'h8;
  LUT2 z_target_height_31_s1 (
    .F(z_target_height[31]),
    .I0(controller_target_height[31]),
    .I1(nav_z_active) 
);
defparam z_target_height_31_s1.INIT=4'h8;
  LUT2 nav_z_collective_0_s (
    .F(nav_z_collective[0]),
    .I0(controller_collective[0]),
    .I1(nav_z_active) 
);
defparam nav_z_collective_0_s.INIT=4'h8;
  LUT2 nav_z_collective_1_s (
    .F(nav_z_collective[1]),
    .I0(controller_collective[1]),
    .I1(nav_z_active) 
);
defparam nav_z_collective_1_s.INIT=4'h8;
  LUT2 nav_z_collective_2_s (
    .F(nav_z_collective[2]),
    .I0(controller_collective[2]),
    .I1(nav_z_active) 
);
defparam nav_z_collective_2_s.INIT=4'h8;
  LUT2 nav_z_collective_3_s (
    .F(nav_z_collective[3]),
    .I0(controller_collective[3]),
    .I1(nav_z_active) 
);
defparam nav_z_collective_3_s.INIT=4'h8;
  LUT2 nav_z_collective_4_s (
    .F(nav_z_collective[4]),
    .I0(controller_collective[4]),
    .I1(nav_z_active) 
);
defparam nav_z_collective_4_s.INIT=4'h8;
  LUT2 nav_z_collective_5_s (
    .F(nav_z_collective[5]),
    .I0(controller_collective[5]),
    .I1(nav_z_active) 
);
defparam nav_z_collective_5_s.INIT=4'h8;
  LUT2 nav_z_collective_6_s (
    .F(nav_z_collective[6]),
    .I0(controller_collective[6]),
    .I1(nav_z_active) 
);
defparam nav_z_collective_6_s.INIT=4'h8;
  LUT2 nav_z_collective_7_s (
    .F(nav_z_collective[7]),
    .I0(controller_collective[7]),
    .I1(nav_z_active) 
);
defparam nav_z_collective_7_s.INIT=4'h8;
  LUT2 nav_z_collective_8_s (
    .F(nav_z_collective[8]),
    .I0(controller_collective[8]),
    .I1(nav_z_active) 
);
defparam nav_z_collective_8_s.INIT=4'h8;
  LUT2 nav_z_collective_9_s (
    .F(nav_z_collective[9]),
    .I0(controller_collective[9]),
    .I1(nav_z_active) 
);
defparam nav_z_collective_9_s.INIT=4'h8;
  LUT2 nav_z_collective_10_s (
    .F(nav_z_collective[10]),
    .I0(controller_collective[10]),
    .I1(nav_z_active) 
);
defparam nav_z_collective_10_s.INIT=4'h8;
  LUT2 nav_z_collective_11_s (
    .F(nav_z_collective[11]),
    .I0(controller_collective[11]),
    .I1(nav_z_active) 
);
defparam nav_z_collective_11_s.INIT=4'h8;
  LUT2 nav_z_collective_12_s (
    .F(nav_z_collective[12]),
    .I0(controller_collective[15]),
    .I1(nav_z_active) 
);
defparam nav_z_collective_12_s.INIT=4'h8;
  LUT2 nav_z_throttle_0_s (
    .F(nav_z_throttle[0]),
    .I0(controller_delta[0]),
    .I1(nav_z_active) 
);
defparam nav_z_throttle_0_s.INIT=4'h8;
  LUT2 nav_z_throttle_1_s (
    .F(nav_z_throttle[1]),
    .I0(controller_delta[1]),
    .I1(nav_z_active) 
);
defparam nav_z_throttle_1_s.INIT=4'h8;
  LUT2 nav_z_throttle_2_s (
    .F(nav_z_throttle[2]),
    .I0(controller_delta[2]),
    .I1(nav_z_active) 
);
defparam nav_z_throttle_2_s.INIT=4'h8;
  LUT2 nav_z_throttle_3_s (
    .F(nav_z_throttle[3]),
    .I0(controller_delta[3]),
    .I1(nav_z_active) 
);
defparam nav_z_throttle_3_s.INIT=4'h8;
  LUT2 nav_z_throttle_4_s (
    .F(nav_z_throttle[4]),
    .I0(controller_delta[4]),
    .I1(nav_z_active) 
);
defparam nav_z_throttle_4_s.INIT=4'h8;
  LUT2 nav_z_throttle_5_s (
    .F(nav_z_throttle[5]),
    .I0(controller_delta[5]),
    .I1(nav_z_active) 
);
defparam nav_z_throttle_5_s.INIT=4'h8;
  LUT2 nav_z_throttle_6_s (
    .F(nav_z_throttle[6]),
    .I0(controller_delta[6]),
    .I1(nav_z_active) 
);
defparam nav_z_throttle_6_s.INIT=4'h8;
  LUT2 nav_z_throttle_7_s (
    .F(nav_z_throttle[7]),
    .I0(controller_delta[7]),
    .I1(nav_z_active) 
);
defparam nav_z_throttle_7_s.INIT=4'h8;
  LUT2 nav_z_throttle_8_s (
    .F(nav_z_throttle[8]),
    .I0(controller_delta[8]),
    .I1(nav_z_active) 
);
defparam nav_z_throttle_8_s.INIT=4'h8;
  LUT2 nav_z_throttle_9_s (
    .F(nav_z_throttle[9]),
    .I0(controller_delta[9]),
    .I1(nav_z_active) 
);
defparam nav_z_throttle_9_s.INIT=4'h8;
  LUT2 nav_z_throttle_10_s (
    .F(nav_z_throttle[10]),
    .I0(controller_delta[15]),
    .I1(nav_z_active) 
);
defparam nav_z_throttle_10_s.INIT=4'h8;
  LUT2 nav_z_throttle_11_s (
    .F(nav_z_throttle[11]),
    .I0(controller_delta[15]),
    .I1(nav_z_active) 
);
defparam nav_z_throttle_11_s.INIT=4'h8;
  LUT2 nav_z_throttle_12_s (
    .F(nav_z_throttle[12]),
    .I0(controller_delta[15]),
    .I1(nav_z_active) 
);
defparam nav_z_throttle_12_s.INIT=4'h8;
  LUT2 nav_z_throttle_13_s (
    .F(nav_z_throttle[13]),
    .I0(controller_delta[15]),
    .I1(nav_z_active) 
);
defparam nav_z_throttle_13_s.INIT=4'h8;
  LUT2 nav_z_throttle_14_s (
    .F(nav_z_throttle[14]),
    .I0(controller_delta[15]),
    .I1(nav_z_active) 
);
defparam nav_z_throttle_14_s.INIT=4'h8;
  LUT2 nav_z_throttle_15_s (
    .F(nav_z_throttle[15]),
    .I0(controller_delta[15]),
    .I1(nav_z_active) 
);
defparam nav_z_throttle_15_s.INIT=4'h8;
  LUT4 nav_xy_reason_1_s (
    .F(nav_xy_reason_1),
    .I0(controller_reason[1]),
    .I1(nav_xy_reason_1_5),
    .I2(n16969_6),
    .I3(nav_xy_reason_1_8) 
);
defparam nav_xy_reason_1_s.INIT=16'h8F00;
  LUT4 nav_xy_reason_2_s (
    .F(nav_xy_reason_2),
    .I0(controller_reason[2]),
    .I1(flight_state_flags_0_2),
    .I2(nav_xy_ready),
    .I3(nav_xy_reason_2_9) 
);
defparam nav_xy_reason_2_s.INIT=16'h8F00;
  LUT3 nav_xy_reason_8_s (
    .F(nav_xy_reason_8),
    .I0(flight_state_flags_0_2),
    .I1(nav_xy_ready),
    .I2(nav_xy_reason_2_9) 
);
defparam nav_xy_reason_8_s.INIT=8'h40;
  LUT4 nav_xy_reason_10_s (
    .F(nav_xy_reason_10),
    .I0(controller_reason[10]),
    .I1(nav_xy_reason_10_5),
    .I2(nav_xy_reason_1_5),
    .I3(observer_reset) 
);
defparam nav_xy_reason_10_s.INIT=16'hFF80;
  LUT4 live_acc_s2 (
    .F(live_acc_5),
    .I0(time_adapter_fault[0]),
    .I1(observer_reset),
    .I2(ready),
    .I3(converted_acc_valid) 
);
defparam live_acc_s2.INIT=16'h1000;
  LUT3 module_fresh_s1 (
    .F(module_fresh_4),
    .I0(mtf_age_ms[7]),
    .I1(n774_8),
    .I2(link_fresh_7) 
);
defparam module_fresh_s1.INIT=8'h10;
  LUT4 nav_vertical_ready_s0 (
    .F(nav_vertical_ready_3),
    .I0(nav_vertical_ready_6),
    .I1(nav_vertical_ready_7),
    .I2(live_acc),
    .I3(nav_vertical_ready_8) 
);
defparam nav_vertical_ready_s0.INIT=16'h1000;
  LUT4 nav_vertical_ready_s1 (
    .F(nav_vertical_ready_4),
    .I0(observer_reset),
    .I1(mtf_range_ok),
    .I2(extension_113_5),
    .I3(n1126_5) 
);
defparam nav_vertical_ready_s1.INIT=16'h4000;
  LUT4 n2750_s1 (
    .F(n2750_4),
    .I0(position_timer[6]),
    .I1(position_timer[7]),
    .I2(position_timer[4]),
    .I3(position_timer[5]) 
);
defparam n2750_s1.INIT=16'h1000;
  LUT4 n2750_s2 (
    .F(n2750_5),
    .I0(position_timer[0]),
    .I1(position_timer[1]),
    .I2(position_timer[2]),
    .I3(position_timer[3]) 
);
defparam n2750_s2.INIT=16'h8000;
  LUT3 n2750_s3 (
    .F(n2750_6),
    .I0(n2750_7),
    .I1(n2750_8),
    .I2(n2750_9) 
);
defparam n2750_s3.INIT=8'h80;
  LUT4 nav_xy_ready_s1 (
    .F(nav_xy_ready_4),
    .I0(nav_vertical_ready_6),
    .I1(nav_xy_ready_7),
    .I2(nav_xy_ready_8),
    .I3(nav_xy_ready_9) 
);
defparam nav_xy_ready_s1.INIT=16'h1000;
  LUT4 nav_xy_active_s0 (
    .F(nav_xy_active_3),
    .I0(command_seen),
    .I1(nav_xy_reason_10_5),
    .I2(nav_z_active_3),
    .I3(xy_cancel_now_17) 
);
defparam nav_xy_active_s0.INIT=16'h8000;
  LUT2 nav_z_active_s0 (
    .F(nav_z_active_3),
    .I0(cancel_now_4),
    .I1(nav_z_active_11) 
);
defparam nav_z_active_s0.INIT=4'h8;
  LUT4 reasons_18_s1 (
    .F(reasons_18_4),
    .I0(position_reason[5]),
    .I1(position_reason[6]),
    .I2(position_reason[7]),
    .I3(position_reason[8]) 
);
defparam reasons_18_s1.INIT=16'h0001;
  LUT4 reasons_18_s2 (
    .F(reasons_18_5),
    .I0(position_reason[0]),
    .I1(position_reason[1]),
    .I2(position_reason[2]),
    .I3(position_reason[3]) 
);
defparam reasons_18_s2.INIT=16'h0001;
  LUT2 nav_z_reason_0_s0 (
    .F(nav_z_reason_0_5),
    .I0(controller_z_reason[0]),
    .I1(n316_14) 
);
defparam nav_z_reason_0_s0.INIT=4'h8;
  LUT2 nav_xy_reason_1_s0 (
    .F(nav_xy_reason_1_5),
    .I0(flight_state_flags_0_2),
    .I1(nav_xy_ready) 
);
defparam nav_xy_reason_1_s0.INIT=4'h8;
  LUT2 nav_z_reason_10_s0 (
    .F(nav_z_reason_10_5),
    .I0(n316_14),
    .I1(control_bad_7) 
);
defparam nav_z_reason_10_s0.INIT=4'h8;
  LUT2 nav_xy_reason_10_s0 (
    .F(nav_xy_reason_10_5),
    .I0(source_loc_selected),
    .I1(n16969_6) 
);
defparam nav_xy_reason_10_s0.INIT=4'h8;
  LUT4 nav_vertical_ready_s3 (
    .F(nav_vertical_ready_6),
    .I0(nav_vertical_ready_9),
    .I1(nav_vertical_ready_10),
    .I2(nav_vertical_ready_11),
    .I3(converted_az[31]) 
);
defparam nav_vertical_ready_s3.INIT=16'h0FBB;
  LUT4 nav_vertical_ready_s4 (
    .F(nav_vertical_ready_7),
    .I0(n769_2),
    .I1(n770_2),
    .I2(nav_vertical_ready_12),
    .I3(n768_2) 
);
defparam nav_vertical_ready_s4.INIT=16'hFE00;
  LUT3 nav_vertical_ready_s5 (
    .F(nav_vertical_ready_8),
    .I0(nav_vertical_ready_13),
    .I1(module_fresh_4),
    .I2(nav_vertical_ready_14) 
);
defparam nav_vertical_ready_s5.INIT=8'h40;
  LUT4 n2750_s4 (
    .F(n2750_7),
    .I0(position_timer[16]),
    .I1(position_timer[17]),
    .I2(position_timer[18]),
    .I3(position_timer[19]) 
);
defparam n2750_s4.INIT=16'h8000;
  LUT4 n2750_s5 (
    .F(n2750_8),
    .I0(position_timer[12]),
    .I1(position_timer[13]),
    .I2(position_timer[15]),
    .I3(position_timer[14]) 
);
defparam n2750_s5.INIT=16'h0100;
  LUT4 n2750_s6 (
    .F(n2750_9),
    .I0(position_timer[8]),
    .I1(position_timer[10]),
    .I2(position_timer[11]),
    .I3(position_timer[9]) 
);
defparam n2750_s6.INIT=16'h0100;
  LUT4 nav_xy_ready_s2 (
    .F(nav_xy_ready_5),
    .I0(nav_xy_ready_10),
    .I1(nav_xy_ready_11),
    .I2(nav_xy_ready_12),
    .I3(converted_ax[31]) 
);
defparam nav_xy_ready_s2.INIT=16'h0FBB;
  LUT4 nav_xy_ready_s3 (
    .F(nav_xy_ready_6),
    .I0(nav_xy_ready_13),
    .I1(nav_xy_ready_14),
    .I2(nav_xy_ready_15),
    .I3(converted_ay[31]) 
);
defparam nav_xy_ready_s3.INIT=16'h0FBB;
  LUT4 nav_xy_ready_s4 (
    .F(nav_xy_ready_7),
    .I0(nav_xy_ready_16),
    .I1(nav_xy_ready_17),
    .I2(fused_vz_q16[30]),
    .I3(fused_vz_q16[31]) 
);
defparam nav_xy_ready_s4.INIT=16'hCFFA;
  LUT4 nav_xy_ready_s5 (
    .F(nav_xy_ready_8),
    .I0(nav_xy_ready_18),
    .I1(nav_xy_ready_19),
    .I2(nav_xy_ready_20),
    .I3(nav_xy_ready_21) 
);
defparam nav_xy_ready_s5.INIT=16'h0D00;
  LUT4 nav_xy_ready_s6 (
    .F(nav_xy_ready_9),
    .I0(fused_vx_q16_Z[30]),
    .I1(nav_xy_ready_22),
    .I2(fused_vx_q16_Z[29]),
    .I3(n22634_5) 
);
defparam nav_xy_ready_s6.INIT=16'hEF00;
  LUT4 nav_vertical_ready_s6 (
    .F(nav_vertical_ready_9),
    .I0(nav_vertical_ready_15),
    .I1(converted_az[14]),
    .I2(converted_az[13]),
    .I3(converted_az[12]) 
);
defparam nav_vertical_ready_s6.INIT=16'h4000;
  LUT4 nav_vertical_ready_s7 (
    .F(nav_vertical_ready_10),
    .I0(nav_vertical_ready_16),
    .I1(nav_vertical_ready_17),
    .I2(nav_vertical_ready_18),
    .I3(nav_vertical_ready_19) 
);
defparam nav_vertical_ready_s7.INIT=16'h8000;
  LUT4 nav_vertical_ready_s8 (
    .F(nav_vertical_ready_11),
    .I0(nav_vertical_ready_20),
    .I1(converted_az[11]),
    .I2(nav_vertical_ready_21),
    .I3(nav_vertical_ready_22) 
);
defparam nav_vertical_ready_s8.INIT=16'h4F00;
  LUT4 nav_vertical_ready_s9 (
    .F(nav_vertical_ready_12),
    .I0(nav_vertical_ready_23),
    .I1(nav_vertical_ready_24),
    .I2(n772_2),
    .I3(n771_2) 
);
defparam nav_vertical_ready_s9.INIT=16'hD000;
  LUT4 nav_vertical_ready_s10 (
    .F(nav_vertical_ready_13),
    .I0(height_mm_Z[11]),
    .I1(height_mm_Z[10]),
    .I2(nav_vertical_ready_25),
    .I3(height_mm_Z[12]) 
);
defparam nav_vertical_ready_s10.INIT=16'hFE00;
  LUT4 nav_vertical_ready_s11 (
    .F(nav_vertical_ready_14),
    .I0(nav_vertical_ready_26),
    .I1(nav_vertical_ready_27),
    .I2(nav_vertical_ready_28),
    .I3(nav_vertical_ready_29) 
);
defparam nav_vertical_ready_s11.INIT=16'h8000;
  LUT4 nav_xy_ready_s7 (
    .F(nav_xy_ready_10),
    .I0(nav_xy_ready_23),
    .I1(converted_ax[13]),
    .I2(converted_ax[14]),
    .I3(converted_ax[12]) 
);
defparam nav_xy_ready_s7.INIT=16'h4000;
  LUT4 nav_xy_ready_s8 (
    .F(nav_xy_ready_11),
    .I0(nav_xy_ready_24),
    .I1(nav_xy_ready_25),
    .I2(nav_xy_ready_26),
    .I3(nav_xy_ready_27) 
);
defparam nav_xy_ready_s8.INIT=16'h8000;
  LUT4 nav_xy_ready_s9 (
    .F(nav_xy_ready_12),
    .I0(nav_xy_ready_28),
    .I1(converted_ax[11]),
    .I2(nav_xy_ready_29),
    .I3(nav_xy_ready_30) 
);
defparam nav_xy_ready_s9.INIT=16'h4F00;
  LUT4 nav_xy_ready_s10 (
    .F(nav_xy_ready_13),
    .I0(nav_xy_ready_31),
    .I1(converted_ay[13]),
    .I2(converted_ay[14]),
    .I3(converted_ay[12]) 
);
defparam nav_xy_ready_s10.INIT=16'h4000;
  LUT4 nav_xy_ready_s11 (
    .F(nav_xy_ready_14),
    .I0(nav_xy_ready_32),
    .I1(nav_xy_ready_33),
    .I2(nav_xy_ready_34),
    .I3(nav_xy_ready_35) 
);
defparam nav_xy_ready_s11.INIT=16'h8000;
  LUT4 nav_xy_ready_s12 (
    .F(nav_xy_ready_15),
    .I0(nav_xy_ready_36),
    .I1(converted_ay[11]),
    .I2(nav_xy_ready_37),
    .I3(nav_xy_ready_38) 
);
defparam nav_xy_ready_s12.INIT=16'h4F00;
  LUT4 nav_xy_ready_s13 (
    .F(nav_xy_ready_16),
    .I0(fused_vz_q16[28]),
    .I1(fused_vz_q16[27]),
    .I2(nav_xy_ready_39),
    .I3(fused_vz_q16[29]) 
);
defparam nav_xy_ready_s13.INIT=16'hFE00;
  LUT4 nav_xy_ready_s14 (
    .F(nav_xy_ready_17),
    .I0(nav_xy_ready_40),
    .I1(fused_vz_q16[27]),
    .I2(fused_vz_q16[28]),
    .I3(fused_vz_q16[29]) 
);
defparam nav_xy_ready_s14.INIT=16'h00BF;
  LUT4 nav_xy_ready_s15 (
    .F(nav_xy_ready_18),
    .I0(height_sample_az[31]),
    .I1(height_sample_az[13]),
    .I2(height_sample_az[14]),
    .I3(height_sample_az[12]) 
);
defparam nav_xy_ready_s15.INIT=16'h4000;
  LUT4 nav_xy_ready_s16 (
    .F(nav_xy_ready_19),
    .I0(height_sample_az[9]),
    .I1(nav_xy_ready_41),
    .I2(height_sample_az[10]),
    .I3(height_sample_az[11]) 
);
defparam nav_xy_ready_s16.INIT=16'h001F;
  LUT3 nav_xy_ready_s17 (
    .F(nav_xy_ready_20),
    .I0(nav_xy_ready_42),
    .I1(height_sample_az[11]),
    .I2(nav_xy_ready_43) 
);
defparam nav_xy_ready_s17.INIT=8'hB0;
  LUT4 nav_xy_ready_s18 (
    .F(nav_xy_ready_21),
    .I0(fused_vy_q16_Z[30]),
    .I1(nav_xy_ready_44),
    .I2(fused_vy_q16_Z[29]),
    .I3(nav_xy_ready_45) 
);
defparam nav_xy_ready_s18.INIT=16'hEF00;
  LUT4 nav_xy_ready_s19 (
    .F(nav_xy_ready_22),
    .I0(nav_xy_ready_46),
    .I1(nav_xy_ready_47),
    .I2(fused_vx_q16_Z[27]),
    .I3(fused_vx_q16_Z[28]) 
);
defparam nav_xy_ready_s19.INIT=16'h000D;
  LUT4 nav_vertical_ready_s12 (
    .F(nav_vertical_ready_15),
    .I0(converted_az[9]),
    .I1(nav_vertical_ready_30),
    .I2(converted_az[10]),
    .I3(converted_az[11]) 
);
defparam nav_vertical_ready_s12.INIT=16'h001F;
  LUT4 nav_vertical_ready_s13 (
    .F(nav_vertical_ready_16),
    .I0(converted_az[23]),
    .I1(converted_az[25]),
    .I2(converted_az[27]),
    .I3(converted_az[29]) 
);
defparam nav_vertical_ready_s13.INIT=16'h0001;
  LUT4 nav_vertical_ready_s14 (
    .F(nav_vertical_ready_17),
    .I0(converted_az[15]),
    .I1(converted_az[17]),
    .I2(converted_az[19]),
    .I3(converted_az[21]) 
);
defparam nav_vertical_ready_s14.INIT=16'h0001;
  LUT4 nav_vertical_ready_s15 (
    .F(nav_vertical_ready_18),
    .I0(converted_az[24]),
    .I1(converted_az[26]),
    .I2(converted_az[28]),
    .I3(converted_az[30]) 
);
defparam nav_vertical_ready_s15.INIT=16'h0001;
  LUT4 nav_vertical_ready_s16 (
    .F(nav_vertical_ready_19),
    .I0(converted_az[16]),
    .I1(converted_az[18]),
    .I2(converted_az[20]),
    .I3(converted_az[22]) 
);
defparam nav_vertical_ready_s16.INIT=16'h0001;
  LUT4 nav_vertical_ready_s17 (
    .F(nav_vertical_ready_20),
    .I0(converted_az[8]),
    .I1(nav_vertical_ready_31),
    .I2(converted_az[9]),
    .I3(converted_az[10]) 
);
defparam nav_vertical_ready_s17.INIT=16'h001F;
  LUT3 nav_vertical_ready_s18 (
    .F(nav_vertical_ready_21),
    .I0(converted_az[12]),
    .I1(converted_az[14]),
    .I2(converted_az[13]) 
);
defparam nav_vertical_ready_s18.INIT=8'h01;
  LUT4 nav_vertical_ready_s19 (
    .F(nav_vertical_ready_22),
    .I0(nav_vertical_ready_32),
    .I1(nav_vertical_ready_33),
    .I2(nav_vertical_ready_34),
    .I3(nav_vertical_ready_35) 
);
defparam nav_vertical_ready_s19.INIT=16'h8000;
  LUT3 nav_vertical_ready_s20 (
    .F(nav_vertical_ready_23),
    .I0(n775_2),
    .I1(n774_2),
    .I2(n773_2) 
);
defparam nav_vertical_ready_s20.INIT=8'h01;
  LUT4 nav_vertical_ready_s21 (
    .F(nav_vertical_ready_24),
    .I0(n777_2),
    .I1(n778_2),
    .I2(nav_vertical_ready_36),
    .I3(n776_2) 
);
defparam nav_vertical_ready_s21.INIT=16'hFE00;
  LUT4 nav_vertical_ready_s22 (
    .F(nav_vertical_ready_25),
    .I0(nav_vertical_ready_37),
    .I1(height_mm_Z[8]),
    .I2(height_mm_Z[7]),
    .I3(height_mm_Z[9]) 
);
defparam nav_vertical_ready_s22.INIT=16'h4000;
  LUT4 nav_vertical_ready_s23 (
    .F(nav_vertical_ready_26),
    .I0(n762_2),
    .I1(n761_2),
    .I2(n760_2),
    .I3(n759_2) 
);
defparam nav_vertical_ready_s23.INIT=16'h0001;
  LUT4 nav_vertical_ready_s24 (
    .F(nav_vertical_ready_27),
    .I0(n766_2),
    .I1(n765_2),
    .I2(n764_2),
    .I3(n763_2) 
);
defparam nav_vertical_ready_s24.INIT=16'h0001;
  LUT4 nav_vertical_ready_s25 (
    .F(nav_vertical_ready_28),
    .I0(height_mm_Z[31]),
    .I1(height_mm_Z[31]),
    .I2(height_mm_Z[31]),
    .I3(n767_2) 
);
defparam nav_vertical_ready_s25.INIT=16'h0001;
  LUT4 nav_vertical_ready_s26 (
    .F(nav_vertical_ready_29),
    .I0(nav_vertical_ready_38),
    .I1(nav_vertical_ready_38),
    .I2(nav_vertical_ready_38),
    .I3(nav_vertical_ready_38) 
);
defparam nav_vertical_ready_s26.INIT=16'h8000;
  LUT4 nav_xy_ready_s20 (
    .F(nav_xy_ready_23),
    .I0(converted_ax[9]),
    .I1(nav_xy_ready_48),
    .I2(converted_ax[10]),
    .I3(converted_ax[11]) 
);
defparam nav_xy_ready_s20.INIT=16'h001F;
  LUT4 nav_xy_ready_s21 (
    .F(nav_xy_ready_24),
    .I0(converted_ax[27]),
    .I1(converted_ax[28]),
    .I2(converted_ax[29]),
    .I3(converted_ax[30]) 
);
defparam nav_xy_ready_s21.INIT=16'h0001;
  LUT4 nav_xy_ready_s22 (
    .F(nav_xy_ready_25),
    .I0(converted_ax[23]),
    .I1(converted_ax[24]),
    .I2(converted_ax[25]),
    .I3(converted_ax[26]) 
);
defparam nav_xy_ready_s22.INIT=16'h0001;
  LUT4 nav_xy_ready_s23 (
    .F(nav_xy_ready_26),
    .I0(converted_ax[19]),
    .I1(converted_ax[20]),
    .I2(converted_ax[21]),
    .I3(converted_ax[22]) 
);
defparam nav_xy_ready_s23.INIT=16'h0001;
  LUT4 nav_xy_ready_s24 (
    .F(nav_xy_ready_27),
    .I0(converted_ax[15]),
    .I1(converted_ax[16]),
    .I2(converted_ax[17]),
    .I3(converted_ax[18]) 
);
defparam nav_xy_ready_s24.INIT=16'h0001;
  LUT4 nav_xy_ready_s25 (
    .F(nav_xy_ready_28),
    .I0(converted_ax[8]),
    .I1(nav_xy_ready_49),
    .I2(converted_ax[9]),
    .I3(converted_ax[10]) 
);
defparam nav_xy_ready_s25.INIT=16'h001F;
  LUT3 nav_xy_ready_s26 (
    .F(nav_xy_ready_29),
    .I0(converted_ax[12]),
    .I1(converted_ax[13]),
    .I2(converted_ax[14]) 
);
defparam nav_xy_ready_s26.INIT=8'h01;
  LUT4 nav_xy_ready_s27 (
    .F(nav_xy_ready_30),
    .I0(nav_xy_ready_50),
    .I1(nav_xy_ready_51),
    .I2(nav_xy_ready_52),
    .I3(nav_xy_ready_53) 
);
defparam nav_xy_ready_s27.INIT=16'h8000;
  LUT4 nav_xy_ready_s28 (
    .F(nav_xy_ready_31),
    .I0(converted_ay[9]),
    .I1(nav_xy_ready_54),
    .I2(converted_ay[10]),
    .I3(converted_ay[11]) 
);
defparam nav_xy_ready_s28.INIT=16'h001F;
  LUT4 nav_xy_ready_s29 (
    .F(nav_xy_ready_32),
    .I0(converted_ay[27]),
    .I1(converted_ay[28]),
    .I2(converted_ay[29]),
    .I3(converted_ay[30]) 
);
defparam nav_xy_ready_s29.INIT=16'h0001;
  LUT4 nav_xy_ready_s30 (
    .F(nav_xy_ready_33),
    .I0(converted_ay[23]),
    .I1(converted_ay[24]),
    .I2(converted_ay[25]),
    .I3(converted_ay[26]) 
);
defparam nav_xy_ready_s30.INIT=16'h0001;
  LUT4 nav_xy_ready_s31 (
    .F(nav_xy_ready_34),
    .I0(converted_ay[19]),
    .I1(converted_ay[20]),
    .I2(converted_ay[21]),
    .I3(converted_ay[22]) 
);
defparam nav_xy_ready_s31.INIT=16'h0001;
  LUT4 nav_xy_ready_s32 (
    .F(nav_xy_ready_35),
    .I0(converted_ay[15]),
    .I1(converted_ay[16]),
    .I2(converted_ay[17]),
    .I3(converted_ay[18]) 
);
defparam nav_xy_ready_s32.INIT=16'h0001;
  LUT4 nav_xy_ready_s33 (
    .F(nav_xy_ready_36),
    .I0(converted_ay[8]),
    .I1(nav_xy_ready_55),
    .I2(converted_ay[9]),
    .I3(converted_ay[10]) 
);
defparam nav_xy_ready_s33.INIT=16'h001F;
  LUT3 nav_xy_ready_s34 (
    .F(nav_xy_ready_37),
    .I0(converted_ay[12]),
    .I1(converted_ay[13]),
    .I2(converted_ay[14]) 
);
defparam nav_xy_ready_s34.INIT=8'h01;
  LUT4 nav_xy_ready_s35 (
    .F(nav_xy_ready_38),
    .I0(nav_xy_ready_56),
    .I1(nav_xy_ready_57),
    .I2(nav_xy_ready_58),
    .I3(nav_xy_ready_59) 
);
defparam nav_xy_ready_s35.INIT=16'h8000;
  LUT4 nav_xy_ready_s36 (
    .F(nav_xy_ready_39),
    .I0(nav_xy_ready_60),
    .I1(fused_vz_q16[25]),
    .I2(fused_vz_q16[26]),
    .I3(fused_vz_q16[24]) 
);
defparam nav_xy_ready_s36.INIT=16'h4000;
  LUT4 nav_xy_ready_s37 (
    .F(nav_xy_ready_40),
    .I0(fused_vz_q16[24]),
    .I1(fused_vz_q16[25]),
    .I2(fused_vz_q16[26]),
    .I3(nav_xy_ready_61) 
);
defparam nav_xy_ready_s37.INIT=16'h0001;
  LUT4 nav_xy_ready_s38 (
    .F(nav_xy_ready_41),
    .I0(height_sample_az[7]),
    .I1(height_sample_az[6]),
    .I2(nav_xy_ready_62),
    .I3(height_sample_az[8]) 
);
defparam nav_xy_ready_s38.INIT=16'hFE00;
  LUT4 nav_xy_ready_s39 (
    .F(nav_xy_ready_42),
    .I0(height_sample_az[8]),
    .I1(nav_xy_ready_63),
    .I2(height_sample_az[9]),
    .I3(height_sample_az[10]) 
);
defparam nav_xy_ready_s39.INIT=16'h001F;
  LUT4 nav_xy_ready_s40 (
    .F(nav_xy_ready_43),
    .I0(height_sample_az[12]),
    .I1(height_sample_az[13]),
    .I2(height_sample_az[14]),
    .I3(height_sample_az[31]) 
);
defparam nav_xy_ready_s40.INIT=16'h0100;
  LUT4 nav_xy_ready_s41 (
    .F(nav_xy_ready_44),
    .I0(nav_xy_ready_64),
    .I1(nav_xy_ready_65),
    .I2(fused_vy_q16_Z[27]),
    .I3(fused_vy_q16_Z[28]) 
);
defparam nav_xy_ready_s41.INIT=16'h000D;
  LUT4 nav_xy_ready_s42 (
    .F(nav_xy_ready_45),
    .I0(core_body_860_6),
    .I1(nav_xy_ready_66),
    .I2(nav_xy_ready_67),
    .I3(nav_xy_ready_68) 
);
defparam nav_xy_ready_s42.INIT=16'h4000;
  LUT3 nav_xy_ready_s43 (
    .F(nav_xy_ready_46),
    .I0(fused_vx_q16_Z[24]),
    .I1(fused_vx_q16_Z[25]),
    .I2(fused_vx_q16_Z[26]) 
);
defparam nav_xy_ready_s43.INIT=8'h80;
  LUT4 nav_xy_ready_s44 (
    .F(nav_xy_ready_47),
    .I0(fused_vx_q16_Z[21]),
    .I1(fused_vx_q16_Z[22]),
    .I2(fused_vx_q16_Z[23]),
    .I3(nav_xy_ready_69) 
);
defparam nav_xy_ready_s44.INIT=16'h0001;
  LUT4 nav_vertical_ready_s27 (
    .F(nav_vertical_ready_30),
    .I0(converted_az[6]),
    .I1(converted_az[7]),
    .I2(nav_vertical_ready_42),
    .I3(converted_az[8]) 
);
defparam nav_vertical_ready_s27.INIT=16'hFE00;
  LUT4 nav_vertical_ready_s28 (
    .F(nav_vertical_ready_31),
    .I0(converted_az[5]),
    .I1(converted_az[4]),
    .I2(converted_az[6]),
    .I3(converted_az[7]) 
);
defparam nav_vertical_ready_s28.INIT=16'hE000;
  LUT4 nav_vertical_ready_s29 (
    .F(nav_vertical_ready_32),
    .I0(converted_az[23]),
    .I1(converted_az[25]),
    .I2(converted_az[27]),
    .I3(converted_az[29]) 
);
defparam nav_vertical_ready_s29.INIT=16'h8000;
  LUT4 nav_vertical_ready_s30 (
    .F(nav_vertical_ready_33),
    .I0(converted_az[15]),
    .I1(converted_az[17]),
    .I2(converted_az[19]),
    .I3(converted_az[21]) 
);
defparam nav_vertical_ready_s30.INIT=16'h8000;
  LUT4 nav_vertical_ready_s31 (
    .F(nav_vertical_ready_34),
    .I0(converted_az[24]),
    .I1(converted_az[26]),
    .I2(converted_az[28]),
    .I3(converted_az[30]) 
);
defparam nav_vertical_ready_s31.INIT=16'h8000;
  LUT4 nav_vertical_ready_s32 (
    .F(nav_vertical_ready_35),
    .I0(converted_az[16]),
    .I1(converted_az[18]),
    .I2(converted_az[20]),
    .I3(converted_az[22]) 
);
defparam nav_vertical_ready_s32.INIT=16'h8000;
  LUT3 nav_vertical_ready_s33 (
    .F(nav_vertical_ready_36),
    .I0(nav_vertical_ready_43),
    .I1(n780_2),
    .I2(n779_2) 
);
defparam nav_vertical_ready_s33.INIT=8'hE0;
  LUT4 nav_vertical_ready_s34 (
    .F(nav_vertical_ready_37),
    .I0(height_mm_Z[6]),
    .I1(height_mm_Z[5]),
    .I2(height_mm_Z[4]),
    .I3(nav_vertical_ready_44) 
);
defparam nav_vertical_ready_s34.INIT=16'h0001;
  LUT4 nav_vertical_ready_s35 (
    .F(nav_vertical_ready_38),
    .I0(height_mm_Z[31]),
    .I1(height_mm_Z[31]),
    .I2(height_mm_Z[31]),
    .I3(height_mm_Z[31]) 
);
defparam nav_vertical_ready_s35.INIT=16'h0001;
  LUT4 nav_xy_ready_s45 (
    .F(nav_xy_ready_48),
    .I0(converted_ax[7]),
    .I1(converted_ax[6]),
    .I2(nav_xy_ready_70),
    .I3(converted_ax[8]) 
);
defparam nav_xy_ready_s45.INIT=16'hFE00;
  LUT4 nav_xy_ready_s46 (
    .F(nav_xy_ready_49),
    .I0(converted_ax[5]),
    .I1(converted_ax[4]),
    .I2(converted_ax[6]),
    .I3(converted_ax[7]) 
);
defparam nav_xy_ready_s46.INIT=16'hE000;
  LUT4 nav_xy_ready_s47 (
    .F(nav_xy_ready_50),
    .I0(converted_ax[27]),
    .I1(converted_ax[28]),
    .I2(converted_ax[29]),
    .I3(converted_ax[30]) 
);
defparam nav_xy_ready_s47.INIT=16'h8000;
  LUT4 nav_xy_ready_s48 (
    .F(nav_xy_ready_51),
    .I0(converted_ax[23]),
    .I1(converted_ax[24]),
    .I2(converted_ax[25]),
    .I3(converted_ax[26]) 
);
defparam nav_xy_ready_s48.INIT=16'h8000;
  LUT4 nav_xy_ready_s49 (
    .F(nav_xy_ready_52),
    .I0(converted_ax[19]),
    .I1(converted_ax[20]),
    .I2(converted_ax[21]),
    .I3(converted_ax[22]) 
);
defparam nav_xy_ready_s49.INIT=16'h8000;
  LUT4 nav_xy_ready_s50 (
    .F(nav_xy_ready_53),
    .I0(converted_ax[15]),
    .I1(converted_ax[16]),
    .I2(converted_ax[17]),
    .I3(converted_ax[18]) 
);
defparam nav_xy_ready_s50.INIT=16'h8000;
  LUT4 nav_xy_ready_s51 (
    .F(nav_xy_ready_54),
    .I0(converted_ay[7]),
    .I1(converted_ay[6]),
    .I2(nav_xy_ready_71),
    .I3(converted_ay[8]) 
);
defparam nav_xy_ready_s51.INIT=16'hFE00;
  LUT4 nav_xy_ready_s52 (
    .F(nav_xy_ready_55),
    .I0(converted_ay[5]),
    .I1(converted_ay[4]),
    .I2(converted_ay[6]),
    .I3(converted_ay[7]) 
);
defparam nav_xy_ready_s52.INIT=16'hE000;
  LUT4 nav_xy_ready_s53 (
    .F(nav_xy_ready_56),
    .I0(converted_ay[27]),
    .I1(converted_ay[28]),
    .I2(converted_ay[29]),
    .I3(converted_ay[30]) 
);
defparam nav_xy_ready_s53.INIT=16'h8000;
  LUT4 nav_xy_ready_s54 (
    .F(nav_xy_ready_57),
    .I0(converted_ay[23]),
    .I1(converted_ay[24]),
    .I2(converted_ay[25]),
    .I3(converted_ay[26]) 
);
defparam nav_xy_ready_s54.INIT=16'h8000;
  LUT4 nav_xy_ready_s55 (
    .F(nav_xy_ready_58),
    .I0(converted_ay[19]),
    .I1(converted_ay[20]),
    .I2(converted_ay[21]),
    .I3(converted_ay[22]) 
);
defparam nav_xy_ready_s55.INIT=16'h8000;
  LUT4 nav_xy_ready_s56 (
    .F(nav_xy_ready_59),
    .I0(converted_ay[15]),
    .I1(converted_ay[16]),
    .I2(converted_ay[17]),
    .I3(converted_ay[18]) 
);
defparam nav_xy_ready_s56.INIT=16'h8000;
  LUT4 nav_xy_ready_s57 (
    .F(nav_xy_ready_60),
    .I0(fused_vz_q16[21]),
    .I1(fused_vz_q16[22]),
    .I2(fused_vz_q16[23]),
    .I3(nav_xy_ready_72) 
);
defparam nav_xy_ready_s57.INIT=16'h0001;
  LUT4 nav_xy_ready_s58 (
    .F(nav_xy_ready_61),
    .I0(fused_vz_q16[21]),
    .I1(fused_vz_q16[20]),
    .I2(fused_vz_q16[22]),
    .I3(fused_vz_q16[23]) 
);
defparam nav_xy_ready_s58.INIT=16'h8000;
  LUT3 nav_xy_ready_s59 (
    .F(nav_xy_ready_62),
    .I0(nav_xy_ready_73),
    .I1(height_sample_az[5]),
    .I2(height_sample_az[4]) 
);
defparam nav_xy_ready_s59.INIT=8'h40;
  LUT4 nav_xy_ready_s60 (
    .F(nav_xy_ready_63),
    .I0(height_sample_az[5]),
    .I1(height_sample_az[4]),
    .I2(height_sample_az[6]),
    .I3(height_sample_az[7]) 
);
defparam nav_xy_ready_s60.INIT=16'hE000;
  LUT3 nav_xy_ready_s61 (
    .F(nav_xy_ready_64),
    .I0(fused_vy_q16_Z[24]),
    .I1(fused_vy_q16_Z[25]),
    .I2(fused_vy_q16_Z[26]) 
);
defparam nav_xy_ready_s61.INIT=8'h80;
  LUT4 nav_xy_ready_s62 (
    .F(nav_xy_ready_65),
    .I0(fused_vy_q16_Z[21]),
    .I1(fused_vy_q16_Z[22]),
    .I2(fused_vy_q16_Z[23]),
    .I3(nav_xy_ready_74) 
);
defparam nav_xy_ready_s62.INIT=16'h0001;
  LUT4 nav_xy_ready_s63 (
    .F(nav_xy_ready_66),
    .I0(nav_xy_ready_126),
    .I1(nav_xy_ready_124),
    .I2(nav_xy_ready_77),
    .I3(base_throttle_us_Z_10) 
);
defparam nav_xy_ready_s63.INIT=16'hAFC0;
  LUT4 nav_xy_ready_s64 (
    .F(nav_xy_ready_67),
    .I0(nav_xy_ready_78),
    .I1(entry_stick[10]),
    .I2(nav_xy_ready_120),
    .I3(nav_xy_ready_80) 
);
defparam nav_xy_ready_s64.INIT=16'hE000;
  LUT4 nav_xy_ready_s65 (
    .F(nav_xy_ready_68),
    .I0(nav_xy_ready_81),
    .I1(fused_height[12]),
    .I2(nav_xy_ready_82),
    .I3(nav_xy_ready_83) 
);
defparam nav_xy_ready_s65.INIT=16'h000B;
  LUT4 nav_xy_ready_s66 (
    .F(nav_xy_ready_69),
    .I0(nav_xy_ready_84),
    .I1(nav_xy_ready_85),
    .I2(nav_xy_ready_86),
    .I3(fused_vx_q16_Z[20]) 
);
defparam nav_xy_ready_s66.INIT=16'h7F00;
  LUT3 nav_vertical_ready_s39 (
    .F(nav_vertical_ready_42),
    .I0(nav_vertical_ready_45),
    .I1(converted_az[5]),
    .I2(converted_az[4]) 
);
defparam nav_vertical_ready_s39.INIT=8'h40;
  LUT4 nav_vertical_ready_s40 (
    .F(nav_vertical_ready_43),
    .I0(n783_2),
    .I1(n784_2),
    .I2(n782_2),
    .I3(n781_2) 
);
defparam nav_vertical_ready_s40.INIT=16'hE000;
  LUT4 nav_vertical_ready_s41 (
    .F(nav_vertical_ready_44),
    .I0(height_mm_Z[2]),
    .I1(height_mm_Z[1]),
    .I2(height_mm_Z[0]),
    .I3(height_mm_Z[3]) 
);
defparam nav_vertical_ready_s41.INIT=16'hFE00;
  LUT3 nav_xy_ready_s67 (
    .F(nav_xy_ready_70),
    .I0(nav_xy_ready_87),
    .I1(converted_ax[5]),
    .I2(converted_ax[4]) 
);
defparam nav_xy_ready_s67.INIT=8'h40;
  LUT3 nav_xy_ready_s68 (
    .F(nav_xy_ready_71),
    .I0(nav_xy_ready_88),
    .I1(converted_ay[5]),
    .I2(converted_ay[4]) 
);
defparam nav_xy_ready_s68.INIT=8'h40;
  LUT4 nav_xy_ready_s69 (
    .F(nav_xy_ready_72),
    .I0(nav_xy_ready_89),
    .I1(nav_xy_ready_90),
    .I2(nav_xy_ready_91),
    .I3(fused_vz_q16[20]) 
);
defparam nav_xy_ready_s69.INIT=16'h7F00;
  LUT4 nav_xy_ready_s70 (
    .F(nav_xy_ready_73),
    .I0(height_sample_az[3]),
    .I1(height_sample_az[2]),
    .I2(height_sample_az[1]),
    .I3(height_sample_az[0]) 
);
defparam nav_xy_ready_s70.INIT=16'h0001;
  LUT4 nav_xy_ready_s71 (
    .F(nav_xy_ready_74),
    .I0(nav_xy_ready_92),
    .I1(nav_xy_ready_93),
    .I2(nav_xy_ready_94),
    .I3(fused_vy_q16_Z[20]) 
);
defparam nav_xy_ready_s71.INIT=16'h7F00;
  LUT4 nav_xy_ready_s74 (
    .F(nav_xy_ready_77),
    .I0(base_throttle_us_Z_6),
    .I1(base_throttle_us_Z_7),
    .I2(base_throttle_us_Z_9),
    .I3(base_throttle_us_Z_8) 
);
defparam nav_xy_ready_s74.INIT=16'h8000;
  LUT4 nav_xy_ready_s75 (
    .F(nav_xy_ready_78),
    .I0(core_body_788),
    .I1(core_body_860_8),
    .I2(stick_4_14),
    .I3(stick_4_16) 
);
defparam nav_xy_ready_s75.INIT=16'hBF00;
  LUT4 nav_xy_ready_s77 (
    .F(nav_xy_ready_80),
    .I0(nav_xy_ready_97),
    .I1(nav_xy_ready_98),
    .I2(nav_xy_ready_99),
    .I3(nav_xy_ready_100) 
);
defparam nav_xy_ready_s77.INIT=16'h8000;
  LUT4 nav_xy_ready_s78 (
    .F(nav_xy_ready_81),
    .I0(nav_xy_ready_101),
    .I1(nav_xy_ready_102),
    .I2(fused_height[11]),
    .I3(fused_height[10]) 
);
defparam nav_xy_ready_s78.INIT=16'h000D;
  LUT3 nav_xy_ready_s79 (
    .F(nav_xy_ready_82),
    .I0(fused_vy_q16_Z[29]),
    .I1(nav_xy_ready_103),
    .I2(fused_vy_q16_Z[30]) 
);
defparam nav_xy_ready_s79.INIT=8'h10;
  LUT3 nav_xy_ready_s80 (
    .F(nav_xy_ready_83),
    .I0(fused_vx_q16_Z[29]),
    .I1(nav_xy_ready_104),
    .I2(fused_vx_q16_Z[30]) 
);
defparam nav_xy_ready_s80.INIT=8'h10;
  LUT4 nav_xy_ready_s81 (
    .F(nav_xy_ready_84),
    .I0(fused_vx_q16_Z[15]),
    .I1(fused_vx_q16_Z[14]),
    .I2(fused_vx_q16_Z[13]),
    .I3(fused_vx_q16_Z[12]) 
);
defparam nav_xy_ready_s81.INIT=16'h0001;
  LUT4 nav_xy_ready_s82 (
    .F(nav_xy_ready_85),
    .I0(fused_vx_q16_Z[19]),
    .I1(fused_vx_q16_Z[18]),
    .I2(fused_vx_q16_Z[17]),
    .I3(fused_vx_q16_Z[16]) 
);
defparam nav_xy_ready_s82.INIT=16'h0001;
  LUT3 nav_xy_ready_s83 (
    .F(nav_xy_ready_86),
    .I0(nav_xy_ready_105),
    .I1(nav_xy_ready_106),
    .I2(nav_xy_ready_107) 
);
defparam nav_xy_ready_s83.INIT=8'h80;
  LUT4 nav_vertical_ready_s42 (
    .F(nav_vertical_ready_45),
    .I0(converted_az[3]),
    .I1(converted_az[2]),
    .I2(converted_az[1]),
    .I3(converted_az[0]) 
);
defparam nav_vertical_ready_s42.INIT=16'h0001;
  LUT4 nav_xy_ready_s84 (
    .F(nav_xy_ready_87),
    .I0(converted_ax[0]),
    .I1(converted_ax[1]),
    .I2(converted_ax[2]),
    .I3(converted_ax[3]) 
);
defparam nav_xy_ready_s84.INIT=16'h0001;
  LUT4 nav_xy_ready_s85 (
    .F(nav_xy_ready_88),
    .I0(converted_ay[0]),
    .I1(converted_ay[1]),
    .I2(converted_ay[2]),
    .I3(converted_ay[3]) 
);
defparam nav_xy_ready_s85.INIT=16'h0001;
  LUT4 nav_xy_ready_s86 (
    .F(nav_xy_ready_89),
    .I0(fused_vz_q16[15]),
    .I1(fused_vz_q16[14]),
    .I2(fused_vz_q16[13]),
    .I3(fused_vz_q16[12]) 
);
defparam nav_xy_ready_s86.INIT=16'h0001;
  LUT4 nav_xy_ready_s87 (
    .F(nav_xy_ready_90),
    .I0(fused_vz_q16[19]),
    .I1(fused_vz_q16[18]),
    .I2(fused_vz_q16[17]),
    .I3(fused_vz_q16[16]) 
);
defparam nav_xy_ready_s87.INIT=16'h0001;
  LUT3 nav_xy_ready_s88 (
    .F(nav_xy_ready_91),
    .I0(nav_xy_ready_108),
    .I1(nav_xy_ready_109),
    .I2(nav_xy_ready_110) 
);
defparam nav_xy_ready_s88.INIT=8'h80;
  LUT4 nav_xy_ready_s89 (
    .F(nav_xy_ready_92),
    .I0(fused_vy_q16_Z[15]),
    .I1(fused_vy_q16_Z[14]),
    .I2(fused_vy_q16_Z[13]),
    .I3(fused_vy_q16_Z[12]) 
);
defparam nav_xy_ready_s89.INIT=16'h0001;
  LUT4 nav_xy_ready_s90 (
    .F(nav_xy_ready_93),
    .I0(fused_vy_q16_Z[19]),
    .I1(fused_vy_q16_Z[18]),
    .I2(fused_vy_q16_Z[17]),
    .I3(fused_vy_q16_Z[16]) 
);
defparam nav_xy_ready_s90.INIT=16'h0001;
  LUT3 nav_xy_ready_s91 (
    .F(nav_xy_ready_94),
    .I0(nav_xy_ready_111),
    .I1(nav_xy_ready_112),
    .I2(nav_xy_ready_113) 
);
defparam nav_xy_ready_s91.INIT=8'h80;
  LUT4 nav_xy_ready_s92 (
    .F(nav_xy_ready_95),
    .I0(base_throttle_us_Z_3),
    .I1(base_throttle_us_Z_0),
    .I2(base_throttle_us_Z_1),
    .I3(base_throttle_us_Z_2) 
);
defparam nav_xy_ready_s92.INIT=16'h0001;
  LUT4 nav_xy_ready_s93 (
    .F(nav_xy_ready_96),
    .I0(fused_height[31]),
    .I1(fused_height[30]),
    .I2(fused_height[29]),
    .I3(body_yaw_range_ok) 
);
defparam nav_xy_ready_s93.INIT=16'h0100;
  LUT4 nav_xy_ready_s94 (
    .F(nav_xy_ready_97),
    .I0(fused_height[16]),
    .I1(fused_height[15]),
    .I2(fused_height[14]),
    .I3(fused_height[13]) 
);
defparam nav_xy_ready_s94.INIT=16'h0001;
  LUT4 nav_xy_ready_s95 (
    .F(nav_xy_ready_98),
    .I0(fused_height[20]),
    .I1(fused_height[19]),
    .I2(fused_height[18]),
    .I3(fused_height[17]) 
);
defparam nav_xy_ready_s95.INIT=16'h0001;
  LUT4 nav_xy_ready_s96 (
    .F(nav_xy_ready_99),
    .I0(fused_height[24]),
    .I1(fused_height[23]),
    .I2(fused_height[22]),
    .I3(fused_height[21]) 
);
defparam nav_xy_ready_s96.INIT=16'h0001;
  LUT4 nav_xy_ready_s97 (
    .F(nav_xy_ready_100),
    .I0(fused_height[28]),
    .I1(fused_height[27]),
    .I2(fused_height[26]),
    .I3(fused_height[25]) 
);
defparam nav_xy_ready_s97.INIT=16'h0001;
  LUT3 nav_xy_ready_s98 (
    .F(nav_xy_ready_101),
    .I0(fused_height[9]),
    .I1(fused_height[8]),
    .I2(fused_height[7]) 
);
defparam nav_xy_ready_s98.INIT=8'h80;
  LUT4 nav_xy_ready_s99 (
    .F(nav_xy_ready_102),
    .I0(fused_height[6]),
    .I1(fused_height[5]),
    .I2(fused_height[4]),
    .I3(nav_xy_ready_114) 
);
defparam nav_xy_ready_s99.INIT=16'h0001;
  LUT4 nav_xy_ready_s100 (
    .F(nav_xy_ready_103),
    .I0(nav_xy_ready_115),
    .I1(nav_xy_ready_116),
    .I2(fused_vy_q16_Z[27]),
    .I3(fused_vy_q16_Z[28]) 
);
defparam nav_xy_ready_s100.INIT=16'hD000;
  LUT4 nav_xy_ready_s101 (
    .F(nav_xy_ready_104),
    .I0(nav_xy_ready_117),
    .I1(nav_xy_ready_118),
    .I2(fused_vx_q16_Z[27]),
    .I3(fused_vx_q16_Z[28]) 
);
defparam nav_xy_ready_s101.INIT=16'hD000;
  LUT4 nav_xy_ready_s102 (
    .F(nav_xy_ready_105),
    .I0(fused_vx_q16_Z[3]),
    .I1(fused_vx_q16_Z[2]),
    .I2(fused_vx_q16_Z[1]),
    .I3(fused_vx_q16_Z[0]) 
);
defparam nav_xy_ready_s102.INIT=16'h0001;
  LUT4 nav_xy_ready_s103 (
    .F(nav_xy_ready_106),
    .I0(fused_vx_q16_Z[7]),
    .I1(fused_vx_q16_Z[6]),
    .I2(fused_vx_q16_Z[5]),
    .I3(fused_vx_q16_Z[4]) 
);
defparam nav_xy_ready_s103.INIT=16'h0001;
  LUT4 nav_xy_ready_s104 (
    .F(nav_xy_ready_107),
    .I0(fused_vx_q16_Z[11]),
    .I1(fused_vx_q16_Z[10]),
    .I2(fused_vx_q16_Z[9]),
    .I3(fused_vx_q16_Z[8]) 
);
defparam nav_xy_ready_s104.INIT=16'h0001;
  LUT4 nav_xy_ready_s105 (
    .F(nav_xy_ready_108),
    .I0(fused_vz_q16[3]),
    .I1(fused_vz_q16[2]),
    .I2(fused_vz_q16[1]),
    .I3(fused_vz_q16[0]) 
);
defparam nav_xy_ready_s105.INIT=16'h0001;
  LUT4 nav_xy_ready_s106 (
    .F(nav_xy_ready_109),
    .I0(fused_vz_q16[7]),
    .I1(fused_vz_q16[6]),
    .I2(fused_vz_q16[5]),
    .I3(fused_vz_q16[4]) 
);
defparam nav_xy_ready_s106.INIT=16'h0001;
  LUT4 nav_xy_ready_s107 (
    .F(nav_xy_ready_110),
    .I0(fused_vz_q16[11]),
    .I1(fused_vz_q16[10]),
    .I2(fused_vz_q16[9]),
    .I3(fused_vz_q16[8]) 
);
defparam nav_xy_ready_s107.INIT=16'h0001;
  LUT4 nav_xy_ready_s108 (
    .F(nav_xy_ready_111),
    .I0(fused_vy_q16_Z[3]),
    .I1(fused_vy_q16_Z[2]),
    .I2(fused_vy_q16_Z[1]),
    .I3(fused_vy_q16_Z[0]) 
);
defparam nav_xy_ready_s108.INIT=16'h0001;
  LUT4 nav_xy_ready_s109 (
    .F(nav_xy_ready_112),
    .I0(fused_vy_q16_Z[7]),
    .I1(fused_vy_q16_Z[6]),
    .I2(fused_vy_q16_Z[5]),
    .I3(fused_vy_q16_Z[4]) 
);
defparam nav_xy_ready_s109.INIT=16'h0001;
  LUT4 nav_xy_ready_s110 (
    .F(nav_xy_ready_113),
    .I0(fused_vy_q16_Z[11]),
    .I1(fused_vy_q16_Z[10]),
    .I2(fused_vy_q16_Z[9]),
    .I3(fused_vy_q16_Z[8]) 
);
defparam nav_xy_ready_s110.INIT=16'h0001;
  LUT4 nav_xy_ready_s111 (
    .F(nav_xy_ready_114),
    .I0(fused_height[1]),
    .I1(fused_height[0]),
    .I2(fused_height[2]),
    .I3(fused_height[3]) 
);
defparam nav_xy_ready_s111.INIT=16'hFE00;
  LUT3 nav_xy_ready_s112 (
    .F(nav_xy_ready_115),
    .I0(fused_vy_q16_Z[24]),
    .I1(fused_vy_q16_Z[25]),
    .I2(fused_vy_q16_Z[26]) 
);
defparam nav_xy_ready_s112.INIT=8'h01;
  LUT4 nav_xy_ready_s113 (
    .F(nav_xy_ready_116),
    .I0(fused_vy_q16_Z[21]),
    .I1(fused_vy_q16_Z[20]),
    .I2(fused_vy_q16_Z[22]),
    .I3(fused_vy_q16_Z[23]) 
);
defparam nav_xy_ready_s113.INIT=16'h8000;
  LUT3 nav_xy_ready_s114 (
    .F(nav_xy_ready_117),
    .I0(fused_vx_q16_Z[24]),
    .I1(fused_vx_q16_Z[25]),
    .I2(fused_vx_q16_Z[26]) 
);
defparam nav_xy_ready_s114.INIT=8'h01;
  LUT4 nav_xy_ready_s115 (
    .F(nav_xy_ready_118),
    .I0(fused_vx_q16_Z[21]),
    .I1(fused_vx_q16_Z[20]),
    .I2(fused_vx_q16_Z[22]),
    .I3(fused_vx_q16_Z[23]) 
);
defparam nav_xy_ready_s115.INIT=16'h8000;
  LUT4 nav_xy_ready_s116 (
    .F(nav_xy_ready_120),
    .I0(z_handoff_active),
    .I1(handoff_collective_11),
    .I2(base_throttle_us_Z_15),
    .I3(nav_xy_ready_96) 
);
defparam nav_xy_ready_s116.INIT=16'h0700;
  LUT4 n10579_s1 (
    .F(n10579_5),
    .I0(n2737_7),
    .I1(n2750_4),
    .I2(n2750_5),
    .I3(n2750_6) 
);
defparam n10579_s1.INIT=16'hEAAA;
  LUT4 nav_xy_ready_s117 (
    .F(nav_xy_ready),
    .I0(live_velocity),
    .I1(nav_xy_ready_5),
    .I2(nav_xy_ready_6),
    .I3(nav_xy_ready_4) 
);
defparam nav_xy_ready_s117.INIT=16'h0200;
  LUT4 nav_z_active_s3 (
    .F(nav_z_active),
    .I0(n1933_5),
    .I1(cancel_now_4),
    .I2(nav_z_active_11),
    .I3(nav_z_active_9) 
);
defparam nav_z_active_s3.INIT=16'h8000;
  LUT4 nav_xy_ready_s118 (
    .F(nav_xy_ready_124),
    .I0(handoff_collective_3),
    .I1(z_handoff_active),
    .I2(base_throttle_us_Z_4),
    .I3(base_throttle_us_Z_5) 
);
defparam nav_xy_ready_s118.INIT=16'hFB00;
  LUT4 nav_xy_ready_s119 (
    .F(nav_xy_ready_126),
    .I0(nav_xy_ready_95),
    .I1(z_handoff_active),
    .I2(handoff_collective_4),
    .I3(base_throttle_us_Z_5) 
);
defparam nav_xy_ready_s119.INIT=16'h00BF;
  LUT4 live_velocity_s2 (
    .F(live_velocity_6),
    .I0(sensor_failure_mask[3]),
    .I1(live_acc_5),
    .I2(geometry_flow_ready),
    .I3(module_fresh) 
);
defparam live_velocity_s2.INIT=16'h4000;
  LUT4 n3190_s2 (
    .F(n3190_6),
    .I0(n13_16),
    .I1(mtf_age_ms[7]),
    .I2(n774_8),
    .I3(link_fresh_7) 
);
defparam n3190_s2.INIT=16'hFEFF;
  LUT4 module_fresh_s2 (
    .F(module_fresh),
    .I0(mtf_age_ms[7]),
    .I1(n774_8),
    .I2(link_fresh_7),
    .I3(mtf_range_ok) 
);
defparam module_fresh_s2.INIT=16'h1000;
  LUT4 nav_xy_reason_0_s1 (
    .F(nav_xy_reason_0_7),
    .I0(controller_reason[0]),
    .I1(n16969_6),
    .I2(flight_state_flags_0_2),
    .I3(nav_xy_ready) 
);
defparam nav_xy_reason_0_s1.INIT=16'h8000;
  LUT4 n1933_s1 (
    .F(n1933_5),
    .I0(v_q16_range),
    .I1(nav_vertical_ready_3),
    .I2(nav_vertical_ready_4),
    .I3(nav_vertical_ready_47) 
);
defparam n1933_s1.INIT=16'h8000;
  LUT4 nav_z_reason_1_s1 (
    .F(nav_z_reason_1_7),
    .I0(observer_reset),
    .I1(fresh_ticks[31]),
    .I2(core_body_856_3),
    .I3(core_body_856_9) 
);
defparam nav_z_reason_1_s1.INIT=16'h4555;
  LUT4 control_bad_s3 (
    .F(control_bad_7),
    .I0(fresh_ticks[31]),
    .I1(core_body_856_3),
    .I2(core_body_856_9),
    .I3(n16969_6) 
);
defparam control_bad_s3.INIT=16'hBF00;
  LUT3 nav_xy_reason_1_s2 (
    .F(nav_xy_reason_1_8),
    .I0(previous_pose_valid),
    .I1(pose_valid),
    .I2(source_loc_selected) 
);
defparam nav_xy_reason_1_s2.INIT=8'h80;
  LUT3 nav_z_active_s4 (
    .F(nav_z_active_9),
    .I0(previous_pose_valid),
    .I1(pose_valid),
    .I2(control_bad_7) 
);
defparam nav_z_active_s4.INIT=8'h80;
  LUT4 position_ready_s3 (
    .F(position_ready_7),
    .I0(previous_pose_valid),
    .I1(pose_valid),
    .I2(p_live),
    .I3(n845_7) 
);
defparam position_ready_s3.INIT=16'h8000;
  LUT4 nav_z_reason_10_s1 (
    .F(nav_z_reason_10),
    .I0(controller_z_reason[10]),
    .I1(nav_z_reason_10_5),
    .I2(previous_pose_valid),
    .I3(pose_valid) 
);
defparam nav_z_reason_10_s1.INIT=16'h8FFF;
  LUT4 nav_xy_reason_0_s2 (
    .F(nav_xy_reason_0[0]),
    .I0(nav_xy_reason_0_7),
    .I1(source_loc_selected),
    .I2(previous_pose_valid),
    .I3(pose_valid) 
);
defparam nav_xy_reason_0_s2.INIT=16'hB000;
  LUT4 position_x_q8_28_s2 (
    .F(position_x_q8[28]),
    .I0(position_raw_x[31]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_x_q8_28_s2.INIT=16'h8000;
  LUT4 position_x_q8_27_s2 (
    .F(position_x_q8[27]),
    .I0(position_raw_x[27]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_x_q8_27_s2.INIT=16'h8000;
  LUT4 position_x_q8_26_s2 (
    .F(position_x_q8[26]),
    .I0(position_raw_x[26]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_x_q8_26_s2.INIT=16'h8000;
  LUT4 position_x_q8_25_s2 (
    .F(position_x_q8[25]),
    .I0(position_raw_x[25]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_x_q8_25_s2.INIT=16'h8000;
  LUT4 position_x_q8_24_s2 (
    .F(position_x_q8[24]),
    .I0(position_raw_x[24]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_x_q8_24_s2.INIT=16'h8000;
  LUT4 position_x_q8_23_s2 (
    .F(position_x_q8[23]),
    .I0(position_raw_x[23]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_x_q8_23_s2.INIT=16'h8000;
  LUT4 position_x_q8_22_s2 (
    .F(position_x_q8[22]),
    .I0(position_raw_x[22]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_x_q8_22_s2.INIT=16'h8000;
  LUT4 position_x_q8_21_s2 (
    .F(position_x_q8[21]),
    .I0(position_raw_x[21]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_x_q8_21_s2.INIT=16'h8000;
  LUT4 position_x_q8_20_s2 (
    .F(position_x_q8[20]),
    .I0(position_raw_x[20]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_x_q8_20_s2.INIT=16'h8000;
  LUT4 position_x_q8_19_s2 (
    .F(position_x_q8[19]),
    .I0(position_raw_x[19]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_x_q8_19_s2.INIT=16'h8000;
  LUT4 position_x_q8_18_s2 (
    .F(position_x_q8[18]),
    .I0(position_raw_x[18]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_x_q8_18_s2.INIT=16'h8000;
  LUT4 position_x_q8_17_s2 (
    .F(position_x_q8[17]),
    .I0(position_raw_x[17]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_x_q8_17_s2.INIT=16'h8000;
  LUT4 position_x_q8_16_s2 (
    .F(position_x_q8[16]),
    .I0(position_raw_x[16]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_x_q8_16_s2.INIT=16'h8000;
  LUT4 position_x_q8_15_s2 (
    .F(position_x_q8[15]),
    .I0(position_raw_x[15]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_x_q8_15_s2.INIT=16'h8000;
  LUT4 position_x_q8_14_s2 (
    .F(position_x_q8[14]),
    .I0(position_raw_x[14]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_x_q8_14_s2.INIT=16'h8000;
  LUT4 position_x_q8_13_s2 (
    .F(position_x_q8[13]),
    .I0(position_raw_x[13]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_x_q8_13_s2.INIT=16'h8000;
  LUT4 position_x_q8_12_s2 (
    .F(position_x_q8[12]),
    .I0(position_raw_x[12]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_x_q8_12_s2.INIT=16'h8000;
  LUT4 position_x_q8_11_s2 (
    .F(position_x_q8[11]),
    .I0(position_raw_x[11]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_x_q8_11_s2.INIT=16'h8000;
  LUT4 position_x_q8_10_s2 (
    .F(position_x_q8[10]),
    .I0(position_raw_x[10]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_x_q8_10_s2.INIT=16'h8000;
  LUT4 position_x_q8_9_s2 (
    .F(position_x_q8[9]),
    .I0(position_raw_x[9]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_x_q8_9_s2.INIT=16'h8000;
  LUT4 position_x_q8_8_s2 (
    .F(position_x_q8[8]),
    .I0(position_raw_x[8]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_x_q8_8_s2.INIT=16'h8000;
  LUT4 position_x_q8_7_s2 (
    .F(position_x_q8[7]),
    .I0(position_raw_x[7]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_x_q8_7_s2.INIT=16'h8000;
  LUT4 position_x_q8_6_s2 (
    .F(position_x_q8[6]),
    .I0(position_raw_x[6]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_x_q8_6_s2.INIT=16'h8000;
  LUT4 position_x_q8_5_s2 (
    .F(position_x_q8[5]),
    .I0(position_raw_x[5]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_x_q8_5_s2.INIT=16'h8000;
  LUT4 position_x_q8_4_s2 (
    .F(position_x_q8[4]),
    .I0(position_raw_x[4]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_x_q8_4_s2.INIT=16'h8000;
  LUT4 position_x_q8_3_s2 (
    .F(position_x_q8[3]),
    .I0(position_raw_x[3]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_x_q8_3_s2.INIT=16'h8000;
  LUT4 position_x_q8_2_s2 (
    .F(position_x_q8[2]),
    .I0(position_raw_x[2]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_x_q8_2_s2.INIT=16'h8000;
  LUT4 position_x_q8_1_s2 (
    .F(position_x_q8[1]),
    .I0(position_raw_x[1]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_x_q8_1_s2.INIT=16'h8000;
  LUT4 position_x_q8_0_s2 (
    .F(position_x_q8[0]),
    .I0(position_raw_x[0]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_x_q8_0_s2.INIT=16'h8000;
  LUT4 position_y_q8_29_s2 (
    .F(position_y_q8[29]),
    .I0(position_raw_y[31]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_y_q8_29_s2.INIT=16'h8000;
  LUT4 position_y_q8_28_s2 (
    .F(position_y_q8[28]),
    .I0(position_raw_y[28]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_y_q8_28_s2.INIT=16'h8000;
  LUT4 position_y_q8_27_s2 (
    .F(position_y_q8[27]),
    .I0(position_raw_y[27]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_y_q8_27_s2.INIT=16'h8000;
  LUT4 position_y_q8_26_s2 (
    .F(position_y_q8[26]),
    .I0(position_raw_y[26]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_y_q8_26_s2.INIT=16'h8000;
  LUT4 position_y_q8_25_s2 (
    .F(position_y_q8[25]),
    .I0(position_raw_y[25]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_y_q8_25_s2.INIT=16'h8000;
  LUT4 position_y_q8_24_s2 (
    .F(position_y_q8[24]),
    .I0(position_raw_y[24]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_y_q8_24_s2.INIT=16'h8000;
  LUT4 position_y_q8_23_s2 (
    .F(position_y_q8[23]),
    .I0(position_raw_y[23]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_y_q8_23_s2.INIT=16'h8000;
  LUT4 position_y_q8_22_s2 (
    .F(position_y_q8[22]),
    .I0(position_raw_y[22]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_y_q8_22_s2.INIT=16'h8000;
  LUT4 position_y_q8_21_s2 (
    .F(position_y_q8[21]),
    .I0(position_raw_y[21]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_y_q8_21_s2.INIT=16'h8000;
  LUT4 position_y_q8_20_s2 (
    .F(position_y_q8[20]),
    .I0(position_raw_y[20]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_y_q8_20_s2.INIT=16'h8000;
  LUT4 position_y_q8_19_s2 (
    .F(position_y_q8[19]),
    .I0(position_raw_y[19]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_y_q8_19_s2.INIT=16'h8000;
  LUT4 position_y_q8_18_s2 (
    .F(position_y_q8[18]),
    .I0(position_raw_y[18]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_y_q8_18_s2.INIT=16'h8000;
  LUT4 position_y_q8_17_s2 (
    .F(position_y_q8[17]),
    .I0(position_raw_y[17]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_y_q8_17_s2.INIT=16'h8000;
  LUT4 position_y_q8_16_s2 (
    .F(position_y_q8[16]),
    .I0(position_raw_y[16]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_y_q8_16_s2.INIT=16'h8000;
  LUT4 position_y_q8_15_s2 (
    .F(position_y_q8[15]),
    .I0(position_raw_y[15]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_y_q8_15_s2.INIT=16'h8000;
  LUT4 position_y_q8_14_s2 (
    .F(position_y_q8[14]),
    .I0(position_raw_y[14]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_y_q8_14_s2.INIT=16'h8000;
  LUT4 position_y_q8_13_s2 (
    .F(position_y_q8[13]),
    .I0(position_raw_y[13]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_y_q8_13_s2.INIT=16'h8000;
  LUT4 position_y_q8_12_s2 (
    .F(position_y_q8[12]),
    .I0(position_raw_y[12]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_y_q8_12_s2.INIT=16'h8000;
  LUT4 position_y_q8_11_s2 (
    .F(position_y_q8[11]),
    .I0(position_raw_y[11]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_y_q8_11_s2.INIT=16'h8000;
  LUT4 position_y_q8_10_s2 (
    .F(position_y_q8[10]),
    .I0(position_raw_y[10]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_y_q8_10_s2.INIT=16'h8000;
  LUT4 position_y_q8_9_s2 (
    .F(position_y_q8[9]),
    .I0(position_raw_y[9]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_y_q8_9_s2.INIT=16'h8000;
  LUT4 position_y_q8_8_s2 (
    .F(position_y_q8[8]),
    .I0(position_raw_y[8]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_y_q8_8_s2.INIT=16'h8000;
  LUT4 position_y_q8_7_s2 (
    .F(position_y_q8[7]),
    .I0(position_raw_y[7]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_y_q8_7_s2.INIT=16'h8000;
  LUT4 position_y_q8_6_s2 (
    .F(position_y_q8[6]),
    .I0(position_raw_y[6]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_y_q8_6_s2.INIT=16'h8000;
  LUT4 position_y_q8_5_s2 (
    .F(position_y_q8[5]),
    .I0(position_raw_y[5]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_y_q8_5_s2.INIT=16'h8000;
  LUT4 position_y_q8_4_s2 (
    .F(position_y_q8[4]),
    .I0(position_raw_y[4]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_y_q8_4_s2.INIT=16'h8000;
  LUT4 position_y_q8_3_s2 (
    .F(position_y_q8[3]),
    .I0(position_raw_y[3]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_y_q8_3_s2.INIT=16'h8000;
  LUT4 position_y_q8_2_s2 (
    .F(position_y_q8[2]),
    .I0(position_raw_y[2]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_y_q8_2_s2.INIT=16'h8000;
  LUT4 position_y_q8_1_s2 (
    .F(position_y_q8[1]),
    .I0(position_raw_y[1]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_y_q8_1_s2.INIT=16'h8000;
  LUT4 position_y_q8_0_s2 (
    .F(position_y_q8[0]),
    .I0(position_raw_y[0]),
    .I1(have_epoch),
    .I2(live_velocity),
    .I3(position_ready_7) 
);
defparam position_y_q8_0_s2.INIT=16'h8000;
  LUT3 n2737_s3 (
    .F(n2737_7),
    .I0(n13_13),
    .I1(n13_14),
    .I2(p_live) 
);
defparam n2737_s3.INIT=8'h7F;
  LUT4 control_event_s1 (
    .F(control_event),
    .I0(control_bad_d),
    .I1(control_bad_7),
    .I2(n1933_5),
    .I3(observation_event) 
);
defparam control_event_s1.INIT=16'hFF15;
  LUT4 nav_z_reason_6_s2 (
    .F(nav_z_reason_6_9),
    .I0(previous_pose_valid),
    .I1(pose_valid),
    .I2(n316_14),
    .I3(control_bad_7) 
);
defparam nav_z_reason_6_s2.INIT=16'h8000;
  LUT4 nav_xy_reason_2_s2 (
    .F(nav_xy_reason_2_9),
    .I0(previous_pose_valid),
    .I1(pose_valid),
    .I2(source_loc_selected),
    .I3(n16969_6) 
);
defparam nav_xy_reason_2_s2.INIT=16'h8000;
  LUT4 nav_xy_reason_6_s2 (
    .F(nav_xy_reason_6),
    .I0(controller_reason[6]),
    .I1(flight_state_flags_0_2),
    .I2(nav_xy_ready),
    .I3(nav_xy_reason_2_9) 
);
defparam nav_xy_reason_6_s2.INIT=16'h8000;
  LUT4 nav_xy_reason_7_s0 (
    .F(nav_xy_reason_7),
    .I0(controller_reason[7]),
    .I1(flight_state_flags_0_2),
    .I2(nav_xy_ready),
    .I3(nav_xy_reason_2_9) 
);
defparam nav_xy_reason_7_s0.INIT=16'h8000;
  LUT4 nav_xy_reason_9_s0 (
    .F(nav_xy_reason_9),
    .I0(controller_reason[9]),
    .I1(flight_state_flags_0_2),
    .I2(nav_xy_ready),
    .I3(nav_xy_reason_2_9) 
);
defparam nav_xy_reason_9_s0.INIT=16'h8000;
  LUT4 observation_bad_s2 (
    .F(observation_bad),
    .I0(v_q16_range),
    .I1(nav_vertical_ready_3),
    .I2(nav_vertical_ready_4),
    .I3(nav_vertical_ready_47) 
);
defparam observation_bad_s2.INIT=16'h7FFF;
  LUT5 nav_z_active_s5 (
    .F(nav_z_active_11),
    .I0(blocked),
    .I1(height_command_seen),
    .I2(n22642_6),
    .I3(flight_state_flags_0_2),
    .I4(tracking) 
);
defparam nav_z_active_s5.INIT=32'h40000000;
  LUT5 nav_vertical_ready_s43 (
    .F(nav_vertical_ready_47),
    .I0(height_qualified_ready),
    .I1(geometry_height_ready_3),
    .I2(height_estimate_ready_20),
    .I3(publication_age[22]),
    .I4(height_estimate_ready_6) 
);
defparam nav_vertical_ready_s43.INIT=32'h80880000;
  DFFRE observation_epoch_6_s0 (
    .Q(observation_epoch[6]),
    .D(next_observation_epoch[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam observation_epoch_6_s0.INIT=1'b0;
  DFFRE observation_epoch_5_s0 (
    .Q(observation_epoch[5]),
    .D(next_observation_epoch[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam observation_epoch_5_s0.INIT=1'b0;
  DFFRE observation_epoch_4_s0 (
    .Q(observation_epoch[4]),
    .D(next_observation_epoch[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam observation_epoch_4_s0.INIT=1'b0;
  DFFRE observation_epoch_3_s0 (
    .Q(observation_epoch[3]),
    .D(next_observation_epoch[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam observation_epoch_3_s0.INIT=1'b0;
  DFFRE observation_epoch_2_s0 (
    .Q(observation_epoch[2]),
    .D(next_observation_epoch[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam observation_epoch_2_s0.INIT=1'b0;
  DFFRE observation_epoch_1_s0 (
    .Q(observation_epoch[1]),
    .D(next_observation_epoch[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam observation_epoch_1_s0.INIT=1'b0;
  DFFRE observation_epoch_0_s0 (
    .Q(observation_epoch[0]),
    .D(next_observation_epoch[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam observation_epoch_0_s0.INIT=1'b0;
  DFFRE control_epoch_7_s0 (
    .Q(control_epoch[7]),
    .D(next_control_epoch[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam control_epoch_7_s0.INIT=1'b0;
  DFFRE control_epoch_6_s0 (
    .Q(control_epoch[6]),
    .D(next_control_epoch[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam control_epoch_6_s0.INIT=1'b0;
  DFFRE control_epoch_5_s0 (
    .Q(control_epoch[5]),
    .D(next_control_epoch[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam control_epoch_5_s0.INIT=1'b0;
  DFFRE control_epoch_4_s0 (
    .Q(control_epoch[4]),
    .D(next_control_epoch[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam control_epoch_4_s0.INIT=1'b0;
  DFFRE control_epoch_3_s0 (
    .Q(control_epoch[3]),
    .D(next_control_epoch[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam control_epoch_3_s0.INIT=1'b0;
  DFFRE control_epoch_2_s0 (
    .Q(control_epoch[2]),
    .D(next_control_epoch[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam control_epoch_2_s0.INIT=1'b0;
  DFFRE control_epoch_1_s0 (
    .Q(control_epoch[1]),
    .D(next_control_epoch[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam control_epoch_1_s0.INIT=1'b0;
  DFFRE control_epoch_0_s0 (
    .Q(control_epoch[0]),
    .D(next_control_epoch[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam control_epoch_0_s0.INIT=1'b0;
  DFFSE observation_bad_d_s0 (
    .Q(observation_bad_d),
    .D(observation_bad),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(VCC) 
);
defparam observation_bad_d_s0.INIT=1'b1;
  DFFSE control_bad_d_s0 (
    .Q(control_bad_d),
    .D(control_bad),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(VCC) 
);
defparam control_bad_d_s0.INIT=1'b1;
  DFFRE origin_d_s0 (
    .Q(origin_d),
    .D(observer_reset),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam origin_d_s0.INIT=1'b0;
  DFFRE p_live_s0 (
    .Q(p_live),
    .D(live_velocity),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_live_s0.INIT=1'b0;
  DFFRE p_height_valid_s0 (
    .Q(p_height_valid),
    .D(n1933_5),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_height_valid_s0.INIT=1'b0;
  DFFRE p_acc_valid_s0 (
    .Q(p_acc_valid),
    .D(live_acc),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_acc_valid_s0.INIT=1'b0;
  DFFRE p_rc_valid_s0 (
    .Q(p_rc_valid),
    .D(core_body_856),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_rc_valid_s0.INIT=1'b0;
  DFFRE p_enabled_s0 (
    .Q(p_enabled),
    .D(n16969_6),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_enabled_s0.INIT=1'b0;
  DFFRE p_observation_epoch_7_s0 (
    .Q(p_observation_epoch[7]),
    .D(next_observation_epoch[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_observation_epoch_7_s0.INIT=1'b0;
  DFFRE p_vx_31_s0 (
    .Q(p_vx[31]),
    .D(fused_vx_q16_Z[30]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vx_31_s0.INIT=1'b0;
  DFFRE p_vx_29_s0 (
    .Q(p_vx[29]),
    .D(fused_vx_q16_Z[29]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vx_29_s0.INIT=1'b0;
  DFFRE p_vx_28_s0 (
    .Q(p_vx[28]),
    .D(fused_vx_q16_Z[28]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vx_28_s0.INIT=1'b0;
  DFFRE p_vx_27_s0 (
    .Q(p_vx[27]),
    .D(fused_vx_q16_Z[27]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vx_27_s0.INIT=1'b0;
  DFFRE p_vx_26_s0 (
    .Q(p_vx[26]),
    .D(fused_vx_q16_Z[26]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vx_26_s0.INIT=1'b0;
  DFFRE p_vx_25_s0 (
    .Q(p_vx[25]),
    .D(fused_vx_q16_Z[25]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vx_25_s0.INIT=1'b0;
  DFFRE p_vx_24_s0 (
    .Q(p_vx[24]),
    .D(fused_vx_q16_Z[24]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vx_24_s0.INIT=1'b0;
  DFFRE p_vx_23_s0 (
    .Q(p_vx[23]),
    .D(fused_vx_q16_Z[23]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vx_23_s0.INIT=1'b0;
  DFFRE p_vx_22_s0 (
    .Q(p_vx[22]),
    .D(fused_vx_q16_Z[22]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vx_22_s0.INIT=1'b0;
  DFFRE p_vx_21_s0 (
    .Q(p_vx[21]),
    .D(fused_vx_q16_Z[21]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vx_21_s0.INIT=1'b0;
  DFFRE p_vx_20_s0 (
    .Q(p_vx[20]),
    .D(fused_vx_q16_Z[20]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vx_20_s0.INIT=1'b0;
  DFFRE p_vx_19_s0 (
    .Q(p_vx[19]),
    .D(fused_vx_q16_Z[19]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vx_19_s0.INIT=1'b0;
  DFFRE p_vx_18_s0 (
    .Q(p_vx[18]),
    .D(fused_vx_q16_Z[18]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vx_18_s0.INIT=1'b0;
  DFFRE p_vx_17_s0 (
    .Q(p_vx[17]),
    .D(fused_vx_q16_Z[17]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vx_17_s0.INIT=1'b0;
  DFFRE p_vx_16_s0 (
    .Q(p_vx[16]),
    .D(fused_vx_q16_Z[16]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vx_16_s0.INIT=1'b0;
  DFFRE p_vx_15_s0 (
    .Q(p_vx[15]),
    .D(fused_vx_q16_Z[15]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vx_15_s0.INIT=1'b0;
  DFFRE p_vx_14_s0 (
    .Q(p_vx[14]),
    .D(fused_vx_q16_Z[14]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vx_14_s0.INIT=1'b0;
  DFFRE p_vx_13_s0 (
    .Q(p_vx[13]),
    .D(fused_vx_q16_Z[13]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vx_13_s0.INIT=1'b0;
  DFFRE p_vx_12_s0 (
    .Q(p_vx[12]),
    .D(fused_vx_q16_Z[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vx_12_s0.INIT=1'b0;
  DFFRE p_vx_11_s0 (
    .Q(p_vx[11]),
    .D(fused_vx_q16_Z[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vx_11_s0.INIT=1'b0;
  DFFRE p_vx_10_s0 (
    .Q(p_vx[10]),
    .D(fused_vx_q16_Z[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vx_10_s0.INIT=1'b0;
  DFFRE p_vx_9_s0 (
    .Q(p_vx[9]),
    .D(fused_vx_q16_Z[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vx_9_s0.INIT=1'b0;
  DFFRE p_vx_8_s0 (
    .Q(p_vx[8]),
    .D(fused_vx_q16_Z[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vx_8_s0.INIT=1'b0;
  DFFRE p_vx_7_s0 (
    .Q(p_vx[7]),
    .D(fused_vx_q16_Z[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vx_7_s0.INIT=1'b0;
  DFFRE p_vx_6_s0 (
    .Q(p_vx[6]),
    .D(fused_vx_q16_Z[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vx_6_s0.INIT=1'b0;
  DFFRE p_vx_5_s0 (
    .Q(p_vx[5]),
    .D(fused_vx_q16_Z[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vx_5_s0.INIT=1'b0;
  DFFRE p_vx_4_s0 (
    .Q(p_vx[4]),
    .D(fused_vx_q16_Z[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vx_4_s0.INIT=1'b0;
  DFFRE p_vx_3_s0 (
    .Q(p_vx[3]),
    .D(fused_vx_q16_Z[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vx_3_s0.INIT=1'b0;
  DFFRE p_vx_2_s0 (
    .Q(p_vx[2]),
    .D(fused_vx_q16_Z[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vx_2_s0.INIT=1'b0;
  DFFRE p_vx_1_s0 (
    .Q(p_vx[1]),
    .D(fused_vx_q16_Z[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vx_1_s0.INIT=1'b0;
  DFFRE p_vx_0_s0 (
    .Q(p_vx[0]),
    .D(fused_vx_q16_Z[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vx_0_s0.INIT=1'b0;
  DFFRE p_vy_31_s0 (
    .Q(p_vy[31]),
    .D(fused_vy_q16_Z[30]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vy_31_s0.INIT=1'b0;
  DFFRE p_vy_29_s0 (
    .Q(p_vy[29]),
    .D(fused_vy_q16_Z[29]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vy_29_s0.INIT=1'b0;
  DFFRE p_vy_28_s0 (
    .Q(p_vy[28]),
    .D(fused_vy_q16_Z[28]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vy_28_s0.INIT=1'b0;
  DFFRE p_vy_27_s0 (
    .Q(p_vy[27]),
    .D(fused_vy_q16_Z[27]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vy_27_s0.INIT=1'b0;
  DFFRE p_vy_26_s0 (
    .Q(p_vy[26]),
    .D(fused_vy_q16_Z[26]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vy_26_s0.INIT=1'b0;
  DFFRE p_vy_25_s0 (
    .Q(p_vy[25]),
    .D(fused_vy_q16_Z[25]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vy_25_s0.INIT=1'b0;
  DFFRE p_vy_24_s0 (
    .Q(p_vy[24]),
    .D(fused_vy_q16_Z[24]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vy_24_s0.INIT=1'b0;
  DFFRE p_vy_23_s0 (
    .Q(p_vy[23]),
    .D(fused_vy_q16_Z[23]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vy_23_s0.INIT=1'b0;
  DFFRE p_vy_22_s0 (
    .Q(p_vy[22]),
    .D(fused_vy_q16_Z[22]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vy_22_s0.INIT=1'b0;
  DFFRE p_vy_21_s0 (
    .Q(p_vy[21]),
    .D(fused_vy_q16_Z[21]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vy_21_s0.INIT=1'b0;
  DFFRE p_vy_20_s0 (
    .Q(p_vy[20]),
    .D(fused_vy_q16_Z[20]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vy_20_s0.INIT=1'b0;
  DFFRE p_vy_19_s0 (
    .Q(p_vy[19]),
    .D(fused_vy_q16_Z[19]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vy_19_s0.INIT=1'b0;
  DFFRE p_vy_18_s0 (
    .Q(p_vy[18]),
    .D(fused_vy_q16_Z[18]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vy_18_s0.INIT=1'b0;
  DFFRE p_vy_17_s0 (
    .Q(p_vy[17]),
    .D(fused_vy_q16_Z[17]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vy_17_s0.INIT=1'b0;
  DFFRE p_vy_16_s0 (
    .Q(p_vy[16]),
    .D(fused_vy_q16_Z[16]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vy_16_s0.INIT=1'b0;
  DFFRE p_vy_15_s0 (
    .Q(p_vy[15]),
    .D(fused_vy_q16_Z[15]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vy_15_s0.INIT=1'b0;
  DFFRE p_vy_14_s0 (
    .Q(p_vy[14]),
    .D(fused_vy_q16_Z[14]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vy_14_s0.INIT=1'b0;
  DFFRE p_vy_13_s0 (
    .Q(p_vy[13]),
    .D(fused_vy_q16_Z[13]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vy_13_s0.INIT=1'b0;
  DFFRE p_vy_12_s0 (
    .Q(p_vy[12]),
    .D(fused_vy_q16_Z[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vy_12_s0.INIT=1'b0;
  DFFRE p_vy_11_s0 (
    .Q(p_vy[11]),
    .D(fused_vy_q16_Z[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vy_11_s0.INIT=1'b0;
  DFFRE p_vy_10_s0 (
    .Q(p_vy[10]),
    .D(fused_vy_q16_Z[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vy_10_s0.INIT=1'b0;
  DFFRE p_vy_9_s0 (
    .Q(p_vy[9]),
    .D(fused_vy_q16_Z[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vy_9_s0.INIT=1'b0;
  DFFRE p_vy_8_s0 (
    .Q(p_vy[8]),
    .D(fused_vy_q16_Z[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vy_8_s0.INIT=1'b0;
  DFFRE p_vy_7_s0 (
    .Q(p_vy[7]),
    .D(fused_vy_q16_Z[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vy_7_s0.INIT=1'b0;
  DFFRE p_vy_6_s0 (
    .Q(p_vy[6]),
    .D(fused_vy_q16_Z[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vy_6_s0.INIT=1'b0;
  DFFRE p_vy_5_s0 (
    .Q(p_vy[5]),
    .D(fused_vy_q16_Z[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vy_5_s0.INIT=1'b0;
  DFFRE p_vy_4_s0 (
    .Q(p_vy[4]),
    .D(fused_vy_q16_Z[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vy_4_s0.INIT=1'b0;
  DFFRE p_vy_3_s0 (
    .Q(p_vy[3]),
    .D(fused_vy_q16_Z[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vy_3_s0.INIT=1'b0;
  DFFRE p_vy_2_s0 (
    .Q(p_vy[2]),
    .D(fused_vy_q16_Z[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vy_2_s0.INIT=1'b0;
  DFFRE p_vy_1_s0 (
    .Q(p_vy[1]),
    .D(fused_vy_q16_Z[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vy_1_s0.INIT=1'b0;
  DFFRE p_vy_0_s0 (
    .Q(p_vy[0]),
    .D(fused_vy_q16_Z[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vy_0_s0.INIT=1'b0;
  DFFRE p_height_31_s0 (
    .Q(p_height[31]),
    .D(fused_height[31]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_height_31_s0.INIT=1'b0;
  DFFRE p_height_30_s0 (
    .Q(p_height[30]),
    .D(fused_height[30]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_height_30_s0.INIT=1'b0;
  DFFRE p_height_29_s0 (
    .Q(p_height[29]),
    .D(fused_height[29]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_height_29_s0.INIT=1'b0;
  DFFRE p_height_28_s0 (
    .Q(p_height[28]),
    .D(fused_height[28]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_height_28_s0.INIT=1'b0;
  DFFRE p_height_27_s0 (
    .Q(p_height[27]),
    .D(fused_height[27]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_height_27_s0.INIT=1'b0;
  DFFRE p_height_26_s0 (
    .Q(p_height[26]),
    .D(fused_height[26]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_height_26_s0.INIT=1'b0;
  DFFRE p_height_25_s0 (
    .Q(p_height[25]),
    .D(fused_height[25]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_height_25_s0.INIT=1'b0;
  DFFRE p_height_24_s0 (
    .Q(p_height[24]),
    .D(fused_height[24]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_height_24_s0.INIT=1'b0;
  DFFRE p_height_23_s0 (
    .Q(p_height[23]),
    .D(fused_height[23]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_height_23_s0.INIT=1'b0;
  DFFRE p_height_22_s0 (
    .Q(p_height[22]),
    .D(fused_height[22]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_height_22_s0.INIT=1'b0;
  DFFRE p_height_21_s0 (
    .Q(p_height[21]),
    .D(fused_height[21]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_height_21_s0.INIT=1'b0;
  DFFRE p_height_20_s0 (
    .Q(p_height[20]),
    .D(fused_height[20]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_height_20_s0.INIT=1'b0;
  DFFRE p_height_19_s0 (
    .Q(p_height[19]),
    .D(fused_height[19]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_height_19_s0.INIT=1'b0;
  DFFRE p_height_18_s0 (
    .Q(p_height[18]),
    .D(fused_height[18]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_height_18_s0.INIT=1'b0;
  DFFRE p_height_17_s0 (
    .Q(p_height[17]),
    .D(fused_height[17]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_height_17_s0.INIT=1'b0;
  DFFRE p_height_16_s0 (
    .Q(p_height[16]),
    .D(fused_height[16]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_height_16_s0.INIT=1'b0;
  DFFRE p_height_15_s0 (
    .Q(p_height[15]),
    .D(fused_height[15]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_height_15_s0.INIT=1'b0;
  DFFRE p_height_14_s0 (
    .Q(p_height[14]),
    .D(fused_height[14]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_height_14_s0.INIT=1'b0;
  DFFRE p_height_13_s0 (
    .Q(p_height[13]),
    .D(fused_height[13]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_height_13_s0.INIT=1'b0;
  DFFRE p_height_12_s0 (
    .Q(p_height[12]),
    .D(fused_height[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_height_12_s0.INIT=1'b0;
  DFFRE p_height_11_s0 (
    .Q(p_height[11]),
    .D(fused_height[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_height_11_s0.INIT=1'b0;
  DFFRE p_height_10_s0 (
    .Q(p_height[10]),
    .D(fused_height[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_height_10_s0.INIT=1'b0;
  DFFRE p_height_9_s0 (
    .Q(p_height[9]),
    .D(fused_height[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_height_9_s0.INIT=1'b0;
  DFFRE p_height_8_s0 (
    .Q(p_height[8]),
    .D(fused_height[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_height_8_s0.INIT=1'b0;
  DFFRE p_height_7_s0 (
    .Q(p_height[7]),
    .D(fused_height[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_height_7_s0.INIT=1'b0;
  DFFRE p_height_6_s0 (
    .Q(p_height[6]),
    .D(fused_height[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_height_6_s0.INIT=1'b0;
  DFFRE p_height_5_s0 (
    .Q(p_height[5]),
    .D(fused_height[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_height_5_s0.INIT=1'b0;
  DFFRE p_height_4_s0 (
    .Q(p_height[4]),
    .D(fused_height[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_height_4_s0.INIT=1'b0;
  DFFRE p_height_3_s0 (
    .Q(p_height[3]),
    .D(fused_height[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_height_3_s0.INIT=1'b0;
  DFFRE p_height_2_s0 (
    .Q(p_height[2]),
    .D(fused_height[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_height_2_s0.INIT=1'b0;
  DFFRE p_height_1_s0 (
    .Q(p_height[1]),
    .D(fused_height[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_height_1_s0.INIT=1'b0;
  DFFRE p_height_0_s0 (
    .Q(p_height[0]),
    .D(fused_height[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_height_0_s0.INIT=1'b0;
  DFFRE p_ax_31_s0 (
    .Q(p_ax[31]),
    .D(converted_ax[31]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ax_31_s0.INIT=1'b0;
  DFFRE p_ax_30_s0 (
    .Q(p_ax[30]),
    .D(converted_ax[30]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ax_30_s0.INIT=1'b0;
  DFFRE p_ax_29_s0 (
    .Q(p_ax[29]),
    .D(converted_ax[29]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ax_29_s0.INIT=1'b0;
  DFFRE p_ax_28_s0 (
    .Q(p_ax[28]),
    .D(converted_ax[28]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ax_28_s0.INIT=1'b0;
  DFFRE p_ax_27_s0 (
    .Q(p_ax[27]),
    .D(converted_ax[27]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ax_27_s0.INIT=1'b0;
  DFFRE p_ax_26_s0 (
    .Q(p_ax[26]),
    .D(converted_ax[26]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ax_26_s0.INIT=1'b0;
  DFFRE p_ax_25_s0 (
    .Q(p_ax[25]),
    .D(converted_ax[25]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ax_25_s0.INIT=1'b0;
  DFFRE p_ax_24_s0 (
    .Q(p_ax[24]),
    .D(converted_ax[24]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ax_24_s0.INIT=1'b0;
  DFFRE p_ax_23_s0 (
    .Q(p_ax[23]),
    .D(converted_ax[23]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ax_23_s0.INIT=1'b0;
  DFFRE p_ax_22_s0 (
    .Q(p_ax[22]),
    .D(converted_ax[22]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ax_22_s0.INIT=1'b0;
  DFFRE p_ax_21_s0 (
    .Q(p_ax[21]),
    .D(converted_ax[21]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ax_21_s0.INIT=1'b0;
  DFFRE p_ax_20_s0 (
    .Q(p_ax[20]),
    .D(converted_ax[20]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ax_20_s0.INIT=1'b0;
  DFFRE p_ax_19_s0 (
    .Q(p_ax[19]),
    .D(converted_ax[19]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ax_19_s0.INIT=1'b0;
  DFFRE p_ax_18_s0 (
    .Q(p_ax[18]),
    .D(converted_ax[18]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ax_18_s0.INIT=1'b0;
  DFFRE p_ax_17_s0 (
    .Q(p_ax[17]),
    .D(converted_ax[17]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ax_17_s0.INIT=1'b0;
  DFFRE p_ax_16_s0 (
    .Q(p_ax[16]),
    .D(converted_ax[16]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ax_16_s0.INIT=1'b0;
  DFFRE p_ax_15_s0 (
    .Q(p_ax[15]),
    .D(converted_ax[15]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ax_15_s0.INIT=1'b0;
  DFFRE p_ax_14_s0 (
    .Q(p_ax[14]),
    .D(converted_ax[14]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ax_14_s0.INIT=1'b0;
  DFFRE p_ax_13_s0 (
    .Q(p_ax[13]),
    .D(converted_ax[13]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ax_13_s0.INIT=1'b0;
  DFFRE p_ax_12_s0 (
    .Q(p_ax[12]),
    .D(converted_ax[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ax_12_s0.INIT=1'b0;
  DFFRE p_ax_11_s0 (
    .Q(p_ax[11]),
    .D(converted_ax[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ax_11_s0.INIT=1'b0;
  DFFRE p_ax_10_s0 (
    .Q(p_ax[10]),
    .D(converted_ax[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ax_10_s0.INIT=1'b0;
  DFFRE p_ax_9_s0 (
    .Q(p_ax[9]),
    .D(converted_ax[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ax_9_s0.INIT=1'b0;
  DFFRE p_ax_8_s0 (
    .Q(p_ax[8]),
    .D(converted_ax[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ax_8_s0.INIT=1'b0;
  DFFRE p_ax_7_s0 (
    .Q(p_ax[7]),
    .D(converted_ax[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ax_7_s0.INIT=1'b0;
  DFFRE p_ax_6_s0 (
    .Q(p_ax[6]),
    .D(converted_ax[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ax_6_s0.INIT=1'b0;
  DFFRE p_ax_5_s0 (
    .Q(p_ax[5]),
    .D(converted_ax[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ax_5_s0.INIT=1'b0;
  DFFRE p_ax_4_s0 (
    .Q(p_ax[4]),
    .D(converted_ax[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ax_4_s0.INIT=1'b0;
  DFFRE p_ax_3_s0 (
    .Q(p_ax[3]),
    .D(converted_ax[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ax_3_s0.INIT=1'b0;
  DFFRE p_ax_2_s0 (
    .Q(p_ax[2]),
    .D(converted_ax[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ax_2_s0.INIT=1'b0;
  DFFRE p_ax_1_s0 (
    .Q(p_ax[1]),
    .D(converted_ax[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ax_1_s0.INIT=1'b0;
  DFFRE p_ax_0_s0 (
    .Q(p_ax[0]),
    .D(converted_ax[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ax_0_s0.INIT=1'b0;
  DFFRE p_ay_31_s0 (
    .Q(p_ay[31]),
    .D(converted_ay[31]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ay_31_s0.INIT=1'b0;
  DFFRE p_ay_30_s0 (
    .Q(p_ay[30]),
    .D(converted_ay[30]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ay_30_s0.INIT=1'b0;
  DFFRE p_ay_29_s0 (
    .Q(p_ay[29]),
    .D(converted_ay[29]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ay_29_s0.INIT=1'b0;
  DFFRE p_ay_28_s0 (
    .Q(p_ay[28]),
    .D(converted_ay[28]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ay_28_s0.INIT=1'b0;
  DFFRE p_ay_27_s0 (
    .Q(p_ay[27]),
    .D(converted_ay[27]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ay_27_s0.INIT=1'b0;
  DFFRE p_ay_26_s0 (
    .Q(p_ay[26]),
    .D(converted_ay[26]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ay_26_s0.INIT=1'b0;
  DFFRE p_ay_25_s0 (
    .Q(p_ay[25]),
    .D(converted_ay[25]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ay_25_s0.INIT=1'b0;
  DFFRE p_ay_24_s0 (
    .Q(p_ay[24]),
    .D(converted_ay[24]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ay_24_s0.INIT=1'b0;
  DFFRE p_ay_23_s0 (
    .Q(p_ay[23]),
    .D(converted_ay[23]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ay_23_s0.INIT=1'b0;
  DFFRE p_ay_22_s0 (
    .Q(p_ay[22]),
    .D(converted_ay[22]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ay_22_s0.INIT=1'b0;
  DFFRE p_ay_21_s0 (
    .Q(p_ay[21]),
    .D(converted_ay[21]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ay_21_s0.INIT=1'b0;
  DFFRE p_ay_20_s0 (
    .Q(p_ay[20]),
    .D(converted_ay[20]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ay_20_s0.INIT=1'b0;
  DFFRE p_ay_19_s0 (
    .Q(p_ay[19]),
    .D(converted_ay[19]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ay_19_s0.INIT=1'b0;
  DFFRE p_ay_18_s0 (
    .Q(p_ay[18]),
    .D(converted_ay[18]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ay_18_s0.INIT=1'b0;
  DFFRE p_ay_17_s0 (
    .Q(p_ay[17]),
    .D(converted_ay[17]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ay_17_s0.INIT=1'b0;
  DFFRE p_ay_16_s0 (
    .Q(p_ay[16]),
    .D(converted_ay[16]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ay_16_s0.INIT=1'b0;
  DFFRE p_ay_15_s0 (
    .Q(p_ay[15]),
    .D(converted_ay[15]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ay_15_s0.INIT=1'b0;
  DFFRE p_ay_14_s0 (
    .Q(p_ay[14]),
    .D(converted_ay[14]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ay_14_s0.INIT=1'b0;
  DFFRE p_ay_13_s0 (
    .Q(p_ay[13]),
    .D(converted_ay[13]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ay_13_s0.INIT=1'b0;
  DFFRE p_ay_12_s0 (
    .Q(p_ay[12]),
    .D(converted_ay[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ay_12_s0.INIT=1'b0;
  DFFRE p_ay_11_s0 (
    .Q(p_ay[11]),
    .D(converted_ay[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ay_11_s0.INIT=1'b0;
  DFFRE p_ay_10_s0 (
    .Q(p_ay[10]),
    .D(converted_ay[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ay_10_s0.INIT=1'b0;
  DFFRE p_ay_9_s0 (
    .Q(p_ay[9]),
    .D(converted_ay[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ay_9_s0.INIT=1'b0;
  DFFRE p_ay_8_s0 (
    .Q(p_ay[8]),
    .D(converted_ay[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ay_8_s0.INIT=1'b0;
  DFFRE p_ay_7_s0 (
    .Q(p_ay[7]),
    .D(converted_ay[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ay_7_s0.INIT=1'b0;
  DFFRE p_ay_6_s0 (
    .Q(p_ay[6]),
    .D(converted_ay[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ay_6_s0.INIT=1'b0;
  DFFRE p_ay_5_s0 (
    .Q(p_ay[5]),
    .D(converted_ay[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ay_5_s0.INIT=1'b0;
  DFFRE p_ay_4_s0 (
    .Q(p_ay[4]),
    .D(converted_ay[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ay_4_s0.INIT=1'b0;
  DFFRE p_ay_3_s0 (
    .Q(p_ay[3]),
    .D(converted_ay[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ay_3_s0.INIT=1'b0;
  DFFRE p_ay_2_s0 (
    .Q(p_ay[2]),
    .D(converted_ay[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ay_2_s0.INIT=1'b0;
  DFFRE p_ay_1_s0 (
    .Q(p_ay[1]),
    .D(converted_ay[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ay_1_s0.INIT=1'b0;
  DFFRE p_ay_0_s0 (
    .Q(p_ay[0]),
    .D(converted_ay[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ay_0_s0.INIT=1'b0;
  DFFRE p_az_31_s0 (
    .Q(p_az[31]),
    .D(height_sample_az[31]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_az_31_s0.INIT=1'b0;
  DFFRE p_az_14_s0 (
    .Q(p_az[14]),
    .D(height_sample_az[14]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_az_14_s0.INIT=1'b0;
  DFFRE p_az_13_s0 (
    .Q(p_az[13]),
    .D(height_sample_az[13]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_az_13_s0.INIT=1'b0;
  DFFRE p_az_12_s0 (
    .Q(p_az[12]),
    .D(height_sample_az[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_az_12_s0.INIT=1'b0;
  DFFRE p_az_11_s0 (
    .Q(p_az[11]),
    .D(height_sample_az[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_az_11_s0.INIT=1'b0;
  DFFRE p_az_10_s0 (
    .Q(p_az[10]),
    .D(height_sample_az[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_az_10_s0.INIT=1'b0;
  DFFRE p_az_9_s0 (
    .Q(p_az[9]),
    .D(height_sample_az[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_az_9_s0.INIT=1'b0;
  DFFRE p_az_8_s0 (
    .Q(p_az[8]),
    .D(height_sample_az[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_az_8_s0.INIT=1'b0;
  DFFRE p_az_7_s0 (
    .Q(p_az[7]),
    .D(height_sample_az[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_az_7_s0.INIT=1'b0;
  DFFRE p_az_6_s0 (
    .Q(p_az[6]),
    .D(height_sample_az[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_az_6_s0.INIT=1'b0;
  DFFRE p_az_5_s0 (
    .Q(p_az[5]),
    .D(height_sample_az[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_az_5_s0.INIT=1'b0;
  DFFRE p_az_4_s0 (
    .Q(p_az[4]),
    .D(height_sample_az[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_az_4_s0.INIT=1'b0;
  DFFRE p_az_3_s0 (
    .Q(p_az[3]),
    .D(height_sample_az[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_az_3_s0.INIT=1'b0;
  DFFRE p_az_2_s0 (
    .Q(p_az[2]),
    .D(height_sample_az[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_az_2_s0.INIT=1'b0;
  DFFRE p_az_1_s0 (
    .Q(p_az[1]),
    .D(height_sample_az[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_az_1_s0.INIT=1'b0;
  DFFRE p_az_0_s0 (
    .Q(p_az[0]),
    .D(height_sample_az[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_az_0_s0.INIT=1'b0;
  DFFRE p_yaw_15_s0 (
    .Q(p_yaw[15]),
    .D(body_yaw[15]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_yaw_15_s0.INIT=1'b0;
  DFFRE p_yaw_14_s0 (
    .Q(p_yaw[14]),
    .D(body_yaw[14]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_yaw_14_s0.INIT=1'b0;
  DFFRE p_yaw_13_s0 (
    .Q(p_yaw[13]),
    .D(body_yaw[13]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_yaw_13_s0.INIT=1'b0;
  DFFRE p_yaw_12_s0 (
    .Q(p_yaw[12]),
    .D(body_yaw[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_yaw_12_s0.INIT=1'b0;
  DFFRE p_yaw_11_s0 (
    .Q(p_yaw[11]),
    .D(body_yaw[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_yaw_11_s0.INIT=1'b0;
  DFFRE p_yaw_10_s0 (
    .Q(p_yaw[10]),
    .D(body_yaw[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_yaw_10_s0.INIT=1'b0;
  DFFRE p_yaw_9_s0 (
    .Q(p_yaw[9]),
    .D(body_yaw[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_yaw_9_s0.INIT=1'b0;
  DFFRE p_yaw_8_s0 (
    .Q(p_yaw[8]),
    .D(body_yaw[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_yaw_8_s0.INIT=1'b0;
  DFFRE p_yaw_7_s0 (
    .Q(p_yaw[7]),
    .D(body_yaw[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_yaw_7_s0.INIT=1'b0;
  DFFRE p_yaw_6_s0 (
    .Q(p_yaw[6]),
    .D(body_yaw[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_yaw_6_s0.INIT=1'b0;
  DFFRE p_yaw_5_s0 (
    .Q(p_yaw[5]),
    .D(body_yaw[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_yaw_5_s0.INIT=1'b0;
  DFFRE p_yaw_4_s0 (
    .Q(p_yaw[4]),
    .D(body_yaw[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_yaw_4_s0.INIT=1'b0;
  DFFRE p_yaw_3_s0 (
    .Q(p_yaw[3]),
    .D(body_yaw[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_yaw_3_s0.INIT=1'b0;
  DFFRE p_yaw_2_s0 (
    .Q(p_yaw[2]),
    .D(body_yaw[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_yaw_2_s0.INIT=1'b0;
  DFFRE p_yaw_1_s0 (
    .Q(p_yaw[1]),
    .D(body_yaw[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_yaw_1_s0.INIT=1'b0;
  DFFRE p_yaw_0_s0 (
    .Q(p_yaw[0]),
    .D(sensor_yaw[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_yaw_0_s0.INIT=1'b0;
  DFFRE p_channel_count_3_s0 (
    .Q(p_channel_count[3]),
    .D(channels[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_channel_count_3_s0.INIT=1'b0;
  DFFRE p_channel_count_2_s0 (
    .Q(p_channel_count[2]),
    .D(channels[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_channel_count_2_s0.INIT=1'b0;
  DFFRE p_channel_count_1_s0 (
    .Q(p_channel_count[1]),
    .D(channels[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_channel_count_1_s0.INIT=1'b0;
  DFFRE p_channel_count_0_s0 (
    .Q(p_channel_count[0]),
    .D(channels[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_channel_count_0_s0.INIT=1'b0;
  DFFRE p_ch1_11_s0 (
    .Q(p_ch1[11]),
    .D(core_body_827),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch1_11_s0.INIT=1'b0;
  DFFRE p_ch1_10_s0 (
    .Q(p_ch1[10]),
    .D(core_body_826),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch1_10_s0.INIT=1'b0;
  DFFRE p_ch1_9_s0 (
    .Q(p_ch1[9]),
    .D(core_body_825),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch1_9_s0.INIT=1'b0;
  DFFRE p_ch1_8_s0 (
    .Q(p_ch1[8]),
    .D(core_body_824),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch1_8_s0.INIT=1'b0;
  DFFRE p_ch1_7_s0 (
    .Q(p_ch1[7]),
    .D(core_body_823),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch1_7_s0.INIT=1'b0;
  DFFRE p_ch1_6_s0 (
    .Q(p_ch1[6]),
    .D(core_body_822),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch1_6_s0.INIT=1'b0;
  DFFRE p_ch1_5_s0 (
    .Q(p_ch1[5]),
    .D(core_body_821),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch1_5_s0.INIT=1'b0;
  DFFRE p_ch1_4_s0 (
    .Q(p_ch1[4]),
    .D(core_body_820),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch1_4_s0.INIT=1'b0;
  DFFRE p_ch1_3_s0 (
    .Q(p_ch1[3]),
    .D(core_body_819),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch1_3_s0.INIT=1'b0;
  DFFRE p_ch1_2_s0 (
    .Q(p_ch1[2]),
    .D(core_body_818),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch1_2_s0.INIT=1'b0;
  DFFRE p_ch1_1_s0 (
    .Q(p_ch1[1]),
    .D(core_body_817),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch1_1_s0.INIT=1'b0;
  DFFRE p_ch1_0_s0 (
    .Q(p_ch1[0]),
    .D(core_body_816),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch1_0_s0.INIT=1'b0;
  DFFRE p_ch2_11_s0 (
    .Q(p_ch2[11]),
    .D(core_body_811),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch2_11_s0.INIT=1'b0;
  DFFRE p_ch2_10_s0 (
    .Q(p_ch2[10]),
    .D(core_body_810),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch2_10_s0.INIT=1'b0;
  DFFRE p_ch2_9_s0 (
    .Q(p_ch2[9]),
    .D(core_body_809),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch2_9_s0.INIT=1'b0;
  DFFRE p_ch2_8_s0 (
    .Q(p_ch2[8]),
    .D(core_body_808),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch2_8_s0.INIT=1'b0;
  DFFRE p_ch2_7_s0 (
    .Q(p_ch2[7]),
    .D(core_body_807),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch2_7_s0.INIT=1'b0;
  DFFRE p_ch2_6_s0 (
    .Q(p_ch2[6]),
    .D(core_body_806),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch2_6_s0.INIT=1'b0;
  DFFRE p_ch2_5_s0 (
    .Q(p_ch2[5]),
    .D(core_body_805),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch2_5_s0.INIT=1'b0;
  DFFRE p_ch2_4_s0 (
    .Q(p_ch2[4]),
    .D(core_body_804),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch2_4_s0.INIT=1'b0;
  DFFRE p_ch2_3_s0 (
    .Q(p_ch2[3]),
    .D(core_body_803),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch2_3_s0.INIT=1'b0;
  DFFRE p_ch2_2_s0 (
    .Q(p_ch2[2]),
    .D(core_body_802),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch2_2_s0.INIT=1'b0;
  DFFRE p_ch2_1_s0 (
    .Q(p_ch2[1]),
    .D(core_body_801),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch2_1_s0.INIT=1'b0;
  DFFRE p_ch2_0_s0 (
    .Q(p_ch2[0]),
    .D(core_body_800),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch2_0_s0.INIT=1'b0;
  DFFRE p_ch3_11_s0 (
    .Q(p_ch3[11]),
    .D(core_body_795),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch3_11_s0.INIT=1'b0;
  DFFRE p_ch3_10_s0 (
    .Q(p_ch3[10]),
    .D(core_body_794),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch3_10_s0.INIT=1'b0;
  DFFRE p_ch3_9_s0 (
    .Q(p_ch3[9]),
    .D(core_body_793),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch3_9_s0.INIT=1'b0;
  DFFRE p_ch3_8_s0 (
    .Q(p_ch3[8]),
    .D(core_body_792),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch3_8_s0.INIT=1'b0;
  DFFRE p_ch3_7_s0 (
    .Q(p_ch3[7]),
    .D(core_body_791),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch3_7_s0.INIT=1'b0;
  DFFRE p_ch3_6_s0 (
    .Q(p_ch3[6]),
    .D(core_body_790),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch3_6_s0.INIT=1'b0;
  DFFRE p_ch3_5_s0 (
    .Q(p_ch3[5]),
    .D(core_body_789),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch3_5_s0.INIT=1'b0;
  DFFRE p_ch3_4_s0 (
    .Q(p_ch3[4]),
    .D(core_body_788),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch3_4_s0.INIT=1'b0;
  DFFRE p_ch3_3_s0 (
    .Q(p_ch3[3]),
    .D(core_body_787),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch3_3_s0.INIT=1'b0;
  DFFRE p_ch3_2_s0 (
    .Q(p_ch3[2]),
    .D(core_body_786),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch3_2_s0.INIT=1'b0;
  DFFRE p_ch3_1_s0 (
    .Q(p_ch3[1]),
    .D(core_body_785),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch3_1_s0.INIT=1'b0;
  DFFRE p_ch3_0_s0 (
    .Q(p_ch3[0]),
    .D(core_body_784),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch3_0_s0.INIT=1'b0;
  DFFRE p_ch7_11_s0 (
    .Q(p_ch7[11]),
    .D(ch7_Z[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch7_11_s0.INIT=1'b0;
  DFFRE p_ch7_10_s0 (
    .Q(p_ch7[10]),
    .D(ch7_Z[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch7_10_s0.INIT=1'b0;
  DFFRE p_ch7_9_s0 (
    .Q(p_ch7[9]),
    .D(ch7_Z[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch7_9_s0.INIT=1'b0;
  DFFRE p_ch7_8_s0 (
    .Q(p_ch7[8]),
    .D(ch7_Z[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch7_8_s0.INIT=1'b0;
  DFFRE p_ch7_7_s0 (
    .Q(p_ch7[7]),
    .D(ch7_Z[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch7_7_s0.INIT=1'b0;
  DFFRE p_ch7_6_s0 (
    .Q(p_ch7[6]),
    .D(ch7_Z[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch7_6_s0.INIT=1'b0;
  DFFRE p_ch7_5_s0 (
    .Q(p_ch7[5]),
    .D(ch7_Z[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch7_5_s0.INIT=1'b0;
  DFFRE p_ch7_4_s0 (
    .Q(p_ch7[4]),
    .D(ch7_Z[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch7_4_s0.INIT=1'b0;
  DFFRE p_ch7_3_s0 (
    .Q(p_ch7[3]),
    .D(ch7_Z[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch7_3_s0.INIT=1'b0;
  DFFRE p_ch7_2_s0 (
    .Q(p_ch7[2]),
    .D(ch7_Z[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch7_2_s0.INIT=1'b0;
  DFFRE p_ch7_1_s0 (
    .Q(p_ch7[1]),
    .D(ch7_Z[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch7_1_s0.INIT=1'b0;
  DFFRE p_ch7_0_s0 (
    .Q(p_ch7[0]),
    .D(ch7_Z[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_ch7_0_s0.INIT=1'b0;
  DFFRE p_height_update_s0 (
    .Q(p_height_update),
    .D(height_fusion_update),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_height_update_s0.INIT=1'b0;
  DFFRE p_sample_update_s0 (
    .Q(p_sample_update),
    .D(acceleration_update),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_sample_update_s0.INIT=1'b0;
  DFFRE p_sample_dt_31_s0 (
    .Q(p_sample_dt[31]),
    .D(converted_dt_us[31]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_sample_dt_31_s0.INIT=1'b0;
  DFFRE p_sample_dt_30_s0 (
    .Q(p_sample_dt[30]),
    .D(converted_dt_us[30]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_sample_dt_30_s0.INIT=1'b0;
  DFFRE p_sample_dt_29_s0 (
    .Q(p_sample_dt[29]),
    .D(converted_dt_us[29]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_sample_dt_29_s0.INIT=1'b0;
  DFFRE p_sample_dt_28_s0 (
    .Q(p_sample_dt[28]),
    .D(converted_dt_us[28]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_sample_dt_28_s0.INIT=1'b0;
  DFFRE p_sample_dt_27_s0 (
    .Q(p_sample_dt[27]),
    .D(converted_dt_us[27]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_sample_dt_27_s0.INIT=1'b0;
  DFFRE p_sample_dt_26_s0 (
    .Q(p_sample_dt[26]),
    .D(converted_dt_us[26]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_sample_dt_26_s0.INIT=1'b0;
  DFFRE p_sample_dt_25_s0 (
    .Q(p_sample_dt[25]),
    .D(converted_dt_us[25]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_sample_dt_25_s0.INIT=1'b0;
  DFFRE p_sample_dt_24_s0 (
    .Q(p_sample_dt[24]),
    .D(converted_dt_us[24]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_sample_dt_24_s0.INIT=1'b0;
  DFFRE p_sample_dt_23_s0 (
    .Q(p_sample_dt[23]),
    .D(converted_dt_us[23]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_sample_dt_23_s0.INIT=1'b0;
  DFFRE p_sample_dt_22_s0 (
    .Q(p_sample_dt[22]),
    .D(converted_dt_us[22]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_sample_dt_22_s0.INIT=1'b0;
  DFFRE p_sample_dt_21_s0 (
    .Q(p_sample_dt[21]),
    .D(converted_dt_us[21]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_sample_dt_21_s0.INIT=1'b0;
  DFFRE p_sample_dt_20_s0 (
    .Q(p_sample_dt[20]),
    .D(converted_dt_us[20]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_sample_dt_20_s0.INIT=1'b0;
  DFFRE p_sample_dt_19_s0 (
    .Q(p_sample_dt[19]),
    .D(converted_dt_us[19]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_sample_dt_19_s0.INIT=1'b0;
  DFFRE p_sample_dt_18_s0 (
    .Q(p_sample_dt[18]),
    .D(converted_dt_us[18]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_sample_dt_18_s0.INIT=1'b0;
  DFFRE p_sample_dt_17_s0 (
    .Q(p_sample_dt[17]),
    .D(converted_dt_us[17]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_sample_dt_17_s0.INIT=1'b0;
  DFFRE p_sample_dt_16_s0 (
    .Q(p_sample_dt[16]),
    .D(converted_dt_us[16]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_sample_dt_16_s0.INIT=1'b0;
  DFFRE p_sample_dt_15_s0 (
    .Q(p_sample_dt[15]),
    .D(converted_dt_us[15]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_sample_dt_15_s0.INIT=1'b0;
  DFFRE p_sample_dt_14_s0 (
    .Q(p_sample_dt[14]),
    .D(converted_dt_us[14]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_sample_dt_14_s0.INIT=1'b0;
  DFFRE p_sample_dt_13_s0 (
    .Q(p_sample_dt[13]),
    .D(converted_dt_us[13]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_sample_dt_13_s0.INIT=1'b0;
  DFFRE p_sample_dt_12_s0 (
    .Q(p_sample_dt[12]),
    .D(converted_dt_us[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_sample_dt_12_s0.INIT=1'b0;
  DFFRE p_sample_dt_11_s0 (
    .Q(p_sample_dt[11]),
    .D(converted_dt_us[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_sample_dt_11_s0.INIT=1'b0;
  DFFRE p_sample_dt_10_s0 (
    .Q(p_sample_dt[10]),
    .D(converted_dt_us[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_sample_dt_10_s0.INIT=1'b0;
  DFFRE p_sample_dt_9_s0 (
    .Q(p_sample_dt[9]),
    .D(converted_dt_us[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_sample_dt_9_s0.INIT=1'b0;
  DFFRE p_sample_dt_8_s0 (
    .Q(p_sample_dt[8]),
    .D(converted_dt_us[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_sample_dt_8_s0.INIT=1'b0;
  DFFRE p_sample_dt_7_s0 (
    .Q(p_sample_dt[7]),
    .D(converted_dt_us[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_sample_dt_7_s0.INIT=1'b0;
  DFFRE p_sample_dt_6_s0 (
    .Q(p_sample_dt[6]),
    .D(converted_dt_us[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_sample_dt_6_s0.INIT=1'b0;
  DFFRE p_sample_dt_5_s0 (
    .Q(p_sample_dt[5]),
    .D(converted_dt_us[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_sample_dt_5_s0.INIT=1'b0;
  DFFRE p_sample_dt_4_s0 (
    .Q(p_sample_dt[4]),
    .D(converted_dt_us[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_sample_dt_4_s0.INIT=1'b0;
  DFFRE p_sample_dt_3_s0 (
    .Q(p_sample_dt[3]),
    .D(converted_dt_us[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_sample_dt_3_s0.INIT=1'b0;
  DFFRE p_sample_dt_2_s0 (
    .Q(p_sample_dt[2]),
    .D(converted_dt_us[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_sample_dt_2_s0.INIT=1'b0;
  DFFRE p_sample_dt_1_s0 (
    .Q(p_sample_dt[1]),
    .D(converted_dt_us[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_sample_dt_1_s0.INIT=1'b0;
  DFFRE p_sample_dt_0_s0 (
    .Q(p_sample_dt[0]),
    .D(converted_dt_us[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_sample_dt_0_s0.INIT=1'b0;
  DFFRE p_vz_31_s0 (
    .Q(p_vz[31]),
    .D(fused_vz_q16[31]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vz_31_s0.INIT=1'b0;
  DFFRE p_vz_30_s0 (
    .Q(p_vz[30]),
    .D(fused_vz_q16[30]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vz_30_s0.INIT=1'b0;
  DFFRE p_vz_29_s0 (
    .Q(p_vz[29]),
    .D(fused_vz_q16[29]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vz_29_s0.INIT=1'b0;
  DFFRE p_vz_28_s0 (
    .Q(p_vz[28]),
    .D(fused_vz_q16[28]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vz_28_s0.INIT=1'b0;
  DFFRE p_vz_27_s0 (
    .Q(p_vz[27]),
    .D(fused_vz_q16[27]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vz_27_s0.INIT=1'b0;
  DFFRE p_vz_26_s0 (
    .Q(p_vz[26]),
    .D(fused_vz_q16[26]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vz_26_s0.INIT=1'b0;
  DFFRE p_vz_25_s0 (
    .Q(p_vz[25]),
    .D(fused_vz_q16[25]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vz_25_s0.INIT=1'b0;
  DFFRE p_vz_24_s0 (
    .Q(p_vz[24]),
    .D(fused_vz_q16[24]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vz_24_s0.INIT=1'b0;
  DFFRE p_vz_23_s0 (
    .Q(p_vz[23]),
    .D(fused_vz_q16[23]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vz_23_s0.INIT=1'b0;
  DFFRE p_vz_22_s0 (
    .Q(p_vz[22]),
    .D(fused_vz_q16[22]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vz_22_s0.INIT=1'b0;
  DFFRE p_vz_21_s0 (
    .Q(p_vz[21]),
    .D(fused_vz_q16[21]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vz_21_s0.INIT=1'b0;
  DFFRE p_vz_20_s0 (
    .Q(p_vz[20]),
    .D(fused_vz_q16[20]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vz_20_s0.INIT=1'b0;
  DFFRE p_vz_19_s0 (
    .Q(p_vz[19]),
    .D(fused_vz_q16[19]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vz_19_s0.INIT=1'b0;
  DFFRE p_vz_18_s0 (
    .Q(p_vz[18]),
    .D(fused_vz_q16[18]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vz_18_s0.INIT=1'b0;
  DFFRE p_vz_17_s0 (
    .Q(p_vz[17]),
    .D(fused_vz_q16[17]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vz_17_s0.INIT=1'b0;
  DFFRE p_vz_16_s0 (
    .Q(p_vz[16]),
    .D(fused_vz_q16[16]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vz_16_s0.INIT=1'b0;
  DFFRE p_vz_15_s0 (
    .Q(p_vz[15]),
    .D(fused_vz_q16[15]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vz_15_s0.INIT=1'b0;
  DFFRE p_vz_14_s0 (
    .Q(p_vz[14]),
    .D(fused_vz_q16[14]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vz_14_s0.INIT=1'b0;
  DFFRE p_vz_13_s0 (
    .Q(p_vz[13]),
    .D(fused_vz_q16[13]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vz_13_s0.INIT=1'b0;
  DFFRE p_vz_12_s0 (
    .Q(p_vz[12]),
    .D(fused_vz_q16[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vz_12_s0.INIT=1'b0;
  DFFRE p_vz_11_s0 (
    .Q(p_vz[11]),
    .D(fused_vz_q16[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vz_11_s0.INIT=1'b0;
  DFFRE p_vz_10_s0 (
    .Q(p_vz[10]),
    .D(fused_vz_q16[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vz_10_s0.INIT=1'b0;
  DFFRE p_vz_9_s0 (
    .Q(p_vz[9]),
    .D(fused_vz_q16[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vz_9_s0.INIT=1'b0;
  DFFRE p_vz_8_s0 (
    .Q(p_vz[8]),
    .D(fused_vz_q16[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vz_8_s0.INIT=1'b0;
  DFFRE p_vz_7_s0 (
    .Q(p_vz[7]),
    .D(fused_vz_q16[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vz_7_s0.INIT=1'b0;
  DFFRE p_vz_6_s0 (
    .Q(p_vz[6]),
    .D(fused_vz_q16[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vz_6_s0.INIT=1'b0;
  DFFRE p_vz_5_s0 (
    .Q(p_vz[5]),
    .D(fused_vz_q16[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vz_5_s0.INIT=1'b0;
  DFFRE p_vz_4_s0 (
    .Q(p_vz[4]),
    .D(fused_vz_q16[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vz_4_s0.INIT=1'b0;
  DFFRE p_vz_3_s0 (
    .Q(p_vz[3]),
    .D(fused_vz_q16[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vz_3_s0.INIT=1'b0;
  DFFRE p_vz_2_s0 (
    .Q(p_vz[2]),
    .D(fused_vz_q16[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vz_2_s0.INIT=1'b0;
  DFFRE p_vz_1_s0 (
    .Q(p_vz[1]),
    .D(fused_vz_q16[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vz_1_s0.INIT=1'b0;
  DFFRE p_vz_0_s0 (
    .Q(p_vz[0]),
    .D(fused_vz_q16[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_vz_0_s0.INIT=1'b0;
  DFFRE p_collective_15_s0 (
    .Q(p_collective[15]),
    .D(base_throttle_us_Z_15),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_collective_15_s0.INIT=1'b0;
  DFFRE p_collective_11_s0 (
    .Q(p_collective[11]),
    .D(base_throttle_us_Z_11),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_collective_11_s0.INIT=1'b0;
  DFFRE p_collective_10_s0 (
    .Q(p_collective[10]),
    .D(base_throttle_us_Z_10),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_collective_10_s0.INIT=1'b0;
  DFFRE p_collective_9_s0 (
    .Q(p_collective[9]),
    .D(base_throttle_us_Z_9),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_collective_9_s0.INIT=1'b0;
  DFFRE p_collective_8_s0 (
    .Q(p_collective[8]),
    .D(base_throttle_us_Z_8),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_collective_8_s0.INIT=1'b0;
  DFFRE p_collective_7_s0 (
    .Q(p_collective[7]),
    .D(base_throttle_us_Z_7),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_collective_7_s0.INIT=1'b0;
  DFFRE p_collective_6_s0 (
    .Q(p_collective[6]),
    .D(base_throttle_us_Z_6),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_collective_6_s0.INIT=1'b0;
  DFFRE p_collective_5_s0 (
    .Q(p_collective[5]),
    .D(base_throttle_us_Z_5),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_collective_5_s0.INIT=1'b0;
  DFFRE p_collective_4_s0 (
    .Q(p_collective[4]),
    .D(base_throttle_us_Z_4),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_collective_4_s0.INIT=1'b0;
  DFFRE p_collective_3_s0 (
    .Q(p_collective[3]),
    .D(base_throttle_us_Z_3),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_collective_3_s0.INIT=1'b0;
  DFFRE p_collective_2_s0 (
    .Q(p_collective[2]),
    .D(base_throttle_us_Z_2),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_collective_2_s0.INIT=1'b0;
  DFFRE p_collective_1_s0 (
    .Q(p_collective[1]),
    .D(base_throttle_us_Z_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_collective_1_s0.INIT=1'b0;
  DFFRE p_collective_0_s0 (
    .Q(p_collective[0]),
    .D(base_throttle_us_Z_0),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam p_collective_0_s0.INIT=1'b0;
  DFFRE position_tick_s0 (
    .Q(position_tick),
    .D(n2750_3),
    .CLK(clk50_d),
    .RESET(n2737_7),
    .CE(VCC) 
);
defparam position_tick_s0.INIT=1'b0;
  DFFRE position_timer_19_s0 (
    .Q(position_timer[19]),
    .D(n2752_1),
    .CLK(clk50_d),
    .RESET(n10579_5),
    .CE(VCC) 
);
defparam position_timer_19_s0.INIT=1'b0;
  DFFRE position_timer_18_s0 (
    .Q(position_timer[18]),
    .D(n2753_1),
    .CLK(clk50_d),
    .RESET(n10579_5),
    .CE(VCC) 
);
defparam position_timer_18_s0.INIT=1'b0;
  DFFRE position_timer_17_s0 (
    .Q(position_timer[17]),
    .D(n2754_1),
    .CLK(clk50_d),
    .RESET(n10579_5),
    .CE(VCC) 
);
defparam position_timer_17_s0.INIT=1'b0;
  DFFRE position_timer_16_s0 (
    .Q(position_timer[16]),
    .D(n2755_1),
    .CLK(clk50_d),
    .RESET(n10579_5),
    .CE(VCC) 
);
defparam position_timer_16_s0.INIT=1'b0;
  DFFRE position_timer_15_s0 (
    .Q(position_timer[15]),
    .D(n2756_1),
    .CLK(clk50_d),
    .RESET(n10579_5),
    .CE(VCC) 
);
defparam position_timer_15_s0.INIT=1'b0;
  DFFRE position_timer_14_s0 (
    .Q(position_timer[14]),
    .D(n2757_1),
    .CLK(clk50_d),
    .RESET(n10579_5),
    .CE(VCC) 
);
defparam position_timer_14_s0.INIT=1'b0;
  DFFRE position_timer_13_s0 (
    .Q(position_timer[13]),
    .D(n2758_1),
    .CLK(clk50_d),
    .RESET(n10579_5),
    .CE(VCC) 
);
defparam position_timer_13_s0.INIT=1'b0;
  DFFRE position_timer_12_s0 (
    .Q(position_timer[12]),
    .D(n2759_1),
    .CLK(clk50_d),
    .RESET(n10579_5),
    .CE(VCC) 
);
defparam position_timer_12_s0.INIT=1'b0;
  DFFRE position_timer_11_s0 (
    .Q(position_timer[11]),
    .D(n2760_1),
    .CLK(clk50_d),
    .RESET(n10579_5),
    .CE(VCC) 
);
defparam position_timer_11_s0.INIT=1'b0;
  DFFRE position_timer_10_s0 (
    .Q(position_timer[10]),
    .D(n2761_1),
    .CLK(clk50_d),
    .RESET(n10579_5),
    .CE(VCC) 
);
defparam position_timer_10_s0.INIT=1'b0;
  DFFRE position_timer_9_s0 (
    .Q(position_timer[9]),
    .D(n2762_1),
    .CLK(clk50_d),
    .RESET(n10579_5),
    .CE(VCC) 
);
defparam position_timer_9_s0.INIT=1'b0;
  DFFRE position_timer_8_s0 (
    .Q(position_timer[8]),
    .D(n2763_1),
    .CLK(clk50_d),
    .RESET(n10579_5),
    .CE(VCC) 
);
defparam position_timer_8_s0.INIT=1'b0;
  DFFRE position_timer_7_s0 (
    .Q(position_timer[7]),
    .D(n2764_1),
    .CLK(clk50_d),
    .RESET(n10579_5),
    .CE(VCC) 
);
defparam position_timer_7_s0.INIT=1'b0;
  DFFRE position_timer_6_s0 (
    .Q(position_timer[6]),
    .D(n2765_1),
    .CLK(clk50_d),
    .RESET(n10579_5),
    .CE(VCC) 
);
defparam position_timer_6_s0.INIT=1'b0;
  DFFRE position_timer_5_s0 (
    .Q(position_timer[5]),
    .D(n2766_1),
    .CLK(clk50_d),
    .RESET(n10579_5),
    .CE(VCC) 
);
defparam position_timer_5_s0.INIT=1'b0;
  DFFRE position_timer_4_s0 (
    .Q(position_timer[4]),
    .D(n2767_1),
    .CLK(clk50_d),
    .RESET(n10579_5),
    .CE(VCC) 
);
defparam position_timer_4_s0.INIT=1'b0;
  DFFRE position_timer_3_s0 (
    .Q(position_timer[3]),
    .D(n2768_1),
    .CLK(clk50_d),
    .RESET(n10579_5),
    .CE(VCC) 
);
defparam position_timer_3_s0.INIT=1'b0;
  DFFRE position_timer_2_s0 (
    .Q(position_timer[2]),
    .D(n2769_1),
    .CLK(clk50_d),
    .RESET(n10579_5),
    .CE(VCC) 
);
defparam position_timer_2_s0.INIT=1'b0;
  DFFRE position_timer_1_s0 (
    .Q(position_timer[1]),
    .D(n2770_1),
    .CLK(clk50_d),
    .RESET(n10579_5),
    .CE(VCC) 
);
defparam position_timer_1_s0.INIT=1'b0;
  DFFRE position_timer_0_s0 (
    .Q(position_timer[0]),
    .D(n2771_6),
    .CLK(clk50_d),
    .RESET(n10579_5),
    .CE(VCC) 
);
defparam position_timer_0_s0.INIT=1'b0;
  DFFRE c_position_valid_s0 (
    .Q(c_position_valid),
    .D(p_live),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_position_valid_s0.INIT=1'b0;
  DFFRE c_position_update_s0 (
    .Q(c_position_update),
    .D(n3022_3),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_position_update_s0.INIT=1'b0;
  DFFRE c_height_valid_s0 (
    .Q(c_height_valid),
    .D(p_height_valid),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_height_valid_s0.INIT=1'b0;
  DFFRE c_acc_valid_s0 (
    .Q(c_acc_valid),
    .D(p_acc_valid),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_acc_valid_s0.INIT=1'b0;
  DFFRE c_rc_valid_s0 (
    .Q(controller_z_requested),
    .D(p_rc_valid),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_rc_valid_s0.INIT=1'b0;
  DFFRE c_enabled_s0 (
    .Q(c_enabled),
    .D(p_enabled),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_enabled_s0.INIT=1'b0;
  DFFRE c_observation_epoch_7_s0 (
    .Q(c_observation_epoch[7]),
    .D(p_observation_epoch[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_observation_epoch_7_s0.INIT=1'b0;
  DFFRE c_observation_epoch_6_s0 (
    .Q(c_observation_epoch[6]),
    .D(observation_epoch[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_observation_epoch_6_s0.INIT=1'b0;
  DFFRE c_observation_epoch_5_s0 (
    .Q(c_observation_epoch[5]),
    .D(observation_epoch[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_observation_epoch_5_s0.INIT=1'b0;
  DFFRE c_observation_epoch_4_s0 (
    .Q(c_observation_epoch[4]),
    .D(observation_epoch[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_observation_epoch_4_s0.INIT=1'b0;
  DFFRE c_observation_epoch_3_s0 (
    .Q(c_observation_epoch[3]),
    .D(observation_epoch[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_observation_epoch_3_s0.INIT=1'b0;
  DFFRE c_observation_epoch_2_s0 (
    .Q(c_observation_epoch[2]),
    .D(observation_epoch[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_observation_epoch_2_s0.INIT=1'b0;
  DFFRE c_observation_epoch_1_s0 (
    .Q(c_observation_epoch[1]),
    .D(observation_epoch[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_observation_epoch_1_s0.INIT=1'b0;
  DFFRE c_observation_epoch_0_s0 (
    .Q(c_observation_epoch[0]),
    .D(observation_epoch[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_observation_epoch_0_s0.INIT=1'b0;
  DFFRE c_control_epoch_7_s0 (
    .Q(c_control_epoch[7]),
    .D(control_epoch[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_control_epoch_7_s0.INIT=1'b0;
  DFFRE c_control_epoch_6_s0 (
    .Q(c_control_epoch[6]),
    .D(control_epoch[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_control_epoch_6_s0.INIT=1'b0;
  DFFRE c_control_epoch_5_s0 (
    .Q(c_control_epoch[5]),
    .D(control_epoch[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_control_epoch_5_s0.INIT=1'b0;
  DFFRE c_control_epoch_4_s0 (
    .Q(c_control_epoch[4]),
    .D(control_epoch[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_control_epoch_4_s0.INIT=1'b0;
  DFFRE c_control_epoch_3_s0 (
    .Q(c_control_epoch[3]),
    .D(control_epoch[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_control_epoch_3_s0.INIT=1'b0;
  DFFRE c_control_epoch_2_s0 (
    .Q(c_control_epoch[2]),
    .D(control_epoch[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_control_epoch_2_s0.INIT=1'b0;
  DFFRE c_control_epoch_1_s0 (
    .Q(c_control_epoch[1]),
    .D(control_epoch[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_control_epoch_1_s0.INIT=1'b0;
  DFFRE c_control_epoch_0_s0 (
    .Q(c_control_epoch[0]),
    .D(control_epoch[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_control_epoch_0_s0.INIT=1'b0;
  DFFSE c_position_age_31_s0 (
    .Q(c_position_age[31]),
    .D(n759_2),
    .CLK(clk50_d),
    .SET(n3190_6),
    .CE(VCC) 
);
defparam c_position_age_31_s0.INIT=1'b1;
  DFFSE c_position_age_30_s0 (
    .Q(c_position_age[30]),
    .D(n760_2),
    .CLK(clk50_d),
    .SET(n3190_6),
    .CE(VCC) 
);
defparam c_position_age_30_s0.INIT=1'b1;
  DFFSE c_position_age_29_s0 (
    .Q(c_position_age[29]),
    .D(n761_2),
    .CLK(clk50_d),
    .SET(n3190_6),
    .CE(VCC) 
);
defparam c_position_age_29_s0.INIT=1'b1;
  DFFSE c_position_age_28_s0 (
    .Q(c_position_age[28]),
    .D(n762_2),
    .CLK(clk50_d),
    .SET(n3190_6),
    .CE(VCC) 
);
defparam c_position_age_28_s0.INIT=1'b1;
  DFFSE c_position_age_27_s0 (
    .Q(c_position_age[27]),
    .D(n763_2),
    .CLK(clk50_d),
    .SET(n3190_6),
    .CE(VCC) 
);
defparam c_position_age_27_s0.INIT=1'b1;
  DFFSE c_position_age_26_s0 (
    .Q(c_position_age[26]),
    .D(n764_2),
    .CLK(clk50_d),
    .SET(n3190_6),
    .CE(VCC) 
);
defparam c_position_age_26_s0.INIT=1'b1;
  DFFSE c_position_age_25_s0 (
    .Q(c_position_age[25]),
    .D(n765_2),
    .CLK(clk50_d),
    .SET(n3190_6),
    .CE(VCC) 
);
defparam c_position_age_25_s0.INIT=1'b1;
  DFFSE c_position_age_24_s0 (
    .Q(c_position_age[24]),
    .D(n766_2),
    .CLK(clk50_d),
    .SET(n3190_6),
    .CE(VCC) 
);
defparam c_position_age_24_s0.INIT=1'b1;
  DFFSE c_position_age_23_s0 (
    .Q(c_position_age[23]),
    .D(n767_2),
    .CLK(clk50_d),
    .SET(n3190_6),
    .CE(VCC) 
);
defparam c_position_age_23_s0.INIT=1'b1;
  DFFSE c_position_age_22_s0 (
    .Q(c_position_age[22]),
    .D(n768_2),
    .CLK(clk50_d),
    .SET(n3190_6),
    .CE(VCC) 
);
defparam c_position_age_22_s0.INIT=1'b1;
  DFFSE c_position_age_21_s0 (
    .Q(c_position_age[21]),
    .D(n769_2),
    .CLK(clk50_d),
    .SET(n3190_6),
    .CE(VCC) 
);
defparam c_position_age_21_s0.INIT=1'b1;
  DFFSE c_position_age_20_s0 (
    .Q(c_position_age[20]),
    .D(n770_2),
    .CLK(clk50_d),
    .SET(n3190_6),
    .CE(VCC) 
);
defparam c_position_age_20_s0.INIT=1'b1;
  DFFSE c_position_age_19_s0 (
    .Q(c_position_age[19]),
    .D(n771_2),
    .CLK(clk50_d),
    .SET(n3190_6),
    .CE(VCC) 
);
defparam c_position_age_19_s0.INIT=1'b1;
  DFFSE c_position_age_18_s0 (
    .Q(c_position_age[18]),
    .D(n772_2),
    .CLK(clk50_d),
    .SET(n3190_6),
    .CE(VCC) 
);
defparam c_position_age_18_s0.INIT=1'b1;
  DFFSE c_position_age_17_s0 (
    .Q(c_position_age[17]),
    .D(n773_2),
    .CLK(clk50_d),
    .SET(n3190_6),
    .CE(VCC) 
);
defparam c_position_age_17_s0.INIT=1'b1;
  DFFSE c_position_age_16_s0 (
    .Q(c_position_age[16]),
    .D(n774_2),
    .CLK(clk50_d),
    .SET(n3190_6),
    .CE(VCC) 
);
defparam c_position_age_16_s0.INIT=1'b1;
  DFFSE c_position_age_15_s0 (
    .Q(c_position_age[15]),
    .D(n775_2),
    .CLK(clk50_d),
    .SET(n3190_6),
    .CE(VCC) 
);
defparam c_position_age_15_s0.INIT=1'b1;
  DFFSE c_position_age_14_s0 (
    .Q(c_position_age[14]),
    .D(n776_2),
    .CLK(clk50_d),
    .SET(n3190_6),
    .CE(VCC) 
);
defparam c_position_age_14_s0.INIT=1'b1;
  DFFSE c_position_age_13_s0 (
    .Q(c_position_age[13]),
    .D(n777_2),
    .CLK(clk50_d),
    .SET(n3190_6),
    .CE(VCC) 
);
defparam c_position_age_13_s0.INIT=1'b1;
  DFFSE c_position_age_12_s0 (
    .Q(c_position_age[12]),
    .D(n778_2),
    .CLK(clk50_d),
    .SET(n3190_6),
    .CE(VCC) 
);
defparam c_position_age_12_s0.INIT=1'b1;
  DFFSE c_position_age_11_s0 (
    .Q(c_position_age[11]),
    .D(n779_2),
    .CLK(clk50_d),
    .SET(n3190_6),
    .CE(VCC) 
);
defparam c_position_age_11_s0.INIT=1'b1;
  DFFSE c_position_age_10_s0 (
    .Q(c_position_age[10]),
    .D(n780_2),
    .CLK(clk50_d),
    .SET(n3190_6),
    .CE(VCC) 
);
defparam c_position_age_10_s0.INIT=1'b1;
  DFFSE c_position_age_9_s0 (
    .Q(c_position_age[9]),
    .D(n781_2),
    .CLK(clk50_d),
    .SET(n3190_6),
    .CE(VCC) 
);
defparam c_position_age_9_s0.INIT=1'b1;
  DFFSE c_position_age_8_s0 (
    .Q(c_position_age[8]),
    .D(n782_2),
    .CLK(clk50_d),
    .SET(n3190_6),
    .CE(VCC) 
);
defparam c_position_age_8_s0.INIT=1'b1;
  DFFSE c_position_age_7_s0 (
    .Q(c_position_age[7]),
    .D(n783_2),
    .CLK(clk50_d),
    .SET(n3190_6),
    .CE(VCC) 
);
defparam c_position_age_7_s0.INIT=1'b1;
  DFFSE c_position_age_6_s0 (
    .Q(c_position_age[6]),
    .D(n784_2),
    .CLK(clk50_d),
    .SET(n3190_6),
    .CE(VCC) 
);
defparam c_position_age_6_s0.INIT=1'b1;
  DFFRE c_vx_31_s0 (
    .Q(c_vx[31]),
    .D(p_vx[31]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vx_31_s0.INIT=1'b0;
  DFFRE c_vx_29_s0 (
    .Q(c_vx[29]),
    .D(p_vx[29]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vx_29_s0.INIT=1'b0;
  DFFRE c_vx_28_s0 (
    .Q(c_vx[28]),
    .D(p_vx[28]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vx_28_s0.INIT=1'b0;
  DFFRE c_vx_27_s0 (
    .Q(c_vx[27]),
    .D(p_vx[27]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vx_27_s0.INIT=1'b0;
  DFFRE c_vx_26_s0 (
    .Q(c_vx[26]),
    .D(p_vx[26]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vx_26_s0.INIT=1'b0;
  DFFRE c_vx_25_s0 (
    .Q(c_vx[25]),
    .D(p_vx[25]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vx_25_s0.INIT=1'b0;
  DFFRE c_vx_24_s0 (
    .Q(c_vx[24]),
    .D(p_vx[24]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vx_24_s0.INIT=1'b0;
  DFFRE c_vx_23_s0 (
    .Q(c_vx[23]),
    .D(p_vx[23]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vx_23_s0.INIT=1'b0;
  DFFRE c_vx_22_s0 (
    .Q(c_vx[22]),
    .D(p_vx[22]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vx_22_s0.INIT=1'b0;
  DFFRE c_vx_21_s0 (
    .Q(c_vx[21]),
    .D(p_vx[21]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vx_21_s0.INIT=1'b0;
  DFFRE c_vx_20_s0 (
    .Q(c_vx[20]),
    .D(p_vx[20]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vx_20_s0.INIT=1'b0;
  DFFRE c_vx_19_s0 (
    .Q(c_vx[19]),
    .D(p_vx[19]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vx_19_s0.INIT=1'b0;
  DFFRE c_vx_18_s0 (
    .Q(c_vx[18]),
    .D(p_vx[18]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vx_18_s0.INIT=1'b0;
  DFFRE c_vx_17_s0 (
    .Q(c_vx[17]),
    .D(p_vx[17]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vx_17_s0.INIT=1'b0;
  DFFRE c_vx_16_s0 (
    .Q(c_vx[16]),
    .D(p_vx[16]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vx_16_s0.INIT=1'b0;
  DFFRE c_vx_15_s0 (
    .Q(c_vx[15]),
    .D(p_vx[15]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vx_15_s0.INIT=1'b0;
  DFFRE c_vx_14_s0 (
    .Q(c_vx[14]),
    .D(p_vx[14]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vx_14_s0.INIT=1'b0;
  DFFRE c_vx_13_s0 (
    .Q(c_vx[13]),
    .D(p_vx[13]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vx_13_s0.INIT=1'b0;
  DFFRE c_vx_12_s0 (
    .Q(c_vx[12]),
    .D(p_vx[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vx_12_s0.INIT=1'b0;
  DFFRE c_vx_11_s0 (
    .Q(c_vx[11]),
    .D(p_vx[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vx_11_s0.INIT=1'b0;
  DFFRE c_vx_10_s0 (
    .Q(c_vx[10]),
    .D(p_vx[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vx_10_s0.INIT=1'b0;
  DFFRE c_vx_9_s0 (
    .Q(c_vx[9]),
    .D(p_vx[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vx_9_s0.INIT=1'b0;
  DFFRE c_vx_8_s0 (
    .Q(c_vx[8]),
    .D(p_vx[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vx_8_s0.INIT=1'b0;
  DFFRE c_vx_7_s0 (
    .Q(c_vx[7]),
    .D(p_vx[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vx_7_s0.INIT=1'b0;
  DFFRE c_vx_6_s0 (
    .Q(c_vx[6]),
    .D(p_vx[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vx_6_s0.INIT=1'b0;
  DFFRE c_vx_5_s0 (
    .Q(c_vx[5]),
    .D(p_vx[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vx_5_s0.INIT=1'b0;
  DFFRE c_vx_4_s0 (
    .Q(c_vx[4]),
    .D(p_vx[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vx_4_s0.INIT=1'b0;
  DFFRE c_vx_3_s0 (
    .Q(c_vx[3]),
    .D(p_vx[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vx_3_s0.INIT=1'b0;
  DFFRE c_vx_2_s0 (
    .Q(c_vx[2]),
    .D(p_vx[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vx_2_s0.INIT=1'b0;
  DFFRE c_vx_1_s0 (
    .Q(c_vx[1]),
    .D(p_vx[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vx_1_s0.INIT=1'b0;
  DFFRE c_vx_0_s0 (
    .Q(c_vx[0]),
    .D(p_vx[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vx_0_s0.INIT=1'b0;
  DFFRE c_vy_31_s0 (
    .Q(c_vy[31]),
    .D(p_vy[31]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vy_31_s0.INIT=1'b0;
  DFFRE c_vy_29_s0 (
    .Q(c_vy[29]),
    .D(p_vy[29]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vy_29_s0.INIT=1'b0;
  DFFRE c_vy_28_s0 (
    .Q(c_vy[28]),
    .D(p_vy[28]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vy_28_s0.INIT=1'b0;
  DFFRE c_vy_27_s0 (
    .Q(c_vy[27]),
    .D(p_vy[27]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vy_27_s0.INIT=1'b0;
  DFFRE c_vy_26_s0 (
    .Q(c_vy[26]),
    .D(p_vy[26]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vy_26_s0.INIT=1'b0;
  DFFRE c_vy_25_s0 (
    .Q(c_vy[25]),
    .D(p_vy[25]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vy_25_s0.INIT=1'b0;
  DFFRE c_vy_24_s0 (
    .Q(c_vy[24]),
    .D(p_vy[24]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vy_24_s0.INIT=1'b0;
  DFFRE c_vy_23_s0 (
    .Q(c_vy[23]),
    .D(p_vy[23]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vy_23_s0.INIT=1'b0;
  DFFRE c_vy_22_s0 (
    .Q(c_vy[22]),
    .D(p_vy[22]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vy_22_s0.INIT=1'b0;
  DFFRE c_vy_21_s0 (
    .Q(c_vy[21]),
    .D(p_vy[21]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vy_21_s0.INIT=1'b0;
  DFFRE c_vy_20_s0 (
    .Q(c_vy[20]),
    .D(p_vy[20]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vy_20_s0.INIT=1'b0;
  DFFRE c_vy_19_s0 (
    .Q(c_vy[19]),
    .D(p_vy[19]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vy_19_s0.INIT=1'b0;
  DFFRE c_vy_18_s0 (
    .Q(c_vy[18]),
    .D(p_vy[18]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vy_18_s0.INIT=1'b0;
  DFFRE c_vy_17_s0 (
    .Q(c_vy[17]),
    .D(p_vy[17]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vy_17_s0.INIT=1'b0;
  DFFRE c_vy_16_s0 (
    .Q(c_vy[16]),
    .D(p_vy[16]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vy_16_s0.INIT=1'b0;
  DFFRE c_vy_15_s0 (
    .Q(c_vy[15]),
    .D(p_vy[15]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vy_15_s0.INIT=1'b0;
  DFFRE c_vy_14_s0 (
    .Q(c_vy[14]),
    .D(p_vy[14]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vy_14_s0.INIT=1'b0;
  DFFRE c_vy_13_s0 (
    .Q(c_vy[13]),
    .D(p_vy[13]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vy_13_s0.INIT=1'b0;
  DFFRE c_vy_12_s0 (
    .Q(c_vy[12]),
    .D(p_vy[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vy_12_s0.INIT=1'b0;
  DFFRE c_vy_11_s0 (
    .Q(c_vy[11]),
    .D(p_vy[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vy_11_s0.INIT=1'b0;
  DFFRE c_vy_10_s0 (
    .Q(c_vy[10]),
    .D(p_vy[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vy_10_s0.INIT=1'b0;
  DFFRE c_vy_9_s0 (
    .Q(c_vy[9]),
    .D(p_vy[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vy_9_s0.INIT=1'b0;
  DFFRE c_vy_8_s0 (
    .Q(c_vy[8]),
    .D(p_vy[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vy_8_s0.INIT=1'b0;
  DFFRE c_vy_7_s0 (
    .Q(c_vy[7]),
    .D(p_vy[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vy_7_s0.INIT=1'b0;
  DFFRE c_vy_6_s0 (
    .Q(c_vy[6]),
    .D(p_vy[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vy_6_s0.INIT=1'b0;
  DFFRE c_vy_5_s0 (
    .Q(c_vy[5]),
    .D(p_vy[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vy_5_s0.INIT=1'b0;
  DFFRE c_vy_4_s0 (
    .Q(c_vy[4]),
    .D(p_vy[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vy_4_s0.INIT=1'b0;
  DFFRE c_vy_3_s0 (
    .Q(c_vy[3]),
    .D(p_vy[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vy_3_s0.INIT=1'b0;
  DFFRE c_vy_2_s0 (
    .Q(c_vy[2]),
    .D(p_vy[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vy_2_s0.INIT=1'b0;
  DFFRE c_vy_1_s0 (
    .Q(c_vy[1]),
    .D(p_vy[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vy_1_s0.INIT=1'b0;
  DFFRE c_vy_0_s0 (
    .Q(c_vy[0]),
    .D(p_vy[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vy_0_s0.INIT=1'b0;
  DFFRE c_height_31_s0 (
    .Q(c_height[31]),
    .D(p_height[31]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_height_31_s0.INIT=1'b0;
  DFFRE c_height_30_s0 (
    .Q(c_height[30]),
    .D(p_height[30]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_height_30_s0.INIT=1'b0;
  DFFRE c_height_29_s0 (
    .Q(c_height[29]),
    .D(p_height[29]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_height_29_s0.INIT=1'b0;
  DFFRE c_height_28_s0 (
    .Q(c_height[28]),
    .D(p_height[28]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_height_28_s0.INIT=1'b0;
  DFFRE c_height_27_s0 (
    .Q(c_height[27]),
    .D(p_height[27]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_height_27_s0.INIT=1'b0;
  DFFRE c_height_26_s0 (
    .Q(c_height[26]),
    .D(p_height[26]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_height_26_s0.INIT=1'b0;
  DFFRE c_height_25_s0 (
    .Q(c_height[25]),
    .D(p_height[25]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_height_25_s0.INIT=1'b0;
  DFFRE c_height_24_s0 (
    .Q(c_height[24]),
    .D(p_height[24]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_height_24_s0.INIT=1'b0;
  DFFRE c_height_23_s0 (
    .Q(c_height[23]),
    .D(p_height[23]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_height_23_s0.INIT=1'b0;
  DFFRE c_height_22_s0 (
    .Q(c_height[22]),
    .D(p_height[22]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_height_22_s0.INIT=1'b0;
  DFFRE c_height_21_s0 (
    .Q(c_height[21]),
    .D(p_height[21]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_height_21_s0.INIT=1'b0;
  DFFRE c_height_20_s0 (
    .Q(c_height[20]),
    .D(p_height[20]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_height_20_s0.INIT=1'b0;
  DFFRE c_height_19_s0 (
    .Q(c_height[19]),
    .D(p_height[19]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_height_19_s0.INIT=1'b0;
  DFFRE c_height_18_s0 (
    .Q(c_height[18]),
    .D(p_height[18]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_height_18_s0.INIT=1'b0;
  DFFRE c_height_17_s0 (
    .Q(c_height[17]),
    .D(p_height[17]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_height_17_s0.INIT=1'b0;
  DFFRE c_height_16_s0 (
    .Q(c_height[16]),
    .D(p_height[16]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_height_16_s0.INIT=1'b0;
  DFFRE c_height_15_s0 (
    .Q(c_height[15]),
    .D(p_height[15]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_height_15_s0.INIT=1'b0;
  DFFRE c_height_14_s0 (
    .Q(c_height[14]),
    .D(p_height[14]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_height_14_s0.INIT=1'b0;
  DFFRE c_height_13_s0 (
    .Q(c_height[13]),
    .D(p_height[13]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_height_13_s0.INIT=1'b0;
  DFFRE c_height_12_s0 (
    .Q(c_height[12]),
    .D(p_height[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_height_12_s0.INIT=1'b0;
  DFFRE c_height_11_s0 (
    .Q(c_height[11]),
    .D(p_height[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_height_11_s0.INIT=1'b0;
  DFFRE c_height_10_s0 (
    .Q(c_height[10]),
    .D(p_height[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_height_10_s0.INIT=1'b0;
  DFFRE c_height_9_s0 (
    .Q(c_height[9]),
    .D(p_height[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_height_9_s0.INIT=1'b0;
  DFFRE c_height_8_s0 (
    .Q(c_height[8]),
    .D(p_height[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_height_8_s0.INIT=1'b0;
  DFFRE c_height_7_s0 (
    .Q(c_height[7]),
    .D(p_height[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_height_7_s0.INIT=1'b0;
  DFFRE c_height_6_s0 (
    .Q(c_height[6]),
    .D(p_height[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_height_6_s0.INIT=1'b0;
  DFFRE c_height_5_s0 (
    .Q(c_height[5]),
    .D(p_height[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_height_5_s0.INIT=1'b0;
  DFFRE c_height_4_s0 (
    .Q(c_height[4]),
    .D(p_height[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_height_4_s0.INIT=1'b0;
  DFFRE c_height_3_s0 (
    .Q(c_height[3]),
    .D(p_height[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_height_3_s0.INIT=1'b0;
  DFFRE c_height_2_s0 (
    .Q(c_height[2]),
    .D(p_height[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_height_2_s0.INIT=1'b0;
  DFFRE c_height_1_s0 (
    .Q(c_height[1]),
    .D(p_height[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_height_1_s0.INIT=1'b0;
  DFFRE c_height_0_s0 (
    .Q(c_height[0]),
    .D(p_height[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_height_0_s0.INIT=1'b0;
  DFFRE c_ax_31_s0 (
    .Q(c_ax[31]),
    .D(p_ax[31]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ax_31_s0.INIT=1'b0;
  DFFRE c_ax_30_s0 (
    .Q(c_ax[30]),
    .D(p_ax[30]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ax_30_s0.INIT=1'b0;
  DFFRE c_ax_29_s0 (
    .Q(c_ax[29]),
    .D(p_ax[29]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ax_29_s0.INIT=1'b0;
  DFFRE c_ax_28_s0 (
    .Q(c_ax[28]),
    .D(p_ax[28]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ax_28_s0.INIT=1'b0;
  DFFRE c_ax_27_s0 (
    .Q(c_ax[27]),
    .D(p_ax[27]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ax_27_s0.INIT=1'b0;
  DFFRE c_ax_26_s0 (
    .Q(c_ax[26]),
    .D(p_ax[26]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ax_26_s0.INIT=1'b0;
  DFFRE c_ax_25_s0 (
    .Q(c_ax[25]),
    .D(p_ax[25]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ax_25_s0.INIT=1'b0;
  DFFRE c_ax_24_s0 (
    .Q(c_ax[24]),
    .D(p_ax[24]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ax_24_s0.INIT=1'b0;
  DFFRE c_ax_23_s0 (
    .Q(c_ax[23]),
    .D(p_ax[23]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ax_23_s0.INIT=1'b0;
  DFFRE c_ax_22_s0 (
    .Q(c_ax[22]),
    .D(p_ax[22]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ax_22_s0.INIT=1'b0;
  DFFRE c_ax_21_s0 (
    .Q(c_ax[21]),
    .D(p_ax[21]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ax_21_s0.INIT=1'b0;
  DFFRE c_ax_20_s0 (
    .Q(c_ax[20]),
    .D(p_ax[20]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ax_20_s0.INIT=1'b0;
  DFFRE c_ax_19_s0 (
    .Q(c_ax[19]),
    .D(p_ax[19]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ax_19_s0.INIT=1'b0;
  DFFRE c_ax_18_s0 (
    .Q(c_ax[18]),
    .D(p_ax[18]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ax_18_s0.INIT=1'b0;
  DFFRE c_ax_17_s0 (
    .Q(c_ax[17]),
    .D(p_ax[17]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ax_17_s0.INIT=1'b0;
  DFFRE c_ax_16_s0 (
    .Q(c_ax[16]),
    .D(p_ax[16]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ax_16_s0.INIT=1'b0;
  DFFRE c_ax_15_s0 (
    .Q(c_ax[15]),
    .D(p_ax[15]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ax_15_s0.INIT=1'b0;
  DFFRE c_ax_14_s0 (
    .Q(c_ax[14]),
    .D(p_ax[14]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ax_14_s0.INIT=1'b0;
  DFFRE c_ax_13_s0 (
    .Q(c_ax[13]),
    .D(p_ax[13]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ax_13_s0.INIT=1'b0;
  DFFRE c_ax_12_s0 (
    .Q(c_ax[12]),
    .D(p_ax[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ax_12_s0.INIT=1'b0;
  DFFRE c_ax_11_s0 (
    .Q(c_ax[11]),
    .D(p_ax[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ax_11_s0.INIT=1'b0;
  DFFRE c_ax_10_s0 (
    .Q(c_ax[10]),
    .D(p_ax[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ax_10_s0.INIT=1'b0;
  DFFRE c_ax_9_s0 (
    .Q(c_ax[9]),
    .D(p_ax[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ax_9_s0.INIT=1'b0;
  DFFRE c_ax_8_s0 (
    .Q(c_ax[8]),
    .D(p_ax[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ax_8_s0.INIT=1'b0;
  DFFRE c_ax_7_s0 (
    .Q(c_ax[7]),
    .D(p_ax[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ax_7_s0.INIT=1'b0;
  DFFRE c_ax_6_s0 (
    .Q(c_ax[6]),
    .D(p_ax[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ax_6_s0.INIT=1'b0;
  DFFRE c_ax_5_s0 (
    .Q(c_ax[5]),
    .D(p_ax[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ax_5_s0.INIT=1'b0;
  DFFRE c_ax_4_s0 (
    .Q(c_ax[4]),
    .D(p_ax[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ax_4_s0.INIT=1'b0;
  DFFRE c_ax_3_s0 (
    .Q(c_ax[3]),
    .D(p_ax[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ax_3_s0.INIT=1'b0;
  DFFRE c_ax_2_s0 (
    .Q(c_ax[2]),
    .D(p_ax[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ax_2_s0.INIT=1'b0;
  DFFRE c_ax_1_s0 (
    .Q(c_ax[1]),
    .D(p_ax[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ax_1_s0.INIT=1'b0;
  DFFRE c_ax_0_s0 (
    .Q(c_ax[0]),
    .D(p_ax[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ax_0_s0.INIT=1'b0;
  DFFRE c_ay_31_s0 (
    .Q(c_ay[31]),
    .D(p_ay[31]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ay_31_s0.INIT=1'b0;
  DFFRE c_ay_30_s0 (
    .Q(c_ay[30]),
    .D(p_ay[30]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ay_30_s0.INIT=1'b0;
  DFFRE c_ay_29_s0 (
    .Q(c_ay[29]),
    .D(p_ay[29]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ay_29_s0.INIT=1'b0;
  DFFRE c_ay_28_s0 (
    .Q(c_ay[28]),
    .D(p_ay[28]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ay_28_s0.INIT=1'b0;
  DFFRE c_ay_27_s0 (
    .Q(c_ay[27]),
    .D(p_ay[27]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ay_27_s0.INIT=1'b0;
  DFFRE c_ay_26_s0 (
    .Q(c_ay[26]),
    .D(p_ay[26]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ay_26_s0.INIT=1'b0;
  DFFRE c_ay_25_s0 (
    .Q(c_ay[25]),
    .D(p_ay[25]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ay_25_s0.INIT=1'b0;
  DFFRE c_ay_24_s0 (
    .Q(c_ay[24]),
    .D(p_ay[24]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ay_24_s0.INIT=1'b0;
  DFFRE c_ay_23_s0 (
    .Q(c_ay[23]),
    .D(p_ay[23]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ay_23_s0.INIT=1'b0;
  DFFRE c_ay_22_s0 (
    .Q(c_ay[22]),
    .D(p_ay[22]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ay_22_s0.INIT=1'b0;
  DFFRE c_ay_21_s0 (
    .Q(c_ay[21]),
    .D(p_ay[21]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ay_21_s0.INIT=1'b0;
  DFFRE c_ay_20_s0 (
    .Q(c_ay[20]),
    .D(p_ay[20]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ay_20_s0.INIT=1'b0;
  DFFRE c_ay_19_s0 (
    .Q(c_ay[19]),
    .D(p_ay[19]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ay_19_s0.INIT=1'b0;
  DFFRE c_ay_18_s0 (
    .Q(c_ay[18]),
    .D(p_ay[18]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ay_18_s0.INIT=1'b0;
  DFFRE c_ay_17_s0 (
    .Q(c_ay[17]),
    .D(p_ay[17]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ay_17_s0.INIT=1'b0;
  DFFRE c_ay_16_s0 (
    .Q(c_ay[16]),
    .D(p_ay[16]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ay_16_s0.INIT=1'b0;
  DFFRE c_ay_15_s0 (
    .Q(c_ay[15]),
    .D(p_ay[15]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ay_15_s0.INIT=1'b0;
  DFFRE c_ay_14_s0 (
    .Q(c_ay[14]),
    .D(p_ay[14]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ay_14_s0.INIT=1'b0;
  DFFRE c_ay_13_s0 (
    .Q(c_ay[13]),
    .D(p_ay[13]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ay_13_s0.INIT=1'b0;
  DFFRE c_ay_12_s0 (
    .Q(c_ay[12]),
    .D(p_ay[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ay_12_s0.INIT=1'b0;
  DFFRE c_ay_11_s0 (
    .Q(c_ay[11]),
    .D(p_ay[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ay_11_s0.INIT=1'b0;
  DFFRE c_ay_10_s0 (
    .Q(c_ay[10]),
    .D(p_ay[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ay_10_s0.INIT=1'b0;
  DFFRE c_ay_9_s0 (
    .Q(c_ay[9]),
    .D(p_ay[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ay_9_s0.INIT=1'b0;
  DFFRE c_ay_8_s0 (
    .Q(c_ay[8]),
    .D(p_ay[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ay_8_s0.INIT=1'b0;
  DFFRE c_ay_7_s0 (
    .Q(c_ay[7]),
    .D(p_ay[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ay_7_s0.INIT=1'b0;
  DFFRE c_ay_6_s0 (
    .Q(c_ay[6]),
    .D(p_ay[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ay_6_s0.INIT=1'b0;
  DFFRE c_ay_5_s0 (
    .Q(c_ay[5]),
    .D(p_ay[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ay_5_s0.INIT=1'b0;
  DFFRE c_ay_4_s0 (
    .Q(c_ay[4]),
    .D(p_ay[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ay_4_s0.INIT=1'b0;
  DFFRE c_ay_3_s0 (
    .Q(c_ay[3]),
    .D(p_ay[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ay_3_s0.INIT=1'b0;
  DFFRE c_ay_2_s0 (
    .Q(c_ay[2]),
    .D(p_ay[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ay_2_s0.INIT=1'b0;
  DFFRE c_ay_1_s0 (
    .Q(c_ay[1]),
    .D(p_ay[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ay_1_s0.INIT=1'b0;
  DFFRE c_ay_0_s0 (
    .Q(c_ay[0]),
    .D(p_ay[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ay_0_s0.INIT=1'b0;
  DFFRE c_az_31_s0 (
    .Q(c_az[31]),
    .D(p_az[31]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_az_31_s0.INIT=1'b0;
  DFFRE c_az_14_s0 (
    .Q(c_az[14]),
    .D(p_az[14]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_az_14_s0.INIT=1'b0;
  DFFRE c_az_13_s0 (
    .Q(c_az[13]),
    .D(p_az[13]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_az_13_s0.INIT=1'b0;
  DFFRE c_az_12_s0 (
    .Q(c_az[12]),
    .D(p_az[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_az_12_s0.INIT=1'b0;
  DFFRE c_az_11_s0 (
    .Q(c_az[11]),
    .D(p_az[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_az_11_s0.INIT=1'b0;
  DFFRE c_az_10_s0 (
    .Q(c_az[10]),
    .D(p_az[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_az_10_s0.INIT=1'b0;
  DFFRE c_az_9_s0 (
    .Q(c_az[9]),
    .D(p_az[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_az_9_s0.INIT=1'b0;
  DFFRE c_az_8_s0 (
    .Q(c_az[8]),
    .D(p_az[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_az_8_s0.INIT=1'b0;
  DFFRE c_az_7_s0 (
    .Q(c_az[7]),
    .D(p_az[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_az_7_s0.INIT=1'b0;
  DFFRE c_az_6_s0 (
    .Q(c_az[6]),
    .D(p_az[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_az_6_s0.INIT=1'b0;
  DFFRE c_az_5_s0 (
    .Q(c_az[5]),
    .D(p_az[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_az_5_s0.INIT=1'b0;
  DFFRE c_az_4_s0 (
    .Q(c_az[4]),
    .D(p_az[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_az_4_s0.INIT=1'b0;
  DFFRE c_az_3_s0 (
    .Q(c_az[3]),
    .D(p_az[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_az_3_s0.INIT=1'b0;
  DFFRE c_az_2_s0 (
    .Q(c_az[2]),
    .D(p_az[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_az_2_s0.INIT=1'b0;
  DFFRE c_az_1_s0 (
    .Q(c_az[1]),
    .D(p_az[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_az_1_s0.INIT=1'b0;
  DFFRE c_az_0_s0 (
    .Q(c_az[0]),
    .D(p_az[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_az_0_s0.INIT=1'b0;
  DFFRE c_yaw_15_s0 (
    .Q(c_yaw[15]),
    .D(p_yaw[15]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_yaw_15_s0.INIT=1'b0;
  DFFRE c_yaw_14_s0 (
    .Q(c_yaw[14]),
    .D(p_yaw[14]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_yaw_14_s0.INIT=1'b0;
  DFFRE c_yaw_13_s0 (
    .Q(c_yaw[13]),
    .D(p_yaw[13]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_yaw_13_s0.INIT=1'b0;
  DFFRE c_yaw_12_s0 (
    .Q(c_yaw[12]),
    .D(p_yaw[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_yaw_12_s0.INIT=1'b0;
  DFFRE c_yaw_11_s0 (
    .Q(c_yaw[11]),
    .D(p_yaw[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_yaw_11_s0.INIT=1'b0;
  DFFRE c_yaw_10_s0 (
    .Q(c_yaw[10]),
    .D(p_yaw[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_yaw_10_s0.INIT=1'b0;
  DFFRE c_yaw_9_s0 (
    .Q(c_yaw[9]),
    .D(p_yaw[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_yaw_9_s0.INIT=1'b0;
  DFFRE c_yaw_8_s0 (
    .Q(c_yaw[8]),
    .D(p_yaw[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_yaw_8_s0.INIT=1'b0;
  DFFRE c_yaw_7_s0 (
    .Q(c_yaw[7]),
    .D(p_yaw[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_yaw_7_s0.INIT=1'b0;
  DFFRE c_yaw_6_s0 (
    .Q(c_yaw[6]),
    .D(p_yaw[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_yaw_6_s0.INIT=1'b0;
  DFFRE c_yaw_5_s0 (
    .Q(c_yaw[5]),
    .D(p_yaw[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_yaw_5_s0.INIT=1'b0;
  DFFRE c_yaw_4_s0 (
    .Q(c_yaw[4]),
    .D(p_yaw[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_yaw_4_s0.INIT=1'b0;
  DFFRE c_yaw_3_s0 (
    .Q(c_yaw[3]),
    .D(p_yaw[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_yaw_3_s0.INIT=1'b0;
  DFFRE c_yaw_2_s0 (
    .Q(c_yaw[2]),
    .D(p_yaw[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_yaw_2_s0.INIT=1'b0;
  DFFRE c_yaw_1_s0 (
    .Q(c_yaw[1]),
    .D(p_yaw[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_yaw_1_s0.INIT=1'b0;
  DFFRE c_yaw_0_s0 (
    .Q(c_yaw[0]),
    .D(p_yaw[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_yaw_0_s0.INIT=1'b0;
  DFFRE c_channel_count_3_s0 (
    .Q(c_channel_count[3]),
    .D(p_channel_count[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_channel_count_3_s0.INIT=1'b0;
  DFFRE c_channel_count_2_s0 (
    .Q(c_channel_count[2]),
    .D(p_channel_count[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_channel_count_2_s0.INIT=1'b0;
  DFFRE c_channel_count_1_s0 (
    .Q(c_channel_count[1]),
    .D(p_channel_count[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_channel_count_1_s0.INIT=1'b0;
  DFFRE c_channel_count_0_s0 (
    .Q(c_channel_count[0]),
    .D(p_channel_count[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_channel_count_0_s0.INIT=1'b0;
  DFFRE c_ch1_11_s0 (
    .Q(c_ch1[11]),
    .D(p_ch1[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch1_11_s0.INIT=1'b0;
  DFFRE c_ch1_10_s0 (
    .Q(c_ch1[10]),
    .D(p_ch1[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch1_10_s0.INIT=1'b0;
  DFFRE c_ch1_9_s0 (
    .Q(c_ch1[9]),
    .D(p_ch1[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch1_9_s0.INIT=1'b0;
  DFFRE c_ch1_8_s0 (
    .Q(c_ch1[8]),
    .D(p_ch1[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch1_8_s0.INIT=1'b0;
  DFFRE c_ch1_7_s0 (
    .Q(c_ch1[7]),
    .D(p_ch1[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch1_7_s0.INIT=1'b0;
  DFFRE c_ch1_6_s0 (
    .Q(c_ch1[6]),
    .D(p_ch1[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch1_6_s0.INIT=1'b0;
  DFFRE c_ch1_5_s0 (
    .Q(c_ch1[5]),
    .D(p_ch1[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch1_5_s0.INIT=1'b0;
  DFFRE c_ch1_4_s0 (
    .Q(c_ch1[4]),
    .D(p_ch1[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch1_4_s0.INIT=1'b0;
  DFFRE c_ch1_3_s0 (
    .Q(c_ch1[3]),
    .D(p_ch1[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch1_3_s0.INIT=1'b0;
  DFFRE c_ch1_2_s0 (
    .Q(c_ch1[2]),
    .D(p_ch1[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch1_2_s0.INIT=1'b0;
  DFFRE c_ch1_1_s0 (
    .Q(c_ch1[1]),
    .D(p_ch1[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch1_1_s0.INIT=1'b0;
  DFFRE c_ch1_0_s0 (
    .Q(c_ch1[0]),
    .D(p_ch1[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch1_0_s0.INIT=1'b0;
  DFFRE c_ch2_11_s0 (
    .Q(c_ch2[11]),
    .D(p_ch2[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch2_11_s0.INIT=1'b0;
  DFFRE c_ch2_10_s0 (
    .Q(c_ch2[10]),
    .D(p_ch2[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch2_10_s0.INIT=1'b0;
  DFFRE c_ch2_9_s0 (
    .Q(c_ch2[9]),
    .D(p_ch2[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch2_9_s0.INIT=1'b0;
  DFFRE c_ch2_8_s0 (
    .Q(c_ch2[8]),
    .D(p_ch2[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch2_8_s0.INIT=1'b0;
  DFFRE c_ch2_7_s0 (
    .Q(c_ch2[7]),
    .D(p_ch2[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch2_7_s0.INIT=1'b0;
  DFFRE c_ch2_6_s0 (
    .Q(c_ch2[6]),
    .D(p_ch2[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch2_6_s0.INIT=1'b0;
  DFFRE c_ch2_5_s0 (
    .Q(c_ch2[5]),
    .D(p_ch2[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch2_5_s0.INIT=1'b0;
  DFFRE c_ch2_4_s0 (
    .Q(c_ch2[4]),
    .D(p_ch2[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch2_4_s0.INIT=1'b0;
  DFFRE c_ch2_3_s0 (
    .Q(c_ch2[3]),
    .D(p_ch2[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch2_3_s0.INIT=1'b0;
  DFFRE c_ch2_2_s0 (
    .Q(c_ch2[2]),
    .D(p_ch2[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch2_2_s0.INIT=1'b0;
  DFFRE c_ch2_1_s0 (
    .Q(c_ch2[1]),
    .D(p_ch2[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch2_1_s0.INIT=1'b0;
  DFFRE c_ch2_0_s0 (
    .Q(c_ch2[0]),
    .D(p_ch2[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch2_0_s0.INIT=1'b0;
  DFFRE c_ch3_11_s0 (
    .Q(c_ch3[11]),
    .D(p_ch3[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch3_11_s0.INIT=1'b0;
  DFFRE c_ch3_10_s0 (
    .Q(c_ch3[10]),
    .D(p_ch3[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch3_10_s0.INIT=1'b0;
  DFFRE c_ch3_9_s0 (
    .Q(c_ch3[9]),
    .D(p_ch3[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch3_9_s0.INIT=1'b0;
  DFFRE c_ch3_8_s0 (
    .Q(c_ch3[8]),
    .D(p_ch3[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch3_8_s0.INIT=1'b0;
  DFFRE c_ch3_7_s0 (
    .Q(c_ch3[7]),
    .D(p_ch3[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch3_7_s0.INIT=1'b0;
  DFFRE c_ch3_6_s0 (
    .Q(c_ch3[6]),
    .D(p_ch3[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch3_6_s0.INIT=1'b0;
  DFFRE c_ch3_5_s0 (
    .Q(c_ch3[5]),
    .D(p_ch3[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch3_5_s0.INIT=1'b0;
  DFFRE c_ch3_4_s0 (
    .Q(c_ch3[4]),
    .D(p_ch3[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch3_4_s0.INIT=1'b0;
  DFFRE c_ch3_3_s0 (
    .Q(c_ch3[3]),
    .D(p_ch3[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch3_3_s0.INIT=1'b0;
  DFFRE c_ch3_2_s0 (
    .Q(c_ch3[2]),
    .D(p_ch3[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch3_2_s0.INIT=1'b0;
  DFFRE c_ch3_1_s0 (
    .Q(c_ch3[1]),
    .D(p_ch3[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch3_1_s0.INIT=1'b0;
  DFFRE c_ch3_0_s0 (
    .Q(c_ch3[0]),
    .D(p_ch3[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch3_0_s0.INIT=1'b0;
  DFFRE c_ch7_11_s0 (
    .Q(c_ch7[11]),
    .D(p_ch7[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch7_11_s0.INIT=1'b0;
  DFFRE c_ch7_10_s0 (
    .Q(c_ch7[10]),
    .D(p_ch7[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch7_10_s0.INIT=1'b0;
  DFFRE c_ch7_9_s0 (
    .Q(c_ch7[9]),
    .D(p_ch7[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch7_9_s0.INIT=1'b0;
  DFFRE c_ch7_8_s0 (
    .Q(c_ch7[8]),
    .D(p_ch7[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch7_8_s0.INIT=1'b0;
  DFFRE c_ch7_7_s0 (
    .Q(c_ch7[7]),
    .D(p_ch7[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch7_7_s0.INIT=1'b0;
  DFFRE c_ch7_6_s0 (
    .Q(c_ch7[6]),
    .D(p_ch7[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch7_6_s0.INIT=1'b0;
  DFFRE c_ch7_5_s0 (
    .Q(c_ch7[5]),
    .D(p_ch7[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch7_5_s0.INIT=1'b0;
  DFFRE c_ch7_4_s0 (
    .Q(c_ch7[4]),
    .D(p_ch7[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch7_4_s0.INIT=1'b0;
  DFFRE c_ch7_3_s0 (
    .Q(c_ch7[3]),
    .D(p_ch7[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch7_3_s0.INIT=1'b0;
  DFFRE c_ch7_2_s0 (
    .Q(c_ch7[2]),
    .D(p_ch7[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch7_2_s0.INIT=1'b0;
  DFFRE c_ch7_1_s0 (
    .Q(c_ch7[1]),
    .D(p_ch7[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch7_1_s0.INIT=1'b0;
  DFFRE c_ch7_0_s0 (
    .Q(c_ch7[0]),
    .D(p_ch7[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_ch7_0_s0.INIT=1'b0;
  DFFRE c_height_update_s0 (
    .Q(c_height_update),
    .D(p_height_update),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_height_update_s0.INIT=1'b0;
  DFFRE c_sample_update_s0 (
    .Q(c_sample_update),
    .D(p_sample_update),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_sample_update_s0.INIT=1'b0;
  DFFRE c_sample_dt_31_s0 (
    .Q(c_sample_dt[31]),
    .D(p_sample_dt[31]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_sample_dt_31_s0.INIT=1'b0;
  DFFRE c_sample_dt_30_s0 (
    .Q(c_sample_dt[30]),
    .D(p_sample_dt[30]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_sample_dt_30_s0.INIT=1'b0;
  DFFRE c_sample_dt_29_s0 (
    .Q(c_sample_dt[29]),
    .D(p_sample_dt[29]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_sample_dt_29_s0.INIT=1'b0;
  DFFRE c_sample_dt_28_s0 (
    .Q(c_sample_dt[28]),
    .D(p_sample_dt[28]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_sample_dt_28_s0.INIT=1'b0;
  DFFRE c_sample_dt_27_s0 (
    .Q(c_sample_dt[27]),
    .D(p_sample_dt[27]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_sample_dt_27_s0.INIT=1'b0;
  DFFRE c_sample_dt_26_s0 (
    .Q(c_sample_dt[26]),
    .D(p_sample_dt[26]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_sample_dt_26_s0.INIT=1'b0;
  DFFRE c_sample_dt_25_s0 (
    .Q(c_sample_dt[25]),
    .D(p_sample_dt[25]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_sample_dt_25_s0.INIT=1'b0;
  DFFRE c_sample_dt_24_s0 (
    .Q(c_sample_dt[24]),
    .D(p_sample_dt[24]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_sample_dt_24_s0.INIT=1'b0;
  DFFRE c_sample_dt_23_s0 (
    .Q(c_sample_dt[23]),
    .D(p_sample_dt[23]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_sample_dt_23_s0.INIT=1'b0;
  DFFRE c_sample_dt_22_s0 (
    .Q(c_sample_dt[22]),
    .D(p_sample_dt[22]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_sample_dt_22_s0.INIT=1'b0;
  DFFRE c_sample_dt_21_s0 (
    .Q(c_sample_dt[21]),
    .D(p_sample_dt[21]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_sample_dt_21_s0.INIT=1'b0;
  DFFRE c_sample_dt_20_s0 (
    .Q(c_sample_dt[20]),
    .D(p_sample_dt[20]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_sample_dt_20_s0.INIT=1'b0;
  DFFRE c_sample_dt_19_s0 (
    .Q(c_sample_dt[19]),
    .D(p_sample_dt[19]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_sample_dt_19_s0.INIT=1'b0;
  DFFRE c_sample_dt_18_s0 (
    .Q(c_sample_dt[18]),
    .D(p_sample_dt[18]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_sample_dt_18_s0.INIT=1'b0;
  DFFRE c_sample_dt_17_s0 (
    .Q(c_sample_dt[17]),
    .D(p_sample_dt[17]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_sample_dt_17_s0.INIT=1'b0;
  DFFRE c_sample_dt_16_s0 (
    .Q(c_sample_dt[16]),
    .D(p_sample_dt[16]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_sample_dt_16_s0.INIT=1'b0;
  DFFRE c_sample_dt_15_s0 (
    .Q(c_sample_dt[15]),
    .D(p_sample_dt[15]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_sample_dt_15_s0.INIT=1'b0;
  DFFRE c_sample_dt_14_s0 (
    .Q(c_sample_dt[14]),
    .D(p_sample_dt[14]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_sample_dt_14_s0.INIT=1'b0;
  DFFRE c_sample_dt_13_s0 (
    .Q(c_sample_dt[13]),
    .D(p_sample_dt[13]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_sample_dt_13_s0.INIT=1'b0;
  DFFRE c_sample_dt_12_s0 (
    .Q(c_sample_dt[12]),
    .D(p_sample_dt[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_sample_dt_12_s0.INIT=1'b0;
  DFFRE c_sample_dt_11_s0 (
    .Q(c_sample_dt[11]),
    .D(p_sample_dt[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_sample_dt_11_s0.INIT=1'b0;
  DFFRE c_sample_dt_10_s0 (
    .Q(c_sample_dt[10]),
    .D(p_sample_dt[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_sample_dt_10_s0.INIT=1'b0;
  DFFRE c_sample_dt_9_s0 (
    .Q(c_sample_dt[9]),
    .D(p_sample_dt[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_sample_dt_9_s0.INIT=1'b0;
  DFFRE c_sample_dt_8_s0 (
    .Q(c_sample_dt[8]),
    .D(p_sample_dt[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_sample_dt_8_s0.INIT=1'b0;
  DFFRE c_sample_dt_7_s0 (
    .Q(c_sample_dt[7]),
    .D(p_sample_dt[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_sample_dt_7_s0.INIT=1'b0;
  DFFRE c_sample_dt_6_s0 (
    .Q(c_sample_dt[6]),
    .D(p_sample_dt[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_sample_dt_6_s0.INIT=1'b0;
  DFFRE c_sample_dt_5_s0 (
    .Q(c_sample_dt[5]),
    .D(p_sample_dt[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_sample_dt_5_s0.INIT=1'b0;
  DFFRE c_sample_dt_4_s0 (
    .Q(c_sample_dt[4]),
    .D(p_sample_dt[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_sample_dt_4_s0.INIT=1'b0;
  DFFRE c_sample_dt_3_s0 (
    .Q(c_sample_dt[3]),
    .D(p_sample_dt[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_sample_dt_3_s0.INIT=1'b0;
  DFFRE c_sample_dt_2_s0 (
    .Q(c_sample_dt[2]),
    .D(p_sample_dt[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_sample_dt_2_s0.INIT=1'b0;
  DFFRE c_sample_dt_1_s0 (
    .Q(c_sample_dt[1]),
    .D(p_sample_dt[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_sample_dt_1_s0.INIT=1'b0;
  DFFRE c_sample_dt_0_s0 (
    .Q(c_sample_dt[0]),
    .D(p_sample_dt[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_sample_dt_0_s0.INIT=1'b0;
  DFFRE c_vz_31_s0 (
    .Q(c_vz[31]),
    .D(p_vz[31]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vz_31_s0.INIT=1'b0;
  DFFRE c_vz_30_s0 (
    .Q(c_vz[30]),
    .D(p_vz[30]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vz_30_s0.INIT=1'b0;
  DFFRE c_vz_29_s0 (
    .Q(c_vz[29]),
    .D(p_vz[29]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vz_29_s0.INIT=1'b0;
  DFFRE c_vz_28_s0 (
    .Q(c_vz[28]),
    .D(p_vz[28]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vz_28_s0.INIT=1'b0;
  DFFRE c_vz_27_s0 (
    .Q(c_vz[27]),
    .D(p_vz[27]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vz_27_s0.INIT=1'b0;
  DFFRE c_vz_26_s0 (
    .Q(c_vz[26]),
    .D(p_vz[26]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vz_26_s0.INIT=1'b0;
  DFFRE c_vz_25_s0 (
    .Q(c_vz[25]),
    .D(p_vz[25]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vz_25_s0.INIT=1'b0;
  DFFRE c_vz_24_s0 (
    .Q(c_vz[24]),
    .D(p_vz[24]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vz_24_s0.INIT=1'b0;
  DFFRE c_vz_23_s0 (
    .Q(c_vz[23]),
    .D(p_vz[23]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vz_23_s0.INIT=1'b0;
  DFFRE c_vz_22_s0 (
    .Q(c_vz[22]),
    .D(p_vz[22]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vz_22_s0.INIT=1'b0;
  DFFRE c_vz_21_s0 (
    .Q(c_vz[21]),
    .D(p_vz[21]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vz_21_s0.INIT=1'b0;
  DFFRE c_vz_20_s0 (
    .Q(c_vz[20]),
    .D(p_vz[20]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vz_20_s0.INIT=1'b0;
  DFFRE c_vz_19_s0 (
    .Q(c_vz[19]),
    .D(p_vz[19]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vz_19_s0.INIT=1'b0;
  DFFRE c_vz_18_s0 (
    .Q(c_vz[18]),
    .D(p_vz[18]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vz_18_s0.INIT=1'b0;
  DFFRE c_vz_17_s0 (
    .Q(c_vz[17]),
    .D(p_vz[17]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vz_17_s0.INIT=1'b0;
  DFFRE c_vz_16_s0 (
    .Q(c_vz[16]),
    .D(p_vz[16]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vz_16_s0.INIT=1'b0;
  DFFRE c_vz_15_s0 (
    .Q(c_vz[15]),
    .D(p_vz[15]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vz_15_s0.INIT=1'b0;
  DFFRE c_vz_14_s0 (
    .Q(c_vz[14]),
    .D(p_vz[14]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vz_14_s0.INIT=1'b0;
  DFFRE c_vz_13_s0 (
    .Q(c_vz[13]),
    .D(p_vz[13]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vz_13_s0.INIT=1'b0;
  DFFRE c_vz_12_s0 (
    .Q(c_vz[12]),
    .D(p_vz[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vz_12_s0.INIT=1'b0;
  DFFRE c_vz_11_s0 (
    .Q(c_vz[11]),
    .D(p_vz[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vz_11_s0.INIT=1'b0;
  DFFRE c_vz_10_s0 (
    .Q(c_vz[10]),
    .D(p_vz[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vz_10_s0.INIT=1'b0;
  DFFRE c_vz_9_s0 (
    .Q(c_vz[9]),
    .D(p_vz[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vz_9_s0.INIT=1'b0;
  DFFRE c_vz_8_s0 (
    .Q(c_vz[8]),
    .D(p_vz[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vz_8_s0.INIT=1'b0;
  DFFRE c_vz_7_s0 (
    .Q(c_vz[7]),
    .D(p_vz[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vz_7_s0.INIT=1'b0;
  DFFRE c_vz_6_s0 (
    .Q(c_vz[6]),
    .D(p_vz[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vz_6_s0.INIT=1'b0;
  DFFRE c_vz_5_s0 (
    .Q(c_vz[5]),
    .D(p_vz[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vz_5_s0.INIT=1'b0;
  DFFRE c_vz_4_s0 (
    .Q(c_vz[4]),
    .D(p_vz[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vz_4_s0.INIT=1'b0;
  DFFRE c_vz_3_s0 (
    .Q(c_vz[3]),
    .D(p_vz[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vz_3_s0.INIT=1'b0;
  DFFRE c_vz_2_s0 (
    .Q(c_vz[2]),
    .D(p_vz[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vz_2_s0.INIT=1'b0;
  DFFRE c_vz_1_s0 (
    .Q(c_vz[1]),
    .D(p_vz[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vz_1_s0.INIT=1'b0;
  DFFRE c_vz_0_s0 (
    .Q(c_vz[0]),
    .D(p_vz[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_vz_0_s0.INIT=1'b0;
  DFFRE c_collective_15_s0 (
    .Q(c_collective[15]),
    .D(p_collective[15]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_collective_15_s0.INIT=1'b0;
  DFFRE c_collective_11_s0 (
    .Q(c_collective[11]),
    .D(p_collective[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_collective_11_s0.INIT=1'b0;
  DFFRE c_collective_10_s0 (
    .Q(c_collective[10]),
    .D(p_collective[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_collective_10_s0.INIT=1'b0;
  DFFRE c_collective_9_s0 (
    .Q(c_collective[9]),
    .D(p_collective[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_collective_9_s0.INIT=1'b0;
  DFFRE c_collective_8_s0 (
    .Q(c_collective[8]),
    .D(p_collective[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_collective_8_s0.INIT=1'b0;
  DFFRE c_collective_7_s0 (
    .Q(c_collective[7]),
    .D(p_collective[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_collective_7_s0.INIT=1'b0;
  DFFRE c_collective_6_s0 (
    .Q(c_collective[6]),
    .D(p_collective[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_collective_6_s0.INIT=1'b0;
  DFFRE c_collective_5_s0 (
    .Q(c_collective[5]),
    .D(p_collective[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_collective_5_s0.INIT=1'b0;
  DFFRE c_collective_4_s0 (
    .Q(c_collective[4]),
    .D(p_collective[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_collective_4_s0.INIT=1'b0;
  DFFRE c_collective_3_s0 (
    .Q(c_collective[3]),
    .D(p_collective[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_collective_3_s0.INIT=1'b0;
  DFFRE c_collective_2_s0 (
    .Q(c_collective[2]),
    .D(p_collective[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_collective_2_s0.INIT=1'b0;
  DFFRE c_collective_1_s0 (
    .Q(c_collective[1]),
    .D(p_collective[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_collective_1_s0.INIT=1'b0;
  DFFRE c_collective_0_s0 (
    .Q(c_collective[0]),
    .D(p_collective[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(VCC) 
);
defparam c_collective_0_s0.INIT=1'b0;
  DFFRE navigation_sequence_31_s0 (
    .Q(navigation_sequence[31]),
    .D(n5070_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(geometry_update) 
);
defparam navigation_sequence_31_s0.INIT=1'b0;
  DFFRE navigation_sequence_30_s0 (
    .Q(navigation_sequence[30]),
    .D(n5071_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(geometry_update) 
);
defparam navigation_sequence_30_s0.INIT=1'b0;
  DFFRE navigation_sequence_29_s0 (
    .Q(navigation_sequence[29]),
    .D(n5072_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(geometry_update) 
);
defparam navigation_sequence_29_s0.INIT=1'b0;
  DFFRE navigation_sequence_28_s0 (
    .Q(navigation_sequence[28]),
    .D(n5073_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(geometry_update) 
);
defparam navigation_sequence_28_s0.INIT=1'b0;
  DFFRE navigation_sequence_27_s0 (
    .Q(navigation_sequence[27]),
    .D(n5074_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(geometry_update) 
);
defparam navigation_sequence_27_s0.INIT=1'b0;
  DFFRE navigation_sequence_26_s0 (
    .Q(navigation_sequence[26]),
    .D(n5075_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(geometry_update) 
);
defparam navigation_sequence_26_s0.INIT=1'b0;
  DFFRE navigation_sequence_25_s0 (
    .Q(navigation_sequence[25]),
    .D(n5076_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(geometry_update) 
);
defparam navigation_sequence_25_s0.INIT=1'b0;
  DFFRE navigation_sequence_24_s0 (
    .Q(navigation_sequence[24]),
    .D(n5077_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(geometry_update) 
);
defparam navigation_sequence_24_s0.INIT=1'b0;
  DFFRE navigation_sequence_23_s0 (
    .Q(navigation_sequence[23]),
    .D(n5078_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(geometry_update) 
);
defparam navigation_sequence_23_s0.INIT=1'b0;
  DFFRE navigation_sequence_22_s0 (
    .Q(navigation_sequence[22]),
    .D(n5079_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(geometry_update) 
);
defparam navigation_sequence_22_s0.INIT=1'b0;
  DFFRE navigation_sequence_21_s0 (
    .Q(navigation_sequence[21]),
    .D(n5080_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(geometry_update) 
);
defparam navigation_sequence_21_s0.INIT=1'b0;
  DFFRE navigation_sequence_20_s0 (
    .Q(navigation_sequence[20]),
    .D(n5081_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(geometry_update) 
);
defparam navigation_sequence_20_s0.INIT=1'b0;
  DFFRE navigation_sequence_19_s0 (
    .Q(navigation_sequence[19]),
    .D(n5082_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(geometry_update) 
);
defparam navigation_sequence_19_s0.INIT=1'b0;
  DFFRE navigation_sequence_18_s0 (
    .Q(navigation_sequence[18]),
    .D(n5083_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(geometry_update) 
);
defparam navigation_sequence_18_s0.INIT=1'b0;
  DFFRE navigation_sequence_17_s0 (
    .Q(navigation_sequence[17]),
    .D(n5084_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(geometry_update) 
);
defparam navigation_sequence_17_s0.INIT=1'b0;
  DFFRE navigation_sequence_16_s0 (
    .Q(navigation_sequence[16]),
    .D(n5085_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(geometry_update) 
);
defparam navigation_sequence_16_s0.INIT=1'b0;
  DFFRE navigation_sequence_15_s0 (
    .Q(navigation_sequence[15]),
    .D(n5086_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(geometry_update) 
);
defparam navigation_sequence_15_s0.INIT=1'b0;
  DFFRE navigation_sequence_14_s0 (
    .Q(navigation_sequence[14]),
    .D(n5087_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(geometry_update) 
);
defparam navigation_sequence_14_s0.INIT=1'b0;
  DFFRE navigation_sequence_13_s0 (
    .Q(navigation_sequence[13]),
    .D(n5088_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(geometry_update) 
);
defparam navigation_sequence_13_s0.INIT=1'b0;
  DFFRE navigation_sequence_12_s0 (
    .Q(navigation_sequence[12]),
    .D(n5089_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(geometry_update) 
);
defparam navigation_sequence_12_s0.INIT=1'b0;
  DFFRE navigation_sequence_11_s0 (
    .Q(navigation_sequence[11]),
    .D(n5090_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(geometry_update) 
);
defparam navigation_sequence_11_s0.INIT=1'b0;
  DFFRE navigation_sequence_10_s0 (
    .Q(navigation_sequence[10]),
    .D(n5091_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(geometry_update) 
);
defparam navigation_sequence_10_s0.INIT=1'b0;
  DFFRE navigation_sequence_9_s0 (
    .Q(navigation_sequence[9]),
    .D(n5092_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(geometry_update) 
);
defparam navigation_sequence_9_s0.INIT=1'b0;
  DFFRE navigation_sequence_8_s0 (
    .Q(navigation_sequence[8]),
    .D(n5093_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(geometry_update) 
);
defparam navigation_sequence_8_s0.INIT=1'b0;
  DFFRE navigation_sequence_7_s0 (
    .Q(navigation_sequence[7]),
    .D(n5094_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(geometry_update) 
);
defparam navigation_sequence_7_s0.INIT=1'b0;
  DFFRE navigation_sequence_6_s0 (
    .Q(navigation_sequence[6]),
    .D(n5095_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(geometry_update) 
);
defparam navigation_sequence_6_s0.INIT=1'b0;
  DFFRE navigation_sequence_5_s0 (
    .Q(navigation_sequence[5]),
    .D(n5096_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(geometry_update) 
);
defparam navigation_sequence_5_s0.INIT=1'b0;
  DFFRE navigation_sequence_4_s0 (
    .Q(navigation_sequence[4]),
    .D(n5097_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(geometry_update) 
);
defparam navigation_sequence_4_s0.INIT=1'b0;
  DFFRE navigation_sequence_3_s0 (
    .Q(navigation_sequence[3]),
    .D(n5098_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(geometry_update) 
);
defparam navigation_sequence_3_s0.INIT=1'b0;
  DFFRE navigation_sequence_2_s0 (
    .Q(navigation_sequence[2]),
    .D(n5099_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(geometry_update) 
);
defparam navigation_sequence_2_s0.INIT=1'b0;
  DFFRE navigation_sequence_1_s0 (
    .Q(navigation_sequence[1]),
    .D(n5100_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(geometry_update) 
);
defparam navigation_sequence_1_s0.INIT=1'b0;
  DFFRE navigation_sequence_0_s0 (
    .Q(navigation_sequence[0]),
    .D(n5101_6),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(geometry_update) 
);
defparam navigation_sequence_0_s0.INIT=1'b0;
  DFFRE diagnostic_q_709_s0 (
    .Q(navigation_body_709),
    .D(position_ready),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_709_s0.INIT=1'b0;
  DFFRE diagnostic_q_708_s0 (
    .Q(navigation_body_708),
    .D(live_velocity),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_708_s0.INIT=1'b0;
  DFFRE diagnostic_q_707_s0 (
    .Q(navigation_body_707),
    .D(nav_vertical_ready),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_707_s0.INIT=1'b0;
  DFFRE diagnostic_q_706_s0 (
    .Q(navigation_body_706),
    .D(geometry_flow_ready),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_706_s0.INIT=1'b0;
  DFFRE diagnostic_q_705_s0 (
    .Q(navigation_body_705),
    .D(geometry_height_ready),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_705_s0.INIT=1'b0;
  DFFRE diagnostic_q_704_s0 (
    .Q(navigation_body_704),
    .D(module_fresh),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_704_s0.INIT=1'b0;
  DFFRE diagnostic_q_687_s0 (
    .Q(navigation_body_687),
    .D(uptime_ms[63]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_687_s0.INIT=1'b0;
  DFFRE diagnostic_q_686_s0 (
    .Q(navigation_body_686),
    .D(uptime_ms[62]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_686_s0.INIT=1'b0;
  DFFRE diagnostic_q_685_s0 (
    .Q(navigation_body_685),
    .D(uptime_ms[61]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_685_s0.INIT=1'b0;
  DFFRE diagnostic_q_684_s0 (
    .Q(navigation_body_684),
    .D(uptime_ms[60]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_684_s0.INIT=1'b0;
  DFFRE diagnostic_q_683_s0 (
    .Q(navigation_body_683),
    .D(uptime_ms[59]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_683_s0.INIT=1'b0;
  DFFRE diagnostic_q_682_s0 (
    .Q(navigation_body_682),
    .D(uptime_ms[58]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_682_s0.INIT=1'b0;
  DFFRE diagnostic_q_681_s0 (
    .Q(navigation_body_681),
    .D(uptime_ms[57]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_681_s0.INIT=1'b0;
  DFFRE diagnostic_q_680_s0 (
    .Q(navigation_body_680),
    .D(uptime_ms[56]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_680_s0.INIT=1'b0;
  DFFRE diagnostic_q_679_s0 (
    .Q(navigation_body_679),
    .D(uptime_ms[55]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_679_s0.INIT=1'b0;
  DFFRE diagnostic_q_678_s0 (
    .Q(navigation_body_678),
    .D(uptime_ms[54]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_678_s0.INIT=1'b0;
  DFFRE diagnostic_q_677_s0 (
    .Q(navigation_body_677),
    .D(uptime_ms[53]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_677_s0.INIT=1'b0;
  DFFRE diagnostic_q_676_s0 (
    .Q(navigation_body_676),
    .D(uptime_ms[52]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_676_s0.INIT=1'b0;
  DFFRE diagnostic_q_675_s0 (
    .Q(navigation_body_675),
    .D(uptime_ms[51]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_675_s0.INIT=1'b0;
  DFFRE diagnostic_q_674_s0 (
    .Q(navigation_body_674),
    .D(uptime_ms[50]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_674_s0.INIT=1'b0;
  DFFRE diagnostic_q_673_s0 (
    .Q(navigation_body_673),
    .D(uptime_ms[49]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_673_s0.INIT=1'b0;
  DFFRE diagnostic_q_672_s0 (
    .Q(navigation_body_672),
    .D(uptime_ms[48]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_672_s0.INIT=1'b0;
  DFFRE diagnostic_q_671_s0 (
    .Q(navigation_body_671),
    .D(uptime_ms[47]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_671_s0.INIT=1'b0;
  DFFRE diagnostic_q_670_s0 (
    .Q(navigation_body_670),
    .D(uptime_ms[46]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_670_s0.INIT=1'b0;
  DFFRE diagnostic_q_669_s0 (
    .Q(navigation_body_669),
    .D(uptime_ms[45]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_669_s0.INIT=1'b0;
  DFFRE diagnostic_q_668_s0 (
    .Q(navigation_body_668),
    .D(uptime_ms[44]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_668_s0.INIT=1'b0;
  DFFRE diagnostic_q_667_s0 (
    .Q(navigation_body_667),
    .D(uptime_ms[43]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_667_s0.INIT=1'b0;
  DFFRE diagnostic_q_666_s0 (
    .Q(navigation_body_666),
    .D(uptime_ms[42]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_666_s0.INIT=1'b0;
  DFFRE diagnostic_q_665_s0 (
    .Q(navigation_body_665),
    .D(uptime_ms[41]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_665_s0.INIT=1'b0;
  DFFRE diagnostic_q_664_s0 (
    .Q(navigation_body_664),
    .D(uptime_ms[40]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_664_s0.INIT=1'b0;
  DFFRE diagnostic_q_663_s0 (
    .Q(navigation_body_663),
    .D(uptime_ms[39]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_663_s0.INIT=1'b0;
  DFFRE diagnostic_q_662_s0 (
    .Q(navigation_body_662),
    .D(uptime_ms[38]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_662_s0.INIT=1'b0;
  DFFRE diagnostic_q_661_s0 (
    .Q(navigation_body_661),
    .D(uptime_ms[37]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_661_s0.INIT=1'b0;
  DFFRE diagnostic_q_660_s0 (
    .Q(navigation_body_660),
    .D(uptime_ms[36]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_660_s0.INIT=1'b0;
  DFFRE diagnostic_q_659_s0 (
    .Q(navigation_body_659),
    .D(uptime_ms[35]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_659_s0.INIT=1'b0;
  DFFRE diagnostic_q_658_s0 (
    .Q(navigation_body_658),
    .D(uptime_ms[34]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_658_s0.INIT=1'b0;
  DFFRE diagnostic_q_657_s0 (
    .Q(navigation_body_657),
    .D(uptime_ms[33]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_657_s0.INIT=1'b0;
  DFFRE diagnostic_q_656_s0 (
    .Q(navigation_body_656),
    .D(uptime_ms[32]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_656_s0.INIT=1'b0;
  DFFRE diagnostic_q_655_s0 (
    .Q(navigation_body_655),
    .D(uptime_ms[31]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_655_s0.INIT=1'b0;
  DFFRE diagnostic_q_654_s0 (
    .Q(navigation_body_654),
    .D(uptime_ms[30]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_654_s0.INIT=1'b0;
  DFFRE diagnostic_q_653_s0 (
    .Q(navigation_body_653),
    .D(uptime_ms[29]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_653_s0.INIT=1'b0;
  DFFRE diagnostic_q_652_s0 (
    .Q(navigation_body_652),
    .D(uptime_ms[28]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_652_s0.INIT=1'b0;
  DFFRE diagnostic_q_651_s0 (
    .Q(navigation_body_651),
    .D(uptime_ms[27]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_651_s0.INIT=1'b0;
  DFFRE diagnostic_q_650_s0 (
    .Q(navigation_body_650),
    .D(uptime_ms[26]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_650_s0.INIT=1'b0;
  DFFRE diagnostic_q_649_s0 (
    .Q(navigation_body_649),
    .D(uptime_ms[25]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_649_s0.INIT=1'b0;
  DFFRE diagnostic_q_648_s0 (
    .Q(navigation_body_648),
    .D(uptime_ms[24]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_648_s0.INIT=1'b0;
  DFFRE diagnostic_q_647_s0 (
    .Q(navigation_body_647),
    .D(uptime_ms[23]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_647_s0.INIT=1'b0;
  DFFRE diagnostic_q_646_s0 (
    .Q(navigation_body_646),
    .D(uptime_ms[22]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_646_s0.INIT=1'b0;
  DFFRE diagnostic_q_645_s0 (
    .Q(navigation_body_645),
    .D(uptime_ms[21]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_645_s0.INIT=1'b0;
  DFFRE diagnostic_q_644_s0 (
    .Q(navigation_body_644),
    .D(uptime_ms[20]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_644_s0.INIT=1'b0;
  DFFRE diagnostic_q_643_s0 (
    .Q(navigation_body_643),
    .D(uptime_ms[19]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_643_s0.INIT=1'b0;
  DFFRE diagnostic_q_642_s0 (
    .Q(navigation_body_642),
    .D(uptime_ms[18]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_642_s0.INIT=1'b0;
  DFFRE diagnostic_q_641_s0 (
    .Q(navigation_body_641),
    .D(uptime_ms[17]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_641_s0.INIT=1'b0;
  DFFRE diagnostic_q_640_s0 (
    .Q(navigation_body_640),
    .D(uptime_ms[16]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_640_s0.INIT=1'b0;
  DFFRE diagnostic_q_639_s0 (
    .Q(navigation_body_639),
    .D(uptime_ms[15]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_639_s0.INIT=1'b0;
  DFFRE diagnostic_q_638_s0 (
    .Q(navigation_body_638),
    .D(uptime_ms[14]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_638_s0.INIT=1'b0;
  DFFRE diagnostic_q_637_s0 (
    .Q(navigation_body_637),
    .D(uptime_ms[13]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_637_s0.INIT=1'b0;
  DFFRE diagnostic_q_636_s0 (
    .Q(navigation_body_636),
    .D(uptime_ms[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_636_s0.INIT=1'b0;
  DFFRE diagnostic_q_635_s0 (
    .Q(navigation_body_635),
    .D(uptime_ms[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_635_s0.INIT=1'b0;
  DFFRE diagnostic_q_634_s0 (
    .Q(navigation_body_634),
    .D(uptime_ms[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_634_s0.INIT=1'b0;
  DFFRE diagnostic_q_633_s0 (
    .Q(navigation_body_633),
    .D(uptime_ms[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_633_s0.INIT=1'b0;
  DFFRE diagnostic_q_632_s0 (
    .Q(navigation_body_632),
    .D(uptime_ms[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_632_s0.INIT=1'b0;
  DFFRE diagnostic_q_631_s0 (
    .Q(navigation_body_631),
    .D(uptime_ms[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_631_s0.INIT=1'b0;
  DFFRE diagnostic_q_630_s0 (
    .Q(navigation_body_630),
    .D(uptime_ms[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_630_s0.INIT=1'b0;
  DFFRE diagnostic_q_629_s0 (
    .Q(navigation_body_629),
    .D(uptime_ms[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_629_s0.INIT=1'b0;
  DFFRE diagnostic_q_628_s0 (
    .Q(navigation_body_628),
    .D(uptime_ms[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_628_s0.INIT=1'b0;
  DFFRE diagnostic_q_627_s0 (
    .Q(navigation_body_627),
    .D(uptime_ms[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_627_s0.INIT=1'b0;
  DFFRE diagnostic_q_626_s0 (
    .Q(navigation_body_626),
    .D(uptime_ms[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_626_s0.INIT=1'b0;
  DFFRE diagnostic_q_625_s0 (
    .Q(navigation_body_625),
    .D(uptime_ms[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_625_s0.INIT=1'b0;
  DFFRE diagnostic_q_624_s0 (
    .Q(navigation_body_624),
    .D(uptime_ms[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_624_s0.INIT=1'b0;
  DFFRE diagnostic_q_623_s0 (
    .Q(navigation_body_623),
    .D(navigation_sequence[31]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_623_s0.INIT=1'b0;
  DFFRE diagnostic_q_622_s0 (
    .Q(navigation_body_622),
    .D(navigation_sequence[30]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_622_s0.INIT=1'b0;
  DFFRE diagnostic_q_621_s0 (
    .Q(navigation_body_621),
    .D(navigation_sequence[29]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_621_s0.INIT=1'b0;
  DFFRE diagnostic_q_620_s0 (
    .Q(navigation_body_620),
    .D(navigation_sequence[28]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_620_s0.INIT=1'b0;
  DFFRE diagnostic_q_619_s0 (
    .Q(navigation_body_619),
    .D(navigation_sequence[27]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_619_s0.INIT=1'b0;
  DFFRE diagnostic_q_618_s0 (
    .Q(navigation_body_618),
    .D(navigation_sequence[26]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_618_s0.INIT=1'b0;
  DFFRE diagnostic_q_617_s0 (
    .Q(navigation_body_617),
    .D(navigation_sequence[25]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_617_s0.INIT=1'b0;
  DFFRE diagnostic_q_616_s0 (
    .Q(navigation_body_616),
    .D(navigation_sequence[24]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_616_s0.INIT=1'b0;
  DFFRE diagnostic_q_615_s0 (
    .Q(navigation_body_615),
    .D(navigation_sequence[23]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_615_s0.INIT=1'b0;
  DFFRE diagnostic_q_614_s0 (
    .Q(navigation_body_614),
    .D(navigation_sequence[22]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_614_s0.INIT=1'b0;
  DFFRE diagnostic_q_613_s0 (
    .Q(navigation_body_613),
    .D(navigation_sequence[21]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_613_s0.INIT=1'b0;
  DFFRE diagnostic_q_612_s0 (
    .Q(navigation_body_612),
    .D(navigation_sequence[20]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_612_s0.INIT=1'b0;
  DFFRE diagnostic_q_611_s0 (
    .Q(navigation_body_611),
    .D(navigation_sequence[19]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_611_s0.INIT=1'b0;
  DFFRE diagnostic_q_610_s0 (
    .Q(navigation_body_610),
    .D(navigation_sequence[18]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_610_s0.INIT=1'b0;
  DFFRE diagnostic_q_609_s0 (
    .Q(navigation_body_609),
    .D(navigation_sequence[17]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_609_s0.INIT=1'b0;
  DFFRE diagnostic_q_608_s0 (
    .Q(navigation_body_608),
    .D(navigation_sequence[16]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_608_s0.INIT=1'b0;
  DFFRE diagnostic_q_607_s0 (
    .Q(navigation_body_607),
    .D(navigation_sequence[15]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_607_s0.INIT=1'b0;
  DFFRE diagnostic_q_606_s0 (
    .Q(navigation_body_606),
    .D(navigation_sequence[14]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_606_s0.INIT=1'b0;
  DFFRE diagnostic_q_605_s0 (
    .Q(navigation_body_605),
    .D(navigation_sequence[13]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_605_s0.INIT=1'b0;
  DFFRE diagnostic_q_604_s0 (
    .Q(navigation_body_604),
    .D(navigation_sequence[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_604_s0.INIT=1'b0;
  DFFRE diagnostic_q_603_s0 (
    .Q(navigation_body_603),
    .D(navigation_sequence[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_603_s0.INIT=1'b0;
  DFFRE diagnostic_q_602_s0 (
    .Q(navigation_body_602),
    .D(navigation_sequence[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_602_s0.INIT=1'b0;
  DFFRE diagnostic_q_601_s0 (
    .Q(navigation_body_601),
    .D(navigation_sequence[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_601_s0.INIT=1'b0;
  DFFRE diagnostic_q_600_s0 (
    .Q(navigation_body_600),
    .D(navigation_sequence[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_600_s0.INIT=1'b0;
  DFFRE diagnostic_q_599_s0 (
    .Q(navigation_body_599),
    .D(navigation_sequence[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_599_s0.INIT=1'b0;
  DFFRE diagnostic_q_598_s0 (
    .Q(navigation_body_598),
    .D(navigation_sequence[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_598_s0.INIT=1'b0;
  DFFRE diagnostic_q_597_s0 (
    .Q(navigation_body_597),
    .D(navigation_sequence[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_597_s0.INIT=1'b0;
  DFFRE diagnostic_q_596_s0 (
    .Q(navigation_body_596),
    .D(navigation_sequence[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_596_s0.INIT=1'b0;
  DFFRE diagnostic_q_595_s0 (
    .Q(navigation_body_595),
    .D(navigation_sequence[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_595_s0.INIT=1'b0;
  DFFRE diagnostic_q_594_s0 (
    .Q(navigation_body_594),
    .D(navigation_sequence[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_594_s0.INIT=1'b0;
  DFFRE diagnostic_q_593_s0 (
    .Q(navigation_body_593),
    .D(navigation_sequence[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_593_s0.INIT=1'b0;
  DFFRE diagnostic_q_592_s0 (
    .Q(navigation_body_592),
    .D(navigation_sequence[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_592_s0.INIT=1'b0;
  DFFSE diagnostic_q_591_s0 (
    .Q(navigation_body_591),
    .D(mtf_age_ms[31]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_591_s0.INIT=1'b1;
  DFFSE diagnostic_q_590_s0 (
    .Q(navigation_body_590),
    .D(mtf_age_ms[30]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_590_s0.INIT=1'b1;
  DFFSE diagnostic_q_589_s0 (
    .Q(navigation_body_589),
    .D(mtf_age_ms[29]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_589_s0.INIT=1'b1;
  DFFSE diagnostic_q_588_s0 (
    .Q(navigation_body_588),
    .D(mtf_age_ms[28]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_588_s0.INIT=1'b1;
  DFFSE diagnostic_q_587_s0 (
    .Q(navigation_body_587),
    .D(mtf_age_ms[27]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_587_s0.INIT=1'b1;
  DFFSE diagnostic_q_586_s0 (
    .Q(navigation_body_586),
    .D(mtf_age_ms[26]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_586_s0.INIT=1'b1;
  DFFSE diagnostic_q_585_s0 (
    .Q(navigation_body_585),
    .D(mtf_age_ms[25]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_585_s0.INIT=1'b1;
  DFFSE diagnostic_q_584_s0 (
    .Q(navigation_body_584),
    .D(mtf_age_ms[24]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_584_s0.INIT=1'b1;
  DFFSE diagnostic_q_583_s0 (
    .Q(navigation_body_583),
    .D(mtf_age_ms[23]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_583_s0.INIT=1'b1;
  DFFSE diagnostic_q_582_s0 (
    .Q(navigation_body_582),
    .D(mtf_age_ms[22]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_582_s0.INIT=1'b1;
  DFFSE diagnostic_q_581_s0 (
    .Q(navigation_body_581),
    .D(mtf_age_ms[21]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_581_s0.INIT=1'b1;
  DFFSE diagnostic_q_580_s0 (
    .Q(navigation_body_580),
    .D(mtf_age_ms[20]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_580_s0.INIT=1'b1;
  DFFSE diagnostic_q_579_s0 (
    .Q(navigation_body_579),
    .D(mtf_age_ms[19]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_579_s0.INIT=1'b1;
  DFFSE diagnostic_q_578_s0 (
    .Q(navigation_body_578),
    .D(mtf_age_ms[18]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_578_s0.INIT=1'b1;
  DFFSE diagnostic_q_577_s0 (
    .Q(navigation_body_577),
    .D(mtf_age_ms[17]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_577_s0.INIT=1'b1;
  DFFSE diagnostic_q_576_s0 (
    .Q(navigation_body_576),
    .D(mtf_age_ms[16]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_576_s0.INIT=1'b1;
  DFFSE diagnostic_q_575_s0 (
    .Q(navigation_body_575),
    .D(mtf_age_ms[15]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_575_s0.INIT=1'b1;
  DFFSE diagnostic_q_574_s0 (
    .Q(navigation_body_574),
    .D(mtf_age_ms[14]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_574_s0.INIT=1'b1;
  DFFSE diagnostic_q_573_s0 (
    .Q(navigation_body_573),
    .D(mtf_age_ms[13]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_573_s0.INIT=1'b1;
  DFFSE diagnostic_q_572_s0 (
    .Q(navigation_body_572),
    .D(mtf_age_ms[12]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_572_s0.INIT=1'b1;
  DFFSE diagnostic_q_571_s0 (
    .Q(navigation_body_571),
    .D(mtf_age_ms[11]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_571_s0.INIT=1'b1;
  DFFSE diagnostic_q_570_s0 (
    .Q(navigation_body_570),
    .D(mtf_age_ms[10]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_570_s0.INIT=1'b1;
  DFFSE diagnostic_q_569_s0 (
    .Q(navigation_body_569),
    .D(mtf_age_ms[9]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_569_s0.INIT=1'b1;
  DFFSE diagnostic_q_568_s0 (
    .Q(navigation_body_568),
    .D(mtf_age_ms[8]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_568_s0.INIT=1'b1;
  DFFSE diagnostic_q_567_s0 (
    .Q(navigation_body_567),
    .D(mtf_age_ms[7]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_567_s0.INIT=1'b1;
  DFFSE diagnostic_q_566_s0 (
    .Q(navigation_body_566),
    .D(mtf_age_ms[6]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_566_s0.INIT=1'b1;
  DFFSE diagnostic_q_565_s0 (
    .Q(navigation_body_565),
    .D(mtf_age_ms[5]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_565_s0.INIT=1'b1;
  DFFSE diagnostic_q_564_s0 (
    .Q(navigation_body_564),
    .D(mtf_age_ms[4]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_564_s0.INIT=1'b1;
  DFFSE diagnostic_q_563_s0 (
    .Q(navigation_body_563),
    .D(mtf_age_ms[3]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_563_s0.INIT=1'b1;
  DFFSE diagnostic_q_562_s0 (
    .Q(navigation_body_562),
    .D(mtf_age_ms[2]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_562_s0.INIT=1'b1;
  DFFSE diagnostic_q_561_s0 (
    .Q(navigation_body_561),
    .D(mtf_age_ms[1]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_561_s0.INIT=1'b1;
  DFFSE diagnostic_q_560_s0 (
    .Q(navigation_body_560),
    .D(mtf_age_ms[0]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_560_s0.INIT=1'b1;
  DFFRE diagnostic_q_543_s0 (
    .Q(navigation_body_543),
    .D(geometry_dt_us[15]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_543_s0.INIT=1'b0;
  DFFRE diagnostic_q_542_s0 (
    .Q(navigation_body_542),
    .D(geometry_dt_us[14]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_542_s0.INIT=1'b0;
  DFFRE diagnostic_q_541_s0 (
    .Q(navigation_body_541),
    .D(geometry_dt_us[13]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_541_s0.INIT=1'b0;
  DFFRE diagnostic_q_540_s0 (
    .Q(navigation_body_540),
    .D(geometry_dt_us[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_540_s0.INIT=1'b0;
  DFFRE diagnostic_q_539_s0 (
    .Q(navigation_body_539),
    .D(geometry_dt_us[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_539_s0.INIT=1'b0;
  DFFRE diagnostic_q_538_s0 (
    .Q(navigation_body_538),
    .D(geometry_dt_us[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_538_s0.INIT=1'b0;
  DFFRE diagnostic_q_537_s0 (
    .Q(navigation_body_537),
    .D(geometry_dt_us[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_537_s0.INIT=1'b0;
  DFFRE diagnostic_q_536_s0 (
    .Q(navigation_body_536),
    .D(geometry_dt_us[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_536_s0.INIT=1'b0;
  DFFRE diagnostic_q_535_s0 (
    .Q(navigation_body_535),
    .D(geometry_dt_us[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_535_s0.INIT=1'b0;
  DFFRE diagnostic_q_534_s0 (
    .Q(navigation_body_534),
    .D(geometry_dt_us[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_534_s0.INIT=1'b0;
  DFFRE diagnostic_q_533_s0 (
    .Q(navigation_body_533),
    .D(geometry_dt_us[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_533_s0.INIT=1'b0;
  DFFRE diagnostic_q_532_s0 (
    .Q(navigation_body_532),
    .D(geometry_dt_us[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_532_s0.INIT=1'b0;
  DFFRE diagnostic_q_531_s0 (
    .Q(navigation_body_531),
    .D(geometry_dt_us[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_531_s0.INIT=1'b0;
  DFFRE diagnostic_q_530_s0 (
    .Q(navigation_body_530),
    .D(geometry_dt_us[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_530_s0.INIT=1'b0;
  DFFRE diagnostic_q_529_s0 (
    .Q(navigation_body_529),
    .D(geometry_dt_us[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_529_s0.INIT=1'b0;
  DFFRE diagnostic_q_528_s0 (
    .Q(navigation_body_528),
    .D(geometry_dt_us[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_528_s0.INIT=1'b0;
  DFFRE diagnostic_q_526_s0 (
    .Q(navigation_body_526),
    .D(nav_xy_reason_10),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_526_s0.INIT=1'b0;
  DFFRE diagnostic_q_525_s0 (
    .Q(navigation_body_525),
    .D(nav_xy_reason_9),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_525_s0.INIT=1'b0;
  DFFRE diagnostic_q_524_s0 (
    .Q(navigation_body_524),
    .D(nav_xy_reason_8),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_524_s0.INIT=1'b0;
  DFFRE diagnostic_q_523_s0 (
    .Q(navigation_body_523),
    .D(nav_xy_reason_7),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_523_s0.INIT=1'b0;
  DFFRE diagnostic_q_522_s0 (
    .Q(navigation_body_522),
    .D(nav_xy_reason_6),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_522_s0.INIT=1'b0;
  DFFRE diagnostic_q_518_s0 (
    .Q(navigation_body_518),
    .D(nav_xy_reason_2),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_518_s0.INIT=1'b0;
  DFFRE diagnostic_q_517_s0 (
    .Q(navigation_body_517),
    .D(nav_xy_reason_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_517_s0.INIT=1'b0;
  DFFSE diagnostic_q_516_s0 (
    .Q(navigation_body_516),
    .D(nav_xy_reason_0[0]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_516_s0.INIT=1'b1;
  DFFSE diagnostic_q_514_s0 (
    .Q(navigation_body_514),
    .D(reasons[18]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_514_s0.INIT=1'b1;
  DFFSE diagnostic_q_512_s0 (
    .Q(navigation_body_512),
    .D(reasons[16]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_512_s0.INIT=1'b1;
  DFFRE diagnostic_q_507_s0 (
    .Q(navigation_body_507),
    .D(geometry_reason[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_507_s0.INIT=1'b0;
  DFFRE diagnostic_q_506_s0 (
    .Q(navigation_body_506),
    .D(observer_reset),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_506_s0.INIT=1'b0;
  DFFRE diagnostic_q_505_s0 (
    .Q(navigation_body_505),
    .D(VCC),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_505_s0.INIT=1'b0;
  DFFSE diagnostic_q_503_s0 (
    .Q(navigation_body_503),
    .D(geometry_reason_7_4),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_503_s0.INIT=1'b1;
  DFFRE diagnostic_q_502_s0 (
    .Q(navigation_body_502),
    .D(geometry_reason[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_502_s0.INIT=1'b0;
  DFFRE diagnostic_q_501_s0 (
    .Q(navigation_body_501),
    .D(geometry_reason[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_501_s0.INIT=1'b0;
  DFFRE diagnostic_q_500_s0 (
    .Q(navigation_body_500),
    .D(geometry_reason[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_500_s0.INIT=1'b0;
  DFFRE diagnostic_q_499_s0 (
    .Q(navigation_body_499),
    .D(geometry_reason[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_499_s0.INIT=1'b0;
  DFFRE diagnostic_q_498_s0 (
    .Q(navigation_body_498),
    .D(geometry_reason[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_498_s0.INIT=1'b0;
  DFFRE diagnostic_q_497_s0 (
    .Q(navigation_body_497),
    .D(geometry_reason[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_497_s0.INIT=1'b0;
  DFFRE diagnostic_q_496_s0 (
    .Q(navigation_body_496),
    .D(geometry_reason[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_496_s0.INIT=1'b0;
  DFFRE diagnostic_q_495_s0 (
    .Q(navigation_body_495),
    .D(height_mm_Z[31]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_495_s0.INIT=1'b0;
  DFFRE diagnostic_q_476_s0 (
    .Q(navigation_body_476),
    .D(height_mm_Z[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_476_s0.INIT=1'b0;
  DFFRE diagnostic_q_475_s0 (
    .Q(navigation_body_475),
    .D(height_mm_Z[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_475_s0.INIT=1'b0;
  DFFRE diagnostic_q_474_s0 (
    .Q(navigation_body_474),
    .D(height_mm_Z[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_474_s0.INIT=1'b0;
  DFFRE diagnostic_q_473_s0 (
    .Q(navigation_body_473),
    .D(height_mm_Z[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_473_s0.INIT=1'b0;
  DFFRE diagnostic_q_472_s0 (
    .Q(navigation_body_472),
    .D(height_mm_Z[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_472_s0.INIT=1'b0;
  DFFRE diagnostic_q_471_s0 (
    .Q(navigation_body_471),
    .D(height_mm_Z[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_471_s0.INIT=1'b0;
  DFFRE diagnostic_q_470_s0 (
    .Q(navigation_body_470),
    .D(height_mm_Z[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_470_s0.INIT=1'b0;
  DFFRE diagnostic_q_469_s0 (
    .Q(navigation_body_469),
    .D(height_mm_Z[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_469_s0.INIT=1'b0;
  DFFRE diagnostic_q_468_s0 (
    .Q(navigation_body_468),
    .D(height_mm_Z[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_468_s0.INIT=1'b0;
  DFFRE diagnostic_q_467_s0 (
    .Q(navigation_body_467),
    .D(height_mm_Z[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_467_s0.INIT=1'b0;
  DFFRE diagnostic_q_466_s0 (
    .Q(navigation_body_466),
    .D(height_mm_Z[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_466_s0.INIT=1'b0;
  DFFRE diagnostic_q_465_s0 (
    .Q(navigation_body_465),
    .D(height_mm_Z[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_465_s0.INIT=1'b0;
  DFFRE diagnostic_q_464_s0 (
    .Q(navigation_body_464),
    .D(height_mm_Z[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_464_s0.INIT=1'b0;
  DFFRE diagnostic_q_463_s0 (
    .Q(navigation_body_463),
    .D(bvx[31]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_463_s0.INIT=1'b0;
  DFFRE diagnostic_q_461_s0 (
    .Q(navigation_body_461),
    .D(bvx[29]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_461_s0.INIT=1'b0;
  DFFRE diagnostic_q_460_s0 (
    .Q(navigation_body_460),
    .D(bvx[28]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_460_s0.INIT=1'b0;
  DFFRE diagnostic_q_459_s0 (
    .Q(navigation_body_459),
    .D(bvx[27]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_459_s0.INIT=1'b0;
  DFFRE diagnostic_q_458_s0 (
    .Q(navigation_body_458),
    .D(bvx[26]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_458_s0.INIT=1'b0;
  DFFRE diagnostic_q_457_s0 (
    .Q(navigation_body_457),
    .D(bvx[25]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_457_s0.INIT=1'b0;
  DFFRE diagnostic_q_456_s0 (
    .Q(navigation_body_456),
    .D(bvx[24]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_456_s0.INIT=1'b0;
  DFFRE diagnostic_q_455_s0 (
    .Q(navigation_body_455),
    .D(bvx[23]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_455_s0.INIT=1'b0;
  DFFRE diagnostic_q_454_s0 (
    .Q(navigation_body_454),
    .D(bvx[22]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_454_s0.INIT=1'b0;
  DFFRE diagnostic_q_453_s0 (
    .Q(navigation_body_453),
    .D(bvx[21]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_453_s0.INIT=1'b0;
  DFFRE diagnostic_q_452_s0 (
    .Q(navigation_body_452),
    .D(bvx[20]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_452_s0.INIT=1'b0;
  DFFRE diagnostic_q_451_s0 (
    .Q(navigation_body_451),
    .D(bvx[19]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_451_s0.INIT=1'b0;
  DFFRE diagnostic_q_450_s0 (
    .Q(navigation_body_450),
    .D(bvx[18]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_450_s0.INIT=1'b0;
  DFFRE diagnostic_q_449_s0 (
    .Q(navigation_body_449),
    .D(bvx[17]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_449_s0.INIT=1'b0;
  DFFRE diagnostic_q_448_s0 (
    .Q(navigation_body_448),
    .D(bvx[16]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_448_s0.INIT=1'b0;
  DFFRE diagnostic_q_447_s0 (
    .Q(navigation_body_447),
    .D(bvx[15]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_447_s0.INIT=1'b0;
  DFFRE diagnostic_q_446_s0 (
    .Q(navigation_body_446),
    .D(bvx[14]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_446_s0.INIT=1'b0;
  DFFRE diagnostic_q_445_s0 (
    .Q(navigation_body_445),
    .D(bvx[13]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_445_s0.INIT=1'b0;
  DFFRE diagnostic_q_444_s0 (
    .Q(navigation_body_444),
    .D(bvx[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_444_s0.INIT=1'b0;
  DFFRE diagnostic_q_443_s0 (
    .Q(navigation_body_443),
    .D(bvx[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_443_s0.INIT=1'b0;
  DFFRE diagnostic_q_442_s0 (
    .Q(navigation_body_442),
    .D(bvx[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_442_s0.INIT=1'b0;
  DFFRE diagnostic_q_441_s0 (
    .Q(navigation_body_441),
    .D(bvx[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_441_s0.INIT=1'b0;
  DFFRE diagnostic_q_440_s0 (
    .Q(navigation_body_440),
    .D(bvx[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_440_s0.INIT=1'b0;
  DFFRE diagnostic_q_439_s0 (
    .Q(navigation_body_439),
    .D(bvx[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_439_s0.INIT=1'b0;
  DFFRE diagnostic_q_438_s0 (
    .Q(navigation_body_438),
    .D(bvx[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_438_s0.INIT=1'b0;
  DFFRE diagnostic_q_437_s0 (
    .Q(navigation_body_437),
    .D(bvx[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_437_s0.INIT=1'b0;
  DFFRE diagnostic_q_436_s0 (
    .Q(navigation_body_436),
    .D(bvx[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_436_s0.INIT=1'b0;
  DFFRE diagnostic_q_435_s0 (
    .Q(navigation_body_435),
    .D(bvx[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_435_s0.INIT=1'b0;
  DFFRE diagnostic_q_434_s0 (
    .Q(navigation_body_434),
    .D(bvx[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_434_s0.INIT=1'b0;
  DFFRE diagnostic_q_433_s0 (
    .Q(navigation_body_433),
    .D(bvx[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_433_s0.INIT=1'b0;
  DFFRE diagnostic_q_432_s0 (
    .Q(navigation_body_432),
    .D(bvx[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_432_s0.INIT=1'b0;
  DFFRE diagnostic_q_431_s0 (
    .Q(navigation_body_431),
    .D(bvy[31]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_431_s0.INIT=1'b0;
  DFFRE diagnostic_q_429_s0 (
    .Q(navigation_body_429),
    .D(bvy[29]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_429_s0.INIT=1'b0;
  DFFRE diagnostic_q_428_s0 (
    .Q(navigation_body_428),
    .D(bvy[28]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_428_s0.INIT=1'b0;
  DFFRE diagnostic_q_427_s0 (
    .Q(navigation_body_427),
    .D(bvy[27]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_427_s0.INIT=1'b0;
  DFFRE diagnostic_q_426_s0 (
    .Q(navigation_body_426),
    .D(bvy[26]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_426_s0.INIT=1'b0;
  DFFRE diagnostic_q_425_s0 (
    .Q(navigation_body_425),
    .D(bvy[25]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_425_s0.INIT=1'b0;
  DFFRE diagnostic_q_424_s0 (
    .Q(navigation_body_424),
    .D(bvy[24]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_424_s0.INIT=1'b0;
  DFFRE diagnostic_q_423_s0 (
    .Q(navigation_body_423),
    .D(bvy[23]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_423_s0.INIT=1'b0;
  DFFRE diagnostic_q_422_s0 (
    .Q(navigation_body_422),
    .D(bvy[22]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_422_s0.INIT=1'b0;
  DFFRE diagnostic_q_421_s0 (
    .Q(navigation_body_421),
    .D(bvy[21]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_421_s0.INIT=1'b0;
  DFFRE diagnostic_q_420_s0 (
    .Q(navigation_body_420),
    .D(bvy[20]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_420_s0.INIT=1'b0;
  DFFRE diagnostic_q_419_s0 (
    .Q(navigation_body_419),
    .D(bvy[19]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_419_s0.INIT=1'b0;
  DFFRE diagnostic_q_418_s0 (
    .Q(navigation_body_418),
    .D(bvy[18]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_418_s0.INIT=1'b0;
  DFFRE diagnostic_q_417_s0 (
    .Q(navigation_body_417),
    .D(bvy[17]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_417_s0.INIT=1'b0;
  DFFRE diagnostic_q_416_s0 (
    .Q(navigation_body_416),
    .D(bvy[16]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_416_s0.INIT=1'b0;
  DFFRE diagnostic_q_415_s0 (
    .Q(navigation_body_415),
    .D(bvy[15]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_415_s0.INIT=1'b0;
  DFFRE diagnostic_q_414_s0 (
    .Q(navigation_body_414),
    .D(bvy[14]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_414_s0.INIT=1'b0;
  DFFRE diagnostic_q_413_s0 (
    .Q(navigation_body_413),
    .D(bvy[13]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_413_s0.INIT=1'b0;
  DFFRE diagnostic_q_412_s0 (
    .Q(navigation_body_412),
    .D(bvy[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_412_s0.INIT=1'b0;
  DFFRE diagnostic_q_411_s0 (
    .Q(navigation_body_411),
    .D(bvy[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_411_s0.INIT=1'b0;
  DFFRE diagnostic_q_410_s0 (
    .Q(navigation_body_410),
    .D(bvy[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_410_s0.INIT=1'b0;
  DFFRE diagnostic_q_409_s0 (
    .Q(navigation_body_409),
    .D(bvy[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_409_s0.INIT=1'b0;
  DFFRE diagnostic_q_408_s0 (
    .Q(navigation_body_408),
    .D(bvy[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_408_s0.INIT=1'b0;
  DFFRE diagnostic_q_407_s0 (
    .Q(navigation_body_407),
    .D(bvy[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_407_s0.INIT=1'b0;
  DFFRE diagnostic_q_406_s0 (
    .Q(navigation_body_406),
    .D(bvy[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_406_s0.INIT=1'b0;
  DFFRE diagnostic_q_405_s0 (
    .Q(navigation_body_405),
    .D(bvy[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_405_s0.INIT=1'b0;
  DFFRE diagnostic_q_404_s0 (
    .Q(navigation_body_404),
    .D(bvy[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_404_s0.INIT=1'b0;
  DFFRE diagnostic_q_403_s0 (
    .Q(navigation_body_403),
    .D(bvy[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_403_s0.INIT=1'b0;
  DFFRE diagnostic_q_402_s0 (
    .Q(navigation_body_402),
    .D(bvy[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_402_s0.INIT=1'b0;
  DFFRE diagnostic_q_401_s0 (
    .Q(navigation_body_401),
    .D(bvy[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_401_s0.INIT=1'b0;
  DFFRE diagnostic_q_400_s0 (
    .Q(navigation_body_400),
    .D(bvy[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_400_s0.INIT=1'b0;
  DFFRE diagnostic_q_399_s0 (
    .Q(navigation_body_399),
    .D(wvx[31]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_399_s0.INIT=1'b0;
  DFFRE diagnostic_q_397_s0 (
    .Q(navigation_body_397),
    .D(wvx[29]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_397_s0.INIT=1'b0;
  DFFRE diagnostic_q_396_s0 (
    .Q(navigation_body_396),
    .D(wvx[28]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_396_s0.INIT=1'b0;
  DFFRE diagnostic_q_395_s0 (
    .Q(navigation_body_395),
    .D(wvx[27]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_395_s0.INIT=1'b0;
  DFFRE diagnostic_q_394_s0 (
    .Q(navigation_body_394),
    .D(wvx[26]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_394_s0.INIT=1'b0;
  DFFRE diagnostic_q_393_s0 (
    .Q(navigation_body_393),
    .D(wvx[25]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_393_s0.INIT=1'b0;
  DFFRE diagnostic_q_392_s0 (
    .Q(navigation_body_392),
    .D(wvx[24]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_392_s0.INIT=1'b0;
  DFFRE diagnostic_q_391_s0 (
    .Q(navigation_body_391),
    .D(wvx[23]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_391_s0.INIT=1'b0;
  DFFRE diagnostic_q_390_s0 (
    .Q(navigation_body_390),
    .D(wvx[22]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_390_s0.INIT=1'b0;
  DFFRE diagnostic_q_389_s0 (
    .Q(navigation_body_389),
    .D(wvx[21]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_389_s0.INIT=1'b0;
  DFFRE diagnostic_q_388_s0 (
    .Q(navigation_body_388),
    .D(wvx[20]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_388_s0.INIT=1'b0;
  DFFRE diagnostic_q_387_s0 (
    .Q(navigation_body_387),
    .D(wvx[19]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_387_s0.INIT=1'b0;
  DFFRE diagnostic_q_386_s0 (
    .Q(navigation_body_386),
    .D(wvx[18]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_386_s0.INIT=1'b0;
  DFFRE diagnostic_q_385_s0 (
    .Q(navigation_body_385),
    .D(wvx[17]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_385_s0.INIT=1'b0;
  DFFRE diagnostic_q_384_s0 (
    .Q(navigation_body_384),
    .D(wvx[16]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_384_s0.INIT=1'b0;
  DFFRE diagnostic_q_383_s0 (
    .Q(navigation_body_383),
    .D(wvx[15]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_383_s0.INIT=1'b0;
  DFFRE diagnostic_q_382_s0 (
    .Q(navigation_body_382),
    .D(wvx[14]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_382_s0.INIT=1'b0;
  DFFRE diagnostic_q_381_s0 (
    .Q(navigation_body_381),
    .D(wvx[13]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_381_s0.INIT=1'b0;
  DFFRE diagnostic_q_380_s0 (
    .Q(navigation_body_380),
    .D(wvx[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_380_s0.INIT=1'b0;
  DFFRE diagnostic_q_379_s0 (
    .Q(navigation_body_379),
    .D(wvx[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_379_s0.INIT=1'b0;
  DFFRE diagnostic_q_378_s0 (
    .Q(navigation_body_378),
    .D(wvx[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_378_s0.INIT=1'b0;
  DFFRE diagnostic_q_377_s0 (
    .Q(navigation_body_377),
    .D(wvx[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_377_s0.INIT=1'b0;
  DFFRE diagnostic_q_376_s0 (
    .Q(navigation_body_376),
    .D(wvx[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_376_s0.INIT=1'b0;
  DFFRE diagnostic_q_375_s0 (
    .Q(navigation_body_375),
    .D(wvx[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_375_s0.INIT=1'b0;
  DFFRE diagnostic_q_374_s0 (
    .Q(navigation_body_374),
    .D(wvx[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_374_s0.INIT=1'b0;
  DFFRE diagnostic_q_373_s0 (
    .Q(navigation_body_373),
    .D(wvx[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_373_s0.INIT=1'b0;
  DFFRE diagnostic_q_372_s0 (
    .Q(navigation_body_372),
    .D(wvx[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_372_s0.INIT=1'b0;
  DFFRE diagnostic_q_371_s0 (
    .Q(navigation_body_371),
    .D(wvx[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_371_s0.INIT=1'b0;
  DFFRE diagnostic_q_370_s0 (
    .Q(navigation_body_370),
    .D(wvx[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_370_s0.INIT=1'b0;
  DFFRE diagnostic_q_369_s0 (
    .Q(navigation_body_369),
    .D(wvx[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_369_s0.INIT=1'b0;
  DFFRE diagnostic_q_368_s0 (
    .Q(navigation_body_368),
    .D(wvx[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_368_s0.INIT=1'b0;
  DFFRE diagnostic_q_367_s0 (
    .Q(navigation_body_367),
    .D(wvy[31]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_367_s0.INIT=1'b0;
  DFFRE diagnostic_q_365_s0 (
    .Q(navigation_body_365),
    .D(wvy[29]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_365_s0.INIT=1'b0;
  DFFRE diagnostic_q_364_s0 (
    .Q(navigation_body_364),
    .D(wvy[28]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_364_s0.INIT=1'b0;
  DFFRE diagnostic_q_363_s0 (
    .Q(navigation_body_363),
    .D(wvy[27]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_363_s0.INIT=1'b0;
  DFFRE diagnostic_q_362_s0 (
    .Q(navigation_body_362),
    .D(wvy[26]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_362_s0.INIT=1'b0;
  DFFRE diagnostic_q_361_s0 (
    .Q(navigation_body_361),
    .D(wvy[25]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_361_s0.INIT=1'b0;
  DFFRE diagnostic_q_360_s0 (
    .Q(navigation_body_360),
    .D(wvy[24]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_360_s0.INIT=1'b0;
  DFFRE diagnostic_q_359_s0 (
    .Q(navigation_body_359),
    .D(wvy[23]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_359_s0.INIT=1'b0;
  DFFRE diagnostic_q_358_s0 (
    .Q(navigation_body_358),
    .D(wvy[22]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_358_s0.INIT=1'b0;
  DFFRE diagnostic_q_357_s0 (
    .Q(navigation_body_357),
    .D(wvy[21]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_357_s0.INIT=1'b0;
  DFFRE diagnostic_q_356_s0 (
    .Q(navigation_body_356),
    .D(wvy[20]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_356_s0.INIT=1'b0;
  DFFRE diagnostic_q_355_s0 (
    .Q(navigation_body_355),
    .D(wvy[19]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_355_s0.INIT=1'b0;
  DFFRE diagnostic_q_354_s0 (
    .Q(navigation_body_354),
    .D(wvy[18]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_354_s0.INIT=1'b0;
  DFFRE diagnostic_q_353_s0 (
    .Q(navigation_body_353),
    .D(wvy[17]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_353_s0.INIT=1'b0;
  DFFRE diagnostic_q_352_s0 (
    .Q(navigation_body_352),
    .D(wvy[16]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_352_s0.INIT=1'b0;
  DFFRE diagnostic_q_351_s0 (
    .Q(navigation_body_351),
    .D(wvy[15]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_351_s0.INIT=1'b0;
  DFFRE diagnostic_q_350_s0 (
    .Q(navigation_body_350),
    .D(wvy[14]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_350_s0.INIT=1'b0;
  DFFRE diagnostic_q_349_s0 (
    .Q(navigation_body_349),
    .D(wvy[13]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_349_s0.INIT=1'b0;
  DFFRE diagnostic_q_348_s0 (
    .Q(navigation_body_348),
    .D(wvy[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_348_s0.INIT=1'b0;
  DFFRE diagnostic_q_347_s0 (
    .Q(navigation_body_347),
    .D(wvy[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_347_s0.INIT=1'b0;
  DFFRE diagnostic_q_346_s0 (
    .Q(navigation_body_346),
    .D(wvy[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_346_s0.INIT=1'b0;
  DFFRE diagnostic_q_345_s0 (
    .Q(navigation_body_345),
    .D(wvy[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_345_s0.INIT=1'b0;
  DFFRE diagnostic_q_344_s0 (
    .Q(navigation_body_344),
    .D(wvy[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_344_s0.INIT=1'b0;
  DFFRE diagnostic_q_343_s0 (
    .Q(navigation_body_343),
    .D(wvy[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_343_s0.INIT=1'b0;
  DFFRE diagnostic_q_342_s0 (
    .Q(navigation_body_342),
    .D(wvy[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_342_s0.INIT=1'b0;
  DFFRE diagnostic_q_341_s0 (
    .Q(navigation_body_341),
    .D(wvy[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_341_s0.INIT=1'b0;
  DFFRE diagnostic_q_340_s0 (
    .Q(navigation_body_340),
    .D(wvy[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_340_s0.INIT=1'b0;
  DFFRE diagnostic_q_339_s0 (
    .Q(navigation_body_339),
    .D(wvy[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_339_s0.INIT=1'b0;
  DFFRE diagnostic_q_338_s0 (
    .Q(navigation_body_338),
    .D(wvy[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_338_s0.INIT=1'b0;
  DFFRE diagnostic_q_337_s0 (
    .Q(navigation_body_337),
    .D(wvy[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_337_s0.INIT=1'b0;
  DFFRE diagnostic_q_336_s0 (
    .Q(navigation_body_336),
    .D(wvy[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_336_s0.INIT=1'b0;
  DFFRE diagnostic_q_335_s0 (
    .Q(navigation_body_335),
    .D(fused_vx_q16_Z[30]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_335_s0.INIT=1'b0;
  DFFRE diagnostic_q_333_s0 (
    .Q(navigation_body_333),
    .D(fused_vx_q16_Z[29]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_333_s0.INIT=1'b0;
  DFFRE diagnostic_q_332_s0 (
    .Q(navigation_body_332),
    .D(fused_vx_q16_Z[28]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_332_s0.INIT=1'b0;
  DFFRE diagnostic_q_331_s0 (
    .Q(navigation_body_331),
    .D(fused_vx_q16_Z[27]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_331_s0.INIT=1'b0;
  DFFRE diagnostic_q_330_s0 (
    .Q(navigation_body_330),
    .D(fused_vx_q16_Z[26]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_330_s0.INIT=1'b0;
  DFFRE diagnostic_q_329_s0 (
    .Q(navigation_body_329),
    .D(fused_vx_q16_Z[25]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_329_s0.INIT=1'b0;
  DFFRE diagnostic_q_328_s0 (
    .Q(navigation_body_328),
    .D(fused_vx_q16_Z[24]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_328_s0.INIT=1'b0;
  DFFRE diagnostic_q_327_s0 (
    .Q(navigation_body_327),
    .D(fused_vx_q16_Z[23]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_327_s0.INIT=1'b0;
  DFFRE diagnostic_q_326_s0 (
    .Q(navigation_body_326),
    .D(fused_vx_q16_Z[22]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_326_s0.INIT=1'b0;
  DFFRE diagnostic_q_325_s0 (
    .Q(navigation_body_325),
    .D(fused_vx_q16_Z[21]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_325_s0.INIT=1'b0;
  DFFRE diagnostic_q_324_s0 (
    .Q(navigation_body_324),
    .D(fused_vx_q16_Z[20]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_324_s0.INIT=1'b0;
  DFFRE diagnostic_q_323_s0 (
    .Q(navigation_body_323),
    .D(fused_vx_q16_Z[19]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_323_s0.INIT=1'b0;
  DFFRE diagnostic_q_322_s0 (
    .Q(navigation_body_322),
    .D(fused_vx_q16_Z[18]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_322_s0.INIT=1'b0;
  DFFRE diagnostic_q_321_s0 (
    .Q(navigation_body_321),
    .D(fused_vx_q16_Z[17]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_321_s0.INIT=1'b0;
  DFFRE diagnostic_q_320_s0 (
    .Q(navigation_body_320),
    .D(fused_vx_q16_Z[16]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_320_s0.INIT=1'b0;
  DFFRE diagnostic_q_319_s0 (
    .Q(navigation_body_319),
    .D(fused_vx_q16_Z[15]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_319_s0.INIT=1'b0;
  DFFRE diagnostic_q_318_s0 (
    .Q(navigation_body_318),
    .D(fused_vx_q16_Z[14]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_318_s0.INIT=1'b0;
  DFFRE diagnostic_q_317_s0 (
    .Q(navigation_body_317),
    .D(fused_vx_q16_Z[13]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_317_s0.INIT=1'b0;
  DFFRE diagnostic_q_316_s0 (
    .Q(navigation_body_316),
    .D(fused_vx_q16_Z[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_316_s0.INIT=1'b0;
  DFFRE diagnostic_q_315_s0 (
    .Q(navigation_body_315),
    .D(fused_vx_q16_Z[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_315_s0.INIT=1'b0;
  DFFRE diagnostic_q_314_s0 (
    .Q(navigation_body_314),
    .D(fused_vx_q16_Z[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_314_s0.INIT=1'b0;
  DFFRE diagnostic_q_313_s0 (
    .Q(navigation_body_313),
    .D(fused_vx_q16_Z[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_313_s0.INIT=1'b0;
  DFFRE diagnostic_q_312_s0 (
    .Q(navigation_body_312),
    .D(fused_vx_q16_Z[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_312_s0.INIT=1'b0;
  DFFRE diagnostic_q_311_s0 (
    .Q(navigation_body_311),
    .D(fused_vx_q16_Z[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_311_s0.INIT=1'b0;
  DFFRE diagnostic_q_310_s0 (
    .Q(navigation_body_310),
    .D(fused_vx_q16_Z[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_310_s0.INIT=1'b0;
  DFFRE diagnostic_q_309_s0 (
    .Q(navigation_body_309),
    .D(fused_vx_q16_Z[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_309_s0.INIT=1'b0;
  DFFRE diagnostic_q_308_s0 (
    .Q(navigation_body_308),
    .D(fused_vx_q16_Z[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_308_s0.INIT=1'b0;
  DFFRE diagnostic_q_307_s0 (
    .Q(navigation_body_307),
    .D(fused_vx_q16_Z[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_307_s0.INIT=1'b0;
  DFFRE diagnostic_q_306_s0 (
    .Q(navigation_body_306),
    .D(fused_vx_q16_Z[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_306_s0.INIT=1'b0;
  DFFRE diagnostic_q_305_s0 (
    .Q(navigation_body_305),
    .D(fused_vx_q16_Z[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_305_s0.INIT=1'b0;
  DFFRE diagnostic_q_304_s0 (
    .Q(navigation_body_304),
    .D(fused_vx_q16_Z[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_304_s0.INIT=1'b0;
  DFFRE diagnostic_q_303_s0 (
    .Q(navigation_body_303),
    .D(fused_vy_q16_Z[30]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_303_s0.INIT=1'b0;
  DFFRE diagnostic_q_301_s0 (
    .Q(navigation_body_301),
    .D(fused_vy_q16_Z[29]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_301_s0.INIT=1'b0;
  DFFRE diagnostic_q_300_s0 (
    .Q(navigation_body_300),
    .D(fused_vy_q16_Z[28]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_300_s0.INIT=1'b0;
  DFFRE diagnostic_q_299_s0 (
    .Q(navigation_body_299),
    .D(fused_vy_q16_Z[27]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_299_s0.INIT=1'b0;
  DFFRE diagnostic_q_298_s0 (
    .Q(navigation_body_298),
    .D(fused_vy_q16_Z[26]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_298_s0.INIT=1'b0;
  DFFRE diagnostic_q_297_s0 (
    .Q(navigation_body_297),
    .D(fused_vy_q16_Z[25]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_297_s0.INIT=1'b0;
  DFFRE diagnostic_q_296_s0 (
    .Q(navigation_body_296),
    .D(fused_vy_q16_Z[24]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_296_s0.INIT=1'b0;
  DFFRE diagnostic_q_295_s0 (
    .Q(navigation_body_295),
    .D(fused_vy_q16_Z[23]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_295_s0.INIT=1'b0;
  DFFRE diagnostic_q_294_s0 (
    .Q(navigation_body_294),
    .D(fused_vy_q16_Z[22]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_294_s0.INIT=1'b0;
  DFFRE diagnostic_q_293_s0 (
    .Q(navigation_body_293),
    .D(fused_vy_q16_Z[21]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_293_s0.INIT=1'b0;
  DFFRE diagnostic_q_292_s0 (
    .Q(navigation_body_292),
    .D(fused_vy_q16_Z[20]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_292_s0.INIT=1'b0;
  DFFRE diagnostic_q_291_s0 (
    .Q(navigation_body_291),
    .D(fused_vy_q16_Z[19]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_291_s0.INIT=1'b0;
  DFFRE diagnostic_q_290_s0 (
    .Q(navigation_body_290),
    .D(fused_vy_q16_Z[18]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_290_s0.INIT=1'b0;
  DFFRE diagnostic_q_289_s0 (
    .Q(navigation_body_289),
    .D(fused_vy_q16_Z[17]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_289_s0.INIT=1'b0;
  DFFRE diagnostic_q_288_s0 (
    .Q(navigation_body_288),
    .D(fused_vy_q16_Z[16]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_288_s0.INIT=1'b0;
  DFFRE diagnostic_q_287_s0 (
    .Q(navigation_body_287),
    .D(fused_vy_q16_Z[15]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_287_s0.INIT=1'b0;
  DFFRE diagnostic_q_286_s0 (
    .Q(navigation_body_286),
    .D(fused_vy_q16_Z[14]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_286_s0.INIT=1'b0;
  DFFRE diagnostic_q_285_s0 (
    .Q(navigation_body_285),
    .D(fused_vy_q16_Z[13]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_285_s0.INIT=1'b0;
  DFFRE diagnostic_q_284_s0 (
    .Q(navigation_body_284),
    .D(fused_vy_q16_Z[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_284_s0.INIT=1'b0;
  DFFRE diagnostic_q_283_s0 (
    .Q(navigation_body_283),
    .D(fused_vy_q16_Z[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_283_s0.INIT=1'b0;
  DFFRE diagnostic_q_282_s0 (
    .Q(navigation_body_282),
    .D(fused_vy_q16_Z[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_282_s0.INIT=1'b0;
  DFFRE diagnostic_q_281_s0 (
    .Q(navigation_body_281),
    .D(fused_vy_q16_Z[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_281_s0.INIT=1'b0;
  DFFRE diagnostic_q_280_s0 (
    .Q(navigation_body_280),
    .D(fused_vy_q16_Z[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_280_s0.INIT=1'b0;
  DFFRE diagnostic_q_279_s0 (
    .Q(navigation_body_279),
    .D(fused_vy_q16_Z[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_279_s0.INIT=1'b0;
  DFFRE diagnostic_q_278_s0 (
    .Q(navigation_body_278),
    .D(fused_vy_q16_Z[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_278_s0.INIT=1'b0;
  DFFRE diagnostic_q_277_s0 (
    .Q(navigation_body_277),
    .D(fused_vy_q16_Z[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_277_s0.INIT=1'b0;
  DFFRE diagnostic_q_276_s0 (
    .Q(navigation_body_276),
    .D(fused_vy_q16_Z[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_276_s0.INIT=1'b0;
  DFFRE diagnostic_q_275_s0 (
    .Q(navigation_body_275),
    .D(fused_vy_q16_Z[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_275_s0.INIT=1'b0;
  DFFRE diagnostic_q_274_s0 (
    .Q(navigation_body_274),
    .D(fused_vy_q16_Z[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_274_s0.INIT=1'b0;
  DFFRE diagnostic_q_273_s0 (
    .Q(navigation_body_273),
    .D(fused_vy_q16_Z[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_273_s0.INIT=1'b0;
  DFFRE diagnostic_q_272_s0 (
    .Q(navigation_body_272),
    .D(fused_vy_q16_Z[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_272_s0.INIT=1'b0;
  DFFRE diagnostic_q_271_s0 (
    .Q(navigation_body_271),
    .D(fused_height[31]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_271_s0.INIT=1'b0;
  DFFRE diagnostic_q_270_s0 (
    .Q(navigation_body_270),
    .D(fused_height[30]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_270_s0.INIT=1'b0;
  DFFRE diagnostic_q_269_s0 (
    .Q(navigation_body_269),
    .D(fused_height[29]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_269_s0.INIT=1'b0;
  DFFRE diagnostic_q_268_s0 (
    .Q(navigation_body_268),
    .D(fused_height[28]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_268_s0.INIT=1'b0;
  DFFRE diagnostic_q_267_s0 (
    .Q(navigation_body_267),
    .D(fused_height[27]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_267_s0.INIT=1'b0;
  DFFRE diagnostic_q_266_s0 (
    .Q(navigation_body_266),
    .D(fused_height[26]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_266_s0.INIT=1'b0;
  DFFRE diagnostic_q_265_s0 (
    .Q(navigation_body_265),
    .D(fused_height[25]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_265_s0.INIT=1'b0;
  DFFRE diagnostic_q_264_s0 (
    .Q(navigation_body_264),
    .D(fused_height[24]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_264_s0.INIT=1'b0;
  DFFRE diagnostic_q_263_s0 (
    .Q(navigation_body_263),
    .D(fused_height[23]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_263_s0.INIT=1'b0;
  DFFRE diagnostic_q_262_s0 (
    .Q(navigation_body_262),
    .D(fused_height[22]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_262_s0.INIT=1'b0;
  DFFRE diagnostic_q_261_s0 (
    .Q(navigation_body_261),
    .D(fused_height[21]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_261_s0.INIT=1'b0;
  DFFRE diagnostic_q_260_s0 (
    .Q(navigation_body_260),
    .D(fused_height[20]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_260_s0.INIT=1'b0;
  DFFRE diagnostic_q_259_s0 (
    .Q(navigation_body_259),
    .D(fused_height[19]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_259_s0.INIT=1'b0;
  DFFRE diagnostic_q_258_s0 (
    .Q(navigation_body_258),
    .D(fused_height[18]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_258_s0.INIT=1'b0;
  DFFRE diagnostic_q_257_s0 (
    .Q(navigation_body_257),
    .D(fused_height[17]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_257_s0.INIT=1'b0;
  DFFRE diagnostic_q_256_s0 (
    .Q(navigation_body_256),
    .D(fused_height[16]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_256_s0.INIT=1'b0;
  DFFRE diagnostic_q_255_s0 (
    .Q(navigation_body_255),
    .D(fused_height[15]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_255_s0.INIT=1'b0;
  DFFRE diagnostic_q_254_s0 (
    .Q(navigation_body_254),
    .D(fused_height[14]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_254_s0.INIT=1'b0;
  DFFRE diagnostic_q_253_s0 (
    .Q(navigation_body_253),
    .D(fused_height[13]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_253_s0.INIT=1'b0;
  DFFRE diagnostic_q_252_s0 (
    .Q(navigation_body_252),
    .D(fused_height[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_252_s0.INIT=1'b0;
  DFFRE diagnostic_q_251_s0 (
    .Q(navigation_body_251),
    .D(fused_height[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_251_s0.INIT=1'b0;
  DFFRE diagnostic_q_250_s0 (
    .Q(navigation_body_250),
    .D(fused_height[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_250_s0.INIT=1'b0;
  DFFRE diagnostic_q_249_s0 (
    .Q(navigation_body_249),
    .D(fused_height[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_249_s0.INIT=1'b0;
  DFFRE diagnostic_q_248_s0 (
    .Q(navigation_body_248),
    .D(fused_height[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_248_s0.INIT=1'b0;
  DFFRE diagnostic_q_247_s0 (
    .Q(navigation_body_247),
    .D(fused_height[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_247_s0.INIT=1'b0;
  DFFRE diagnostic_q_246_s0 (
    .Q(navigation_body_246),
    .D(fused_height[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_246_s0.INIT=1'b0;
  DFFRE diagnostic_q_245_s0 (
    .Q(navigation_body_245),
    .D(fused_height[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_245_s0.INIT=1'b0;
  DFFRE diagnostic_q_244_s0 (
    .Q(navigation_body_244),
    .D(fused_height[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_244_s0.INIT=1'b0;
  DFFRE diagnostic_q_243_s0 (
    .Q(navigation_body_243),
    .D(fused_height[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_243_s0.INIT=1'b0;
  DFFRE diagnostic_q_242_s0 (
    .Q(navigation_body_242),
    .D(fused_height[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_242_s0.INIT=1'b0;
  DFFRE diagnostic_q_241_s0 (
    .Q(navigation_body_241),
    .D(fused_height[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_241_s0.INIT=1'b0;
  DFFRE diagnostic_q_240_s0 (
    .Q(navigation_body_240),
    .D(fused_height[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_240_s0.INIT=1'b0;
  DFFRE diagnostic_q_239_s0 (
    .Q(navigation_body_239),
    .D(fused_vz_q16[31]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_239_s0.INIT=1'b0;
  DFFRE diagnostic_q_238_s0 (
    .Q(navigation_body_238),
    .D(fused_vz_q16[30]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_238_s0.INIT=1'b0;
  DFFRE diagnostic_q_237_s0 (
    .Q(navigation_body_237),
    .D(fused_vz_q16[29]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_237_s0.INIT=1'b0;
  DFFRE diagnostic_q_236_s0 (
    .Q(navigation_body_236),
    .D(fused_vz_q16[28]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_236_s0.INIT=1'b0;
  DFFRE diagnostic_q_235_s0 (
    .Q(navigation_body_235),
    .D(fused_vz_q16[27]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_235_s0.INIT=1'b0;
  DFFRE diagnostic_q_234_s0 (
    .Q(navigation_body_234),
    .D(fused_vz_q16[26]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_234_s0.INIT=1'b0;
  DFFRE diagnostic_q_233_s0 (
    .Q(navigation_body_233),
    .D(fused_vz_q16[25]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_233_s0.INIT=1'b0;
  DFFRE diagnostic_q_232_s0 (
    .Q(navigation_body_232),
    .D(fused_vz_q16[24]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_232_s0.INIT=1'b0;
  DFFRE diagnostic_q_231_s0 (
    .Q(navigation_body_231),
    .D(fused_vz_q16[23]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_231_s0.INIT=1'b0;
  DFFRE diagnostic_q_230_s0 (
    .Q(navigation_body_230),
    .D(fused_vz_q16[22]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_230_s0.INIT=1'b0;
  DFFRE diagnostic_q_229_s0 (
    .Q(navigation_body_229),
    .D(fused_vz_q16[21]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_229_s0.INIT=1'b0;
  DFFRE diagnostic_q_228_s0 (
    .Q(navigation_body_228),
    .D(fused_vz_q16[20]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_228_s0.INIT=1'b0;
  DFFRE diagnostic_q_227_s0 (
    .Q(navigation_body_227),
    .D(fused_vz_q16[19]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_227_s0.INIT=1'b0;
  DFFRE diagnostic_q_226_s0 (
    .Q(navigation_body_226),
    .D(fused_vz_q16[18]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_226_s0.INIT=1'b0;
  DFFRE diagnostic_q_225_s0 (
    .Q(navigation_body_225),
    .D(fused_vz_q16[17]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_225_s0.INIT=1'b0;
  DFFRE diagnostic_q_224_s0 (
    .Q(navigation_body_224),
    .D(fused_vz_q16[16]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_224_s0.INIT=1'b0;
  DFFRE diagnostic_q_223_s0 (
    .Q(navigation_body_223),
    .D(fused_vz_q16[15]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_223_s0.INIT=1'b0;
  DFFRE diagnostic_q_222_s0 (
    .Q(navigation_body_222),
    .D(fused_vz_q16[14]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_222_s0.INIT=1'b0;
  DFFRE diagnostic_q_221_s0 (
    .Q(navigation_body_221),
    .D(fused_vz_q16[13]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_221_s0.INIT=1'b0;
  DFFRE diagnostic_q_220_s0 (
    .Q(navigation_body_220),
    .D(fused_vz_q16[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_220_s0.INIT=1'b0;
  DFFRE diagnostic_q_219_s0 (
    .Q(navigation_body_219),
    .D(fused_vz_q16[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_219_s0.INIT=1'b0;
  DFFRE diagnostic_q_218_s0 (
    .Q(navigation_body_218),
    .D(fused_vz_q16[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_218_s0.INIT=1'b0;
  DFFRE diagnostic_q_217_s0 (
    .Q(navigation_body_217),
    .D(fused_vz_q16[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_217_s0.INIT=1'b0;
  DFFRE diagnostic_q_216_s0 (
    .Q(navigation_body_216),
    .D(fused_vz_q16[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_216_s0.INIT=1'b0;
  DFFRE diagnostic_q_215_s0 (
    .Q(navigation_body_215),
    .D(fused_vz_q16[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_215_s0.INIT=1'b0;
  DFFRE diagnostic_q_214_s0 (
    .Q(navigation_body_214),
    .D(fused_vz_q16[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_214_s0.INIT=1'b0;
  DFFRE diagnostic_q_213_s0 (
    .Q(navigation_body_213),
    .D(fused_vz_q16[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_213_s0.INIT=1'b0;
  DFFRE diagnostic_q_212_s0 (
    .Q(navigation_body_212),
    .D(fused_vz_q16[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_212_s0.INIT=1'b0;
  DFFRE diagnostic_q_211_s0 (
    .Q(navigation_body_211),
    .D(fused_vz_q16[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_211_s0.INIT=1'b0;
  DFFRE diagnostic_q_210_s0 (
    .Q(navigation_body_210),
    .D(fused_vz_q16[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_210_s0.INIT=1'b0;
  DFFRE diagnostic_q_209_s0 (
    .Q(navigation_body_209),
    .D(fused_vz_q16[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_209_s0.INIT=1'b0;
  DFFRE diagnostic_q_208_s0 (
    .Q(navigation_body_208),
    .D(fused_vz_q16[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_208_s0.INIT=1'b0;
  DFFRE diagnostic_q_207_s0 (
    .Q(navigation_body_207),
    .D(position_x_q8[28]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_207_s0.INIT=1'b0;
  DFFRE diagnostic_q_203_s0 (
    .Q(navigation_body_203),
    .D(position_x_q8[27]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_203_s0.INIT=1'b0;
  DFFRE diagnostic_q_202_s0 (
    .Q(navigation_body_202),
    .D(position_x_q8[26]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_202_s0.INIT=1'b0;
  DFFRE diagnostic_q_201_s0 (
    .Q(navigation_body_201),
    .D(position_x_q8[25]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_201_s0.INIT=1'b0;
  DFFRE diagnostic_q_200_s0 (
    .Q(navigation_body_200),
    .D(position_x_q8[24]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_200_s0.INIT=1'b0;
  DFFRE diagnostic_q_199_s0 (
    .Q(navigation_body_199),
    .D(position_x_q8[23]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_199_s0.INIT=1'b0;
  DFFRE diagnostic_q_198_s0 (
    .Q(navigation_body_198),
    .D(position_x_q8[22]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_198_s0.INIT=1'b0;
  DFFRE diagnostic_q_197_s0 (
    .Q(navigation_body_197),
    .D(position_x_q8[21]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_197_s0.INIT=1'b0;
  DFFRE diagnostic_q_196_s0 (
    .Q(navigation_body_196),
    .D(position_x_q8[20]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_196_s0.INIT=1'b0;
  DFFRE diagnostic_q_195_s0 (
    .Q(navigation_body_195),
    .D(position_x_q8[19]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_195_s0.INIT=1'b0;
  DFFRE diagnostic_q_194_s0 (
    .Q(navigation_body_194),
    .D(position_x_q8[18]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_194_s0.INIT=1'b0;
  DFFRE diagnostic_q_193_s0 (
    .Q(navigation_body_193),
    .D(position_x_q8[17]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_193_s0.INIT=1'b0;
  DFFRE diagnostic_q_192_s0 (
    .Q(navigation_body_192),
    .D(position_x_q8[16]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_192_s0.INIT=1'b0;
  DFFRE diagnostic_q_191_s0 (
    .Q(navigation_body_191),
    .D(position_x_q8[15]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_191_s0.INIT=1'b0;
  DFFRE diagnostic_q_190_s0 (
    .Q(navigation_body_190),
    .D(position_x_q8[14]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_190_s0.INIT=1'b0;
  DFFRE diagnostic_q_189_s0 (
    .Q(navigation_body_189),
    .D(position_x_q8[13]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_189_s0.INIT=1'b0;
  DFFRE diagnostic_q_188_s0 (
    .Q(navigation_body_188),
    .D(position_x_q8[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_188_s0.INIT=1'b0;
  DFFRE diagnostic_q_187_s0 (
    .Q(navigation_body_187),
    .D(position_x_q8[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_187_s0.INIT=1'b0;
  DFFRE diagnostic_q_186_s0 (
    .Q(navigation_body_186),
    .D(position_x_q8[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_186_s0.INIT=1'b0;
  DFFRE diagnostic_q_185_s0 (
    .Q(navigation_body_185),
    .D(position_x_q8[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_185_s0.INIT=1'b0;
  DFFRE diagnostic_q_184_s0 (
    .Q(navigation_body_184),
    .D(position_x_q8[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_184_s0.INIT=1'b0;
  DFFRE diagnostic_q_183_s0 (
    .Q(navigation_body_183),
    .D(position_x_q8[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_183_s0.INIT=1'b0;
  DFFRE diagnostic_q_182_s0 (
    .Q(navigation_body_182),
    .D(position_x_q8[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_182_s0.INIT=1'b0;
  DFFRE diagnostic_q_181_s0 (
    .Q(navigation_body_181),
    .D(position_x_q8[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_181_s0.INIT=1'b0;
  DFFRE diagnostic_q_180_s0 (
    .Q(navigation_body_180),
    .D(position_x_q8[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_180_s0.INIT=1'b0;
  DFFRE diagnostic_q_179_s0 (
    .Q(navigation_body_179),
    .D(position_x_q8[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_179_s0.INIT=1'b0;
  DFFRE diagnostic_q_178_s0 (
    .Q(navigation_body_178),
    .D(position_x_q8[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_178_s0.INIT=1'b0;
  DFFRE diagnostic_q_177_s0 (
    .Q(navigation_body_177),
    .D(position_x_q8[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_177_s0.INIT=1'b0;
  DFFRE diagnostic_q_176_s0 (
    .Q(navigation_body_176),
    .D(position_x_q8[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_176_s0.INIT=1'b0;
  DFFRE diagnostic_q_175_s0 (
    .Q(navigation_body_175),
    .D(position_y_q8[29]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_175_s0.INIT=1'b0;
  DFFRE diagnostic_q_172_s0 (
    .Q(navigation_body_172),
    .D(position_y_q8[28]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_172_s0.INIT=1'b0;
  DFFRE diagnostic_q_171_s0 (
    .Q(navigation_body_171),
    .D(position_y_q8[27]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_171_s0.INIT=1'b0;
  DFFRE diagnostic_q_170_s0 (
    .Q(navigation_body_170),
    .D(position_y_q8[26]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_170_s0.INIT=1'b0;
  DFFRE diagnostic_q_169_s0 (
    .Q(navigation_body_169),
    .D(position_y_q8[25]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_169_s0.INIT=1'b0;
  DFFRE diagnostic_q_168_s0 (
    .Q(navigation_body_168),
    .D(position_y_q8[24]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_168_s0.INIT=1'b0;
  DFFRE diagnostic_q_167_s0 (
    .Q(navigation_body_167),
    .D(position_y_q8[23]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_167_s0.INIT=1'b0;
  DFFRE diagnostic_q_166_s0 (
    .Q(navigation_body_166),
    .D(position_y_q8[22]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_166_s0.INIT=1'b0;
  DFFRE diagnostic_q_165_s0 (
    .Q(navigation_body_165),
    .D(position_y_q8[21]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_165_s0.INIT=1'b0;
  DFFRE diagnostic_q_164_s0 (
    .Q(navigation_body_164),
    .D(position_y_q8[20]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_164_s0.INIT=1'b0;
  DFFRE diagnostic_q_163_s0 (
    .Q(navigation_body_163),
    .D(position_y_q8[19]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_163_s0.INIT=1'b0;
  DFFRE diagnostic_q_162_s0 (
    .Q(navigation_body_162),
    .D(position_y_q8[18]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_162_s0.INIT=1'b0;
  DFFRE diagnostic_q_161_s0 (
    .Q(navigation_body_161),
    .D(position_y_q8[17]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_161_s0.INIT=1'b0;
  DFFRE diagnostic_q_160_s0 (
    .Q(navigation_body_160),
    .D(position_y_q8[16]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_160_s0.INIT=1'b0;
  DFFRE diagnostic_q_159_s0 (
    .Q(navigation_body_159),
    .D(position_y_q8[15]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_159_s0.INIT=1'b0;
  DFFRE diagnostic_q_158_s0 (
    .Q(navigation_body_158),
    .D(position_y_q8[14]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_158_s0.INIT=1'b0;
  DFFRE diagnostic_q_157_s0 (
    .Q(navigation_body_157),
    .D(position_y_q8[13]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_157_s0.INIT=1'b0;
  DFFRE diagnostic_q_156_s0 (
    .Q(navigation_body_156),
    .D(position_y_q8[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_156_s0.INIT=1'b0;
  DFFRE diagnostic_q_155_s0 (
    .Q(navigation_body_155),
    .D(position_y_q8[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_155_s0.INIT=1'b0;
  DFFRE diagnostic_q_154_s0 (
    .Q(navigation_body_154),
    .D(position_y_q8[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_154_s0.INIT=1'b0;
  DFFRE diagnostic_q_153_s0 (
    .Q(navigation_body_153),
    .D(position_y_q8[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_153_s0.INIT=1'b0;
  DFFRE diagnostic_q_152_s0 (
    .Q(navigation_body_152),
    .D(position_y_q8[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_152_s0.INIT=1'b0;
  DFFRE diagnostic_q_151_s0 (
    .Q(navigation_body_151),
    .D(position_y_q8[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_151_s0.INIT=1'b0;
  DFFRE diagnostic_q_150_s0 (
    .Q(navigation_body_150),
    .D(position_y_q8[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_150_s0.INIT=1'b0;
  DFFRE diagnostic_q_149_s0 (
    .Q(navigation_body_149),
    .D(position_y_q8[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_149_s0.INIT=1'b0;
  DFFRE diagnostic_q_148_s0 (
    .Q(navigation_body_148),
    .D(position_y_q8[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_148_s0.INIT=1'b0;
  DFFRE diagnostic_q_147_s0 (
    .Q(navigation_body_147),
    .D(position_y_q8[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_147_s0.INIT=1'b0;
  DFFRE diagnostic_q_146_s0 (
    .Q(navigation_body_146),
    .D(position_y_q8[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_146_s0.INIT=1'b0;
  DFFRE diagnostic_q_145_s0 (
    .Q(navigation_body_145),
    .D(position_y_q8[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_145_s0.INIT=1'b0;
  DFFRE diagnostic_q_144_s0 (
    .Q(navigation_body_144),
    .D(position_y_q8[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_144_s0.INIT=1'b0;
  DFFRE diagnostic_q_143_s0 (
    .Q(diagnostic_q_143),
    .D(nav_xy_payload_roll_15),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_143_s0.INIT=1'b0;
  DFFRE diagnostic_q_139_s0 (
    .Q(diagnostic_q_139),
    .D(nav_xy_payload_roll_11),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_139_s0.INIT=1'b0;
  DFFRE diagnostic_q_138_s0 (
    .Q(diagnostic_q_138),
    .D(nav_xy_payload_roll_10),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_138_s0.INIT=1'b0;
  DFFRE diagnostic_q_137_s0 (
    .Q(diagnostic_q_137),
    .D(nav_xy_payload_roll_9),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_137_s0.INIT=1'b0;
  DFFRE diagnostic_q_136_s0 (
    .Q(diagnostic_q_136),
    .D(nav_xy_payload_roll_8),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_136_s0.INIT=1'b0;
  DFFRE diagnostic_q_135_s0 (
    .Q(diagnostic_q_135),
    .D(nav_xy_payload_roll_7),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_135_s0.INIT=1'b0;
  DFFRE diagnostic_q_134_s0 (
    .Q(diagnostic_q_134),
    .D(nav_xy_payload_roll_6),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_134_s0.INIT=1'b0;
  DFFRE diagnostic_q_133_s0 (
    .Q(diagnostic_q_133),
    .D(nav_xy_payload_roll_5),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_133_s0.INIT=1'b0;
  DFFRE diagnostic_q_132_s0 (
    .Q(diagnostic_q_132),
    .D(nav_xy_payload_roll_4),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_132_s0.INIT=1'b0;
  DFFRE diagnostic_q_131_s0 (
    .Q(diagnostic_q_131),
    .D(nav_xy_payload_roll_3),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_131_s0.INIT=1'b0;
  DFFRE diagnostic_q_130_s0 (
    .Q(diagnostic_q_130),
    .D(nav_xy_payload_roll_2),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_130_s0.INIT=1'b0;
  DFFRE diagnostic_q_129_s0 (
    .Q(diagnostic_q_129),
    .D(nav_xy_payload_roll_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_129_s0.INIT=1'b0;
  DFFRE diagnostic_q_128_s0 (
    .Q(diagnostic_q_128),
    .D(nav_xy_payload_roll_0),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_128_s0.INIT=1'b0;
  DFFRE diagnostic_q_124_s0 (
    .Q(diagnostic_q_124),
    .D(nav_xy_payload_pitch_15),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_124_s0.INIT=1'b0;
  DFFRE diagnostic_q_123_s0 (
    .Q(diagnostic_q_123),
    .D(nav_xy_payload_pitch_11),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_123_s0.INIT=1'b0;
  DFFRE diagnostic_q_122_s0 (
    .Q(diagnostic_q_122),
    .D(nav_xy_payload_pitch_10),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_122_s0.INIT=1'b0;
  DFFRE diagnostic_q_121_s0 (
    .Q(diagnostic_q_121),
    .D(nav_xy_payload_pitch_9),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_121_s0.INIT=1'b0;
  DFFRE diagnostic_q_120_s0 (
    .Q(diagnostic_q_120),
    .D(nav_xy_payload_pitch_8),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_120_s0.INIT=1'b0;
  DFFRE diagnostic_q_119_s0 (
    .Q(diagnostic_q_119),
    .D(nav_xy_payload_pitch_7),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_119_s0.INIT=1'b0;
  DFFRE diagnostic_q_118_s0 (
    .Q(diagnostic_q_118),
    .D(nav_xy_payload_pitch_6),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_118_s0.INIT=1'b0;
  DFFRE diagnostic_q_117_s0 (
    .Q(diagnostic_q_117),
    .D(nav_xy_payload_pitch_5),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_117_s0.INIT=1'b0;
  DFFRE diagnostic_q_116_s0 (
    .Q(diagnostic_q_116),
    .D(nav_xy_payload_pitch_4),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_116_s0.INIT=1'b0;
  DFFRE diagnostic_q_115_s0 (
    .Q(diagnostic_q_115),
    .D(nav_xy_payload_pitch_3),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_115_s0.INIT=1'b0;
  DFFRE diagnostic_q_114_s0 (
    .Q(diagnostic_q_114),
    .D(nav_xy_payload_pitch_2),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_114_s0.INIT=1'b0;
  DFFRE diagnostic_q_113_s0 (
    .Q(diagnostic_q_113),
    .D(nav_xy_payload_pitch_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_113_s0.INIT=1'b0;
  DFFRE diagnostic_q_112_s0 (
    .Q(diagnostic_q_112),
    .D(nav_xy_payload_pitch_0),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_112_s0.INIT=1'b0;
  DFFRE diagnostic_q_111_s0 (
    .Q(navigation_body_111),
    .D(nav_z_throttle[15]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_111_s0.INIT=1'b0;
  DFFRE diagnostic_q_110_s0 (
    .Q(navigation_body_110),
    .D(nav_z_throttle[14]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_110_s0.INIT=1'b0;
  DFFRE diagnostic_q_109_s0 (
    .Q(navigation_body_109),
    .D(nav_z_throttle[13]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_109_s0.INIT=1'b0;
  DFFRE diagnostic_q_108_s0 (
    .Q(navigation_body_108),
    .D(nav_z_throttle[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_108_s0.INIT=1'b0;
  DFFRE diagnostic_q_107_s0 (
    .Q(navigation_body_107),
    .D(nav_z_throttle[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_107_s0.INIT=1'b0;
  DFFRE diagnostic_q_106_s0 (
    .Q(navigation_body_106),
    .D(nav_z_throttle[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_106_s0.INIT=1'b0;
  DFFRE diagnostic_q_105_s0 (
    .Q(navigation_body_105),
    .D(nav_z_throttle[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_105_s0.INIT=1'b0;
  DFFRE diagnostic_q_104_s0 (
    .Q(navigation_body_104),
    .D(nav_z_throttle[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_104_s0.INIT=1'b0;
  DFFRE diagnostic_q_103_s0 (
    .Q(navigation_body_103),
    .D(nav_z_throttle[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_103_s0.INIT=1'b0;
  DFFRE diagnostic_q_102_s0 (
    .Q(navigation_body_102),
    .D(nav_z_throttle[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_102_s0.INIT=1'b0;
  DFFRE diagnostic_q_101_s0 (
    .Q(navigation_body_101),
    .D(nav_z_throttle[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_101_s0.INIT=1'b0;
  DFFRE diagnostic_q_100_s0 (
    .Q(navigation_body_100),
    .D(nav_z_throttle[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_100_s0.INIT=1'b0;
  DFFRE diagnostic_q_99_s0 (
    .Q(navigation_body_99),
    .D(nav_z_throttle[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_99_s0.INIT=1'b0;
  DFFRE diagnostic_q_98_s0 (
    .Q(navigation_body_98),
    .D(nav_z_throttle[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_98_s0.INIT=1'b0;
  DFFRE diagnostic_q_97_s0 (
    .Q(navigation_body_97),
    .D(nav_z_throttle[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_97_s0.INIT=1'b0;
  DFFRE diagnostic_q_96_s0 (
    .Q(navigation_body_96),
    .D(nav_z_throttle[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_96_s0.INIT=1'b0;
  DFFRE diagnostic_q_95_s0 (
    .Q(navigation_body_95),
    .D(position_reason[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_95_s0.INIT=1'b0;
  DFFRE diagnostic_q_94_s0 (
    .Q(navigation_body_94),
    .D(position_reason[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_94_s0.INIT=1'b0;
  DFFRE diagnostic_q_93_s0 (
    .Q(navigation_body_93),
    .D(position_reason[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_93_s0.INIT=1'b0;
  DFFRE diagnostic_q_92_s0 (
    .Q(navigation_body_92),
    .D(position_reason[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_92_s0.INIT=1'b0;
  DFFRE diagnostic_q_91_s0 (
    .Q(navigation_body_91),
    .D(position_reason[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_91_s0.INIT=1'b0;
  DFFRE diagnostic_q_89_s0 (
    .Q(navigation_body_89),
    .D(position_reason[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_89_s0.INIT=1'b0;
  DFFRE diagnostic_q_88_s0 (
    .Q(navigation_body_88),
    .D(position_reason[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_88_s0.INIT=1'b0;
  DFFRE diagnostic_q_87_s0 (
    .Q(navigation_body_87),
    .D(position_reason[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_87_s0.INIT=1'b0;
  DFFSE diagnostic_q_86_s0 (
    .Q(navigation_body_86),
    .D(position_reason[0]),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_86_s0.INIT=1'b1;
  DFFRE diagnostic_q_85_s0 (
    .Q(navigation_body_85),
    .D(nav_xy_active),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_85_s0.INIT=1'b0;
  DFFRE diagnostic_q_84_s0 (
    .Q(navigation_body_84),
    .D(nav_z_active),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_84_s0.INIT=1'b0;
  DFFRE diagnostic_q_83_s0 (
    .Q(navigation_body_83),
    .D(source_loc_selected),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_83_s0.INIT=1'b0;
  DFFRE diagnostic_q_82_s0 (
    .Q(navigation_body_82),
    .D(controller_z_requested),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_82_s0.INIT=1'b0;
  DFFRE diagnostic_q_81_s0 (
    .Q(navigation_body_81),
    .D(nav_xy_ready),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_81_s0.INIT=1'b0;
  DFFRE diagnostic_q_80_s0 (
    .Q(navigation_body_80),
    .D(controller_z_ready),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_80_s0.INIT=1'b0;
  DFFRE diagnostic_q_63_s0 (
    .Q(navigation_body_63),
    .D(nav_z_collective[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_63_s0.INIT=1'b0;
  DFFRE diagnostic_q_59_s0 (
    .Q(navigation_body_59),
    .D(nav_z_collective[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_59_s0.INIT=1'b0;
  DFFRE diagnostic_q_58_s0 (
    .Q(navigation_body_58),
    .D(nav_z_collective[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_58_s0.INIT=1'b0;
  DFFRE diagnostic_q_57_s0 (
    .Q(navigation_body_57),
    .D(nav_z_collective[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_57_s0.INIT=1'b0;
  DFFRE diagnostic_q_56_s0 (
    .Q(navigation_body_56),
    .D(nav_z_collective[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_56_s0.INIT=1'b0;
  DFFRE diagnostic_q_55_s0 (
    .Q(navigation_body_55),
    .D(nav_z_collective[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_55_s0.INIT=1'b0;
  DFFRE diagnostic_q_54_s0 (
    .Q(navigation_body_54),
    .D(nav_z_collective[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_54_s0.INIT=1'b0;
  DFFRE diagnostic_q_53_s0 (
    .Q(navigation_body_53),
    .D(nav_z_collective[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_53_s0.INIT=1'b0;
  DFFRE diagnostic_q_52_s0 (
    .Q(navigation_body_52),
    .D(nav_z_collective[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_52_s0.INIT=1'b0;
  DFFRE diagnostic_q_51_s0 (
    .Q(navigation_body_51),
    .D(nav_z_collective[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_51_s0.INIT=1'b0;
  DFFRE diagnostic_q_50_s0 (
    .Q(navigation_body_50),
    .D(nav_z_collective[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_50_s0.INIT=1'b0;
  DFFRE diagnostic_q_49_s0 (
    .Q(navigation_body_49),
    .D(nav_z_collective[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_49_s0.INIT=1'b0;
  DFFRE diagnostic_q_48_s0 (
    .Q(navigation_body_48),
    .D(nav_z_collective[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_48_s0.INIT=1'b0;
  DFFRE diagnostic_q_42_s0 (
    .Q(navigation_body_42),
    .D(nav_z_reason_10),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_42_s0.INIT=1'b0;
  DFFRE diagnostic_q_41_s0 (
    .Q(navigation_body_41),
    .D(nav_z_reason_9),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_41_s0.INIT=1'b0;
  DFFRE diagnostic_q_40_s0 (
    .Q(navigation_body_40),
    .D(nav_z_reason_2[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_40_s0.INIT=1'b0;
  DFFRE diagnostic_q_39_s0 (
    .Q(navigation_body_39),
    .D(nav_z_reason_7),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_39_s0.INIT=1'b0;
  DFFRE diagnostic_q_38_s0 (
    .Q(navigation_body_38),
    .D(nav_z_reason_6),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_38_s0.INIT=1'b0;
  DFFRE diagnostic_q_35_s0 (
    .Q(navigation_body_35),
    .D(nav_z_reason_3),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_35_s0.INIT=1'b0;
  DFFRE diagnostic_q_33_s0 (
    .Q(navigation_body_33),
    .D(nav_z_reason_1),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_33_s0.INIT=1'b0;
  DFFSE diagnostic_q_32_s0 (
    .Q(navigation_body_32),
    .D(nav_z_reason_0),
    .CLK(clk50_d),
    .SET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_32_s0.INIT=1'b1;
  DFFRE diagnostic_q_31_s0 (
    .Q(navigation_body_31),
    .D(z_target_height[31]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_31_s0.INIT=1'b0;
  DFFRE diagnostic_q_14_s0 (
    .Q(navigation_body_14),
    .D(z_target_height[14]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_14_s0.INIT=1'b0;
  DFFRE diagnostic_q_13_s0 (
    .Q(navigation_body_13),
    .D(z_target_height[13]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_13_s0.INIT=1'b0;
  DFFRE diagnostic_q_12_s0 (
    .Q(navigation_body_12),
    .D(z_target_height[12]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_12_s0.INIT=1'b0;
  DFFRE diagnostic_q_11_s0 (
    .Q(navigation_body_11),
    .D(z_target_height[11]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_11_s0.INIT=1'b0;
  DFFRE diagnostic_q_10_s0 (
    .Q(navigation_body_10),
    .D(z_target_height[10]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_10_s0.INIT=1'b0;
  DFFRE diagnostic_q_9_s0 (
    .Q(navigation_body_9),
    .D(z_target_height[9]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_9_s0.INIT=1'b0;
  DFFRE diagnostic_q_8_s0 (
    .Q(navigation_body_8),
    .D(z_target_height[8]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_8_s0.INIT=1'b0;
  DFFRE diagnostic_q_7_s0 (
    .Q(navigation_body_7),
    .D(z_target_height[7]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_7_s0.INIT=1'b0;
  DFFRE diagnostic_q_6_s0 (
    .Q(navigation_body_6),
    .D(z_target_height[6]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_6_s0.INIT=1'b0;
  DFFRE diagnostic_q_5_s0 (
    .Q(navigation_body_5),
    .D(z_target_height[5]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_5_s0.INIT=1'b0;
  DFFRE diagnostic_q_4_s0 (
    .Q(navigation_body_4),
    .D(z_target_height[4]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_4_s0.INIT=1'b0;
  DFFRE diagnostic_q_3_s0 (
    .Q(navigation_body_3),
    .D(z_target_height[3]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_3_s0.INIT=1'b0;
  DFFRE diagnostic_q_2_s0 (
    .Q(navigation_body_2),
    .D(z_target_height[2]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_2_s0.INIT=1'b0;
  DFFRE diagnostic_q_1_s0 (
    .Q(navigation_body_1),
    .D(z_target_height[1]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_1_s0.INIT=1'b0;
  DFFRE diagnostic_q_0_s0 (
    .Q(navigation_body_0),
    .D(z_target_height[0]),
    .CLK(clk50_d),
    .RESET(n13_16),
    .CE(\staged_telemetry.core_q_453_16 ) 
);
defparam diagnostic_q_0_s0.INIT=1'b0;
  MULT27X36 n790_s (
    .DOUT({DOUT[62:32],n759_2,n760_2,n761_2,n762_2,n763_2,n764_2,n765_2,n766_2,n767_2,n768_2,n769_2,n770_2,n771_2,n772_2,n773_2,n774_2,n775_2,n776_2,n777_2,n778_2,n779_2,n780_2,n781_2,n782_2,n783_2,n784_2,DOUT[5:0]}),
    .A({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,VCC,VCC,GND,GND,GND,GND,VCC,VCC,GND,VCC,GND,VCC,GND,GND,GND,GND}),
    .B({GND,GND,GND,GND,mtf_age_ms[31:0]}),
    .D({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .CLK({GND,GND}),
    .CE({VCC,VCC}),
    .RESET({GND,GND}),
    .PSEL(GND),
    .PADDSUB(GND) 
);
defparam n790_s.MULT_RESET_MODE="SYNC";
defparam n790_s.OREG_CLK="BYPASS";
defparam n790_s.OREG_CE="CE0";
defparam n790_s.OREG_RESET="RESET0";
defparam n790_s.AREG_CLK="BYPASS";
defparam n790_s.AREG_CE="CE0";
defparam n790_s.AREG_RESET="RESET0";
defparam n790_s.BREG_CLK="BYPASS";
defparam n790_s.BREG_CE="CE0";
defparam n790_s.BREG_RESET="RESET0";
defparam n790_s.DREG_CLK="BYPASS";
defparam n790_s.DREG_CE="CE0";
defparam n790_s.DREG_RESET="RESET0";
defparam n790_s.PREG_CLK="BYPASS";
defparam n790_s.PREG_CE="CE0";
defparam n790_s.PREG_RESET="RESET0";
defparam n790_s.DYN_P_SEL="FALSE";
defparam n790_s.P_SEL=1'b0;
defparam n790_s.DYN_P_ADDSUB="FALSE";
defparam n790_s.P_ADDSUB=1'b0;
defparam n790_s.PADDSUB_IREG_CE="CE0";
defparam n790_s.PADDSUB_IREG_CLK="BYPASS";
defparam n790_s.PADDSUB_IREG_RESET="RESET0";
defparam n790_s.PSEL_IREG_CE="CE0";
defparam n790_s.PSEL_IREG_CLK="BYPASS";
defparam n790_s.PSEL_IREG_RESET="RESET0";
  ALU next_observation_epoch_0_s (
    .SUM(next_observation_epoch[0]),
    .COUT(next_observation_epoch_0_2),
    .I0(observation_epoch[0]),
    .I1(observation_event),
    .I3(VCC),
    .CIN(GND) 
);
defparam next_observation_epoch_0_s.ALU_MODE=0;
  ALU next_observation_epoch_1_s (
    .SUM(next_observation_epoch[1]),
    .COUT(next_observation_epoch_1_2),
    .I0(observation_epoch[1]),
    .I1(GND),
    .I3(VCC),
    .CIN(next_observation_epoch_0_2) 
);
defparam next_observation_epoch_1_s.ALU_MODE=0;
  ALU next_observation_epoch_2_s (
    .SUM(next_observation_epoch[2]),
    .COUT(next_observation_epoch_2_2),
    .I0(observation_epoch[2]),
    .I1(GND),
    .I3(VCC),
    .CIN(next_observation_epoch_1_2) 
);
defparam next_observation_epoch_2_s.ALU_MODE=0;
  ALU next_observation_epoch_3_s (
    .SUM(next_observation_epoch[3]),
    .COUT(next_observation_epoch_3_2),
    .I0(observation_epoch[3]),
    .I1(GND),
    .I3(VCC),
    .CIN(next_observation_epoch_2_2) 
);
defparam next_observation_epoch_3_s.ALU_MODE=0;
  ALU next_observation_epoch_4_s (
    .SUM(next_observation_epoch[4]),
    .COUT(next_observation_epoch_4_2),
    .I0(observation_epoch[4]),
    .I1(GND),
    .I3(VCC),
    .CIN(next_observation_epoch_3_2) 
);
defparam next_observation_epoch_4_s.ALU_MODE=0;
  ALU next_observation_epoch_5_s (
    .SUM(next_observation_epoch[5]),
    .COUT(next_observation_epoch_5_2),
    .I0(observation_epoch[5]),
    .I1(GND),
    .I3(VCC),
    .CIN(next_observation_epoch_4_2) 
);
defparam next_observation_epoch_5_s.ALU_MODE=0;
  ALU next_observation_epoch_6_s (
    .SUM(next_observation_epoch[6]),
    .COUT(next_observation_epoch_6_2),
    .I0(observation_epoch[6]),
    .I1(GND),
    .I3(VCC),
    .CIN(next_observation_epoch_5_2) 
);
defparam next_observation_epoch_6_s.ALU_MODE=0;
  ALU next_observation_epoch_7_s (
    .SUM(next_observation_epoch[7]),
    .COUT(next_observation_epoch_7_0_COUT),
    .I0(p_observation_epoch[7]),
    .I1(GND),
    .I3(VCC),
    .CIN(next_observation_epoch_6_2) 
);
defparam next_observation_epoch_7_s.ALU_MODE=0;
  ALU next_control_epoch_0_s (
    .SUM(next_control_epoch[0]),
    .COUT(next_control_epoch_0_2),
    .I0(control_epoch[0]),
    .I1(control_event),
    .I3(VCC),
    .CIN(GND) 
);
defparam next_control_epoch_0_s.ALU_MODE=0;
  ALU next_control_epoch_1_s (
    .SUM(next_control_epoch[1]),
    .COUT(next_control_epoch_1_2),
    .I0(control_epoch[1]),
    .I1(GND),
    .I3(VCC),
    .CIN(next_control_epoch_0_2) 
);
defparam next_control_epoch_1_s.ALU_MODE=0;
  ALU next_control_epoch_2_s (
    .SUM(next_control_epoch[2]),
    .COUT(next_control_epoch_2_2),
    .I0(control_epoch[2]),
    .I1(GND),
    .I3(VCC),
    .CIN(next_control_epoch_1_2) 
);
defparam next_control_epoch_2_s.ALU_MODE=0;
  ALU next_control_epoch_3_s (
    .SUM(next_control_epoch[3]),
    .COUT(next_control_epoch_3_2),
    .I0(control_epoch[3]),
    .I1(GND),
    .I3(VCC),
    .CIN(next_control_epoch_2_2) 
);
defparam next_control_epoch_3_s.ALU_MODE=0;
  ALU next_control_epoch_4_s (
    .SUM(next_control_epoch[4]),
    .COUT(next_control_epoch_4_2),
    .I0(control_epoch[4]),
    .I1(GND),
    .I3(VCC),
    .CIN(next_control_epoch_3_2) 
);
defparam next_control_epoch_4_s.ALU_MODE=0;
  ALU next_control_epoch_5_s (
    .SUM(next_control_epoch[5]),
    .COUT(next_control_epoch_5_2),
    .I0(control_epoch[5]),
    .I1(GND),
    .I3(VCC),
    .CIN(next_control_epoch_4_2) 
);
defparam next_control_epoch_5_s.ALU_MODE=0;
  ALU next_control_epoch_6_s (
    .SUM(next_control_epoch[6]),
    .COUT(next_control_epoch_6_2),
    .I0(control_epoch[6]),
    .I1(GND),
    .I3(VCC),
    .CIN(next_control_epoch_5_2) 
);
defparam next_control_epoch_6_s.ALU_MODE=0;
  ALU next_control_epoch_7_s (
    .SUM(next_control_epoch[7]),
    .COUT(next_control_epoch_7_0_COUT),
    .I0(control_epoch[7]),
    .I1(GND),
    .I3(VCC),
    .CIN(next_control_epoch_6_2) 
);
defparam next_control_epoch_7_s.ALU_MODE=0;
  ALU n2770_s (
    .SUM(n2770_1),
    .COUT(n2770_2),
    .I0(position_timer[1]),
    .I1(position_timer[0]),
    .I3(VCC),
    .CIN(GND) 
);
defparam n2770_s.ALU_MODE=0;
  ALU n2769_s (
    .SUM(n2769_1),
    .COUT(n2769_2),
    .I0(position_timer[2]),
    .I1(GND),
    .I3(VCC),
    .CIN(n2770_2) 
);
defparam n2769_s.ALU_MODE=0;
  ALU n2768_s (
    .SUM(n2768_1),
    .COUT(n2768_2),
    .I0(position_timer[3]),
    .I1(GND),
    .I3(VCC),
    .CIN(n2769_2) 
);
defparam n2768_s.ALU_MODE=0;
  ALU n2767_s (
    .SUM(n2767_1),
    .COUT(n2767_2),
    .I0(position_timer[4]),
    .I1(GND),
    .I3(VCC),
    .CIN(n2768_2) 
);
defparam n2767_s.ALU_MODE=0;
  ALU n2766_s (
    .SUM(n2766_1),
    .COUT(n2766_2),
    .I0(position_timer[5]),
    .I1(GND),
    .I3(VCC),
    .CIN(n2767_2) 
);
defparam n2766_s.ALU_MODE=0;
  ALU n2765_s (
    .SUM(n2765_1),
    .COUT(n2765_2),
    .I0(position_timer[6]),
    .I1(GND),
    .I3(VCC),
    .CIN(n2766_2) 
);
defparam n2765_s.ALU_MODE=0;
  ALU n2764_s (
    .SUM(n2764_1),
    .COUT(n2764_2),
    .I0(position_timer[7]),
    .I1(GND),
    .I3(VCC),
    .CIN(n2765_2) 
);
defparam n2764_s.ALU_MODE=0;
  ALU n2763_s (
    .SUM(n2763_1),
    .COUT(n2763_2),
    .I0(position_timer[8]),
    .I1(GND),
    .I3(VCC),
    .CIN(n2764_2) 
);
defparam n2763_s.ALU_MODE=0;
  ALU n2762_s (
    .SUM(n2762_1),
    .COUT(n2762_2),
    .I0(position_timer[9]),
    .I1(GND),
    .I3(VCC),
    .CIN(n2763_2) 
);
defparam n2762_s.ALU_MODE=0;
  ALU n2761_s (
    .SUM(n2761_1),
    .COUT(n2761_2),
    .I0(position_timer[10]),
    .I1(GND),
    .I3(VCC),
    .CIN(n2762_2) 
);
defparam n2761_s.ALU_MODE=0;
  ALU n2760_s (
    .SUM(n2760_1),
    .COUT(n2760_2),
    .I0(position_timer[11]),
    .I1(GND),
    .I3(VCC),
    .CIN(n2761_2) 
);
defparam n2760_s.ALU_MODE=0;
  ALU n2759_s (
    .SUM(n2759_1),
    .COUT(n2759_2),
    .I0(position_timer[12]),
    .I1(GND),
    .I3(VCC),
    .CIN(n2760_2) 
);
defparam n2759_s.ALU_MODE=0;
  ALU n2758_s (
    .SUM(n2758_1),
    .COUT(n2758_2),
    .I0(position_timer[13]),
    .I1(GND),
    .I3(VCC),
    .CIN(n2759_2) 
);
defparam n2758_s.ALU_MODE=0;
  ALU n2757_s (
    .SUM(n2757_1),
    .COUT(n2757_2),
    .I0(position_timer[14]),
    .I1(GND),
    .I3(VCC),
    .CIN(n2758_2) 
);
defparam n2757_s.ALU_MODE=0;
  ALU n2756_s (
    .SUM(n2756_1),
    .COUT(n2756_2),
    .I0(position_timer[15]),
    .I1(GND),
    .I3(VCC),
    .CIN(n2757_2) 
);
defparam n2756_s.ALU_MODE=0;
  ALU n2755_s (
    .SUM(n2755_1),
    .COUT(n2755_2),
    .I0(position_timer[16]),
    .I1(GND),
    .I3(VCC),
    .CIN(n2756_2) 
);
defparam n2755_s.ALU_MODE=0;
  ALU n2754_s (
    .SUM(n2754_1),
    .COUT(n2754_2),
    .I0(position_timer[17]),
    .I1(GND),
    .I3(VCC),
    .CIN(n2755_2) 
);
defparam n2754_s.ALU_MODE=0;
  ALU n2753_s (
    .SUM(n2753_1),
    .COUT(n2753_2),
    .I0(position_timer[18]),
    .I1(GND),
    .I3(VCC),
    .CIN(n2754_2) 
);
defparam n2753_s.ALU_MODE=0;
  ALU n2752_s (
    .SUM(n2752_1),
    .COUT(n2752_0_COUT),
    .I0(position_timer[19]),
    .I1(GND),
    .I3(VCC),
    .CIN(n2753_2) 
);
defparam n2752_s.ALU_MODE=0;
  ALU n5100_s (
    .SUM(n5100_1),
    .COUT(n5100_2),
    .I0(navigation_sequence[1]),
    .I1(navigation_sequence[0]),
    .I3(VCC),
    .CIN(GND) 
);
defparam n5100_s.ALU_MODE=0;
  ALU n5099_s (
    .SUM(n5099_1),
    .COUT(n5099_2),
    .I0(navigation_sequence[2]),
    .I1(GND),
    .I3(VCC),
    .CIN(n5100_2) 
);
defparam n5099_s.ALU_MODE=0;
  ALU n5098_s (
    .SUM(n5098_1),
    .COUT(n5098_2),
    .I0(navigation_sequence[3]),
    .I1(GND),
    .I3(VCC),
    .CIN(n5099_2) 
);
defparam n5098_s.ALU_MODE=0;
  ALU n5097_s (
    .SUM(n5097_1),
    .COUT(n5097_2),
    .I0(navigation_sequence[4]),
    .I1(GND),
    .I3(VCC),
    .CIN(n5098_2) 
);
defparam n5097_s.ALU_MODE=0;
  ALU n5096_s (
    .SUM(n5096_1),
    .COUT(n5096_2),
    .I0(navigation_sequence[5]),
    .I1(GND),
    .I3(VCC),
    .CIN(n5097_2) 
);
defparam n5096_s.ALU_MODE=0;
  ALU n5095_s (
    .SUM(n5095_1),
    .COUT(n5095_2),
    .I0(navigation_sequence[6]),
    .I1(GND),
    .I3(VCC),
    .CIN(n5096_2) 
);
defparam n5095_s.ALU_MODE=0;
  ALU n5094_s (
    .SUM(n5094_1),
    .COUT(n5094_2),
    .I0(navigation_sequence[7]),
    .I1(GND),
    .I3(VCC),
    .CIN(n5095_2) 
);
defparam n5094_s.ALU_MODE=0;
  ALU n5093_s (
    .SUM(n5093_1),
    .COUT(n5093_2),
    .I0(navigation_sequence[8]),
    .I1(GND),
    .I3(VCC),
    .CIN(n5094_2) 
);
defparam n5093_s.ALU_MODE=0;
  ALU n5092_s (
    .SUM(n5092_1),
    .COUT(n5092_2),
    .I0(navigation_sequence[9]),
    .I1(GND),
    .I3(VCC),
    .CIN(n5093_2) 
);
defparam n5092_s.ALU_MODE=0;
  ALU n5091_s (
    .SUM(n5091_1),
    .COUT(n5091_2),
    .I0(navigation_sequence[10]),
    .I1(GND),
    .I3(VCC),
    .CIN(n5092_2) 
);
defparam n5091_s.ALU_MODE=0;
  ALU n5090_s (
    .SUM(n5090_1),
    .COUT(n5090_2),
    .I0(navigation_sequence[11]),
    .I1(GND),
    .I3(VCC),
    .CIN(n5091_2) 
);
defparam n5090_s.ALU_MODE=0;
  ALU n5089_s (
    .SUM(n5089_1),
    .COUT(n5089_2),
    .I0(navigation_sequence[12]),
    .I1(GND),
    .I3(VCC),
    .CIN(n5090_2) 
);
defparam n5089_s.ALU_MODE=0;
  ALU n5088_s (
    .SUM(n5088_1),
    .COUT(n5088_2),
    .I0(navigation_sequence[13]),
    .I1(GND),
    .I3(VCC),
    .CIN(n5089_2) 
);
defparam n5088_s.ALU_MODE=0;
  ALU n5087_s (
    .SUM(n5087_1),
    .COUT(n5087_2),
    .I0(navigation_sequence[14]),
    .I1(GND),
    .I3(VCC),
    .CIN(n5088_2) 
);
defparam n5087_s.ALU_MODE=0;
  ALU n5086_s (
    .SUM(n5086_1),
    .COUT(n5086_2),
    .I0(navigation_sequence[15]),
    .I1(GND),
    .I3(VCC),
    .CIN(n5087_2) 
);
defparam n5086_s.ALU_MODE=0;
  ALU n5085_s (
    .SUM(n5085_1),
    .COUT(n5085_2),
    .I0(navigation_sequence[16]),
    .I1(GND),
    .I3(VCC),
    .CIN(n5086_2) 
);
defparam n5085_s.ALU_MODE=0;
  ALU n5084_s (
    .SUM(n5084_1),
    .COUT(n5084_2),
    .I0(navigation_sequence[17]),
    .I1(GND),
    .I3(VCC),
    .CIN(n5085_2) 
);
defparam n5084_s.ALU_MODE=0;
  ALU n5083_s (
    .SUM(n5083_1),
    .COUT(n5083_2),
    .I0(navigation_sequence[18]),
    .I1(GND),
    .I3(VCC),
    .CIN(n5084_2) 
);
defparam n5083_s.ALU_MODE=0;
  ALU n5082_s (
    .SUM(n5082_1),
    .COUT(n5082_2),
    .I0(navigation_sequence[19]),
    .I1(GND),
    .I3(VCC),
    .CIN(n5083_2) 
);
defparam n5082_s.ALU_MODE=0;
  ALU n5081_s (
    .SUM(n5081_1),
    .COUT(n5081_2),
    .I0(navigation_sequence[20]),
    .I1(GND),
    .I3(VCC),
    .CIN(n5082_2) 
);
defparam n5081_s.ALU_MODE=0;
  ALU n5080_s (
    .SUM(n5080_1),
    .COUT(n5080_2),
    .I0(navigation_sequence[21]),
    .I1(GND),
    .I3(VCC),
    .CIN(n5081_2) 
);
defparam n5080_s.ALU_MODE=0;
  ALU n5079_s (
    .SUM(n5079_1),
    .COUT(n5079_2),
    .I0(navigation_sequence[22]),
    .I1(GND),
    .I3(VCC),
    .CIN(n5080_2) 
);
defparam n5079_s.ALU_MODE=0;
  ALU n5078_s (
    .SUM(n5078_1),
    .COUT(n5078_2),
    .I0(navigation_sequence[23]),
    .I1(GND),
    .I3(VCC),
    .CIN(n5079_2) 
);
defparam n5078_s.ALU_MODE=0;
  ALU n5077_s (
    .SUM(n5077_1),
    .COUT(n5077_2),
    .I0(navigation_sequence[24]),
    .I1(GND),
    .I3(VCC),
    .CIN(n5078_2) 
);
defparam n5077_s.ALU_MODE=0;
  ALU n5076_s (
    .SUM(n5076_1),
    .COUT(n5076_2),
    .I0(navigation_sequence[25]),
    .I1(GND),
    .I3(VCC),
    .CIN(n5077_2) 
);
defparam n5076_s.ALU_MODE=0;
  ALU n5075_s (
    .SUM(n5075_1),
    .COUT(n5075_2),
    .I0(navigation_sequence[26]),
    .I1(GND),
    .I3(VCC),
    .CIN(n5076_2) 
);
defparam n5075_s.ALU_MODE=0;
  ALU n5074_s (
    .SUM(n5074_1),
    .COUT(n5074_2),
    .I0(navigation_sequence[27]),
    .I1(GND),
    .I3(VCC),
    .CIN(n5075_2) 
);
defparam n5074_s.ALU_MODE=0;
  ALU n5073_s (
    .SUM(n5073_1),
    .COUT(n5073_2),
    .I0(navigation_sequence[28]),
    .I1(GND),
    .I3(VCC),
    .CIN(n5074_2) 
);
defparam n5073_s.ALU_MODE=0;
  ALU n5072_s (
    .SUM(n5072_1),
    .COUT(n5072_2),
    .I0(navigation_sequence[29]),
    .I1(GND),
    .I3(VCC),
    .CIN(n5073_2) 
);
defparam n5072_s.ALU_MODE=0;
  ALU n5071_s (
    .SUM(n5071_1),
    .COUT(n5071_2),
    .I0(navigation_sequence[30]),
    .I1(GND),
    .I3(VCC),
    .CIN(n5072_2) 
);
defparam n5071_s.ALU_MODE=0;
  ALU n5070_s (
    .SUM(n5070_1),
    .COUT(n5070_0_COUT),
    .I0(navigation_sequence[31]),
    .I1(GND),
    .I3(VCC),
    .CIN(n5071_2) 
);
defparam n5070_s.ALU_MODE=0;
  ALU n4152_s0 (
    .SUM(n4152_1_SUM),
    .COUT(n4152_3),
    .I0(c_observation_epoch[0]),
    .I1(observation_epoch[0]),
    .I3(GND),
    .CIN(GND) 
);
defparam n4152_s0.ALU_MODE=3;
  ALU n4153_s0 (
    .SUM(n4153_1_SUM),
    .COUT(n4153_3),
    .I0(c_observation_epoch[1]),
    .I1(observation_epoch[1]),
    .I3(GND),
    .CIN(n4152_3) 
);
defparam n4153_s0.ALU_MODE=3;
  ALU n4154_s0 (
    .SUM(n4154_1_SUM),
    .COUT(n4154_3),
    .I0(c_observation_epoch[2]),
    .I1(observation_epoch[2]),
    .I3(GND),
    .CIN(n4153_3) 
);
defparam n4154_s0.ALU_MODE=3;
  ALU n4155_s0 (
    .SUM(n4155_1_SUM),
    .COUT(n4155_3),
    .I0(c_observation_epoch[3]),
    .I1(observation_epoch[3]),
    .I3(GND),
    .CIN(n4154_3) 
);
defparam n4155_s0.ALU_MODE=3;
  ALU n4156_s0 (
    .SUM(n4156_1_SUM),
    .COUT(n4156_3),
    .I0(c_observation_epoch[4]),
    .I1(observation_epoch[4]),
    .I3(GND),
    .CIN(n4155_3) 
);
defparam n4156_s0.ALU_MODE=3;
  ALU n4157_s0 (
    .SUM(n4157_1_SUM),
    .COUT(n4157_3),
    .I0(c_observation_epoch[5]),
    .I1(observation_epoch[5]),
    .I3(GND),
    .CIN(n4156_3) 
);
defparam n4157_s0.ALU_MODE=3;
  ALU n4158_s0 (
    .SUM(n4158_1_SUM),
    .COUT(n4158_3),
    .I0(c_observation_epoch[6]),
    .I1(observation_epoch[6]),
    .I3(GND),
    .CIN(n4157_3) 
);
defparam n4158_s0.ALU_MODE=3;
  ALU n4159_s0 (
    .SUM(n4159_1_SUM),
    .COUT(n4159_3),
    .I0(c_observation_epoch[7]),
    .I1(p_observation_epoch[7]),
    .I3(GND),
    .CIN(n4158_3) 
);
defparam n4159_s0.ALU_MODE=3;
  ALU n4161_s0 (
    .SUM(n4161_1_SUM),
    .COUT(n4161_3),
    .I0(c_control_epoch[0]),
    .I1(control_epoch[0]),
    .I3(GND),
    .CIN(GND) 
);
defparam n4161_s0.ALU_MODE=3;
  ALU n4162_s0 (
    .SUM(n4162_1_SUM),
    .COUT(n4162_3),
    .I0(c_control_epoch[1]),
    .I1(control_epoch[1]),
    .I3(GND),
    .CIN(n4161_3) 
);
defparam n4162_s0.ALU_MODE=3;
  ALU n4163_s0 (
    .SUM(n4163_1_SUM),
    .COUT(n4163_3),
    .I0(c_control_epoch[2]),
    .I1(control_epoch[2]),
    .I3(GND),
    .CIN(n4162_3) 
);
defparam n4163_s0.ALU_MODE=3;
  ALU n4164_s0 (
    .SUM(n4164_1_SUM),
    .COUT(n4164_3),
    .I0(c_control_epoch[3]),
    .I1(control_epoch[3]),
    .I3(GND),
    .CIN(n4163_3) 
);
defparam n4164_s0.ALU_MODE=3;
  ALU n4165_s0 (
    .SUM(n4165_1_SUM),
    .COUT(n4165_3),
    .I0(c_control_epoch[4]),
    .I1(control_epoch[4]),
    .I3(GND),
    .CIN(n4164_3) 
);
defparam n4165_s0.ALU_MODE=3;
  ALU n4166_s0 (
    .SUM(n4166_1_SUM),
    .COUT(n4166_3),
    .I0(c_control_epoch[5]),
    .I1(control_epoch[5]),
    .I3(GND),
    .CIN(n4165_3) 
);
defparam n4166_s0.ALU_MODE=3;
  ALU n4167_s0 (
    .SUM(n4167_1_SUM),
    .COUT(n4167_3),
    .I0(c_control_epoch[6]),
    .I1(control_epoch[6]),
    .I3(GND),
    .CIN(n4166_3) 
);
defparam n4167_s0.ALU_MODE=3;
  ALU n4168_s0 (
    .SUM(n4168_1_SUM),
    .COUT(n4168_3),
    .I0(c_control_epoch[7]),
    .I1(control_epoch[7]),
    .I3(GND),
    .CIN(n4167_3) 
);
defparam n4168_s0.ALU_MODE=3;
  INV n2771_s2 (
    .O(n2771_6),
    .I(position_timer[0]) 
);
  INV n5101_s2 (
    .O(n5101_6),
    .I(navigation_sequence[0]) 
);
  nav_math_service multiply_service (
    .clk50_d(clk50_d),
    .n13_16(n13_16),
    .m_cancel_0_7(m_cancel_0_7),
    .nav_vertical_ready_4(nav_vertical_ready_4),
    .d_cancel(d_cancel_1[3]),
    .d_cancel_27(d_cancel_0[2]),
    .d_cancel_28(d_cancel[1]),
    .m_cancel(m_cancel[0]),
    .m_request(m_request_2[3]),
    .m_request_29(m_request_1[2]),
    .m_request_30(m_request_0[1]),
    .m_a(m_a_1[191:128]),
    .m_b_192(m_b_2[192]),
    .m_b_193(m_b_2[193]),
    .m_b_194(m_b_2[194]),
    .m_b_195(m_b_2[195]),
    .m_b_196(m_b_2[196]),
    .m_b_197(m_b_2[197]),
    .m_b_198(m_b_2[198]),
    .m_b_199(m_b_2[199]),
    .m_b_200(m_b_2[200]),
    .m_b_201(m_b_2[201]),
    .m_b_202(m_b_2[202]),
    .m_b_203(m_b_2[203]),
    .m_b_204(m_b_2[204]),
    .m_b_205(m_b_2[205]),
    .m_b_206(m_b_2[206]),
    .m_b_207(m_b_2[207]),
    .m_b_208(m_b_2[208]),
    .m_b_209(m_b_2[209]),
    .m_b_210(m_b_2[210]),
    .m_b_211(m_b_2[211]),
    .m_b_212(m_b_2[212]),
    .m_b_213(m_b_2[213]),
    .m_b_214(m_b_2[214]),
    .m_b_215(m_b_2[215]),
    .m_b_216(m_b_2[216]),
    .m_b_217(m_b_2[217]),
    .m_b_218(m_b_2[218]),
    .m_b_225(m_b_2[225]),
    .m_request_31(m_request[0]),
    .m_a_32(m_a_2[241:192]),
    .m_a_33(m_a_0[96:64]),
    .m_a_34(m_a[47:0]),
    .m_b_35(m_b_0[81:64]),
    .m_b_0(m_b[0]),
    .m_b_1(m_b[1]),
    .m_b_2(m_b[2]),
    .m_b_3(m_b[3]),
    .m_b_4(m_b[4]),
    .m_b_5(m_b[5]),
    .m_b_6(m_b[6]),
    .m_b_7(m_b[7]),
    .m_b_8(m_b[8]),
    .m_b_9(m_b[9]),
    .m_b_10(m_b[10]),
    .m_b_11(m_b[11]),
    .m_b_12(m_b[12]),
    .m_b_13(m_b[13]),
    .m_b_14(m_b[14]),
    .m_b_15(m_b[15]),
    .m_b_16(m_b[16]),
    .m_b_23(m_b[23]),
    .m_b_24(m_b[24]),
    .m_b_37(m_b_1[151:128]),
    .n107_3(n107_3),
    .n128_3(n128_3),
    .n149_3(n149_3),
    .m_done_1_3(m_done_1_3),
    .m_done_3_3(m_done_3_3),
    .n2322_5(n2322_5),
    .n2330_5(n2330_5),
    .n2338_5(n2338_5),
    .done_q_0(done_q[0]),
    .done_q_2(done_q[2]),
    .m_result(m_result[63:0]),
    .response_owner(response_owner[1:0]),
    .previous_cancel(previous_cancel[0]),
    .m_done_1(m_done[1]),
    .m_done_3(m_done[3]),
    .\generation[1] (\generation[1] [0]),
    .\generation[2] (\generation[2] [0]),
    .\generation[3] (\generation[3] [0])
);
  nav_math_service_0 divide_service (
    .clk50_d(clk50_d),
    .n13_16(n13_16),
    .n2322_5(n2322_5),
    .n2330_5(n2330_5),
    .n2338_5(n2338_5),
    .\generation[1] (\generation[1] [0]),
    .\generation[2] (\generation[2] [0]),
    .\generation[3] (\generation[3] [0]),
    .d_cancel(d_cancel_1[3]),
    .d_request(d_request_1[3]),
    .d_request_38(d_request[1]),
    .d_b_192(d_b_1[192]),
    .d_b_193(d_b_1[193]),
    .d_b_194(d_b_1[194]),
    .d_b_195(d_b_1[195]),
    .d_b_196(d_b_1[196]),
    .d_b_197(d_b_1[197]),
    .d_b_198(d_b_1[198]),
    .d_b_199(d_b_1[199]),
    .d_b_200(d_b_1[200]),
    .d_b_201(d_b_1[201]),
    .d_b_202(d_b_1[202]),
    .d_b_203(d_b_1[203]),
    .d_b_204(d_b_1[204]),
    .d_b_205(d_b_1[205]),
    .d_b_206(d_b_1[206]),
    .d_b_207(d_b_1[207]),
    .d_b_208(d_b_1[208]),
    .d_b_209(d_b_1[209]),
    .d_b_210(d_b_1[210]),
    .d_b_211(d_b_1[211]),
    .d_b_212(d_b_1[212]),
    .d_b_213(d_b_1[213]),
    .d_b_214(d_b_1[214]),
    .d_b_215(d_b_1[215]),
    .d_b_216(d_b_1[216]),
    .d_b_217(d_b_1[217]),
    .d_b_223(d_b_1[223]),
    .d_b_39(d_b[95:64]),
    .d_cancel_40(d_cancel_0[2]),
    .d_cancel_41(d_cancel[1]),
    .d_request_42(d_request_0[2]),
    .d_a(d_a_1[255:192]),
    .d_a_43(d_a_0[191:128]),
    .d_b_128(d_b_0[128]),
    .d_b_129(d_b_0[129]),
    .d_b_130(d_b_0[130]),
    .d_b_131(d_b_0[131]),
    .d_b_132(d_b_0[132]),
    .d_b_133(d_b_0[133]),
    .d_b_134(d_b_0[134]),
    .d_b_135(d_b_0[135]),
    .d_b_137(d_b_0[137]),
    .d_b_141(d_b_0[141]),
    .d_b_147(d_b_0[147]),
    .d_b_152(d_b_0[152]),
    .d_a_45(d_a[113:64]),
    .n128_3(n128_3_52),
    .n149_3(n149_3_53),
    .n172_3(n172_3),
    .done_q(done_q_0[3:1]),
    .error_q(error_q[3:1]),
    .d_result(d_result[63:0]),
    .response_owner(response_owner_0[1:0])
);
  mtf_shared_geometry geometry (
    .clk50_d(clk50_d),
    .nav_vertical_ready_4(nav_vertical_ready_4),
    .n3216_8(n3216_8),
    .extension_113_5(extension_113_5),
    .mtf_range_ok(mtf_range_ok),
    .body_yaw_range_ok(body_yaw_range_ok),
    .saturated_Z(saturated_Z),
    .mtf_integrated(mtf_integrated),
    .flow_ok(flow_ok),
    .n13_16(n13_16),
    .mtf_sample(mtf_sample),
    .n6355_9(n6355_9),
    .n6363_6(n6363_6),
    .n6360_5(n6360_5),
    .n6370_4(n6370_4),
    .n107_3(n107_3),
    .n3649_6(n3649_6),
    .n3649_7(n3649_7),
    .n3648_6(n3648_6),
    .n3648_12(n3648_12),
    .pitch_Z_6_13(pitch_Z_6_13),
    .pitch_Z_2_13(pitch_Z_2_13),
    .link_fresh(link_fresh),
    .sample_valid_Z(sample_valid_Z),
    .mtf_range_ok_3(mtf_range_ok_3),
    .n13_13(n13_13),
    .n13_14(n13_14),
    .pitch_Z(pitch_Z[15:1]),
    .sensor_pitch_0(sensor_pitch_0),
    .sensor_pitch_2(sensor_pitch_2),
    .sensor_pitch_3(sensor_pitch_3),
    .sensor_pitch_4(sensor_pitch_4),
    .sensor_pitch_5(sensor_pitch_5),
    .sensor_pitch_6(sensor_pitch_6),
    .sensor_pitch_7(sensor_pitch_7),
    .sensor_pitch_8(sensor_pitch_8),
    .sensor_pitch_9(sensor_pitch_9),
    .sensor_pitch_10(sensor_pitch_10),
    .sensor_pitch_11(sensor_pitch_11),
    .sensor_pitch_12(sensor_pitch_12),
    .body_yaw(body_yaw[15:1]),
    .sensor_yaw(sensor_yaw[0]),
    .mtf_distance_mm(mtf_distance_mm[13:0]),
    .mtf_vy_x100_0(mtf_vy_x100_0),
    .mtf_vy_x100_1(mtf_vy_x100_1),
    .mtf_vy_x100_2(mtf_vy_x100_2),
    .mtf_vy_x100_3(mtf_vy_x100_3),
    .mtf_vy_x100_4(mtf_vy_x100_4),
    .mtf_vy_x100_5(mtf_vy_x100_5),
    .mtf_vy_x100_6(mtf_vy_x100_6),
    .mtf_vy_x100_7(mtf_vy_x100_7),
    .mtf_vy_x100_8(mtf_vy_x100_8),
    .mtf_vy_x100_9(mtf_vy_x100_9),
    .mtf_vy_x100_10(mtf_vy_x100_10),
    .mtf_vy_x100_11(mtf_vy_x100_11),
    .mtf_vy_x100_12(mtf_vy_x100_12),
    .mtf_vy_x100_13(mtf_vy_x100_13),
    .mtf_vy_x100_14(mtf_vy_x100_14),
    .mtf_vy_x100_15(mtf_vy_x100_15),
    .mtf_vy_x100_16(mtf_vy_x100_16),
    .mtf_vy_x100_17(mtf_vy_x100_17),
    .mtf_vy_x100_18(mtf_vy_x100_18),
    .mtf_vy_x100_19(mtf_vy_x100_19),
    .mtf_vy_x100_20(mtf_vy_x100_20),
    .mtf_vy_x100_21(mtf_vy_x100_21),
    .mtf_vy_x100_22(mtf_vy_x100_22),
    .mtf_vy_x100_23(mtf_vy_x100_23),
    .mtf_vy_x100_24(mtf_vy_x100_24),
    .mtf_vy_x100_25(mtf_vy_x100_25),
    .mtf_vy_x100_26(mtf_vy_x100_26),
    .mtf_vy_x100_27(mtf_vy_x100_27),
    .mtf_vy_x100_28(mtf_vy_x100_28),
    .mtf_vy_x100_29(mtf_vy_x100_29),
    .mtf_vy_x100_31(mtf_vy_x100_31),
    .mtf_vx_x100_0(mtf_vx_x100_0),
    .mtf_vx_x100_1(mtf_vx_x100_1),
    .mtf_vx_x100_2(mtf_vx_x100_2),
    .mtf_vx_x100_3(mtf_vx_x100_3),
    .mtf_vx_x100_4(mtf_vx_x100_4),
    .mtf_vx_x100_5(mtf_vx_x100_5),
    .mtf_vx_x100_6(mtf_vx_x100_6),
    .mtf_vx_x100_7(mtf_vx_x100_7),
    .mtf_vx_x100_8(mtf_vx_x100_8),
    .mtf_vx_x100_9(mtf_vx_x100_9),
    .mtf_vx_x100_10(mtf_vx_x100_10),
    .mtf_vx_x100_11(mtf_vx_x100_11),
    .mtf_vx_x100_12(mtf_vx_x100_12),
    .mtf_vx_x100_13(mtf_vx_x100_13),
    .mtf_vx_x100_14(mtf_vx_x100_14),
    .mtf_vx_x100_15(mtf_vx_x100_15),
    .mtf_vx_x100_16(mtf_vx_x100_16),
    .mtf_vx_x100_17(mtf_vx_x100_17),
    .mtf_vx_x100_18(mtf_vx_x100_18),
    .mtf_vx_x100_19(mtf_vx_x100_19),
    .mtf_vx_x100_20(mtf_vx_x100_20),
    .mtf_vx_x100_21(mtf_vx_x100_21),
    .mtf_vx_x100_22(mtf_vx_x100_22),
    .mtf_vx_x100_23(mtf_vx_x100_23),
    .mtf_vx_x100_24(mtf_vx_x100_24),
    .mtf_vx_x100_25(mtf_vx_x100_25),
    .mtf_vx_x100_26(mtf_vx_x100_26),
    .mtf_vx_x100_27(mtf_vx_x100_27),
    .mtf_vx_x100_28(mtf_vx_x100_28),
    .mtf_vx_x100_29(mtf_vx_x100_29),
    .mtf_vx_x100_31(mtf_vx_x100_31),
    .m_result(m_result[63:0]),
    .mtf_dt_ms(mtf_dt_ms[30:0]),
    .roll(roll[15:0]),
    .response_owner(response_owner[1:0]),
    .done_q(done_q[0]),
    .previous_cancel(previous_cancel[0]),
    .geometry_update(geometry_update),
    .geometry_height_ready(geometry_height_ready),
    .geometry_height_ready_3(geometry_height_ready_3),
    .n1126_5(n1126_5),
    .geometry_reason_1_7(geometry_reason_1_7),
    .geometry_reason_1_8(geometry_reason_1_8),
    .geometry_flow_ready(geometry_flow_ready),
    .m_cancel_0_7(m_cancel_0_7),
    .geometry_reason_7_4(geometry_reason_7_4),
    .m_request(m_request[0]),
    .bvx_0(bvx[0]),
    .bvx_1(bvx[1]),
    .bvx_2(bvx[2]),
    .bvx_3(bvx[3]),
    .bvx_4(bvx[4]),
    .bvx_5(bvx[5]),
    .bvx_6(bvx[6]),
    .bvx_7(bvx[7]),
    .bvx_8(bvx[8]),
    .bvx_9(bvx[9]),
    .bvx_10(bvx[10]),
    .bvx_11(bvx[11]),
    .bvx_12(bvx[12]),
    .bvx_13(bvx[13]),
    .bvx_14(bvx[14]),
    .bvx_15(bvx[15]),
    .bvx_16(bvx[16]),
    .bvx_17(bvx[17]),
    .bvx_18(bvx[18]),
    .bvx_19(bvx[19]),
    .bvx_20(bvx[20]),
    .bvx_21(bvx[21]),
    .bvx_22(bvx[22]),
    .bvx_23(bvx[23]),
    .bvx_24(bvx[24]),
    .bvx_25(bvx[25]),
    .bvx_26(bvx[26]),
    .bvx_27(bvx[27]),
    .bvx_28(bvx[28]),
    .bvx_29(bvx[29]),
    .bvx_31(bvx[31]),
    .bvy_0(bvy[0]),
    .bvy_1(bvy[1]),
    .bvy_2(bvy[2]),
    .bvy_3(bvy[3]),
    .bvy_4(bvy[4]),
    .bvy_5(bvy[5]),
    .bvy_6(bvy[6]),
    .bvy_7(bvy[7]),
    .bvy_8(bvy[8]),
    .bvy_9(bvy[9]),
    .bvy_10(bvy[10]),
    .bvy_11(bvy[11]),
    .bvy_12(bvy[12]),
    .bvy_13(bvy[13]),
    .bvy_14(bvy[14]),
    .bvy_15(bvy[15]),
    .bvy_16(bvy[16]),
    .bvy_17(bvy[17]),
    .bvy_18(bvy[18]),
    .bvy_19(bvy[19]),
    .bvy_20(bvy[20]),
    .bvy_21(bvy[21]),
    .bvy_22(bvy[22]),
    .bvy_23(bvy[23]),
    .bvy_24(bvy[24]),
    .bvy_25(bvy[25]),
    .bvy_26(bvy[26]),
    .bvy_27(bvy[27]),
    .bvy_28(bvy[28]),
    .bvy_29(bvy[29]),
    .bvy_31(bvy[31]),
    .wvx_0(wvx[0]),
    .wvx_1(wvx[1]),
    .wvx_2(wvx[2]),
    .wvx_3(wvx[3]),
    .wvx_4(wvx[4]),
    .wvx_5(wvx[5]),
    .wvx_6(wvx[6]),
    .wvx_7(wvx[7]),
    .wvx_8(wvx[8]),
    .wvx_9(wvx[9]),
    .wvx_10(wvx[10]),
    .wvx_11(wvx[11]),
    .wvx_12(wvx[12]),
    .wvx_13(wvx[13]),
    .wvx_14(wvx[14]),
    .wvx_15(wvx[15]),
    .wvx_16(wvx[16]),
    .wvx_17(wvx[17]),
    .wvx_18(wvx[18]),
    .wvx_19(wvx[19]),
    .wvx_20(wvx[20]),
    .wvx_21(wvx[21]),
    .wvx_22(wvx[22]),
    .wvx_23(wvx[23]),
    .wvx_24(wvx[24]),
    .wvx_25(wvx[25]),
    .wvx_26(wvx[26]),
    .wvx_27(wvx[27]),
    .wvx_28(wvx[28]),
    .wvx_29(wvx[29]),
    .wvx_31(wvx[31]),
    .wvy_0(wvy[0]),
    .wvy_1(wvy[1]),
    .wvy_2(wvy[2]),
    .wvy_3(wvy[3]),
    .wvy_4(wvy[4]),
    .wvy_5(wvy[5]),
    .wvy_6(wvy[6]),
    .wvy_7(wvy[7]),
    .wvy_8(wvy[8]),
    .wvy_9(wvy[9]),
    .wvy_10(wvy[10]),
    .wvy_11(wvy[11]),
    .wvy_12(wvy[12]),
    .wvy_13(wvy[13]),
    .wvy_14(wvy[14]),
    .wvy_15(wvy[15]),
    .wvy_16(wvy[16]),
    .wvy_17(wvy[17]),
    .wvy_18(wvy[18]),
    .wvy_19(wvy[19]),
    .wvy_20(wvy[20]),
    .wvy_21(wvy[21]),
    .wvy_22(wvy[22]),
    .wvy_23(wvy[23]),
    .wvy_24(wvy[24]),
    .wvy_25(wvy[25]),
    .wvy_26(wvy[26]),
    .wvy_27(wvy[27]),
    .wvy_28(wvy[28]),
    .wvy_29(wvy[29]),
    .wvy_31(wvy[31]),
    .geometry_dt_us(geometry_dt_us[15:0]),
    .geometry_reason_0(geometry_reason[0]),
    .geometry_reason_1(geometry_reason[1]),
    .geometry_reason_2(geometry_reason[2]),
    .geometry_reason_3(geometry_reason[3]),
    .geometry_reason_4(geometry_reason[4]),
    .geometry_reason_5(geometry_reason[5]),
    .geometry_reason_6(geometry_reason[6]),
    .geometry_reason_11(geometry_reason[11]),
    .m_a(m_a[47:0]),
    .m_b_0(m_b[0]),
    .m_b_1(m_b[1]),
    .m_b_2(m_b[2]),
    .m_b_3(m_b[3]),
    .m_b_4(m_b[4]),
    .m_b_5(m_b[5]),
    .m_b_6(m_b[6]),
    .m_b_7(m_b[7]),
    .m_b_8(m_b[8]),
    .m_b_9(m_b[9]),
    .m_b_10(m_b[10]),
    .m_b_11(m_b[11]),
    .m_b_12(m_b[12]),
    .m_b_13(m_b[13]),
    .m_b_14(m_b[14]),
    .m_b_15(m_b[15]),
    .m_b_16(m_b[16]),
    .m_b_23(m_b[23]),
    .m_b_24(m_b[24]),
    .height_mm_Z_0(height_mm_Z[0]),
    .height_mm_Z_1(height_mm_Z[1]),
    .height_mm_Z_2(height_mm_Z[2]),
    .height_mm_Z_3(height_mm_Z[3]),
    .height_mm_Z_4(height_mm_Z[4]),
    .height_mm_Z_5(height_mm_Z[5]),
    .height_mm_Z_6(height_mm_Z[6]),
    .height_mm_Z_7(height_mm_Z[7]),
    .height_mm_Z_8(height_mm_Z[8]),
    .height_mm_Z_9(height_mm_Z[9]),
    .height_mm_Z_10(height_mm_Z[10]),
    .height_mm_Z_11(height_mm_Z[11]),
    .height_mm_Z_12(height_mm_Z[12]),
    .height_mm_Z_31(height_mm_Z[31]),
    .m_cancel(m_cancel[0])
);
  mtf_shared_flow_fusion velocity_fusion (
    .clk50_d(clk50_d),
    .n3216_8(n3216_8),
    .n13_16(n13_16),
    .live_velocity_6(live_velocity_6),
    .acceleration_update(acceleration_update),
    .geometry_update(geometry_update),
    .geometry_flow_ready(geometry_flow_ready),
    .n128_3(n128_3_52),
    .nav_xy_ready_5(nav_xy_ready_5),
    .nav_xy_ready_6(nav_xy_ready_6),
    .previous_pose_valid(previous_pose_valid),
    .pose_valid(pose_valid),
    .n128_3_46(n128_3),
    .m_done_1_3(m_done_1_3),
    .m_done(m_done[1]),
    .converted_ax(converted_ax[15:0]),
    .converted_ay(converted_ay[15:0]),
    .converted_dt_us(converted_dt_us[31:0]),
    .wvx_0(wvx[0]),
    .wvx_1(wvx[1]),
    .wvx_2(wvx[2]),
    .wvx_3(wvx[3]),
    .wvx_4(wvx[4]),
    .wvx_5(wvx[5]),
    .wvx_6(wvx[6]),
    .wvx_7(wvx[7]),
    .wvx_8(wvx[8]),
    .wvx_9(wvx[9]),
    .wvx_10(wvx[10]),
    .wvx_11(wvx[11]),
    .wvx_12(wvx[12]),
    .wvx_13(wvx[13]),
    .wvx_14(wvx[14]),
    .wvx_15(wvx[15]),
    .wvx_16(wvx[16]),
    .wvx_17(wvx[17]),
    .wvx_18(wvx[18]),
    .wvx_19(wvx[19]),
    .wvx_20(wvx[20]),
    .wvx_21(wvx[21]),
    .wvx_22(wvx[22]),
    .wvx_23(wvx[23]),
    .wvx_24(wvx[24]),
    .wvx_25(wvx[25]),
    .wvx_26(wvx[26]),
    .wvx_27(wvx[27]),
    .wvx_28(wvx[28]),
    .wvx_29(wvx[29]),
    .wvx_31(wvx[31]),
    .wvy_0(wvy[0]),
    .wvy_1(wvy[1]),
    .wvy_2(wvy[2]),
    .wvy_3(wvy[3]),
    .wvy_4(wvy[4]),
    .wvy_5(wvy[5]),
    .wvy_6(wvy[6]),
    .wvy_7(wvy[7]),
    .wvy_8(wvy[8]),
    .wvy_9(wvy[9]),
    .wvy_10(wvy[10]),
    .wvy_11(wvy[11]),
    .wvy_12(wvy[12]),
    .wvy_13(wvy[13]),
    .wvy_14(wvy[14]),
    .wvy_15(wvy[15]),
    .wvy_16(wvy[16]),
    .wvy_17(wvy[17]),
    .wvy_18(wvy[18]),
    .wvy_19(wvy[19]),
    .wvy_20(wvy[20]),
    .wvy_21(wvy[21]),
    .wvy_22(wvy[22]),
    .wvy_23(wvy[23]),
    .wvy_24(wvy[24]),
    .wvy_25(wvy[25]),
    .wvy_26(wvy[26]),
    .wvy_27(wvy[27]),
    .wvy_28(wvy[28]),
    .wvy_29(wvy[29]),
    .wvy_31(wvy[31]),
    .geometry_dt_us(geometry_dt_us[15:0]),
    .m_result(m_result[49:0]),
    .d_result(d_result[32:0]),
    .error_q(error_q[1]),
    .response_owner(response_owner_0[1:0]),
    .done_q(done_q_0[1]),
    .flow_fusion_qualified(flow_fusion_qualified),
    .pending_acc_epoch_ok_9(pending_acc_epoch_ok_9),
    .pending_acc_epoch_ok_10(pending_acc_epoch_ok_10),
    .pending_acc_epoch_ok_11(pending_acc_epoch_ok_11),
    .flow_fusion_valid(flow_fusion_valid),
    .m_request(m_request_0[1]),
    .d_request(d_request[1]),
    .fused_vx_q16_Z(fused_vx_q16_Z[30:0]),
    .fused_vy_q16_Z(fused_vy_q16_Z[30:0]),
    .flow_reason_0(flow_reason[0]),
    .flow_reason_2(flow_reason[2]),
    .flow_reason_3(flow_reason[3]),
    .m_a(m_a_0[96:64]),
    .m_b(m_b_0[81:64]),
    .d_a(d_a[113:64]),
    .d_b(d_b[95:64]),
    .d_cancel(d_cancel[1])
);
  mtf_shared_height_fusion height_fusion (
    .clk50_d(clk50_d),
    .n3216_8(n3216_8),
    .n13_16(n13_16),
    .acceleration_update(acceleration_update),
    .n149_3(n149_3),
    .n149_3_47(n149_3_53),
    .pending_acc_epoch_ok_9(pending_acc_epoch_ok_9),
    .pending_acc_epoch_ok_10(pending_acc_epoch_ok_10),
    .pending_acc_epoch_ok_11(pending_acc_epoch_ok_11),
    .nav_vertical_ready_3(nav_vertical_ready_3),
    .geometry_height_ready_3(geometry_height_ready_3),
    .nav_vertical_ready_4(nav_vertical_ready_4),
    .n13_13(n13_13),
    .n13_14(n13_14),
    .converted_az(converted_az[15:0]),
    .converted_dt_us(converted_dt_us[16:0]),
    .height_mm_Z_0(height_mm_Z[0]),
    .height_mm_Z_1(height_mm_Z[1]),
    .height_mm_Z_2(height_mm_Z[2]),
    .height_mm_Z_3(height_mm_Z[3]),
    .height_mm_Z_4(height_mm_Z[4]),
    .height_mm_Z_5(height_mm_Z[5]),
    .height_mm_Z_6(height_mm_Z[6]),
    .height_mm_Z_7(height_mm_Z[7]),
    .height_mm_Z_8(height_mm_Z[8]),
    .height_mm_Z_9(height_mm_Z[9]),
    .height_mm_Z_10(height_mm_Z[10]),
    .height_mm_Z_11(height_mm_Z[11]),
    .height_mm_Z_12(height_mm_Z[12]),
    .height_mm_Z_31(height_mm_Z[31]),
    .d_result(d_result[63:0]),
    .m_result(m_result[63:0]),
    .error_q(error_q[2]),
    .response_owner(response_owner[1:0]),
    .done_q(done_q[2]),
    .response_owner_48(response_owner_0[1:0]),
    .done_q_49(done_q_0[2]),
    .height_qualified_ready(height_qualified_ready),
    .height_fusion_update(height_fusion_update),
    .v_q16_range(v_q16_range),
    .n6360_5(n6360_5),
    .n6370_4(n6370_4),
    .height_estimate_ready_6(height_estimate_ready_6),
    .n6355_9(n6355_9),
    .n6363_6(n6363_6),
    .height_estimate_ready_20(height_estimate_ready_20),
    .m_request(m_request_1[2]),
    .d_request(d_request_0[2]),
    .height_sample_az_0(height_sample_az[0]),
    .height_sample_az_1(height_sample_az[1]),
    .height_sample_az_2(height_sample_az[2]),
    .height_sample_az_3(height_sample_az[3]),
    .height_sample_az_4(height_sample_az[4]),
    .height_sample_az_5(height_sample_az[5]),
    .height_sample_az_6(height_sample_az[6]),
    .height_sample_az_7(height_sample_az[7]),
    .height_sample_az_8(height_sample_az[8]),
    .height_sample_az_9(height_sample_az[9]),
    .height_sample_az_10(height_sample_az[10]),
    .height_sample_az_11(height_sample_az[11]),
    .height_sample_az_12(height_sample_az[12]),
    .height_sample_az_13(height_sample_az[13]),
    .height_sample_az_14(height_sample_az[14]),
    .height_sample_az_31(height_sample_az[31]),
    .fused_vz_q16(fused_vz_q16[31:0]),
    .m_a(m_a_1[191:128]),
    .m_b(m_b_1[151:128]),
    .d_a(d_a_0[191:128]),
    .d_b_128(d_b_0[128]),
    .d_b_129(d_b_0[129]),
    .d_b_130(d_b_0[130]),
    .d_b_131(d_b_0[131]),
    .d_b_132(d_b_0[132]),
    .d_b_133(d_b_0[133]),
    .d_b_134(d_b_0[134]),
    .d_b_135(d_b_0[135]),
    .d_b_137(d_b_0[137]),
    .d_b_141(d_b_0[141]),
    .d_b_147(d_b_0[147]),
    .d_b_152(d_b_0[152]),
    .d_cancel(d_cancel_0[2]),
    .publication_age(publication_age[22]),
    .fused_height(fused_height[31:0])
);
  mtf_position_integrator position (
    .clk50_d(clk50_d),
    .n13_16(n13_16),
    .observer_reset(observer_reset),
    .p_live(p_live),
    .position_tick(position_tick),
    .previous_pose_valid(previous_pose_valid),
    .pose_valid(pose_valid),
    .n2737_7(n2737_7),
    .n13_13(n13_13),
    .n13_14(n13_14),
    .position_ready_7(position_ready_7),
    .p_vy_0(p_vy[0]),
    .p_vy_1(p_vy[1]),
    .p_vy_2(p_vy[2]),
    .p_vy_3(p_vy[3]),
    .p_vy_4(p_vy[4]),
    .p_vy_5(p_vy[5]),
    .p_vy_6(p_vy[6]),
    .p_vy_7(p_vy[7]),
    .p_vy_8(p_vy[8]),
    .p_vy_9(p_vy[9]),
    .p_vy_10(p_vy[10]),
    .p_vy_11(p_vy[11]),
    .p_vy_12(p_vy[12]),
    .p_vy_13(p_vy[13]),
    .p_vy_14(p_vy[14]),
    .p_vy_15(p_vy[15]),
    .p_vy_16(p_vy[16]),
    .p_vy_17(p_vy[17]),
    .p_vy_18(p_vy[18]),
    .p_vy_19(p_vy[19]),
    .p_vy_20(p_vy[20]),
    .p_vy_21(p_vy[21]),
    .p_vy_22(p_vy[22]),
    .p_vy_23(p_vy[23]),
    .p_vy_24(p_vy[24]),
    .p_vy_25(p_vy[25]),
    .p_vy_26(p_vy[26]),
    .p_vy_27(p_vy[27]),
    .p_vy_28(p_vy[28]),
    .p_vy_29(p_vy[29]),
    .p_vy_31(p_vy[31]),
    .p_vx_0(p_vx[0]),
    .p_vx_1(p_vx[1]),
    .p_vx_2(p_vx[2]),
    .p_vx_3(p_vx[3]),
    .p_vx_4(p_vx[4]),
    .p_vx_5(p_vx[5]),
    .p_vx_6(p_vx[6]),
    .p_vx_7(p_vx[7]),
    .p_vx_8(p_vx[8]),
    .p_vx_9(p_vx[9]),
    .p_vx_10(p_vx[10]),
    .p_vx_11(p_vx[11]),
    .p_vx_12(p_vx[12]),
    .p_vx_13(p_vx[13]),
    .p_vx_14(p_vx[14]),
    .p_vx_15(p_vx[15]),
    .p_vx_16(p_vx[16]),
    .p_vx_17(p_vx[17]),
    .p_vx_18(p_vx[18]),
    .p_vx_19(p_vx[19]),
    .p_vx_20(p_vx[20]),
    .p_vx_21(p_vx[21]),
    .p_vx_22(p_vx[22]),
    .p_vx_23(p_vx[23]),
    .p_vx_24(p_vx[24]),
    .p_vx_25(p_vx[25]),
    .p_vx_26(p_vx[26]),
    .p_vx_27(p_vx[27]),
    .p_vx_28(p_vx[28]),
    .p_vx_29(p_vx[29]),
    .p_vx_31(p_vx[31]),
    .have_epoch(have_epoch),
    .n845_7(n845_7),
    .position_reason_0(position_reason[0]),
    .position_reason_1(position_reason[1]),
    .position_reason_2(position_reason[2]),
    .position_reason_3(position_reason[3]),
    .position_reason_5(position_reason[5]),
    .position_reason_6(position_reason[6]),
    .position_reason_7(position_reason[7]),
    .position_reason_8(position_reason[8]),
    .position_reason_9(position_reason[9]),
    .position_raw_x_0(position_raw_x[0]),
    .position_raw_x_1(position_raw_x[1]),
    .position_raw_x_2(position_raw_x[2]),
    .position_raw_x_3(position_raw_x[3]),
    .position_raw_x_4(position_raw_x[4]),
    .position_raw_x_5(position_raw_x[5]),
    .position_raw_x_6(position_raw_x[6]),
    .position_raw_x_7(position_raw_x[7]),
    .position_raw_x_8(position_raw_x[8]),
    .position_raw_x_9(position_raw_x[9]),
    .position_raw_x_10(position_raw_x[10]),
    .position_raw_x_11(position_raw_x[11]),
    .position_raw_x_12(position_raw_x[12]),
    .position_raw_x_13(position_raw_x[13]),
    .position_raw_x_14(position_raw_x[14]),
    .position_raw_x_15(position_raw_x[15]),
    .position_raw_x_16(position_raw_x[16]),
    .position_raw_x_17(position_raw_x[17]),
    .position_raw_x_18(position_raw_x[18]),
    .position_raw_x_19(position_raw_x[19]),
    .position_raw_x_20(position_raw_x[20]),
    .position_raw_x_21(position_raw_x[21]),
    .position_raw_x_22(position_raw_x[22]),
    .position_raw_x_23(position_raw_x[23]),
    .position_raw_x_24(position_raw_x[24]),
    .position_raw_x_25(position_raw_x[25]),
    .position_raw_x_26(position_raw_x[26]),
    .position_raw_x_27(position_raw_x[27]),
    .position_raw_x_31(position_raw_x[31]),
    .position_raw_y_0(position_raw_y[0]),
    .position_raw_y_1(position_raw_y[1]),
    .position_raw_y_2(position_raw_y[2]),
    .position_raw_y_3(position_raw_y[3]),
    .position_raw_y_4(position_raw_y[4]),
    .position_raw_y_5(position_raw_y[5]),
    .position_raw_y_6(position_raw_y[6]),
    .position_raw_y_7(position_raw_y[7]),
    .position_raw_y_8(position_raw_y[8]),
    .position_raw_y_9(position_raw_y[9]),
    .position_raw_y_10(position_raw_y[10]),
    .position_raw_y_11(position_raw_y[11]),
    .position_raw_y_12(position_raw_y[12]),
    .position_raw_y_13(position_raw_y[13]),
    .position_raw_y_14(position_raw_y[14]),
    .position_raw_y_15(position_raw_y[15]),
    .position_raw_y_16(position_raw_y[16]),
    .position_raw_y_17(position_raw_y[17]),
    .position_raw_y_18(position_raw_y[18]),
    .position_raw_y_19(position_raw_y[19]),
    .position_raw_y_20(position_raw_y[20]),
    .position_raw_y_21(position_raw_y[21]),
    .position_raw_y_22(position_raw_y[22]),
    .position_raw_y_23(position_raw_y[23]),
    .position_raw_y_24(position_raw_y[24]),
    .position_raw_y_25(position_raw_y[25]),
    .position_raw_y_26(position_raw_y[26]),
    .position_raw_y_27(position_raw_y[27]),
    .position_raw_y_28(position_raw_y[28]),
    .position_raw_y_31(position_raw_y[31])
);
  mtf_xyz_hold_control controller_proof (
    .clk50_d(clk50_d),
    .n13_16(n13_16),
    .c_height_update(c_height_update),
    .c_position_update(c_position_update),
    .c_acc_valid(c_acc_valid),
    .c_height_valid(c_height_valid),
    .controller_z_requested(controller_z_requested),
    .c_sample_update(c_sample_update),
    .n4168_3(n4168_3),
    .c_enabled(c_enabled),
    .n172_3(n172_3),
    .flight_state_flags_0_2(flight_state_flags_0_2),
    .n4159_3(n4159_3),
    .previous_pose_valid(previous_pose_valid),
    .pose_valid(pose_valid),
    .n13_13(n13_13),
    .n13_14(n13_14),
    .m_done_3_3(m_done_3_3),
    .c_position_valid(c_position_valid),
    .c_collective_0(c_collective[0]),
    .c_collective_1(c_collective[1]),
    .c_collective_2(c_collective[2]),
    .c_collective_3(c_collective[3]),
    .c_collective_4(c_collective[4]),
    .c_collective_5(c_collective[5]),
    .c_collective_6(c_collective[6]),
    .c_collective_7(c_collective[7]),
    .c_collective_8(c_collective[8]),
    .c_collective_9(c_collective[9]),
    .c_collective_10(c_collective[10]),
    .c_collective_11(c_collective[11]),
    .c_collective_15(c_collective[15]),
    .c_ch3(c_ch3[11:0]),
    .c_height(c_height[31:0]),
    .c_vz(c_vz[31:0]),
    .c_az_0(c_az[0]),
    .c_az_1(c_az[1]),
    .c_az_2(c_az[2]),
    .c_az_3(c_az[3]),
    .c_az_4(c_az[4]),
    .c_az_5(c_az[5]),
    .c_az_6(c_az[6]),
    .c_az_7(c_az[7]),
    .c_az_8(c_az[8]),
    .c_az_9(c_az[9]),
    .c_az_10(c_az[10]),
    .c_az_11(c_az[11]),
    .c_az_12(c_az[12]),
    .c_az_13(c_az[13]),
    .c_az_14(c_az[14]),
    .c_az_31(c_az[31]),
    .c_vx_0(c_vx[0]),
    .c_vx_1(c_vx[1]),
    .c_vx_2(c_vx[2]),
    .c_vx_3(c_vx[3]),
    .c_vx_4(c_vx[4]),
    .c_vx_5(c_vx[5]),
    .c_vx_6(c_vx[6]),
    .c_vx_7(c_vx[7]),
    .c_vx_8(c_vx[8]),
    .c_vx_9(c_vx[9]),
    .c_vx_10(c_vx[10]),
    .c_vx_11(c_vx[11]),
    .c_vx_12(c_vx[12]),
    .c_vx_13(c_vx[13]),
    .c_vx_14(c_vx[14]),
    .c_vx_15(c_vx[15]),
    .c_vx_16(c_vx[16]),
    .c_vx_17(c_vx[17]),
    .c_vx_18(c_vx[18]),
    .c_vx_19(c_vx[19]),
    .c_vx_20(c_vx[20]),
    .c_vx_21(c_vx[21]),
    .c_vx_22(c_vx[22]),
    .c_vx_23(c_vx[23]),
    .c_vx_24(c_vx[24]),
    .c_vx_25(c_vx[25]),
    .c_vx_26(c_vx[26]),
    .c_vx_27(c_vx[27]),
    .c_vx_28(c_vx[28]),
    .c_vx_29(c_vx[29]),
    .c_vx_31(c_vx[31]),
    .c_vy_0(c_vy[0]),
    .c_vy_1(c_vy[1]),
    .c_vy_2(c_vy[2]),
    .c_vy_3(c_vy[3]),
    .c_vy_4(c_vy[4]),
    .c_vy_5(c_vy[5]),
    .c_vy_6(c_vy[6]),
    .c_vy_7(c_vy[7]),
    .c_vy_8(c_vy[8]),
    .c_vy_9(c_vy[9]),
    .c_vy_10(c_vy[10]),
    .c_vy_11(c_vy[11]),
    .c_vy_12(c_vy[12]),
    .c_vy_13(c_vy[13]),
    .c_vy_14(c_vy[14]),
    .c_vy_15(c_vy[15]),
    .c_vy_16(c_vy[16]),
    .c_vy_17(c_vy[17]),
    .c_vy_18(c_vy[18]),
    .c_vy_19(c_vy[19]),
    .c_vy_20(c_vy[20]),
    .c_vy_21(c_vy[21]),
    .c_vy_22(c_vy[22]),
    .c_vy_23(c_vy[23]),
    .c_vy_24(c_vy[24]),
    .c_vy_25(c_vy[25]),
    .c_vy_26(c_vy[26]),
    .c_vy_27(c_vy[27]),
    .c_vy_28(c_vy[28]),
    .c_vy_29(c_vy[29]),
    .c_vy_31(c_vy[31]),
    .c_ax(c_ax[31:0]),
    .c_ay(c_ay[31:0]),
    .c_yaw(c_yaw[15:0]),
    .m_done(m_done[3]),
    .m_result(m_result[63:0]),
    .d_result(d_result[47:0]),
    .flight_state_flags(flight_state_flags[0]),
    .c_position_age(c_position_age[31:6]),
    .c_ch7(c_ch7[11:0]),
    .c_channel_count(c_channel_count[3:0]),
    .response_owner(response_owner_0[1:0]),
    .done_q(done_q_0[3]),
    .error_q(error_q[3]),
    .c_sample_dt(c_sample_dt[31:0]),
    .c_ch2(c_ch2[11:0]),
    .c_ch1(c_ch1[11:0]),
    .tracking(tracking),
    .command_seen(command_seen),
    .height_command_seen(height_command_seen),
    .blocked(blocked),
    .cancel_now_4(cancel_now_4),
    .n22634_5(n22634_5),
    .n22642_6(n22642_6),
    .controller_z_ready(controller_z_ready),
    .xy_cancel_now_17(xy_cancel_now_17),
    .n164_9(n164_9),
    .pilot_norm_update(pilot_norm_update),
    .seen(seen),
    .xy_stick_fault(xy_stick_fault),
    .m_request(m_request_2[3]),
    .d_request(d_request_1[3]),
    .nav_xy_payload_roll_0(nav_xy_payload_roll_0),
    .nav_xy_payload_roll_1(nav_xy_payload_roll_1),
    .nav_xy_payload_roll_2(nav_xy_payload_roll_2),
    .nav_xy_payload_roll_3(nav_xy_payload_roll_3),
    .nav_xy_payload_roll_4(nav_xy_payload_roll_4),
    .nav_xy_payload_roll_5(nav_xy_payload_roll_5),
    .nav_xy_payload_roll_6(nav_xy_payload_roll_6),
    .nav_xy_payload_roll_7(nav_xy_payload_roll_7),
    .nav_xy_payload_roll_8(nav_xy_payload_roll_8),
    .nav_xy_payload_roll_9(nav_xy_payload_roll_9),
    .nav_xy_payload_roll_10(nav_xy_payload_roll_10),
    .nav_xy_payload_roll_11(nav_xy_payload_roll_11),
    .nav_xy_payload_roll_15(nav_xy_payload_roll_15),
    .nav_xy_payload_pitch_0(nav_xy_payload_pitch_0),
    .nav_xy_payload_pitch_1(nav_xy_payload_pitch_1),
    .nav_xy_payload_pitch_2(nav_xy_payload_pitch_2),
    .nav_xy_payload_pitch_3(nav_xy_payload_pitch_3),
    .nav_xy_payload_pitch_4(nav_xy_payload_pitch_4),
    .nav_xy_payload_pitch_5(nav_xy_payload_pitch_5),
    .nav_xy_payload_pitch_6(nav_xy_payload_pitch_6),
    .nav_xy_payload_pitch_7(nav_xy_payload_pitch_7),
    .nav_xy_payload_pitch_8(nav_xy_payload_pitch_8),
    .nav_xy_payload_pitch_9(nav_xy_payload_pitch_9),
    .nav_xy_payload_pitch_10(nav_xy_payload_pitch_10),
    .nav_xy_payload_pitch_11(nav_xy_payload_pitch_11),
    .nav_xy_payload_pitch_15(nav_xy_payload_pitch_15),
    .controller_delta_0(controller_delta[0]),
    .controller_delta_1(controller_delta[1]),
    .controller_delta_2(controller_delta[2]),
    .controller_delta_3(controller_delta[3]),
    .controller_delta_4(controller_delta[4]),
    .controller_delta_5(controller_delta[5]),
    .controller_delta_6(controller_delta[6]),
    .controller_delta_7(controller_delta[7]),
    .controller_delta_8(controller_delta[8]),
    .controller_delta_9(controller_delta[9]),
    .controller_delta_15(controller_delta[15]),
    .controller_collective_0(controller_collective[0]),
    .controller_collective_1(controller_collective[1]),
    .controller_collective_2(controller_collective[2]),
    .controller_collective_3(controller_collective[3]),
    .controller_collective_4(controller_collective[4]),
    .controller_collective_5(controller_collective[5]),
    .controller_collective_6(controller_collective[6]),
    .controller_collective_7(controller_collective[7]),
    .controller_collective_8(controller_collective[8]),
    .controller_collective_9(controller_collective[9]),
    .controller_collective_10(controller_collective[10]),
    .controller_collective_11(controller_collective[11]),
    .controller_collective_15(controller_collective[15]),
    .auto_phase(auto_phase[1:0]),
    .m_a(m_a_2[241:192]),
    .m_b_192(m_b_2[192]),
    .m_b_193(m_b_2[193]),
    .m_b_194(m_b_2[194]),
    .m_b_195(m_b_2[195]),
    .m_b_196(m_b_2[196]),
    .m_b_197(m_b_2[197]),
    .m_b_198(m_b_2[198]),
    .m_b_199(m_b_2[199]),
    .m_b_200(m_b_2[200]),
    .m_b_201(m_b_2[201]),
    .m_b_202(m_b_2[202]),
    .m_b_203(m_b_2[203]),
    .m_b_204(m_b_2[204]),
    .m_b_205(m_b_2[205]),
    .m_b_206(m_b_2[206]),
    .m_b_207(m_b_2[207]),
    .m_b_208(m_b_2[208]),
    .m_b_209(m_b_2[209]),
    .m_b_210(m_b_2[210]),
    .m_b_211(m_b_2[211]),
    .m_b_212(m_b_2[212]),
    .m_b_213(m_b_2[213]),
    .m_b_214(m_b_2[214]),
    .m_b_215(m_b_2[215]),
    .m_b_216(m_b_2[216]),
    .m_b_217(m_b_2[217]),
    .m_b_218(m_b_2[218]),
    .m_b_225(m_b_2[225]),
    .d_a(d_a_1[255:192]),
    .d_b_192(d_b_1[192]),
    .d_b_193(d_b_1[193]),
    .d_b_194(d_b_1[194]),
    .d_b_195(d_b_1[195]),
    .d_b_196(d_b_1[196]),
    .d_b_197(d_b_1[197]),
    .d_b_198(d_b_1[198]),
    .d_b_199(d_b_1[199]),
    .d_b_200(d_b_1[200]),
    .d_b_201(d_b_1[201]),
    .d_b_202(d_b_1[202]),
    .d_b_203(d_b_1[203]),
    .d_b_204(d_b_1[204]),
    .d_b_205(d_b_1[205]),
    .d_b_206(d_b_1[206]),
    .d_b_207(d_b_1[207]),
    .d_b_208(d_b_1[208]),
    .d_b_209(d_b_1[209]),
    .d_b_210(d_b_1[210]),
    .d_b_211(d_b_1[211]),
    .d_b_212(d_b_1[212]),
    .d_b_213(d_b_1[213]),
    .d_b_214(d_b_1[214]),
    .d_b_215(d_b_1[215]),
    .d_b_216(d_b_1[216]),
    .d_b_217(d_b_1[217]),
    .d_b_223(d_b_1[223]),
    .controller_reason_0(controller_reason[0]),
    .controller_reason_1(controller_reason[1]),
    .controller_reason_2(controller_reason[2]),
    .controller_reason_6(controller_reason[6]),
    .controller_reason_7(controller_reason[7]),
    .controller_reason_9(controller_reason[9]),
    .controller_reason_10(controller_reason[10]),
    .controller_z_reason_0(controller_z_reason[0]),
    .controller_z_reason_1(controller_z_reason[1]),
    .controller_z_reason_3(controller_z_reason[3]),
    .controller_z_reason_6(controller_z_reason[6]),
    .controller_z_reason_7(controller_z_reason[7]),
    .controller_z_reason_9(controller_z_reason[9]),
    .controller_z_reason_10(controller_z_reason[10]),
    .controller_target_height_0(controller_target_height[0]),
    .controller_target_height_1(controller_target_height[1]),
    .controller_target_height_2(controller_target_height[2]),
    .controller_target_height_3(controller_target_height[3]),
    .controller_target_height_4(controller_target_height[4]),
    .controller_target_height_5(controller_target_height[5]),
    .controller_target_height_6(controller_target_height[6]),
    .controller_target_height_7(controller_target_height[7]),
    .controller_target_height_8(controller_target_height[8]),
    .controller_target_height_9(controller_target_height[9]),
    .controller_target_height_10(controller_target_height[10]),
    .controller_target_height_11(controller_target_height[11]),
    .controller_target_height_12(controller_target_height[12]),
    .controller_target_height_13(controller_target_height[13]),
    .controller_target_height_14(controller_target_height[14]),
    .controller_target_height_31(controller_target_height[31]),
    .flight_state_flags_50(flight_state_flags_51[3]),
    .d_cancel(d_cancel_1[3]),
    .pilot_norm_x(pilot_norm_x[17:0]),
    .pilot_norm_y(pilot_norm_y[17:0]),
    .pilot_norm_dt_us(pilot_norm_dt_us[15:0])
);
  VCC VCC_cZ (
    .V(VCC)
);
  GND GND_cZ (
    .G(GND)
);
endmodule