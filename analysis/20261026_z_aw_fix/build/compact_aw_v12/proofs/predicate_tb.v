`timescale 1ns/1ps
`default_nettype none
module pred #(parameter integer AGE_LIMIT=5000000)(input wire [31:0] publication_age,output wire same);
wire a=((publication_age+32'd1)<AGE_LIMIT);wire b=((AGE_LIMIT!=0)&&(publication_age<(AGE_LIMIT-32'd1)));assign same=(publication_age==32'hffffffff)||(a===b);endmodule
module predicate_tb;reg[31:0]publication_age=0;wire[8:0]same;integer checks=0,n;reg[31:0]rng=32'h9c137ac5;
pred #(.AGE_LIMIT(32'h00000000)) p0(.publication_age(publication_age),.same(same[0]));
pred #(.AGE_LIMIT(32'h00000001)) p1(.publication_age(publication_age),.same(same[1]));
pred #(.AGE_LIMIT(32'h0000001f)) p2(.publication_age(publication_age),.same(same[2]));
pred #(.AGE_LIMIT(32'h00010000)) p3(.publication_age(publication_age),.same(same[3]));
pred #(.AGE_LIMIT(32'h004c4b40)) p4(.publication_age(publication_age),.same(same[4]));
pred #(.AGE_LIMIT(32'h7fffffff)) p5(.publication_age(publication_age),.same(same[5]));
pred #(.AGE_LIMIT(32'h80000000)) p6(.publication_age(publication_age),.same(same[6]));
pred #(.AGE_LIMIT(32'hfffffffe)) p7(.publication_age(publication_age),.same(same[7]));
pred #(.AGE_LIMIT(32'hffffffff)) p8(.publication_age(publication_age),.same(same[8]));
task check;input[31:0]x;begin publication_age=x;#1;if(same!==9'h1ff)$fatal(1,"unsigned rewrite mismatch A=%h same=%h",x,same);checks=checks+1;end endtask
initial begin
check(32'h00000000);
check(32'h00000001);
check(32'hfffffffe);
check(32'hffffffff);
check(32'hfffffffe);
check(32'hffffffff);
check(32'h00000000);
check(32'h00000001);
check(32'hffffffff);
check(32'h00000000);
check(32'h00000001);
check(32'h00000002);
check(32'h0000001d);
check(32'h0000001e);
check(32'h0000001f);
check(32'h00000020);
check(32'h0000fffe);
check(32'h0000ffff);
check(32'h00010000);
check(32'h00010001);
check(32'h004c4b3e);
check(32'h004c4b3f);
check(32'h004c4b40);
check(32'h004c4b41);
check(32'h7ffffffd);
check(32'h7ffffffe);
check(32'h7fffffff);
check(32'h80000000);
check(32'h7ffffffe);
check(32'h7fffffff);
check(32'h80000000);
check(32'h80000001);
check(32'hfffffffc);
check(32'hfffffffd);
check(32'hfffffffe);
check(32'hffffffff);
check(32'hfffffffd);
check(32'hfffffffe);
check(32'hffffffff);
check(32'h00000000);
for(n=0;n<200000;n=n+1)begin rng=(rng*32'd1664525)+32'd1013904223;check(rng);end
$display("PASS predicate vectors=%0d integer_limits=9 eligible_increment_age_excludes_MAX=1",checks);$finish;end
endmodule
`default_nettype wire
