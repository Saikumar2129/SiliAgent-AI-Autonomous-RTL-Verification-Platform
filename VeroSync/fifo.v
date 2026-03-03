module fifo_8x8 (
    input wire clk,
    input wire rst,
    input wire wr_en,
    input wire rd_en,
    input wire [7:0] din,
    output reg [7:0] dout,
    output wire full,
    output wire empty
);

    reg [7:0] mem [0:7];
    reg [2:0] wr_ptr;
    reg [2:0] rd_ptr;
    reg [3:0] count;

    assign full = (count == 4'd8);
    assign empty = (count == 4'd0);

    always @(posedge clk) begin
        if (rst) begin
            wr_ptr <= 3'd0;
            rd_ptr <= 3'd0;
            count <= 4'd0;
            dout <= 8'd0;
        end else begin
            if (wr_en && !full) begin
                mem[wr_ptr] <= din;
                wr_ptr <= wr_ptr + 1'd1;
            end

            if (rd_en && !empty) begin
                dout <= mem[rd_ptr];
                rd_ptr <= rd_ptr + 1'd1;
            end

            if ((wr_en && !full) && (rd_en && !empty)) begin
                count <= count;
            end else if (wr_en && !full) begin
                count <= count + 1'd1;
            end else if (rd_en && !empty) begin
                count <= count - 1'd1;
            end
        end
    end

endmodule