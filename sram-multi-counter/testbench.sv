// Code your testbench here
// or browse Examples
module tb;

  bit clk = 0 ;
  always #5 clk = ~clk ;

  logic   rst;

  logic [7:0] id, data, output_data ;
  logic output_valid, valid;
  logic [2:0] cmd ;
  bit b2b_switch = 1;

  class op_transaction ;
    rand bit [7:0] id ;
    rand bit [7:0] data ;
    rand bit [2:0] op ;
  endclass

  sram_multi_counter dut (.*);

  initial begin
    int i;

    $dumpfile("dump.vcd");
    $dumpvars;

    initialize_inputs();
    reset();

    for (i=0;i<10;i=i+1) begin
      init_counter(i,-1,b2b_switch);
    end

    for (i=0;i<10;i=i+1) begin
      inc_counter(i,b2b_switch);
    end

    for (i=0;i<10;i=i+1) begin
      read_counter(i,b2b_switch);
    end

    for (i=0;i<10;i=i+1) begin
      dec_counter(i,b2b_switch);
    end

    for (i=0;i<10;i=i+1) begin
      read_counter(i,b2b_switch);
    end

    quiet();

    for (i=0;i<10;i=i+1) begin
      init_counter(i,-1,b2b_switch);
      inc_counter(i,b2b_switch);
      inc_counter(i,b2b_switch);
      read_counter(i,b2b_switch);
      dec_counter(i,b2b_switch);
      read_counter(i,b2b_switch);
    end

    quiet();

    $finish;

  end

  task tick(int n=1);
    repeat(n) @(posedge clk);
  endtask

  task rand_delay();
    tick( $urandom_range(10,20));
  endtask

  task initialize_inputs();
    rst = 0;
    valid = 0;
    data = 0;
    id = 0;
    cmd = 0;
  endtask

  task quiet();
    tick();
  endtask

  task init_counter(int _id, int _data = -1 ,bit b2b=1 );
    op_transaction xact  ;
    xact = new ;

    tick();

    xact.randomize() with { id == _id ; op == `LOAD; } ;

    if (_data == -1)
      xact.data = _id + 8'h10;
    else
      xact.data = _data;

    valid <= 1;
    id <= xact.id;
    cmd <= xact.op;
    data <= xact.data;

    if (~b2b) begin
      tick();
      valid <= 0;
    end

  endtask

  task inc_counter(int _id,bit b2b=1);
    op_transaction xact  ;
    xact = new ;

    tick();

    xact.randomize() with { id == _id ; op == `INC; } ;

    valid <= 1;
    id <= xact.id;
    cmd <= xact.op;
    if (~b2b) begin
      tick();
      valid <= 0;
    end
  endtask


  task dec_counter(int _id,bit b2b=1);
    op_transaction xact  ;
    xact = new ;

    tick();

    xact.randomize() with { id == _id ; op == `DEC ; } ;
    valid <= 1;
    id <= xact.id;
    cmd <= xact.op;
    if (~b2b) begin
      tick();
      valid <= 0;
    end
  endtask

  task read_counter(int _id, bit b2b=1);
    op_transaction xact  ;
    xact = new ;

    tick();

    xact.randomize() with { id == _id ; op == `READ ; } ;
    valid <= 1;
    id <= xact.id;
    cmd <= xact.op;
    if (~b2b) begin
      tick();
      valid <= 0;
    end
  endtask

  task reset();
    tick();
    rst <= 1;
    tick(5);
    rst <= 0;
  endtask
endmodule
