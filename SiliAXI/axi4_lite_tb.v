`timescale 1ns/1ns

module tb_axi4_lite;

reg clk, rst;
reg [7:0]  awaddr, araddr;
reg [31:0] wdata;
reg [3:0]  wstrb;
reg awvalid, wvalid, bready, arvalid, rready;
reg [31:0] read_data;

wire awready, wready, bvalid, arready, rvalid;
wire [31:0] rdata;
wire [1:0]  bresp, rresp;

axi4_lite_slave #(.DATA_WIDTH(32),.ADDR_WIDTH(8)) dut (
    .clk(clk),.rst(rst),
    .awvalid(awvalid),.awready(awready),.awaddr(awaddr),
    .wvalid(wvalid),.wready(wready),.wdata(wdata),.wstrb(wstrb),
    .bvalid(bvalid),.bready(bready),.bresp(bresp),
    .arvalid(arvalid),.arready(arready),.araddr(araddr),
    .rvalid(rvalid),.rready(rready),.rdata(rdata),.rresp(rresp)
);

always #5 clk = ~clk;

task axi_write;
    input [7:0]  addr;
    input [31:0] data;
    integer timeout;
    begin
        @(posedge clk); #1;
        awaddr = addr; awvalid = 1;
        timeout = 0;
        while (!awready && timeout < 20) begin @(posedge clk); #1; timeout=timeout+1; end
        awvalid = 0;
        @(posedge clk); #1;
        wdata = data; wstrb = 4'hF; wvalid = 1;
        timeout = 0;
        while (!wready && timeout < 20) begin @(posedge clk); #1; timeout=timeout+1; end
        wvalid = 0;
        bready = 1;
        timeout = 0;
        while (!bvalid && timeout < 20) begin @(posedge clk); #1; timeout=timeout+1; end
        @(posedge clk); #1;
        bready = 0;
        @(posedge clk); #1;
    end
endtask

task axi_read;
    input  [7:0]  addr;
    output [31:0] data;
    integer timeout;
    begin
        @(posedge clk); #1;
        araddr = addr; arvalid = 1;
        timeout = 0;
        while (!arready && timeout < 20) begin @(posedge clk); #1; timeout=timeout+1; end
        arvalid = 0;
        rready = 1;
        timeout = 0;
        while (!rvalid && timeout < 20) begin @(posedge clk); #1; timeout=timeout+1; end
        data = rdata;
        @(posedge clk); #1;
        rready = 0;
        @(posedge clk); #1;
    end
endtask

initial begin
    $dumpfile("dump.vcd");
    $dumpvars(0, tb_axi4_lite);
    clk=0; rst=1;
    awvalid=0; wvalid=0; bready=0; arvalid=0; rready=0;
    awaddr=0; wdata=0; wstrb=0; araddr=0;
    @(posedge clk); @(posedge clk);
    rst = 0;
    @(posedge clk);

    axi_write(8'h04, 32'hDEADBEEF);
    axi_read(8'h04, read_data);
    $display("Read 0x04: 0x%08h", read_data);

    axi_write(8'h08, 32'hCAFEBABE);
    axi_write(8'h0C, 32'h12345678);
    axi_write(8'h10, 32'hAABBCCDD);

    axi_read(8'h08, read_data); $display("Read 0x08: 0x%08h", read_data);
    axi_read(8'h0C, read_data); $display("Read 0x0C: 0x%08h", read_data);
    axi_read(8'h10, read_data); $display("Read 0x10: 0x%08h", read_data);

    axi_write(8'h04, 32'h11223344);
    axi_read(8'h04, read_data);
    $display("Read 0x04: 0x%08h", read_data);

    #100;
    $finish;
end

endmodule
