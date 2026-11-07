`timescale 1ns/1ps
module signed_fir4_tb;
 reg clk=0,rst=0,in_valid=0,out_ready=0;
 reg signed [7:0] x=0;
 wire in_ready,out_valid;
 wire signed [12:0] out_data;
 signed_fir4 dut(.clk(clk),.rst(rst),.x(x),.in_valid(in_valid),.in_ready(in_ready),.out_data(out_data),.out_valid(out_valid),.out_ready(out_ready));
 always #5 clk=~clk;
 integer cycle=0,errors=0,head=0,tail=0,accepted=0,retired=0,aborted=0;
 integer h1=0,h2=0,h3=0,mathvalue,samplevalue;
 reg a=0,b=0,c=0,ra,rb,rc,push,pop,blocked=0;
 reg [7:0] held;
 reg [12:0] da,db,dc,queue[0:4095];
 integer born[0:4095],reset_masks[0:7];
 integer replaces=0,stalls=0,invalid_noise=0,minimum=0,maximum=0,pulses=0;
 integer i,j,m,seed=32'h71f423ab,rv;
 task behavior_fail;
 input [255:0] rule;
 begin errors=errors+1; if(errors<40) $display("FAIL BEHAVIOR rule=%0s cycle=%0d",rule,cycle); end
 endtask
 task checker_fail;
 input [255:0] rule;
 begin errors=errors+1; $display("CHECKER_FAIL rule=%0s cycle=%0d",rule,cycle); end
 endtask
 task coverage_fail;
 input [255:0] rule;
 begin errors=errors+1; $display("COVERAGE_FAIL rule=%0s",rule); end
 endtask
 task check_ports;
 begin
  if(in_ready !== (!a || !b || !c || out_ready)) behavior_fail("exact_ready");
  if(out_valid !== c) behavior_fail("exact_valid");
  if(c && out_data !== dc) behavior_fail("slot_data_or_hold");
  if(c && head<tail && out_data !== queue[head]) behavior_fail("accepted_history_order");
 end
 endtask
 task step;
 input reset_now,offer;
 input integer sample;
 input ready_now;
 begin
  @(negedge clk);
  rst=reset_now;out_ready=ready_now;
  if(blocked && !reset_now) begin in_valid=1;x=held; end
  else begin in_valid=offer;x=sample; end
  #1;if(cycle>0) check_ports;
  @(posedge clk);
  cycle=cycle+1;
  rc=!c || out_ready;rb=!b || rc;ra=!a || rb;
  push=in_valid && ra;pop=c && out_ready;
  blocked=!rst && in_valid && (in_ready !== 1'b1);held=x;
  if(rst) begin
   reset_masks[{c,b,a}]=reset_masks[{c,b,a}]+1;
   aborted=aborted+tail-head;head=tail;a=0;b=0;c=0;h1=0;h2=0;h3=0;
  end else begin
   if(c && !out_ready) stalls=stalls+1;
   if(a && b && c && pop && push) replaces=replaces+1;
   if(!in_valid && ra) invalid_noise=invalid_noise+1;
   if(pop) begin
    if(head>=tail) checker_fail("queue_underflow");
    else begin
     if(cycle-born[head]<3) behavior_fail("transfer_age");
     head=head+1;retired=retired+1;
    end
   end
   if(push) begin
    samplevalue=x; // signed port sign-extends into integer
    mathvalue=3*samplevalue-5*h1+7*h2-2*h3;
    if(mathvalue==-2169) minimum=minimum+1;
    if(mathvalue==2166) maximum=maximum+1;
    if(tail>=4096) checker_fail("queue_overflow");
    else begin queue[tail]=mathvalue & 8191;born[tail]=cycle;tail=tail+1; end
    accepted=accepted+1;
    h3=h2;h2=h1;h1=samplevalue;
   end
   // Descending assignments consume the OLD predecessor slots.
   if(rc) begin c=b;if(b) dc=db;end
   if(rb) begin b=a;if(a) db=da;end
   if(ra) begin a=in_valid;if(push) da=mathvalue & 8191;end
  end
  if(tail-head != a+b+c) checker_fail("queue_slot_conservation");
  if(accepted != retired+aborted+tail-head) checker_fail("transaction_conservation");
  #1;check_ports;
 end
 endtask
 task pulse_reset;
 begin
  // Called one ns after rising edge: pulse ends before next rising edge.
  #1;rst=1;#1;check_ports;#1;rst=0;#0.1;check_ports;pulses=pulses+1;
 end
 endtask
 initial begin
  for(i=0;i<8;i=i+1) reset_masks[i]=0;
  step(1,0,0,0);
  // Every nonempty three-slot occupancy pattern is reset, including stalled output.
  for(m=1;m<8;m=m+1) begin
   step(1,0,0,1);
   step(0,(m & 4)!=0,37,1);step(0,(m & 2)!=0,-91,1);step(0,(m & 1)!=0,113,1);
   if({c,b,a} != m) coverage_fail("reset_pattern_setup");
   step(1,1,-47,0);step(0,1,23,1);
   for(j=0;j<4;j=j+1) step(0,0,51+j,1);
  end
  // Both-sign impulse tails, with accepted zeros (not invalid cycles).
  for(m=0;m<2;m=m+1) begin
   step(1,0,0,1);step(0,1,m==0?127:-128,1);
   for(j=0;j<6;j=j+1) step(0,1,0,1);
  end
  // Exact signed13 extrema, continuous throughput.
  step(1,0,0,1);
  for(i=0;i<48;i=i+1) step(0,1,(i%2)==0?127:-128,1);
  // Invalid data must not update accepted history.
  for(i=0;i<16;i=i+1) begin step(0,0,i*13-120,1);step(0,1,i*7-61,1);end
  for(i=0;i<5;i=i+1) step(0,0,91,1);
  if(a || b || c || (h1==0 && h2==0 && h3==0)) coverage_fail("history_pulse_setup");
  pulse_reset;step(0,1,-117,1);
  for(i=0;i<4;i=i+1) step(0,0,73+i,1);
  step(1,0,0,0);
  step(0,1,39,0);step(0,1,-72,0);step(0,1,105,0);
  if(!(a && b && c)) coverage_fail("full_pulse_setup");
  pulse_reset;
  // Fourth held token differs from all occupied samples.
  for(i=0;i<12;i=i+1) step(0,1,-119,0);
  for(i=0;i<48;i=i+1) step(0,1,i*5-112,1);
  for(i=0;i<550;i=i+1) begin
   rv=$random(seed);
   step(i==173 || i==391,(rv & 3)!=0,(rv>>8), (rv & 12)!=0);
  end
  for(i=0;i<8;i=i+1) step(0,0,i+99,1);
  for(i=1;i<8;i=i+1) if(reset_masks[i]==0) coverage_fail("reset_mask");
  if(replaces<60) coverage_fail("continuous_full_replacement");
  if(stalls<12 || invalid_noise<16 || pulses!=2) coverage_fail("stalls_noise_pulses");
  if(minimum==0 || maximum==0) coverage_fail("signed13_extrema");
  if(head!=tail) coverage_fail("final_drain");
  $display("COVERAGE cycles=%0d accepted=%0d retired=%0d aborted=%0d replaces=%0d stalls=%0d noise=%0d minimum=%0d maximum=%0d pulses=%0d",cycle,accepted,retired,aborted,replaces,stalls,invalid_noise,minimum,maximum,pulses);
  for(i=0;i<8;i=i+1) $display("COVERAGE reset_mask=%0d count=%0d",i,reset_masks[i]);
  if(errors==0) $display("TEST PASSED");
  else $display("TEST FAILED: errors=%0d",errors);
  $finish;
 end
 initial begin #200000; $display("CHECKER_FAIL watchdog");$display("TEST FAILED");$finish;end
endmodule
