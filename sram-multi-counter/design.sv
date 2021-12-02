// Code your design here
//command defines
`define LOAD  3'b000
`define CLEAR 3'b001
`define INC   3'b010
`define DEC   3'b011
`define READ  3'b100

`include "dpsram.sv"

module sram_multi_counter (
  input logic clk,rst,
  input logic valid,
  input logic [7:0] id,
  input logic [7:0] data,
  input logic [2:0] cmd ,
  output logic [7:0] output_data,
  output logic [7:0] output_id,
  output logic output_valid
);
  
  //Wires for dual port sram
  logic read_enable,write_enable;
  logic [7:0] read_data,dummy_data,write_data,read_addr,write_addr;

   logic [11:0] cmd_state_p0, cmd_state_p1, cmd_state_p2,cmd_state_p3;
   

  //Combine valid and command into 1 field
  //for use in building state vector (see next block)
  always_comb 
     if (valid)
       cmd_state_p0 = {valid,cmd,id};
     else
       cmd_state_p0 = 12'b0;

  //Build State vector from previous command history
  //State vector can be {cmd_state_p1,cmd_state_p2,..}
  always_ff @(posedge clk) begin
     cmd_state_p1 <= cmd_state_p0;
     cmd_state_p2 <= cmd_state_p1;
     cmd_state_p3 <= cmd_state_p2;     
  end
   
  //Port 0, read port
  //Port 1, write port
  dpsram #(256,8) mem
  (.clk0(clk),
   .clk1(clk),
   
   .en0(read_enable),
   .en1(write_enable),
   
   .wen0(1'b0), //port 0 is always read
   .wen1(1'b1), //port 1 is always write
  
   .din0(8'b0),
   .din1(write_data),
   
   .addr0(read_addr),
   .addr1(write_addr),
   
   .dout0(read_data),
   .dout1(dummy_data)
  );
  
  typedef struct packed {
    logic valid ;
    logic [7:0] data ;
    logic [7:0] id ;
    logic [2:0] cmd ;
  } pipe_input_t ;

  logic hazard_p0, hazard_p1;
  logic [7:0] data_fwd;
  
  logic valid_p1,output_valid_w;
  logic [7:0] data_p1;
  logic [7:0] id_p1;
  logic [2:0] cmd_p1;

  pipe_input_t pipe_input_p0, pipe_input_p1 ;

  always_comb begin
    pipe_input_p0.valid = valid ;
    pipe_input_p0.data = data ;
    pipe_input_p0.id = id ;
    pipe_input_p0.cmd = cmd ;
  end
  
  always_ff @(posedge clk)
    pipe_input_p1 <= pipe_input_p0;

   logic hazard_state;

  //hazard_state toggles based on hazard_p1
  always_ff @(posedge clk) 
     if (rst)
       hazard_state <= 0;
     else
       if (hazard_p1)
         hazard_state <= 1;
       else
         hazard_state <= 0;

  //Generate pipe stage signals
  always_ff @(posedge clk)
    if (rst) begin
      hazard_p1 <= 0;
      valid_p1 <= 0;
      id_p1 <= 0;
    end
  else
    begin
      valid_p1 <= pipe_input_p0.valid;
      if (valid) begin
         hazard_p1 <= hazard_p0;
	 id_p1 <= id ;
         data_p1 <= data;
         cmd_p1 <= cmd ;
      end
    end
  
  //Cycle p0, always dispatch read
  always_comb begin

    //Default values
    read_addr = 0;
    read_enable = 0 ;

    if (valid) begin
      read_addr = id;
      read_enable = 1;
    end
    
    //Hazard detect, Read after Write
    //Same id in cycle 0 as in cycle 1
    //and both ids are valid
    //operation requiring Read (Read, Inc, Dec) in p0 and 
    //operation requiring Write (Load,Clear,Inc,Dec) in p1
    hazard_p0 = (id == id_p1) & valid_p1 & valid & 
                (cmd == `READ | cmd == `INC | cmd == `DEC) &
                (cmd_p1 == `LOAD | cmd_p1 == `CLEAR | cmd_p1 == `INC | cmd_p1 == `DEC) ;

    //hazard_p0 = (id == id_p1) & valid_p1 & valid ;

    output_valid_w = 0;
    if (cmd == `READ) 
        output_valid_w = 1;
  end

  always_ff @(posedge clk)
    if (rst)
      output_valid <= 0;
    else
      output_valid <= output_valid_w;

  assign output_id = id_p1;
  assign output_data = hazard_p1 ? write_data : read_data ;

  //cycle p1, write into SRAM
  always_comb begin

    //Default values
    write_enable = 0;
    
    if (valid_p1 & (cmd_p1 == `LOAD | cmd_p1 == `CLEAR | cmd_p1 == `INC | cmd_p1 == `DEC ) ) begin

      write_enable = 1;
      write_addr = id_p1;
      
      case(cmd_p1)
        `LOAD: write_data = data_p1;
        `CLEAR: write_data = 0;
        `INC: begin
          if (hazard_p1)
            write_data = data_fwd + 1'b1;
          else
	    write_data = read_data + 1'b1;
         end
        `DEC: begin
          if (hazard_p1)
            write_data = data_fwd - 1'b1;
          else
            write_data = read_data - 1'b1;
          end

        default: ;
       endcase
    end
  end
  
  always_ff @(posedge clk)
    if (rst) 
      data_fwd <= 0;
  else 
    if (valid_p1)
  	  data_fwd <= write_data;
  
endmodule
