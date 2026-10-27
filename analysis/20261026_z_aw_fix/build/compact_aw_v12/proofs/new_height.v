`timescale 1ns/1ps
// ANO Tech Ano_MotionCal.c WCZ_Data_Calc + Ano_Filter.c numerical port.
// WCZ11ms: acceleration bias Ki=.1, speed correction Kp=.6 (limit100cm/s),
// height correction Kp=.3. Reference derivatives update every5 WCZ cycles.
// TFmini tilt-corrected range replaces the source barometer/TOF selection.
// Source integer cm observations/derivatives are retained; public mm units.
// An origin offset exposes real measured absolute distance while internally
// preserving source zero-relative-height reset. No source coefficients changed.
// Default calibration mask0 permits displayed estimates, NEVER valid control.
module height_new #(
 parameter integer CLK_HZ=50000000,AGE_LIMIT=5000000,
 parameter [7:0] CAL_MASK=0,
 parameter integer RANGE_AGE_PRECHECKED=0,PRECHECKED_AZ_RANGE=0
)(
 input wire clk,rst_n,origin_reset,
 input wire range_valid,acc_valid,acc_update,
 input wire az_range_ok,
 input wire [31:0] acc_dt_us,
 input wire [31:0] range_age_ticks,
 input wire signed [31:0] ref_height_mm,az_up_mmps2,
 output wire math_mul_start,math_mul_cancel,
 output wire signed [63:0] math_mul_a,math_mul_b,
 input wire math_mul_busy,math_mul_done,
 input wire signed [63:0] math_mul_result,
 output wire math_div_start,math_div_cancel,
 output wire signed [63:0] math_div_numerator,
 output wire [31:0] math_div_denominator,
 input wire math_div_busy,math_div_done,math_div_error,
 input wire signed [63:0] math_div_result,
 output wire valid,estimate_ready,
 output reg qualified_ready=0,output reg qualified_valid=0,
 output reg update,
 output reg signed [31:0] fused_height_mm,vz_mmps,sample_az_mmps2,
 output reg signed [31:0] vz_q16,output wire vz_q16_valid,
 output reg [15:0] reason,
 output wire estimate_ready_state_numeric_tail,
 output wire vz_q16_range_raw
);
 localparam PERIOD_TICKS=CLK_HZ*11/1000;
 localparam integer TIMER_STORAGE_BITS=(CLK_HZ==50000000) ? 20:32;
 reg [TIMER_STORAGE_BITS-1:0] timer_store=0;
 wire [31:0] timer={{(32-TIMER_STORAGE_BITS){1'b0}},timer_store};
 reg [31:0] publication_age=32'hffffffff;
 // Exact predicate of the same published age, including the expiry clock.
 reg publication_fresh=(32'hffffffff < AGE_LIMIT);
 reg seeded=0,seen=0,fault=0;
 reg [2:0] cycle5=0;
 reg acc_pending=0,height_pending=0;
 reg pending_height_epoch_ok=0,height_transaction_epoch_ok=0,seed_epoch_ok=0;
 reg [16:0] pending_acc_dt_store=0;
 wire [31:0] pending_acc_dt={15'd0,pending_acc_dt_store};
 reg [31:0] held_acc_dt=0;
 reg signed [31:0] pending_acc=0,pending_height=0,pending_rawaz=0;
 reg signed [15:0] held_rawaz_store=0;
 wire signed [31:0] held_rawaz={{16{held_rawaz_store[15]}},held_rawaz_store};
 reg signed [31:0] filtered_acc_store=0;
 wire signed [63:0] filtered_acc={{32{filtered_acc_store[31]}},filtered_acc_store};
 reg signed [31:0] filter_input_store=0;
 wire signed [63:0] filter_input={{32{filter_input_store[31]}},filter_input_store};
 reg [6:0] filter_steps=0;reg [9:0] filter_fraction=0;
 reg [12:0] origin_mm_store=0;
 wire signed [31:0] origin_mm={19'd0,origin_mm_store};
 reg signed [13:0] held_relative_mm_store=0;
 wire signed [31:0] held_relative_mm={{18{held_relative_mm_store[13]}},held_relative_mm_store};
 reg signed [15:0] held_acc_mm_store=0;
 wire signed [31:0] held_acc_mm={{16{held_acc_mm_store[15]}},held_acc_mm_store};
 reg signed [13:0] ref_height_old_store=0;
 wire signed [31:0] ref_height_old={{18{ref_height_old_store[13]}},ref_height_old_store};
 reg signed [17:0] ref_speed_old_store=0;
 wire signed [31:0] ref_speed_old={{14{ref_speed_old_store[17]}},ref_speed_old_store};
 reg signed [17:0] ref_speed_store=0;
 wire signed [31:0] ref_speed={{14{ref_speed_store[17]}},ref_speed_store};
 reg signed [22:0] ref_acc_store=0;
 wire signed [31:0] ref_acc={{9{ref_acc_store[22]}},ref_acc_store};
 reg signed [63:0] acc_i=0,acc_out=0,vq=0,hq=0,vel_e=0,height_e=0;
 reg [7:0] state=0,return_state=0;
 reg mul_start=0,div_start=0;
 reg signed [63:0] ma=0,mb=0,num=0,value=0;
 reg [30:0] trunc_magnitude_store=0;
 wire signed [63:0] trunc_magnitude={33'd0,trunc_magnitude_store};
 reg trunc_negative=0;reg signed [31:0] publish_h_integer=0,publish_v_integer=0;
 reg signed [31:0] publish_v_q16=0;
 reg publish_v_q16_range=0,v_q16_range=0;
 assign vz_q16_range_raw=v_q16_range;
 // Check the full signed64 state BEFORE narrowing. An invalid fine bus
 // must never masquerade as an in-range control velocity after wrapping.
 assign vz_q16_valid=estimate_ready && v_q16_range;
 reg [31:0] den=1,pending_den=1;
 wire md,mbusy,dd,dbusy,derr;wire signed [63:0] product,quotient;
 wire az_numeric_ok=PRECHECKED_AZ_RANGE ?az_range_ok:(az_up_mmps2>=-30000 && az_up_mmps2<=30000);
 wire sources_ok=range_valid && acc_valid && ((RANGE_AGE_PRECHECKED && AGE_LIMIT==5000000) || range_age_ticks<AGE_LIMIT) &&
     ref_height_mm>=0 && ref_height_mm<=5000 && az_numeric_ok;
 reg cleanup=1;
 always @(posedge clk) if(!rst_n) cleanup<=1;else cleanup<=origin_reset || !sources_ok || fault;
 assign estimate_ready=sources_ok && !origin_reset && !cleanup && seeded && seen && publication_fresh && !fault;
 // Caller supplies range_valid, acc_valid and !origin_reset at final control gate.
 (* syn_keep = 1 *) wire estimate_ready_state_numeric_tail_kept=
  ((RANGE_AGE_PRECHECKED && AGE_LIMIT==5000000) || range_age_ticks<AGE_LIMIT) &&
  ref_height_mm>=0 && ref_height_mm<=5000 &&
  az_numeric_ok && !cleanup && seeded && seen &&
  publication_fresh && !fault;
 assign estimate_ready_state_numeric_tail=estimate_ready_state_numeric_tail_kept;
 assign valid=CAL_MASK[3] && CAL_MASK[4] && estimate_ready;
 always @(posedge clk)begin
  if(!rst_n || origin_reset)begin qualified_ready<=0;qualified_valid<=0;end
  else begin qualified_ready<=estimate_ready;qualified_valid<=valid;end
 end
 // A source invalidation clears the transaction epoch with normal cleanup.
 // COMMIT independently checks current source health and the captured epoch.
 wire new_acc_fault=acc_update && (acc_pending || acc_dt_us==0 || acc_dt_us>100000);
 wire new_height_fault=seeded && timer==PERIOD_TICKS-1 && height_pending;
 assign math_mul_start=mul_start;
 assign math_mul_cancel=cleanup;
 assign math_mul_a=ma;assign math_mul_b=mb;
 assign mbusy=math_mul_busy;assign md=math_mul_done;assign product=math_mul_result;
 assign math_div_start=div_start;
 assign math_div_cancel=cleanup;
 assign math_div_numerator=num;assign math_div_denominator=den;
 assign dbusy=math_div_busy;assign dd=math_div_done;assign derr=math_div_error;assign quotient=math_div_result;
 function signed [63:0] clip;
 input signed [63:0] a,lo,hi;begin clip=a<lo ? lo:a>hi ? hi:a;end endfunction
 // Source .03/1ms fractional-time pole coefficients, Q24.
 // A clocked ROM read maps the 1024x24 table into BSRAM instead of a
 // 1000-way combinational selection network. All source coefficients
 // retain the previous exact integer values; unused addresses are zero.
 (* rom_style="block", syn_romstyle="block_rom" *) reg [23:0] fraction_rom [0:1023];
 reg [23:0] fraction_q=0;
 initial begin
  fraction_rom[0]=24'd0;
  fraction_rom[1]=24'd511;
  fraction_rom[2]=24'd1022;
  fraction_rom[3]=24'd1533;
  fraction_rom[4]=24'd2044;
  fraction_rom[5]=24'd2555;
  fraction_rom[6]=24'd3066;
  fraction_rom[7]=24'd3577;
  fraction_rom[8]=24'd4088;
  fraction_rom[9]=24'd4599;
  fraction_rom[10]=24'd5109;
  fraction_rom[11]=24'd5620;
  fraction_rom[12]=24'd6131;
  fraction_rom[13]=24'd6642;
  fraction_rom[14]=24'd7153;
  fraction_rom[15]=24'd7664;
  fraction_rom[16]=24'd8174;
  fraction_rom[17]=24'd8685;
  fraction_rom[18]=24'd9196;
  fraction_rom[19]=24'd9707;
  fraction_rom[20]=24'd10217;
  fraction_rom[21]=24'd10728;
  fraction_rom[22]=24'd11239;
  fraction_rom[23]=24'd11749;
  fraction_rom[24]=24'd12260;
  fraction_rom[25]=24'd12771;
  fraction_rom[26]=24'd13281;
  fraction_rom[27]=24'd13792;
  fraction_rom[28]=24'd14302;
  fraction_rom[29]=24'd14813;
  fraction_rom[30]=24'd15324;
  fraction_rom[31]=24'd15834;
  fraction_rom[32]=24'd16345;
  fraction_rom[33]=24'd16855;
  fraction_rom[34]=24'd17366;
  fraction_rom[35]=24'd17876;
  fraction_rom[36]=24'd18387;
  fraction_rom[37]=24'd18897;
  fraction_rom[38]=24'd19408;
  fraction_rom[39]=24'd19918;
  fraction_rom[40]=24'd20428;
  fraction_rom[41]=24'd20939;
  fraction_rom[42]=24'd21449;
  fraction_rom[43]=24'd21960;
  fraction_rom[44]=24'd22470;
  fraction_rom[45]=24'd22980;
  fraction_rom[46]=24'd23490;
  fraction_rom[47]=24'd24001;
  fraction_rom[48]=24'd24511;
  fraction_rom[49]=24'd25021;
  fraction_rom[50]=24'd25532;
  fraction_rom[51]=24'd26042;
  fraction_rom[52]=24'd26552;
  fraction_rom[53]=24'd27062;
  fraction_rom[54]=24'd27572;
  fraction_rom[55]=24'd28083;
  fraction_rom[56]=24'd28593;
  fraction_rom[57]=24'd29103;
  fraction_rom[58]=24'd29613;
  fraction_rom[59]=24'd30123;
  fraction_rom[60]=24'd30633;
  fraction_rom[61]=24'd31143;
  fraction_rom[62]=24'd31653;
  fraction_rom[63]=24'd32163;
  fraction_rom[64]=24'd32673;
  fraction_rom[65]=24'd33183;
  fraction_rom[66]=24'd33693;
  fraction_rom[67]=24'd34203;
  fraction_rom[68]=24'd34713;
  fraction_rom[69]=24'd35223;
  fraction_rom[70]=24'd35733;
  fraction_rom[71]=24'd36243;
  fraction_rom[72]=24'd36753;
  fraction_rom[73]=24'd37263;
  fraction_rom[74]=24'd37773;
  fraction_rom[75]=24'd38283;
  fraction_rom[76]=24'd38793;
  fraction_rom[77]=24'd39302;
  fraction_rom[78]=24'd39812;
  fraction_rom[79]=24'd40322;
  fraction_rom[80]=24'd40832;
  fraction_rom[81]=24'd41342;
  fraction_rom[82]=24'd41851;
  fraction_rom[83]=24'd42361;
  fraction_rom[84]=24'd42871;
  fraction_rom[85]=24'd43381;
  fraction_rom[86]=24'd43890;
  fraction_rom[87]=24'd44400;
  fraction_rom[88]=24'd44910;
  fraction_rom[89]=24'd45419;
  fraction_rom[90]=24'd45929;
  fraction_rom[91]=24'd46438;
  fraction_rom[92]=24'd46948;
  fraction_rom[93]=24'd47458;
  fraction_rom[94]=24'd47967;
  fraction_rom[95]=24'd48477;
  fraction_rom[96]=24'd48986;
  fraction_rom[97]=24'd49496;
  fraction_rom[98]=24'd50005;
  fraction_rom[99]=24'd50515;
  fraction_rom[100]=24'd51024;
  fraction_rom[101]=24'd51534;
  fraction_rom[102]=24'd52043;
  fraction_rom[103]=24'd52553;
  fraction_rom[104]=24'd53062;
  fraction_rom[105]=24'd53571;
  fraction_rom[106]=24'd54081;
  fraction_rom[107]=24'd54590;
  fraction_rom[108]=24'd55100;
  fraction_rom[109]=24'd55609;
  fraction_rom[110]=24'd56118;
  fraction_rom[111]=24'd56628;
  fraction_rom[112]=24'd57137;
  fraction_rom[113]=24'd57646;
  fraction_rom[114]=24'd58155;
  fraction_rom[115]=24'd58665;
  fraction_rom[116]=24'd59174;
  fraction_rom[117]=24'd59683;
  fraction_rom[118]=24'd60192;
  fraction_rom[119]=24'd60701;
  fraction_rom[120]=24'd61211;
  fraction_rom[121]=24'd61720;
  fraction_rom[122]=24'd62229;
  fraction_rom[123]=24'd62738;
  fraction_rom[124]=24'd63247;
  fraction_rom[125]=24'd63756;
  fraction_rom[126]=24'd64265;
  fraction_rom[127]=24'd64774;
  fraction_rom[128]=24'd65283;
  fraction_rom[129]=24'd65792;
  fraction_rom[130]=24'd66301;
  fraction_rom[131]=24'd66810;
  fraction_rom[132]=24'd67319;
  fraction_rom[133]=24'd67828;
  fraction_rom[134]=24'd68337;
  fraction_rom[135]=24'd68846;
  fraction_rom[136]=24'd69355;
  fraction_rom[137]=24'd69864;
  fraction_rom[138]=24'd70373;
  fraction_rom[139]=24'd70882;
  fraction_rom[140]=24'd71391;
  fraction_rom[141]=24'd71899;
  fraction_rom[142]=24'd72408;
  fraction_rom[143]=24'd72917;
  fraction_rom[144]=24'd73426;
  fraction_rom[145]=24'd73935;
  fraction_rom[146]=24'd74443;
  fraction_rom[147]=24'd74952;
  fraction_rom[148]=24'd75461;
  fraction_rom[149]=24'd75970;
  fraction_rom[150]=24'd76478;
  fraction_rom[151]=24'd76987;
  fraction_rom[152]=24'd77496;
  fraction_rom[153]=24'd78004;
  fraction_rom[154]=24'd78513;
  fraction_rom[155]=24'd79022;
  fraction_rom[156]=24'd79530;
  fraction_rom[157]=24'd80039;
  fraction_rom[158]=24'd80547;
  fraction_rom[159]=24'd81056;
  fraction_rom[160]=24'd81564;
  fraction_rom[161]=24'd82073;
  fraction_rom[162]=24'd82581;
  fraction_rom[163]=24'd83090;
  fraction_rom[164]=24'd83598;
  fraction_rom[165]=24'd84107;
  fraction_rom[166]=24'd84615;
  fraction_rom[167]=24'd85124;
  fraction_rom[168]=24'd85632;
  fraction_rom[169]=24'd86141;
  fraction_rom[170]=24'd86649;
  fraction_rom[171]=24'd87157;
  fraction_rom[172]=24'd87666;
  fraction_rom[173]=24'd88174;
  fraction_rom[174]=24'd88682;
  fraction_rom[175]=24'd89191;
  fraction_rom[176]=24'd89699;
  fraction_rom[177]=24'd90207;
  fraction_rom[178]=24'd90716;
  fraction_rom[179]=24'd91224;
  fraction_rom[180]=24'd91732;
  fraction_rom[181]=24'd92240;
  fraction_rom[182]=24'd92748;
  fraction_rom[183]=24'd93257;
  fraction_rom[184]=24'd93765;
  fraction_rom[185]=24'd94273;
  fraction_rom[186]=24'd94781;
  fraction_rom[187]=24'd95289;
  fraction_rom[188]=24'd95797;
  fraction_rom[189]=24'd96305;
  fraction_rom[190]=24'd96814;
  fraction_rom[191]=24'd97322;
  fraction_rom[192]=24'd97830;
  fraction_rom[193]=24'd98338;
  fraction_rom[194]=24'd98846;
  fraction_rom[195]=24'd99354;
  fraction_rom[196]=24'd99862;
  fraction_rom[197]=24'd100370;
  fraction_rom[198]=24'd100878;
  fraction_rom[199]=24'd101386;
  fraction_rom[200]=24'd101893;
  fraction_rom[201]=24'd102401;
  fraction_rom[202]=24'd102909;
  fraction_rom[203]=24'd103417;
  fraction_rom[204]=24'd103925;
  fraction_rom[205]=24'd104433;
  fraction_rom[206]=24'd104941;
  fraction_rom[207]=24'd105449;
  fraction_rom[208]=24'd105956;
  fraction_rom[209]=24'd106464;
  fraction_rom[210]=24'd106972;
  fraction_rom[211]=24'd107480;
  fraction_rom[212]=24'd107987;
  fraction_rom[213]=24'd108495;
  fraction_rom[214]=24'd109003;
  fraction_rom[215]=24'd109510;
  fraction_rom[216]=24'd110018;
  fraction_rom[217]=24'd110526;
  fraction_rom[218]=24'd111033;
  fraction_rom[219]=24'd111541;
  fraction_rom[220]=24'd112049;
  fraction_rom[221]=24'd112556;
  fraction_rom[222]=24'd113064;
  fraction_rom[223]=24'd113571;
  fraction_rom[224]=24'd114079;
  fraction_rom[225]=24'd114587;
  fraction_rom[226]=24'd115094;
  fraction_rom[227]=24'd115602;
  fraction_rom[228]=24'd116109;
  fraction_rom[229]=24'd116617;
  fraction_rom[230]=24'd117124;
  fraction_rom[231]=24'd117631;
  fraction_rom[232]=24'd118139;
  fraction_rom[233]=24'd118646;
  fraction_rom[234]=24'd119154;
  fraction_rom[235]=24'd119661;
  fraction_rom[236]=24'd120168;
  fraction_rom[237]=24'd120676;
  fraction_rom[238]=24'd121183;
  fraction_rom[239]=24'd121690;
  fraction_rom[240]=24'd122198;
  fraction_rom[241]=24'd122705;
  fraction_rom[242]=24'd123212;
  fraction_rom[243]=24'd123720;
  fraction_rom[244]=24'd124227;
  fraction_rom[245]=24'd124734;
  fraction_rom[246]=24'd125241;
  fraction_rom[247]=24'd125748;
  fraction_rom[248]=24'd126256;
  fraction_rom[249]=24'd126763;
  fraction_rom[250]=24'd127270;
  fraction_rom[251]=24'd127777;
  fraction_rom[252]=24'd128284;
  fraction_rom[253]=24'd128791;
  fraction_rom[254]=24'd129298;
  fraction_rom[255]=24'd129806;
  fraction_rom[256]=24'd130313;
  fraction_rom[257]=24'd130820;
  fraction_rom[258]=24'd131327;
  fraction_rom[259]=24'd131834;
  fraction_rom[260]=24'd132341;
  fraction_rom[261]=24'd132848;
  fraction_rom[262]=24'd133355;
  fraction_rom[263]=24'd133862;
  fraction_rom[264]=24'd134368;
  fraction_rom[265]=24'd134875;
  fraction_rom[266]=24'd135382;
  fraction_rom[267]=24'd135889;
  fraction_rom[268]=24'd136396;
  fraction_rom[269]=24'd136903;
  fraction_rom[270]=24'd137410;
  fraction_rom[271]=24'd137917;
  fraction_rom[272]=24'd138423;
  fraction_rom[273]=24'd138930;
  fraction_rom[274]=24'd139437;
  fraction_rom[275]=24'd139944;
  fraction_rom[276]=24'd140451;
  fraction_rom[277]=24'd140957;
  fraction_rom[278]=24'd141464;
  fraction_rom[279]=24'd141971;
  fraction_rom[280]=24'd142477;
  fraction_rom[281]=24'd142984;
  fraction_rom[282]=24'd143491;
  fraction_rom[283]=24'd143997;
  fraction_rom[284]=24'd144504;
  fraction_rom[285]=24'd145011;
  fraction_rom[286]=24'd145517;
  fraction_rom[287]=24'd146024;
  fraction_rom[288]=24'd146530;
  fraction_rom[289]=24'd147037;
  fraction_rom[290]=24'd147543;
  fraction_rom[291]=24'd148050;
  fraction_rom[292]=24'd148556;
  fraction_rom[293]=24'd149063;
  fraction_rom[294]=24'd149569;
  fraction_rom[295]=24'd150076;
  fraction_rom[296]=24'd150582;
  fraction_rom[297]=24'd151089;
  fraction_rom[298]=24'd151595;
  fraction_rom[299]=24'd152102;
  fraction_rom[300]=24'd152608;
  fraction_rom[301]=24'd153114;
  fraction_rom[302]=24'd153621;
  fraction_rom[303]=24'd154127;
  fraction_rom[304]=24'd154633;
  fraction_rom[305]=24'd155140;
  fraction_rom[306]=24'd155646;
  fraction_rom[307]=24'd156152;
  fraction_rom[308]=24'd156658;
  fraction_rom[309]=24'd157165;
  fraction_rom[310]=24'd157671;
  fraction_rom[311]=24'd158177;
  fraction_rom[312]=24'd158683;
  fraction_rom[313]=24'd159189;
  fraction_rom[314]=24'd159696;
  fraction_rom[315]=24'd160202;
  fraction_rom[316]=24'd160708;
  fraction_rom[317]=24'd161214;
  fraction_rom[318]=24'd161720;
  fraction_rom[319]=24'd162226;
  fraction_rom[320]=24'd162732;
  fraction_rom[321]=24'd163238;
  fraction_rom[322]=24'd163744;
  fraction_rom[323]=24'd164250;
  fraction_rom[324]=24'd164756;
  fraction_rom[325]=24'd165262;
  fraction_rom[326]=24'd165768;
  fraction_rom[327]=24'd166274;
  fraction_rom[328]=24'd166780;
  fraction_rom[329]=24'd167286;
  fraction_rom[330]=24'd167792;
  fraction_rom[331]=24'd168298;
  fraction_rom[332]=24'd168804;
  fraction_rom[333]=24'd169310;
  fraction_rom[334]=24'd169816;
  fraction_rom[335]=24'd170321;
  fraction_rom[336]=24'd170827;
  fraction_rom[337]=24'd171333;
  fraction_rom[338]=24'd171839;
  fraction_rom[339]=24'd172345;
  fraction_rom[340]=24'd172850;
  fraction_rom[341]=24'd173356;
  fraction_rom[342]=24'd173862;
  fraction_rom[343]=24'd174368;
  fraction_rom[344]=24'd174873;
  fraction_rom[345]=24'd175379;
  fraction_rom[346]=24'd175885;
  fraction_rom[347]=24'd176390;
  fraction_rom[348]=24'd176896;
  fraction_rom[349]=24'd177402;
  fraction_rom[350]=24'd177907;
  fraction_rom[351]=24'd178413;
  fraction_rom[352]=24'd178918;
  fraction_rom[353]=24'd179424;
  fraction_rom[354]=24'd179930;
  fraction_rom[355]=24'd180435;
  fraction_rom[356]=24'd180941;
  fraction_rom[357]=24'd181446;
  fraction_rom[358]=24'd181952;
  fraction_rom[359]=24'd182457;
  fraction_rom[360]=24'd182962;
  fraction_rom[361]=24'd183468;
  fraction_rom[362]=24'd183973;
  fraction_rom[363]=24'd184479;
  fraction_rom[364]=24'd184984;
  fraction_rom[365]=24'd185490;
  fraction_rom[366]=24'd185995;
  fraction_rom[367]=24'd186500;
  fraction_rom[368]=24'd187006;
  fraction_rom[369]=24'd187511;
  fraction_rom[370]=24'd188016;
  fraction_rom[371]=24'd188521;
  fraction_rom[372]=24'd189027;
  fraction_rom[373]=24'd189532;
  fraction_rom[374]=24'd190037;
  fraction_rom[375]=24'd190542;
  fraction_rom[376]=24'd191048;
  fraction_rom[377]=24'd191553;
  fraction_rom[378]=24'd192058;
  fraction_rom[379]=24'd192563;
  fraction_rom[380]=24'd193068;
  fraction_rom[381]=24'd193574;
  fraction_rom[382]=24'd194079;
  fraction_rom[383]=24'd194584;
  fraction_rom[384]=24'd195089;
  fraction_rom[385]=24'd195594;
  fraction_rom[386]=24'd196099;
  fraction_rom[387]=24'd196604;
  fraction_rom[388]=24'd197109;
  fraction_rom[389]=24'd197614;
  fraction_rom[390]=24'd198119;
  fraction_rom[391]=24'd198624;
  fraction_rom[392]=24'd199129;
  fraction_rom[393]=24'd199634;
  fraction_rom[394]=24'd200139;
  fraction_rom[395]=24'd200644;
  fraction_rom[396]=24'd201149;
  fraction_rom[397]=24'd201654;
  fraction_rom[398]=24'd202158;
  fraction_rom[399]=24'd202663;
  fraction_rom[400]=24'd203168;
  fraction_rom[401]=24'd203673;
  fraction_rom[402]=24'd204178;
  fraction_rom[403]=24'd204683;
  fraction_rom[404]=24'd205187;
  fraction_rom[405]=24'd205692;
  fraction_rom[406]=24'd206197;
  fraction_rom[407]=24'd206702;
  fraction_rom[408]=24'd207206;
  fraction_rom[409]=24'd207711;
  fraction_rom[410]=24'd208216;
  fraction_rom[411]=24'd208720;
  fraction_rom[412]=24'd209225;
  fraction_rom[413]=24'd209730;
  fraction_rom[414]=24'd210234;
  fraction_rom[415]=24'd210739;
  fraction_rom[416]=24'd211243;
  fraction_rom[417]=24'd211748;
  fraction_rom[418]=24'd212253;
  fraction_rom[419]=24'd212757;
  fraction_rom[420]=24'd213262;
  fraction_rom[421]=24'd213766;
  fraction_rom[422]=24'd214271;
  fraction_rom[423]=24'd214775;
  fraction_rom[424]=24'd215280;
  fraction_rom[425]=24'd215784;
  fraction_rom[426]=24'd216289;
  fraction_rom[427]=24'd216793;
  fraction_rom[428]=24'd217297;
  fraction_rom[429]=24'd217802;
  fraction_rom[430]=24'd218306;
  fraction_rom[431]=24'd218811;
  fraction_rom[432]=24'd219315;
  fraction_rom[433]=24'd219819;
  fraction_rom[434]=24'd220324;
  fraction_rom[435]=24'd220828;
  fraction_rom[436]=24'd221332;
  fraction_rom[437]=24'd221836;
  fraction_rom[438]=24'd222341;
  fraction_rom[439]=24'd222845;
  fraction_rom[440]=24'd223349;
  fraction_rom[441]=24'd223853;
  fraction_rom[442]=24'd224358;
  fraction_rom[443]=24'd224862;
  fraction_rom[444]=24'd225366;
  fraction_rom[445]=24'd225870;
  fraction_rom[446]=24'd226374;
  fraction_rom[447]=24'd226878;
  fraction_rom[448]=24'd227382;
  fraction_rom[449]=24'd227886;
  fraction_rom[450]=24'd228391;
  fraction_rom[451]=24'd228895;
  fraction_rom[452]=24'd229399;
  fraction_rom[453]=24'd229903;
  fraction_rom[454]=24'd230407;
  fraction_rom[455]=24'd230911;
  fraction_rom[456]=24'd231415;
  fraction_rom[457]=24'd231919;
  fraction_rom[458]=24'd232423;
  fraction_rom[459]=24'd232926;
  fraction_rom[460]=24'd233430;
  fraction_rom[461]=24'd233934;
  fraction_rom[462]=24'd234438;
  fraction_rom[463]=24'd234942;
  fraction_rom[464]=24'd235446;
  fraction_rom[465]=24'd235950;
  fraction_rom[466]=24'd236454;
  fraction_rom[467]=24'd236957;
  fraction_rom[468]=24'd237461;
  fraction_rom[469]=24'd237965;
  fraction_rom[470]=24'd238469;
  fraction_rom[471]=24'd238972;
  fraction_rom[472]=24'd239476;
  fraction_rom[473]=24'd239980;
  fraction_rom[474]=24'd240484;
  fraction_rom[475]=24'd240987;
  fraction_rom[476]=24'd241491;
  fraction_rom[477]=24'd241995;
  fraction_rom[478]=24'd242498;
  fraction_rom[479]=24'd243002;
  fraction_rom[480]=24'd243506;
  fraction_rom[481]=24'd244009;
  fraction_rom[482]=24'd244513;
  fraction_rom[483]=24'd245016;
  fraction_rom[484]=24'd245520;
  fraction_rom[485]=24'd246023;
  fraction_rom[486]=24'd246527;
  fraction_rom[487]=24'd247030;
  fraction_rom[488]=24'd247534;
  fraction_rom[489]=24'd248037;
  fraction_rom[490]=24'd248541;
  fraction_rom[491]=24'd249044;
  fraction_rom[492]=24'd249548;
  fraction_rom[493]=24'd250051;
  fraction_rom[494]=24'd250554;
  fraction_rom[495]=24'd251058;
  fraction_rom[496]=24'd251561;
  fraction_rom[497]=24'd252065;
  fraction_rom[498]=24'd252568;
  fraction_rom[499]=24'd253071;
  fraction_rom[500]=24'd253575;
  fraction_rom[501]=24'd254078;
  fraction_rom[502]=24'd254581;
  fraction_rom[503]=24'd255084;
  fraction_rom[504]=24'd255588;
  fraction_rom[505]=24'd256091;
  fraction_rom[506]=24'd256594;
  fraction_rom[507]=24'd257097;
  fraction_rom[508]=24'd257600;
  fraction_rom[509]=24'd258104;
  fraction_rom[510]=24'd258607;
  fraction_rom[511]=24'd259110;
  fraction_rom[512]=24'd259613;
  fraction_rom[513]=24'd260116;
  fraction_rom[514]=24'd260619;
  fraction_rom[515]=24'd261122;
  fraction_rom[516]=24'd261625;
  fraction_rom[517]=24'd262128;
  fraction_rom[518]=24'd262631;
  fraction_rom[519]=24'd263134;
  fraction_rom[520]=24'd263637;
  fraction_rom[521]=24'd264140;
  fraction_rom[522]=24'd264643;
  fraction_rom[523]=24'd265146;
  fraction_rom[524]=24'd265649;
  fraction_rom[525]=24'd266152;
  fraction_rom[526]=24'd266655;
  fraction_rom[527]=24'd267158;
  fraction_rom[528]=24'd267661;
  fraction_rom[529]=24'd268164;
  fraction_rom[530]=24'd268667;
  fraction_rom[531]=24'd269169;
  fraction_rom[532]=24'd269672;
  fraction_rom[533]=24'd270175;
  fraction_rom[534]=24'd270678;
  fraction_rom[535]=24'd271181;
  fraction_rom[536]=24'd271683;
  fraction_rom[537]=24'd272186;
  fraction_rom[538]=24'd272689;
  fraction_rom[539]=24'd273191;
  fraction_rom[540]=24'd273694;
  fraction_rom[541]=24'd274197;
  fraction_rom[542]=24'd274699;
  fraction_rom[543]=24'd275202;
  fraction_rom[544]=24'd275705;
  fraction_rom[545]=24'd276207;
  fraction_rom[546]=24'd276710;
  fraction_rom[547]=24'd277213;
  fraction_rom[548]=24'd277715;
  fraction_rom[549]=24'd278218;
  fraction_rom[550]=24'd278720;
  fraction_rom[551]=24'd279223;
  fraction_rom[552]=24'd279725;
  fraction_rom[553]=24'd280228;
  fraction_rom[554]=24'd280730;
  fraction_rom[555]=24'd281233;
  fraction_rom[556]=24'd281735;
  fraction_rom[557]=24'd282238;
  fraction_rom[558]=24'd282740;
  fraction_rom[559]=24'd283242;
  fraction_rom[560]=24'd283745;
  fraction_rom[561]=24'd284247;
  fraction_rom[562]=24'd284750;
  fraction_rom[563]=24'd285252;
  fraction_rom[564]=24'd285754;
  fraction_rom[565]=24'd286256;
  fraction_rom[566]=24'd286759;
  fraction_rom[567]=24'd287261;
  fraction_rom[568]=24'd287763;
  fraction_rom[569]=24'd288266;
  fraction_rom[570]=24'd288768;
  fraction_rom[571]=24'd289270;
  fraction_rom[572]=24'd289772;
  fraction_rom[573]=24'd290274;
  fraction_rom[574]=24'd290777;
  fraction_rom[575]=24'd291279;
  fraction_rom[576]=24'd291781;
  fraction_rom[577]=24'd292283;
  fraction_rom[578]=24'd292785;
  fraction_rom[579]=24'd293287;
  fraction_rom[580]=24'd293789;
  fraction_rom[581]=24'd294291;
  fraction_rom[582]=24'd294793;
  fraction_rom[583]=24'd295295;
  fraction_rom[584]=24'd295797;
  fraction_rom[585]=24'd296299;
  fraction_rom[586]=24'd296801;
  fraction_rom[587]=24'd297303;
  fraction_rom[588]=24'd297805;
  fraction_rom[589]=24'd298307;
  fraction_rom[590]=24'd298809;
  fraction_rom[591]=24'd299311;
  fraction_rom[592]=24'd299813;
  fraction_rom[593]=24'd300315;
  fraction_rom[594]=24'd300817;
  fraction_rom[595]=24'd301319;
  fraction_rom[596]=24'd301820;
  fraction_rom[597]=24'd302322;
  fraction_rom[598]=24'd302824;
  fraction_rom[599]=24'd303326;
  fraction_rom[600]=24'd303828;
  fraction_rom[601]=24'd304329;
  fraction_rom[602]=24'd304831;
  fraction_rom[603]=24'd305333;
  fraction_rom[604]=24'd305835;
  fraction_rom[605]=24'd306336;
  fraction_rom[606]=24'd306838;
  fraction_rom[607]=24'd307340;
  fraction_rom[608]=24'd307841;
  fraction_rom[609]=24'd308343;
  fraction_rom[610]=24'd308845;
  fraction_rom[611]=24'd309346;
  fraction_rom[612]=24'd309848;
  fraction_rom[613]=24'd310349;
  fraction_rom[614]=24'd310851;
  fraction_rom[615]=24'd311352;
  fraction_rom[616]=24'd311854;
  fraction_rom[617]=24'd312355;
  fraction_rom[618]=24'd312857;
  fraction_rom[619]=24'd313358;
  fraction_rom[620]=24'd313860;
  fraction_rom[621]=24'd314361;
  fraction_rom[622]=24'd314863;
  fraction_rom[623]=24'd315364;
  fraction_rom[624]=24'd315866;
  fraction_rom[625]=24'd316367;
  fraction_rom[626]=24'd316868;
  fraction_rom[627]=24'd317370;
  fraction_rom[628]=24'd317871;
  fraction_rom[629]=24'd318372;
  fraction_rom[630]=24'd318874;
  fraction_rom[631]=24'd319375;
  fraction_rom[632]=24'd319876;
  fraction_rom[633]=24'd320378;
  fraction_rom[634]=24'd320879;
  fraction_rom[635]=24'd321380;
  fraction_rom[636]=24'd321881;
  fraction_rom[637]=24'd322383;
  fraction_rom[638]=24'd322884;
  fraction_rom[639]=24'd323385;
  fraction_rom[640]=24'd323886;
  fraction_rom[641]=24'd324387;
  fraction_rom[642]=24'd324888;
  fraction_rom[643]=24'd325389;
  fraction_rom[644]=24'd325891;
  fraction_rom[645]=24'd326392;
  fraction_rom[646]=24'd326893;
  fraction_rom[647]=24'd327394;
  fraction_rom[648]=24'd327895;
  fraction_rom[649]=24'd328396;
  fraction_rom[650]=24'd328897;
  fraction_rom[651]=24'd329398;
  fraction_rom[652]=24'd329899;
  fraction_rom[653]=24'd330400;
  fraction_rom[654]=24'd330901;
  fraction_rom[655]=24'd331402;
  fraction_rom[656]=24'd331903;
  fraction_rom[657]=24'd332404;
  fraction_rom[658]=24'd332904;
  fraction_rom[659]=24'd333405;
  fraction_rom[660]=24'd333906;
  fraction_rom[661]=24'd334407;
  fraction_rom[662]=24'd334908;
  fraction_rom[663]=24'd335409;
  fraction_rom[664]=24'd335909;
  fraction_rom[665]=24'd336410;
  fraction_rom[666]=24'd336911;
  fraction_rom[667]=24'd337412;
  fraction_rom[668]=24'd337912;
  fraction_rom[669]=24'd338413;
  fraction_rom[670]=24'd338914;
  fraction_rom[671]=24'd339415;
  fraction_rom[672]=24'd339915;
  fraction_rom[673]=24'd340416;
  fraction_rom[674]=24'd340917;
  fraction_rom[675]=24'd341417;
  fraction_rom[676]=24'd341918;
  fraction_rom[677]=24'd342418;
  fraction_rom[678]=24'd342919;
  fraction_rom[679]=24'd343420;
  fraction_rom[680]=24'd343920;
  fraction_rom[681]=24'd344421;
  fraction_rom[682]=24'd344921;
  fraction_rom[683]=24'd345422;
  fraction_rom[684]=24'd345922;
  fraction_rom[685]=24'd346423;
  fraction_rom[686]=24'd346923;
  fraction_rom[687]=24'd347424;
  fraction_rom[688]=24'd347924;
  fraction_rom[689]=24'd348424;
  fraction_rom[690]=24'd348925;
  fraction_rom[691]=24'd349425;
  fraction_rom[692]=24'd349926;
  fraction_rom[693]=24'd350426;
  fraction_rom[694]=24'd350926;
  fraction_rom[695]=24'd351427;
  fraction_rom[696]=24'd351927;
  fraction_rom[697]=24'd352427;
  fraction_rom[698]=24'd352927;
  fraction_rom[699]=24'd353428;
  fraction_rom[700]=24'd353928;
  fraction_rom[701]=24'd354428;
  fraction_rom[702]=24'd354928;
  fraction_rom[703]=24'd355429;
  fraction_rom[704]=24'd355929;
  fraction_rom[705]=24'd356429;
  fraction_rom[706]=24'd356929;
  fraction_rom[707]=24'd357429;
  fraction_rom[708]=24'd357929;
  fraction_rom[709]=24'd358430;
  fraction_rom[710]=24'd358930;
  fraction_rom[711]=24'd359430;
  fraction_rom[712]=24'd359930;
  fraction_rom[713]=24'd360430;
  fraction_rom[714]=24'd360930;
  fraction_rom[715]=24'd361430;
  fraction_rom[716]=24'd361930;
  fraction_rom[717]=24'd362430;
  fraction_rom[718]=24'd362930;
  fraction_rom[719]=24'd363430;
  fraction_rom[720]=24'd363930;
  fraction_rom[721]=24'd364430;
  fraction_rom[722]=24'd364930;
  fraction_rom[723]=24'd365429;
  fraction_rom[724]=24'd365929;
  fraction_rom[725]=24'd366429;
  fraction_rom[726]=24'd366929;
  fraction_rom[727]=24'd367429;
  fraction_rom[728]=24'd367929;
  fraction_rom[729]=24'd368429;
  fraction_rom[730]=24'd368928;
  fraction_rom[731]=24'd369428;
  fraction_rom[732]=24'd369928;
  fraction_rom[733]=24'd370428;
  fraction_rom[734]=24'd370927;
  fraction_rom[735]=24'd371427;
  fraction_rom[736]=24'd371927;
  fraction_rom[737]=24'd372426;
  fraction_rom[738]=24'd372926;
  fraction_rom[739]=24'd373426;
  fraction_rom[740]=24'd373925;
  fraction_rom[741]=24'd374425;
  fraction_rom[742]=24'd374925;
  fraction_rom[743]=24'd375424;
  fraction_rom[744]=24'd375924;
  fraction_rom[745]=24'd376423;
  fraction_rom[746]=24'd376923;
  fraction_rom[747]=24'd377422;
  fraction_rom[748]=24'd377922;
  fraction_rom[749]=24'd378421;
  fraction_rom[750]=24'd378921;
  fraction_rom[751]=24'd379420;
  fraction_rom[752]=24'd379920;
  fraction_rom[753]=24'd380419;
  fraction_rom[754]=24'd380919;
  fraction_rom[755]=24'd381418;
  fraction_rom[756]=24'd381918;
  fraction_rom[757]=24'd382417;
  fraction_rom[758]=24'd382916;
  fraction_rom[759]=24'd383416;
  fraction_rom[760]=24'd383915;
  fraction_rom[761]=24'd384414;
  fraction_rom[762]=24'd384914;
  fraction_rom[763]=24'd385413;
  fraction_rom[764]=24'd385912;
  fraction_rom[765]=24'd386411;
  fraction_rom[766]=24'd386911;
  fraction_rom[767]=24'd387410;
  fraction_rom[768]=24'd387909;
  fraction_rom[769]=24'd388408;
  fraction_rom[770]=24'd388907;
  fraction_rom[771]=24'd389407;
  fraction_rom[772]=24'd389906;
  fraction_rom[773]=24'd390405;
  fraction_rom[774]=24'd390904;
  fraction_rom[775]=24'd391403;
  fraction_rom[776]=24'd391902;
  fraction_rom[777]=24'd392401;
  fraction_rom[778]=24'd392900;
  fraction_rom[779]=24'd393399;
  fraction_rom[780]=24'd393898;
  fraction_rom[781]=24'd394397;
  fraction_rom[782]=24'd394896;
  fraction_rom[783]=24'd395395;
  fraction_rom[784]=24'd395894;
  fraction_rom[785]=24'd396393;
  fraction_rom[786]=24'd396892;
  fraction_rom[787]=24'd397391;
  fraction_rom[788]=24'd397890;
  fraction_rom[789]=24'd398389;
  fraction_rom[790]=24'd398888;
  fraction_rom[791]=24'd399387;
  fraction_rom[792]=24'd399886;
  fraction_rom[793]=24'd400384;
  fraction_rom[794]=24'd400883;
  fraction_rom[795]=24'd401382;
  fraction_rom[796]=24'd401881;
  fraction_rom[797]=24'd402380;
  fraction_rom[798]=24'd402878;
  fraction_rom[799]=24'd403377;
  fraction_rom[800]=24'd403876;
  fraction_rom[801]=24'd404375;
  fraction_rom[802]=24'd404873;
  fraction_rom[803]=24'd405372;
  fraction_rom[804]=24'd405871;
  fraction_rom[805]=24'd406369;
  fraction_rom[806]=24'd406868;
  fraction_rom[807]=24'd407367;
  fraction_rom[808]=24'd407865;
  fraction_rom[809]=24'd408364;
  fraction_rom[810]=24'd408862;
  fraction_rom[811]=24'd409361;
  fraction_rom[812]=24'd409859;
  fraction_rom[813]=24'd410358;
  fraction_rom[814]=24'd410856;
  fraction_rom[815]=24'd411355;
  fraction_rom[816]=24'd411853;
  fraction_rom[817]=24'd412352;
  fraction_rom[818]=24'd412850;
  fraction_rom[819]=24'd413349;
  fraction_rom[820]=24'd413847;
  fraction_rom[821]=24'd414346;
  fraction_rom[822]=24'd414844;
  fraction_rom[823]=24'd415342;
  fraction_rom[824]=24'd415841;
  fraction_rom[825]=24'd416339;
  fraction_rom[826]=24'd416837;
  fraction_rom[827]=24'd417336;
  fraction_rom[828]=24'd417834;
  fraction_rom[829]=24'd418332;
  fraction_rom[830]=24'd418831;
  fraction_rom[831]=24'd419329;
  fraction_rom[832]=24'd419827;
  fraction_rom[833]=24'd420325;
  fraction_rom[834]=24'd420824;
  fraction_rom[835]=24'd421322;
  fraction_rom[836]=24'd421820;
  fraction_rom[837]=24'd422318;
  fraction_rom[838]=24'd422816;
  fraction_rom[839]=24'd423314;
  fraction_rom[840]=24'd423812;
  fraction_rom[841]=24'd424311;
  fraction_rom[842]=24'd424809;
  fraction_rom[843]=24'd425307;
  fraction_rom[844]=24'd425805;
  fraction_rom[845]=24'd426303;
  fraction_rom[846]=24'd426801;
  fraction_rom[847]=24'd427299;
  fraction_rom[848]=24'd427797;
  fraction_rom[849]=24'd428295;
  fraction_rom[850]=24'd428793;
  fraction_rom[851]=24'd429291;
  fraction_rom[852]=24'd429789;
  fraction_rom[853]=24'd430287;
  fraction_rom[854]=24'd430785;
  fraction_rom[855]=24'd431282;
  fraction_rom[856]=24'd431780;
  fraction_rom[857]=24'd432278;
  fraction_rom[858]=24'd432776;
  fraction_rom[859]=24'd433274;
  fraction_rom[860]=24'd433772;
  fraction_rom[861]=24'd434269;
  fraction_rom[862]=24'd434767;
  fraction_rom[863]=24'd435265;
  fraction_rom[864]=24'd435763;
  fraction_rom[865]=24'd436261;
  fraction_rom[866]=24'd436758;
  fraction_rom[867]=24'd437256;
  fraction_rom[868]=24'd437754;
  fraction_rom[869]=24'd438251;
  fraction_rom[870]=24'd438749;
  fraction_rom[871]=24'd439247;
  fraction_rom[872]=24'd439744;
  fraction_rom[873]=24'd440242;
  fraction_rom[874]=24'd440740;
  fraction_rom[875]=24'd441237;
  fraction_rom[876]=24'd441735;
  fraction_rom[877]=24'd442232;
  fraction_rom[878]=24'd442730;
  fraction_rom[879]=24'd443227;
  fraction_rom[880]=24'd443725;
  fraction_rom[881]=24'd444222;
  fraction_rom[882]=24'd444720;
  fraction_rom[883]=24'd445217;
  fraction_rom[884]=24'd445715;
  fraction_rom[885]=24'd446212;
  fraction_rom[886]=24'd446710;
  fraction_rom[887]=24'd447207;
  fraction_rom[888]=24'd447704;
  fraction_rom[889]=24'd448202;
  fraction_rom[890]=24'd448699;
  fraction_rom[891]=24'd449196;
  fraction_rom[892]=24'd449694;
  fraction_rom[893]=24'd450191;
  fraction_rom[894]=24'd450688;
  fraction_rom[895]=24'd451186;
  fraction_rom[896]=24'd451683;
  fraction_rom[897]=24'd452180;
  fraction_rom[898]=24'd452677;
  fraction_rom[899]=24'd453175;
  fraction_rom[900]=24'd453672;
  fraction_rom[901]=24'd454169;
  fraction_rom[902]=24'd454666;
  fraction_rom[903]=24'd455163;
  fraction_rom[904]=24'd455661;
  fraction_rom[905]=24'd456158;
  fraction_rom[906]=24'd456655;
  fraction_rom[907]=24'd457152;
  fraction_rom[908]=24'd457649;
  fraction_rom[909]=24'd458146;
  fraction_rom[910]=24'd458643;
  fraction_rom[911]=24'd459140;
  fraction_rom[912]=24'd459637;
  fraction_rom[913]=24'd460134;
  fraction_rom[914]=24'd460631;
  fraction_rom[915]=24'd461128;
  fraction_rom[916]=24'd461625;
  fraction_rom[917]=24'd462122;
  fraction_rom[918]=24'd462619;
  fraction_rom[919]=24'd463116;
  fraction_rom[920]=24'd463613;
  fraction_rom[921]=24'd464110;
  fraction_rom[922]=24'd464607;
  fraction_rom[923]=24'd465104;
  fraction_rom[924]=24'd465600;
  fraction_rom[925]=24'd466097;
  fraction_rom[926]=24'd466594;
  fraction_rom[927]=24'd467091;
  fraction_rom[928]=24'd467588;
  fraction_rom[929]=24'd468084;
  fraction_rom[930]=24'd468581;
  fraction_rom[931]=24'd469078;
  fraction_rom[932]=24'd469575;
  fraction_rom[933]=24'd470071;
  fraction_rom[934]=24'd470568;
  fraction_rom[935]=24'd471065;
  fraction_rom[936]=24'd471561;
  fraction_rom[937]=24'd472058;
  fraction_rom[938]=24'd472555;
  fraction_rom[939]=24'd473051;
  fraction_rom[940]=24'd473548;
  fraction_rom[941]=24'd474044;
  fraction_rom[942]=24'd474541;
  fraction_rom[943]=24'd475038;
  fraction_rom[944]=24'd475534;
  fraction_rom[945]=24'd476031;
  fraction_rom[946]=24'd476527;
  fraction_rom[947]=24'd477024;
  fraction_rom[948]=24'd477520;
  fraction_rom[949]=24'd478017;
  fraction_rom[950]=24'd478513;
  fraction_rom[951]=24'd479010;
  fraction_rom[952]=24'd479506;
  fraction_rom[953]=24'd480002;
  fraction_rom[954]=24'd480499;
  fraction_rom[955]=24'd480995;
  fraction_rom[956]=24'd481491;
  fraction_rom[957]=24'd481988;
  fraction_rom[958]=24'd482484;
  fraction_rom[959]=24'd482980;
  fraction_rom[960]=24'd483477;
  fraction_rom[961]=24'd483973;
  fraction_rom[962]=24'd484469;
  fraction_rom[963]=24'd484966;
  fraction_rom[964]=24'd485462;
  fraction_rom[965]=24'd485958;
  fraction_rom[966]=24'd486454;
  fraction_rom[967]=24'd486950;
  fraction_rom[968]=24'd487447;
  fraction_rom[969]=24'd487943;
  fraction_rom[970]=24'd488439;
  fraction_rom[971]=24'd488935;
  fraction_rom[972]=24'd489431;
  fraction_rom[973]=24'd489927;
  fraction_rom[974]=24'd490423;
  fraction_rom[975]=24'd490920;
  fraction_rom[976]=24'd491416;
  fraction_rom[977]=24'd491912;
  fraction_rom[978]=24'd492408;
  fraction_rom[979]=24'd492904;
  fraction_rom[980]=24'd493400;
  fraction_rom[981]=24'd493896;
  fraction_rom[982]=24'd494392;
  fraction_rom[983]=24'd494888;
  fraction_rom[984]=24'd495384;
  fraction_rom[985]=24'd495879;
  fraction_rom[986]=24'd496375;
  fraction_rom[987]=24'd496871;
  fraction_rom[988]=24'd497367;
  fraction_rom[989]=24'd497863;
  fraction_rom[990]=24'd498359;
  fraction_rom[991]=24'd498855;
  fraction_rom[992]=24'd499350;
  fraction_rom[993]=24'd499846;
  fraction_rom[994]=24'd500342;
  fraction_rom[995]=24'd500838;
  fraction_rom[996]=24'd501334;
  fraction_rom[997]=24'd501829;
  fraction_rom[998]=24'd502325;
  fraction_rom[999]=24'd502821;
  fraction_rom[1000]=24'd0;
  fraction_rom[1001]=24'd0;
  fraction_rom[1002]=24'd0;
  fraction_rom[1003]=24'd0;
  fraction_rom[1004]=24'd0;
  fraction_rom[1005]=24'd0;
  fraction_rom[1006]=24'd0;
  fraction_rom[1007]=24'd0;
  fraction_rom[1008]=24'd0;
  fraction_rom[1009]=24'd0;
  fraction_rom[1010]=24'd0;
  fraction_rom[1011]=24'd0;
  fraction_rom[1012]=24'd0;
  fraction_rom[1013]=24'd0;
  fraction_rom[1014]=24'd0;
  fraction_rom[1015]=24'd0;
  fraction_rom[1016]=24'd0;
  fraction_rom[1017]=24'd0;
  fraction_rom[1018]=24'd0;
  fraction_rom[1019]=24'd0;
  fraction_rom[1020]=24'd0;
  fraction_rom[1021]=24'd0;
  fraction_rom[1022]=24'd0;
  fraction_rom[1023]=24'd0;
 end
 always @(posedge clk) fraction_q<=fraction_rom[filter_fraction];
 task calc;
 input signed [63:0] a,b;input [31:0] denominator;input [7:0] dest;
 begin ma<=a;mb<=b;pending_den<=denominator;return_state<=dest;trunc_negative<=0;mul_start<=1;state<=100;end endtask
 task calc_trunc;
 input signed [63:0] a;input [31:0] denominator;input [7:0] dest;
 begin ma<=a;mb<=1;pending_den<=denominator;return_state<=dest;mul_start<=1;state<=102;end endtask
 function signed [63:0] integer_q16;
 input signed [63:0] a;
 begin integer_q16=(a>>>16)+(a[63] && |a[15:0] ? 64'sd1:64'sd0);end endfunction
 initial begin vz_q16=0;update=0;fused_height_mm=0;vz_mmps=0;sample_az_mmps2=0;reason=1;end
 always @(posedge clk) begin
  update<=0;mul_start<=0;div_start<=0;
  if(!rst_n || cleanup) begin
   state<=0;timer_store<=0;publication_age<=32'hffffffff;publication_fresh<=(32'hffffffff < AGE_LIMIT);seeded<=0;seen<=0;cycle5<=0;
   origin_mm_store<=0;ref_height_old_store<=0;ref_speed_old_store<=0;ref_speed_store<=0;ref_acc_store<=0;
   acc_i<=0;acc_out<=0;vq<=0;hq<=0;vel_e<=0;height_e<=0;
   acc_pending<=0;height_pending<=0;pending_height_epoch_ok<=0;height_transaction_epoch_ok<=0;seed_epoch_ok<=0;filtered_acc_store<=0;filter_steps<=0;filter_fraction<=0;
   vz_mmps<=0;fused_height_mm<=0;sample_az_mmps2<=0;vz_q16<=0;v_q16_range<=0;publish_v_q16<=0;publish_v_q16_range<=0;
   reason<=origin_reset ? 2:!sources_ok ? 1:4;
   // Fault recovery starts a new height epoch; no stale interval integration.
   if(!rst_n || origin_reset || !sources_ok) fault<=0;
  end else begin
   if(publication_age!=32'hffffffff)begin publication_age<=publication_age+1'b1;publication_fresh<=((AGE_LIMIT!=0)&&(publication_age<(AGE_LIMIT-32'd1)));end
   if(acc_update)begin
    if(acc_pending || acc_dt_us==0 || acc_dt_us>100000)begin fault<=1;reason<=4;end
    else begin acc_pending<=1;pending_acc<=az_up_mmps2;pending_acc_dt_store<=acc_dt_us;end
   end
   if(seeded)begin
    if(timer==PERIOD_TICKS-1)begin
     timer_store<=0;
     if(height_pending)begin fault<=1;reason<=4;end
     else begin height_pending<=1;pending_height<=ref_height_mm;pending_rawaz<=az_up_mmps2;pending_height_epoch_ok<=sources_ok && !origin_reset && !fault;end
    end else timer_store<=timer+1'b1;
   end else timer_store<=0;
    case(state)
     0:if(!seeded)begin seed_epoch_ok<=sources_ok && !origin_reset && !fault;calc_trunc($signed(ref_height_mm),10,80);end
     else if(acc_pending)begin
      acc_pending<=0;filter_input_store<=$signed(pending_acc)*64'sd65536;held_acc_dt<=pending_acc_dt;
      calc($signed({1'b0,pending_acc_dt}),1,1000,70);
     end else if(height_pending)begin
      height_pending<=0;held_rawaz_store<=pending_rawaz;height_transaction_epoch_ok<=pending_height_epoch_ok;
      calc_trunc($signed(pending_height),10,81);
     end
     80:if(!sources_ok || origin_reset || fault || !seed_epoch_ok)begin seeded<=0;seen<=0;state<=0;reason<=4;end else begin
      origin_mm_store<=$signed(value[31:0])*32'sd10;fused_height_mm<=$signed(value[31:0])*32'sd10;
      acc_i<=-filtered_acc;seeded<=1;timer_store<=0;cycle5<=0;state<=0;
     end
     81:begin held_relative_mm_store<=$signed(value[31:0])*32'sd10-origin_mm;calc_trunc(filtered_acc,655360,82);end
     82:begin
      held_acc_mm_store<=$signed(value[31:0])*32'sd10;
      if(cycle5==4)begin cycle5<=0;state<=1;end
      else begin cycle5<=cycle5+1'b1;state<=4;end
     end
     1:begin
      // Original s32 reference_speed truncates cm/s; do the division in cm.
      // Subtract half-denominator before round-to-nearest serial divide to
      // obtain original truncation-towards-zero, including both signs.
      ma<=($signed(held_relative_mm)-$signed(ref_height_old))*100;
      mb<=1;pending_den<=55;return_state<=2;mul_start<=1;state<=102;
     end
     2:begin
      ref_speed_store<=$signed(value[31:0])*32'sd10;state<=83;
     end
     83:begin ma<=($signed(ref_speed)-$signed(ref_speed_old))*100;mb<=1;pending_den<=55;return_state<=3;mul_start<=1;state<=102;end
     3:begin
      ref_acc_store<=$signed(value[31:0])*32'sd10;ref_height_old_store<=held_relative_mm;ref_speed_old_store<=ref_speed;state<=4;
     end
     4:begin
      acc_out<=$signed(held_acc_mm)*65536+clip(acc_i,-65536000,65536000);
      state<=5;
     end
     5:calc($signed(ref_acc)*65536-acc_out,11,10000,6);
     6:begin
      // Source clips ei only when used; keep accumulated ei un-clipped.
      acc_i<=acc_i+value;calc(acc_out+vel_e,11,1000,7);
     end
     7:begin vq<=vq+value;calc($signed(ref_speed)*65536-vq-value,3,5,8);end
     8:begin vel_e<=clip(value,-65536000,65536000);calc(vq+height_e,11,1000,9);end
     9:begin hq<=hq+value;calc($signed(held_relative_mm)*65536-hq-value,3,10,10);end
     10:begin height_e<=value;state<=11;end
     11:begin publish_h_integer<=integer_q16(hq);publish_v_integer<=integer_q16(vq);publish_v_q16<=vq[31:0];publish_v_q16_range<=vq>=-64'sd655360000 && vq<=64'sd655360000;state<=84;end
     84:if(!sources_ok || origin_reset || fault || new_acc_fault || new_height_fault || !height_transaction_epoch_ok || held_rawaz< -30000 || held_rawaz>30000 || held_relative_mm+origin_mm<0 || held_relative_mm+origin_mm>5000)begin
      fault<=sources_ok && !origin_reset;seen<=0;height_transaction_epoch_ok<=0;state<=0;reason<=4;
     end else begin
      height_transaction_epoch_ok<=0;fused_height_mm<=origin_mm+publish_h_integer;vz_mmps<=publish_v_integer;vz_q16<=publish_v_q16;v_q16_range<=publish_v_q16_range;
      sample_az_mmps2<=held_rawaz;publication_age<=0;publication_fresh<=(32'd0<AGE_LIMIT);seen<=1;update<=1;reason<=CAL_MASK[3] && CAL_MASK[4] ? 0:16;state<=0;
     end
     // Equivalent original .03-per1ms pole, using actual accepted pose dt.
     // Whole milliseconds run the original update verbatim; fractional time
     // usesQ24 1-.97^(dt/1ms). This is not .03-at11ms or a gain retune.
     70:begin
      if(({10'd0,value[6:0]}*17'd1000)>held_acc_dt[16:0])begin filter_steps<=value[6:0]-1'b1;filter_fraction<=held_acc_dt[16:0]-({10'd0,value[6:0]}*17'd1000)+17'd1000;end
      else begin filter_steps<=value[6:0];filter_fraction<=held_acc_dt[16:0]-({10'd0,value[6:0]}*17'd1000);end
      state<=71;
     end
     71:if(filter_steps!=0)calc(filter_input-filtered_acc,3,100,72);
     else if(filter_fraction!=0)state<=74;
     else state<=0;
     72:begin filtered_acc_store<=filtered_acc+value;filter_steps<=filter_steps-1'b1;state<=71;end
     73:begin filtered_acc_store<=filtered_acc+value;filter_fraction<=0;state<=0;end
     // State71 supplies the stable address; this additional clock consumes
     // the synchronous BSRAM result, retaining the exact previous formula.
     74:calc(filter_input-filtered_acc,{1'b0,fraction_q},16777216,73);
     100:if(md) begin num<=product;den<=pending_den;div_start<=1;state<=101;end
     101:if(dd) begin if(derr) begin fault<=1;reason<=4;state<=0;end else begin value<=trunc_negative ? -quotient:quotient;state<=return_state;end end
     102:if(md)begin
      trunc_negative<=product<0;trunc_magnitude_store<=product<0 ? -product:product;state<=103;
     end
     103:begin
      num<=trunc_magnitude>($signed({1'b0,pending_den})>>>1) ? trunc_magnitude-($signed({1'b0,pending_den})>>>1):0;
      den<=pending_den;div_start<=1;state<=101;
     end
     default:state<=0;
    endcase
  end
 end
endmodule
