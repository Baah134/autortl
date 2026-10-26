"""Materialize legal scoreboard-driver controls; never launch vendor/model jobs.

Call save(fresh_output) to obtain rows containing source_paths, tb_path, top,
expected_pass and required_coverage. Root may run each through xsim_run serially,
then call coverage_verdict(raw, row). Missing stimulus coverage is separate from
DUT behavioral failure: these monitors never fail a correct old DUT merely
because the old driver did not create bubbles or off-edge pulses.
"""
import hashlib
import json
import re
from pathlib import Path

from autortl.spec import ModuleSpec, Port, ResetSpec
from autortl.tbgen import generate_scoreboard_tb


def channel(name, latency=1, *, renamed=False, kind='sync'):
    reset = 'reset_n' if renamed else 'rst'
    iv, ir, ov, ore = (('request_valid', 'request_ready', 'response_valid', 'response_ready')
                       if renamed else ('in_valid', 'in_ready', 'out_valid', 'out_ready'))
    return ModuleSpec(name, 'Each accepted pair returns its modulo8 sum and xor',
        [Port('clk', 'input', 1), Port(reset, 'input', 1),
         Port('a', 'input', 8), Port('b', 'input', 5),
         Port('y', 'output', 8), Port('z', 'output', 8),
         Port(iv, 'input', 1, protocol='valid_ready'),
         Port(ir, 'output', 1, protocol='valid_ready'),
         Port(ov, 'output', 1, protocol='valid_ready'),
         Port(ore, 'input', 1, protocol='valid_ready')],
        latency=latency, compare_mode='scoreboard',
        reset=ResetSpec(signal=reset, kind=kind, active_high=not renamed, duration_cycles=3))


def _signals(spec):
    controls = [p for p in spec.ports if p.protocol == 'valid_ready']
    return tuple(next(p.name for p in controls if p.direction == direction and p.name.endswith(suffix))
                 for direction, suffix in [('input','valid'), ('output','ready'), ('output','valid'), ('input','ready')])


def _source(spec, mode):
    iv, ir, ov, ore = _signals(spec)
    rst = spec.reset.signal
    condition = rst if spec.reset.active_high else '!'+rst
    reset_edge = 'posedge' if spec.reset.active_high else 'negedge'
    sensitivity = 'posedge clk' + (f' or {reset_edge} {rst}' if spec.reset.kind == 'async' else '')
    header = f'''`timescale 1ns/1ps
module {spec.name}(input clk,{rst},input [7:0] a,input [4:0] b,
 input {iv},{ore},output {ir},output {'wire' if mode=='forward' else 'reg'} {ov},
 output {'wire' if mode=='forward' else 'reg'} [7:0] y,z);
'''
    if mode == 'forward':
        return header+f'assign {ir}={ore}; assign {ov}={iv}; assign y=a+b; assign z=a^b;\nendmodule\n'
    if mode == 'busy':
        return header+f'''reg [1:0] busy;
assign {ir}=(busy==0) && (!{ov} || {ore});
always @({sensitivity}) begin
 if({condition}) begin busy<=0;{ov}<=0;y<=0;z<=0;end
 else begin
  if({ov} && {ore}) {ov}<=0;
  if(busy!=0) begin busy<=busy-1'b1;if(busy==1) {ov}<=1;end
  if({iv} && {ir}) begin busy<=3;{ov}<=0;y<=a+b;z<=a^b;end
 end
end
endmodule
'''
    warm_decl = 'reg [5:0] warm;\n' if mode == 'blocked' else ''
    warm_gate = '(warm>=17) && ' if mode == 'blocked' else ''
    warm_reset = 'warm<=0;' if mode == 'blocked' else ''
    warm_advance = 'if(warm<17) warm<=warm+1\'b1;' if mode == 'blocked' else ''
    return header+warm_decl+f'''assign {ir}={warm_gate}(!{ov} || {ore});
always @({sensitivity}) begin
 if({condition}) begin {warm_reset}{ov}<=0;y<=0;z<=0;end
 else begin
  {warm_advance}
  if({ir}) begin {ov}<={iv};if({iv}) begin y<=a+b;z<=a^b;end end
 end
end
endmodule
'''


