module tb_sync_fifo;

reg clk;
reg rst;
reg wr_en;
reg rd_en;
reg [7:0] din;
wire [7:0] dout;
wire full;
wire empty;

fifo_8x8 dut (
    .clk(clk),
    .rst(rst),
    .wr_en(wr_en),
    .rd_en(rd_en),
    .din(din),
    .dout(dout),
    .full(full),
    .empty(empty)
);

always #5 clk = ~clk;

initial begin
    $dumpfile("dump.vcd");
    $dumpvars(0, tb_sync_fifo);
    clk = 0;
    rst = 1;
    wr_en = 0;
    rd_en = 0;
    din = 8'h00;

    #20; rst = 0;

    #10; wr_en = 1; din = 8'hAA;
    #10; din = 8'hBB;
    #10; din = 8'hCC;
    #10; wr_en = 0;

    #20;
    rd_en = 1;
    #10;
    #10;
    #10;
    rd_en = 0;

    #50;
    $finish;
end

endmodule
