`timescale 1ns/1ps

module tb_counter;

reg clk;
reg rst;
reg up_en;
reg down_en;
wire [3:0] count;

counter dut (
    .clk(clk),
    .rst(rst),
    .up_en(up_en),
    .down_en(down_en),
    .count(count)
);

initial begin
    $dumpfile("dump.vcd");
    $dumpvars(0, tb_counter);
    
    clk = 0;
    rst = 0;
    up_en = 0;
    down_en = 0;
    
    // 1. Reset
    rst = 1;
    #10;
    rst = 0;
    #10;
    
    // 2. Count up from 0 to 8 (8 cycles)
    up_en = 1;
    down_en = 0;
    repeat(8) #10;
    
    // 3. Count down from 8 to 4 (4 cycles)
    up_en = 0;
    down_en = 1;
    repeat(4) #10;
    
    // 4. Both enabled - count holds (2 cycles)
    up_en = 1;
    down_en = 1;
    repeat(2) #10;
    
    // 5. Count up to 15
    up_en = 1;
    down_en = 0;
    repeat(11) #10;
    
    // 6. Overflow: count up from 15 to 0
    up_en = 1;
    down_en = 0;
    #10;
    
    // 7. Count up to 5
    up_en = 1;
    down_en = 0;
    repeat(5) #10;
    
    // 8. Reset while count > 0
    rst = 1;
    #10;
    rst = 0;
    #10;
    
    // 9. Count up to 3
    up_en = 1;
    down_en = 0;
    repeat(3) #10;
    
    // 10. Underflow: count down from 3 to 2 to 1 to 0 to 15
    up_en = 0;
    down_en = 1;
    repeat(4) #10;
    
    #20;
    $finish;
end

always #5 clk = ~clk;

endmodule