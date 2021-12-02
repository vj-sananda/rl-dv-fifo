`ifndef DPSRAM_MODULE
`define DPSRAM_MODULE

//Dual port SRAM
//Parameters N = Size
//           DW = Data width
//           AW = Address width ($clog2(N))
module dpsram #( parameter int N = 16, 
                           int DW = 32,
                		   int AW = $clog2(N) )
  	(
      //Inputs
      input logic clk0,clk1,en0,en1,wen0,wen1,
      input logic [DW-1:0] din0,din1,
      input logic [AW-1:0] addr0,addr1,
      
      //Outputs
      output logic [DW-1:0] dout0,dout1
    );
  
  
  logic [DW-1:0] mem [0:N-1];
  
  always @(posedge clk0) 
    if ( en0 ) begin
      if (wen0)
        mem[addr0] <= din0;
      else
        dout0 <= mem[addr0];
    end
    
  always @(posedge clk1)
     if( en1) begin
       if (wen1)
         mem[addr1] <= din1;
       else
         dout1 <= mem[addr1];
    end
    
endmodule

`endif

