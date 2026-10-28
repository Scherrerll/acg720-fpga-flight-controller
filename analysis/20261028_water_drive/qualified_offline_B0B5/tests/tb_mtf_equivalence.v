`timescale 1ns/1ps
// Public wrapper equivalence through actual UART and parser. No force on data,
// status, range flags, frame commits, arithmetic or diagnostic snapshots.
module tb_mtf_equivalence;
    reg clk=0;always #10 clk=~clk;
    reg rst=0,rx=1,hold=0;reg [63:0] uptime=0;integer clock_count=0;
    always @(posedge clk)begin clock_count=clock_count+1;if(clock_count%1000==0)uptime<=uptime+1;end
    wire [975:0] body_a,body_b;wire sa,ra,fa,ia,va,sb,rb,fb,ib,vb;
    wire [31:0] da,dta,aa,db,dtb,ab;wire signed [31:0] xa,ya,xb,yb;
    mtf01p_reader #(.CLOCK_HZ(1000000),.EXTERNAL_DIAGNOSTIC_HOLD(1),.DIAGNOSTIC_VERSION(3),.PHYSICAL_STOP_LOCK(0),.CONTROL_PATH(1),.STARTUP_ONLY_DIAGNOSTIC_RESET(1)) dut(
        .clk(clk),.rst_n(rst),.rx(rx),.uptime_ms(uptime),.diagnostic_hold(hold),.diagnostic_body(body_a),
        .metric_sample_valid(sa),.metric_range_valid(ra),.metric_flow_valid(fa),.metric_interval_integrated(ia),
        .metric_distance_mm(da),.metric_dt_ms(dta),.module_age_ms(aa),.metric_vx_x100(xa),.metric_vy_x100(ya),.metric_velocity_range_ok(va));
    mtf01p_reader_reference #(.CLOCK_HZ(1000000),.EXTERNAL_DIAGNOSTIC_HOLD(1),.DIAGNOSTIC_VERSION(3),.PHYSICAL_STOP_LOCK(0),.CONTROL_PATH(1),.STARTUP_ONLY_DIAGNOSTIC_RESET(1)) refreader(
        .clk(clk),.rst_n(rst),.rx(rx),.uptime_ms(uptime),.diagnostic_hold(hold),.diagnostic_body(body_b),
        .metric_sample_valid(sb),.metric_range_valid(rb),.metric_flow_valid(fb),.metric_interval_integrated(ib),
        .metric_distance_mm(db),.metric_dt_ms(dtb),.module_age_ms(ab),.metric_vx_x100(xb),.metric_vy_x100(yb),.metric_velocity_range_ok(vb));
    integer comparisons=0,samples=0,range_edges=0;reg old_range=0;
    always @(posedge clk)begin #2;
        comparisons=comparisons+1;
        if({body_a,sa,ra,fa,ia,da,dta,aa,xa,ya,va} !== {body_b,sb,rb,fb,ib,db,dtb,ab,xb,yb,vb})
            $fatal(1,"MTF public mismatch cycle%0d samples%0d range%0d/%0d distance%0d/%0d",comparisons,samples,ra,rb,da,db);
        if(dut.parser.raw_frame!==refreader.parser.raw_frame)$fatal(1,"raw frame changed");
        if(sa)samples=samples+1;
        if(ra!=old_range)range_edges=range_edges+1;old_range=ra;
    end
    task cycles;input integer n;integer j;begin for(j=0;j<n;j=j+1)@(negedge clk);end endtask
    task byte_tx;input[7:0] b;input bad_stop;integer j;begin
        rx=0;cycles(9);for(j=0;j<8;j=j+1)begin rx=b[j];cycles(9);end
        rx=!bad_stop;cycles(9);rx=1;cycles(3);
    end endtask
    reg [7:0] packet[0:26];reg [31:0] rng=32'h2c7e811b,d,t;
    integer i,k;reg [7:0] sum,tof;
    task build;input[31:0] distance,tm;input[7:0] sequence_id,status;input[3:0] faults;begin
        for(k=0;k<27;k=k+1)packet[k]=0;
        packet[0]=8'hef;packet[1]=1;packet[3]=faults[2]?8'h52:8'h51;packet[4]=sequence_id;packet[5]=faults[1]?19:20;
        packet[6]=tm[7:0];packet[7]=tm[15:8];packet[8]=tm[23:16];packet[9]=tm[31:24];
        packet[10]=distance[7:0];packet[11]=distance[15:8];packet[12]=distance[23:16];packet[13]=distance[31:24];
        packet[14]=80;packet[15]=10;packet[16]=status;
        packet[18]=rng[7:0];packet[19]=rng[15:8];packet[20]=rng[23:16];packet[21]=rng[31:24];
        packet[22]=faults[3]?0:(sequence_id%3==0?1:sequence_id%3==1?200:255);packet[23]=sequence_id%19==0?0:sequence_id%23==0?2:sequence_id%29==0?255:1;
        sum=0;for(k=0;k<26;k=k+1)sum=sum+packet[k];packet[26]=faults[0]?(sum^8'd1):sum;
    end endtask
    initial begin
        cycles(5);rst=1;cycles(40);
        for(i=0;i<512;i=i+1)begin
            rng={rng[30:0],rng[31]^rng[21]^rng[1]^rng[0]};
            case(i%16)0:d=0;1:d=9;2:d=10;3:d=79;4:d=80;5:d=12000;6:d=12001;7:d=32'hffffffff;8:d=32'h80000000;9:d=32'h7fffffff;default:d=rng&32'h3fff;endcase
            tof=i%17==0?2:i%5==0?0:1;t=i%19==0?(i-1)*11:i%23==0?32'hffffff00+i:i*11;
            build(d,t,i[7:0],tof,{i%11==0,i%31==0,i%29==0,i%13==0});
            hold=i%7==0;
            for(k=0;k<27;k=k+1)byte_tx(packet[k],0);
            cycles(40);
            if(i==255)begin rst=0;cycles(10);rst=1;cycles(40);end
        end
        hold=0;byte_tx(8'h55,1);cycles(100);
        build(1000,32'd9000,8'd9,8'd1,0);
        for(k=0;k<6;k=k+1)byte_tx(packet[k],0);
        cycles(7000);cycles(250000);
        if(samples<200 || range_edges<20 || dut.parser.samples<100 || dut.parser.checksum_errors<8 || dut.parser.length_errors==0 || dut.parser.uart_errors==0 || dut.parser.timeouts==0)
            $fatal(1,"MTF coverage insufficient samples%0d rangeedges%0d checksum%0d length%0d UART%0d timeout%0d",samples,range_edges,dut.parser.checksum_errors,dut.parser.length_errors,dut.parser.uart_errors,dut.parser.timeouts);
        if(ra || rb)$fatal(1,"stale module remained range-valid");
        $display("PASS MTF public cycle equivalence: %0d comparisons %0d samples %0d range edges; boundary/random32/TOF/quality/checksum/length/unknown-ID/UART/timeout/reset/epoch/hold/freshness",comparisons,samples,range_edges);$finish;
    end
    initial begin #100000000;$fatal(1,"MTF equivalence timeout");end
endmodule