def _monitor(tb, spec, label, count):
    """Observe wires/clock independently; no DUT or driver signal is changed."""
    iv, ir, ov, ore = _signals(spec)
    rst = spec.reset.signal
    asserted = int(spec.reset.active_high)
    declarations = f'''integer probe_cycle,probe_accepted,probe_retired,probe_invalid_before_accept;
integer probe_invalid_followed_by_accept,probe_noise_changes,probe_blocked,probe_longest_block;
integer probe_block_run,probe_release_on_bubble,probe_pulses,probe_edge_resets;
integer probe_producer_errors,probe_timing_errors;
reg probe_waiting,probe_invalid_pending,probe_invalid_seen,probe_started,probe_pulse_open;
reg [12:0] probe_held_payload,probe_last_invalid;
reg [14:0] probe_pulse_inputs;
realtime probe_last_fall,probe_assert_time;
initial begin
 probe_cycle=0;probe_accepted=0;probe_retired=0;probe_invalid_before_accept=0;
 probe_invalid_followed_by_accept=0;probe_noise_changes=0;probe_blocked=0;probe_longest_block=0;
 probe_block_run=0;probe_release_on_bubble=0;probe_pulses=0;probe_edge_resets=0;
 probe_producer_errors=0;probe_timing_errors=0;probe_waiting=0;probe_invalid_pending=0;
 probe_invalid_seen=0;probe_started=0;probe_pulse_open=0;probe_held_payload=0;
 probe_last_invalid=0;probe_pulse_inputs=0;probe_last_fall=0;probe_assert_time=0;
end
always @(negedge _autortl_clk) probe_last_fall=$realtime;
always @(posedge _autortl_clk) begin
 if({rst} === 1'b{asserted}) begin
  probe_waiting=0;
  if(probe_started) begin
   probe_edge_resets=probe_edge_resets+1;
   $display("FAIL DRIVER pulse overlaps rising edge");probe_timing_errors=probe_timing_errors+1;
  end
 end else begin
  probe_started=1;
  if(probe_pulse_open) begin
   $display("FAIL DRIVER pulse still open at rising edge");probe_timing_errors=probe_timing_errors+1;
  end
  if(probe_waiting) begin
   if({iv} !== 1'b1 || {{a,b}} !== probe_held_payload) begin
    $display("FAIL DRIVER producer changed blocked offer cycle=%0d",probe_cycle);
    probe_producer_errors=probe_producer_errors+1;
   end
   if({ir} === 1'b1 && probe_cycle%5==0) probe_release_on_bubble=probe_release_on_bubble+1;
  end
  if({iv} === 1'b0 && probe_accepted<{count}) begin
   probe_invalid_before_accept=probe_invalid_before_accept+1;probe_invalid_pending=1;
   if(probe_invalid_seen && {{a,b}} !== probe_last_invalid) probe_noise_changes=probe_noise_changes+1;
   probe_invalid_seen=1;probe_last_invalid={{a,b}};
  end
  if({iv} === 1'b1 && {ir} === 1'b1) begin
   probe_accepted=probe_accepted+1;
   if(probe_invalid_pending) probe_invalid_followed_by_accept=probe_invalid_followed_by_accept+1;
   probe_invalid_pending=0;
  end
  if({ov} === 1'b1 && {ore} === 1'b1) probe_retired=probe_retired+1;
  probe_waiting=({iv} === 1'b1 && {ir} === 1'b0);probe_held_payload={{a,b}};
  if(probe_waiting) begin
   probe_blocked=probe_blocked+1;probe_block_run=probe_block_run+1;
   if(probe_block_run>probe_longest_block) probe_longest_block=probe_block_run;
  end else probe_block_run=0;
  probe_cycle=probe_cycle+1;
 end
end
always @({rst}) begin
 if(probe_started && {rst} === 1'b{asserted}) begin
  probe_pulses=probe_pulses+1;probe_pulse_open=1;probe_assert_time=$realtime;
  probe_pulse_inputs={{a,b,{iv},{ore}}};
  if($realtime-probe_last_fall < 0.99 || $realtime-probe_last_fall > 1.01) begin
   $display("FAIL DRIVER pulse assertion phase");probe_timing_errors=probe_timing_errors+1;
  end
 end else if(probe_pulse_open && {rst} === 1'b{1-asserted}) begin
  if($realtime-probe_assert_time < 1.99 || $realtime-probe_assert_time > 2.01 ||
     $realtime-probe_last_fall < 2.99 || $realtime-probe_last_fall > 3.01 ||
     {{a,b,{iv},{ore}}} !== probe_pulse_inputs) begin
   $display("FAIL DRIVER pulse duration or held inputs");probe_timing_errors=probe_timing_errors+1;
  end
  probe_pulse_open=0;
 end
end
always @(a or b or {iv} or {ore}) begin
 if(probe_pulse_open && {{a,b,{iv},{ore}}} !== probe_pulse_inputs) begin
  $display("FAIL DRIVER input changed during pulse");probe_timing_errors=probe_timing_errors+1;
 end
end
'''
    marker='initial begin\n_autortl_errors = 0;'
    assert tb.count(marker)==1
    tb=tb.replace(marker,declarations+marker,1)
    summary=f'''#0.001; // let the independent observation processes finish this edge
$display("DRIVER_COVERAGE case={label} accepted=%0d retired=%0d invalid_before_accept=%0d invalid_followed_by_accept=%0d noise_changes=%0d blocked=%0d longest_block=%0d release_on_bubble=%0d pulses=%0d edge_resets=%0d producer_errors=%0d timing_errors=%0d",probe_accepted,probe_retired,probe_invalid_before_accept,probe_invalid_followed_by_accept,probe_noise_changes,probe_blocked,probe_longest_block,probe_release_on_bubble,probe_pulses,probe_edge_resets,probe_producer_errors,probe_timing_errors);
if(probe_invalid_before_accept==0 || probe_invalid_followed_by_accept==0 || probe_noise_changes==0) $display("COVERAGE_MISSING driver invalid traffic");
if(probe_producer_errors || probe_timing_errors) _autortl_errors=_autortl_errors+probe_producer_errors+probe_timing_errors;
'''
    marker='if (_autortl_errors == 0) $display("TEST PASSED");'
    assert tb.count(marker)==1
    return tb.replace(marker,summary+marker,1)


