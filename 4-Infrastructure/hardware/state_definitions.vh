// state_definitions.vh — Shared S3C scalar state machine encoding
`ifndef STATE_DEFINITIONS_VH
`define STATE_DEFINITIONS_VH

localparam STATE_SUPERPOSED           = 4'd0;
localparam STATE_SCOUTING             = 4'd1;
localparam STATE_MEASURE_LOCAL_NEED   = 4'd2;
localparam STATE_COLLAPSED_PROFILE     = 4'd3;
localparam STATE_EXECUTE              = 4'd4;
localparam STATE_RECEIPT              = 4'd5;
localparam STATE_AMPLITUDE_UPDATE     = 4'd6;
localparam STATE_QUERY_COLLECTIVE     = 4'd7;
localparam STATE_COLLECTIVE_RESPONSE  = 4'd8;
localparam STATE_QUERY_LLM            = 4'd9;
localparam STATE_DIRECTED             = 4'd10;
localparam STATE_HOLD                 = 4'd11;
localparam STATE_OPERATOR_ALERT       = 4'd12;
localparam STATE_LOW_POWER_PASSIVE    = 4'd13;
localparam STATE_QUARANTINE           = 4'd14;
localparam STATE_MIGRATE              = 4'd15;

`endif
