// Code your design here
//Write in verilog, not sure of system verilog support
//in FPGA synthesis

module fifo #(parameter depth = 8) 
  (/*AUTOARG*/
   // Outputs
   full, empty, dataout, count, full_posedge, empty_posedge,filled,
   // Inputs
   clk, rst, push, pop, datain
   );

   //------------------------------
   parameter width=8;
   parameter log2depth=$clog2(depth);
   //------------------------------
   input     clk,rst;
   input     push,pop;
   input [width-1:0] datain;

   output    full,empty,full_posedge,empty_posedge,filled;
   output [log2depth+3:0] count;
   output [width-1:0] dataout;
   //------------------------------
   reg [width-1:0]    mem[0:depth-1];
   //------------------------------

   integer reward ;
   reg [log2depth-1:0]  rd_ptr,wr_ptr;
   reg [log2depth:0] 	cnt, cnt_d1 ,cnt_w ;
   reg 			full, empty,full_d1,empty_d1,filled;
   wire full_posedge, empty_posedge;

   wire [log2depth+3:0] count ;
   assign count[log2depth:0] = cnt_w ;
  //Additional bits for count state
  //to garble actual count sampled by RL agent
   assign count[log2depth+3] = ^cnt_w ;
   assign count[log2depth+2] = &cnt_w ;
   assign count[log2depth+1] = |cnt_w ;   
   

   always @(posedge clk)
    if (rst) begin
      full_d1 <= 0;
      empty_d1 <= 1;
    end
    else begin
      full_d1 <= full;
      empty_d1 <= empty;
    end

   assign full_posedge = full &  ~full_d1 ;
   assign empty_posedge = empty & ~empty_d1;

  //filled flag 
   always @(posedge clk)
    if (rst)
      filled <= 0;
    else if (full_posedge)
      filled <= 1;
    else if (empty_posedge)
      filled <= 0;

   always @(posedge clk)
     if (rst)
       begin
        cnt <= 0;
        cnt_d1 <= 0;
        rd_ptr <=0 ;
        wr_ptr <=0 ;
       end
     else
      begin
        cnt <= cnt_w;
        cnt_d1 <= cnt ;

        if (push)
          begin
            mem[wr_ptr] <= datain;
            wr_ptr <= wr_ptr + 1;
          end

        if (pop)
          rd_ptr <= rd_ptr + 1 ;
       end // else: !if(rst)

   always @*
     casez({rst,push,pop})
       3'b000,3'b011:begin
        cnt_w = cnt ;
        full = (cnt_w == depth);
        empty = (cnt_w == 0);
       end

       3'b010: begin
        cnt_w = cnt + 1;
        full = (cnt_w == depth);
        empty = 0;
       end

       3'b001: begin
        cnt_w = cnt - 1;
        full = 0;
        empty = (cnt_w == 0);
       end

       3'b1zz: begin
         cnt_w = 0;
         full = 0;
         empty = 1;
       end
     endcase // case({push,pop})

   wire [width-1:0]	       dataout = mem[rd_ptr] ;

endmodule // fifo