def cases():
    rows=[]
    for label,mode,latency,renamed,kind in [
        ('forward_zero','forward',0,False,'sync'),
        ('busy_sequential','busy',4,False,'sync'),
        ('prolonged_block','blocked',1,False,'sync'),
        ('renamed_active_low','elastic',1,True,'sync'),
        ('async_no_pulse','elastic',1,False,'async')]:
        spec=channel('driver_'+label,latency,renamed=renamed,kind=kind)
        stimulus=[{'a':a,'b':b} for a,b in [(0,0),(255,31),(128,17)]]
        stimulus += [{'a':(i*37+3)&255,'b':(i*11+5)&31} for i in range(37)]
        expected=[{'y':(row['a']+row['b'])&255,'z':row['a']^row['b']} for row in stimulus]
        tb=_monitor(generate_scoreboard_tb(spec,stimulus,expected),spec,label,len(stimulus))
        required={name:{'min':0,'max':0} for name in ('producer_errors','timing_errors','edge_resets')}
        required.update({name:{'min':len(stimulus),'max':len(stimulus)} for name in ('accepted','retired')})
        required.update({name:{'min':1} for name in ('invalid_before_accept','invalid_followed_by_accept','noise_changes','blocked')})
        required['pulses']={'min':0,'max':0} if kind=='async' else {'min':1}
        if mode=='blocked':
            required['longest_block']={'min':12}
            required['release_on_bubble']={'min':1}
        rows.append({'name':label,'spec':spec,'source':_source(spec,mode),'tb':tb,
                     'stimulus':stimulus,'expected':expected,'required_coverage':required})
    return rows


def save(directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
    rows=[]
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    for case in cases():
        target=directory/case['name'];target.mkdir()
        source=target/'dut.v';tb=target/'tb.v';payload=target/'stimulus.json'
        source.write_bytes(case['source'].encode('utf-8'));tb.write_bytes(case['tb'].encode('utf-8'))
        payload.write_text(json.dumps({'stimulus':case['stimulus'],'expected':case['expected']},indent=2),encoding='utf-8')
        rows.append({'name':case['name'],'top':case['spec'].name+'_tb','expected_pass':True,
            'source_paths':[str(source.resolve())],'tb_path':str(tb.resolve()),
            'files':{str(p.resolve()):sha(p) for p in (source,tb,payload)},
            'required_coverage':case['required_coverage'],'reset_kind':case['spec'].reset.kind,
            'latency':case['spec'].latency})
    (directory/'manifest.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    return rows


def coverage_verdict(raw, row):
    lines=re.findall(r'^DRIVER_COVERAGE case='+re.escape(row['name'])+r' ([^\n]+)$',raw,re.MULTILINE)
    if len(lines)!=1:return {'ok':False,'counts':{},'missing':['one complete DRIVER_COVERAGE line required']}
    counts={name:int(value) for name,value in re.findall(r'(\w+)=(\d+)',lines[0])}
    missing=[]
    for name,limits in row['required_coverage'].items():
        if name not in counts or counts[name]<limits['min'] or ('max' in limits and counts[name]>limits['max']):
            missing.append(name)
    return {'ok':not missing,'counts':counts,'missing':missing}
