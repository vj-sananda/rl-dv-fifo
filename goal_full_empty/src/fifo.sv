// Code your design here
//Write in verilog, not sure of system verilog support
//in FPGA synthesis

module fifo (/*AUTOARG*/
   // Outputs
   full, empty, dataout, count,
   // Inputs
   clk, rst, push, pop, datain,select,reward
   );

   //------------------------------
   parameter width=8;
   parameter depth=4;
   parameter log2depth=2;
   //------------------------------
   input     clk,rst;
   input     push,pop,select;
   input reward;
   input [width-1:0] datain;

   output    full,empty;
   output [log2depth:0] count;
   output [width-1:0] dataout;
   //------------------------------
   reg [width-1:0]    mem[0:depth-1];
   //------------------------------

   integer reward ;
   reg [log2depth-1:0]  rd_ptr,wr_ptr;
   reg [log2depth:0] 	cnt, cnt_d1 ,cnt_w ;
   reg 			full, empty;

   wire [log2depth:0] count = cnt_w ;

   /*
   always @(posedge clk)
     if (cnt_d1 > cnt)
        assert ( cnt_d1 - cnt >= 1);

   always @(posedge clk)
     if ( cnt > cnt_d1 )
        assert ( cnt - cnt_d1 >= 1);
   */

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
         empty = 0;
       end
     endcase // case({push,pop})

   wire [width-1:0]	       dataout = mem[rd_ptr] ;

endmodule // fifo
