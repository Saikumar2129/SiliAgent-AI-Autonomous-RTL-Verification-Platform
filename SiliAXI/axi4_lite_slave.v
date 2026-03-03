module axi4_lite_slave #(
    parameter DATA_WIDTH = 32,
    parameter ADDR_WIDTH = 8
)(
    input wire clk,
    input wire rst,
    input  wire                    awvalid,
    output reg                     awready,
    input  wire [ADDR_WIDTH-1:0]   awaddr,
    input  wire                    wvalid,
    output reg                     wready,
    input  wire [DATA_WIDTH-1:0]   wdata,
    input  wire [DATA_WIDTH/8-1:0] wstrb,
    output reg                     bvalid,
    input  wire                    bready,
    output reg  [1:0]              bresp,
    input  wire                    arvalid,
    output reg                     arready,
    input  wire [ADDR_WIDTH-1:0]   araddr,
    output reg                     rvalid,
    input  wire                    rready,
    output reg  [DATA_WIDTH-1:0]   rdata,
    output reg  [1:0]              rresp
);
    reg [DATA_WIDTH-1:0] mem [0:255];
    reg [ADDR_WIDTH-1:0] write_addr;
    reg write_addr_valid;
    integer i;

    always @(posedge clk) begin
        if (rst) begin
            awready <= 0; wready <= 0; bvalid <= 0; bresp <= 0;
            arready <= 0; rvalid <= 0; rdata <= 0; rresp <= 0;
            write_addr <= 0; write_addr_valid <= 0;
            for (i = 0; i < 256; i = i + 1) mem[i] <= 0;
        end else begin
            awready <= 0; wready <= 0; arready <= 0;

            if (awvalid && !write_addr_valid) begin
                awready <= 1;
                write_addr <= awaddr;
                write_addr_valid <= 1;
            end

            if (wvalid && write_addr_valid) begin
                wready <= 1;
                mem[write_addr] <= wdata;
                write_addr_valid <= 0;
                bvalid <= 1;
                bresp <= 2'b00;
            end

            if (bvalid && bready) bvalid <= 0;

            if (arvalid && !rvalid) begin
                arready <= 1;
                rdata <= mem[araddr];
                rresp <= 2'b00;
                rvalid <= 1;
            end

            if (rvalid && rready) rvalid <= 0;
        end
    end
endmodule