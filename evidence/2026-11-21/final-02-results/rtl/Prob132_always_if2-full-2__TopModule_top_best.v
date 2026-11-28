`timescale 1ns/1ps
// @latency 0
// Inherited fixed logical latency from transparent typed child wiring; not measured timing.
module TopModule_top (
    input wire cpu_overheated,
    output wire shut_off_computer,
    input wire arrived,
    input wire gas_tank_empty,
    output wire keep_driving
);
    TopModule u_TopModule (
        .cpu_overheated(cpu_overheated),
        .shut_off_computer(shut_off_computer),
        .arrived(arrived),
        .gas_tank_empty(gas_tank_empty),
        .keep_driving(keep_driving)
    );
endmodule
