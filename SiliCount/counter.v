module counter(
    input clk,
    input rst,
    input up_en,
    input down_en,
    output reg [3:0] count
);

always @(posedge clk) begin
    if (rst) begin
        count <= 4'b0000;
    end
    else if (up_en && !down_en) begin
        count <= count + 1;
    end
    else if (down_en && !up_en) begin
        count <= count - 1;
    end
end

endmodule