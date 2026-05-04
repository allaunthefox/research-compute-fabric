// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See VSparkleTangNano9KTop.h for the primary calling header

#ifndef VERILATED_VSPARKLETANGNANO9KTOP___024ROOT_H_
#define VERILATED_VSPARKLETANGNANO9KTOP___024ROOT_H_  // guard

#include "verilated.h"


class VSparkleTangNano9KTop__Syms;

class alignas(VL_CACHE_LINE_BYTES) VSparkleTangNano9KTop___024root final {
  public:

    // DESIGN SPECIFIC STATE
    // Anonymous structures to workaround compiler member-count bugs
    struct {
        VL_IN8(clk,0,0);
        VL_IN8(rst_n,0,0);
        VL_IN8(user_btn,0,0);
        VL_OUT8(led,5,0);
        VL_OUT8(uart_tx,0,0);
        VL_IN8(uart_rx,0,0);
        VL_OUT8(i2s_sclk,0,0);
        VL_OUT8(i2s_ws,0,0);
        VL_IN8(i2s_sd,0,0);
        CData/*0:0*/ SparkleTangNano9KTop__DOT__s3c_emit;
        CData/*3:0*/ SparkleTangNano9KTop__DOT__payload__DOT__state_next;
        CData/*3:0*/ SparkleTangNano9KTop__DOT__payload__DOT__state_q;
        CData/*3:0*/ SparkleTangNano9KTop__DOT__payload__DOT__manual_state_next;
        CData/*3:0*/ SparkleTangNano9KTop__DOT__payload__DOT__manual_state_q;
        CData/*0:0*/ SparkleTangNano9KTop__DOT__payload__DOT__audio_mode_next;
        CData/*0:0*/ SparkleTangNano9KTop__DOT__payload__DOT__audio_mode_q;
        CData/*0:0*/ SparkleTangNano9KTop__DOT__payload__DOT__button_d1;
        CData/*0:0*/ SparkleTangNano9KTop__DOT__payload__DOT__button_d2;
        CData/*0:0*/ SparkleTangNano9KTop__DOT__payload__DOT__button_prev;
        CData/*0:0*/ SparkleTangNano9KTop__DOT__payload__DOT__button_rise;
        CData/*0:0*/ SparkleTangNano9KTop__DOT__payload__DOT__uart_start;
        CData/*0:0*/ SparkleTangNano9KTop__DOT__payload__DOT__uart_busy_next;
        CData/*0:0*/ SparkleTangNano9KTop__DOT__payload__DOT__uart_busy_q;
        CData/*7:0*/ SparkleTangNano9KTop__DOT__payload__DOT__uart_baud_next;
        CData/*7:0*/ SparkleTangNano9KTop__DOT__payload__DOT__uart_baud_q;
        CData/*3:0*/ SparkleTangNano9KTop__DOT__payload__DOT__uart_bit_next;
        CData/*3:0*/ SparkleTangNano9KTop__DOT__payload__DOT__uart_bit_q;
        CData/*0:0*/ SparkleTangNano9KTop__DOT__payload__DOT__uart_byte_idx_next;
        CData/*0:0*/ SparkleTangNano9KTop__DOT__payload__DOT__uart_byte_idx_q;
        CData/*0:0*/ SparkleTangNano9KTop__DOT__payload__DOT__uart_all_done;
        CData/*2:0*/ SparkleTangNano9KTop__DOT__payload__DOT__sclk_div_next;
        CData/*2:0*/ SparkleTangNano9KTop__DOT__payload__DOT__sclk_div_q;
        CData/*5:0*/ SparkleTangNano9KTop__DOT__payload__DOT__ws_div_next;
        CData/*5:0*/ SparkleTangNano9KTop__DOT__payload__DOT__ws_div_q;
        CData/*0:0*/ SparkleTangNano9KTop__DOT__payload__DOT__i2s_sclk_prev;
        CData/*0:0*/ SparkleTangNano9KTop__DOT__payload__DOT__i2s_sclk_rise;
        CData/*0:0*/ SparkleTangNano9KTop__DOT__payload__DOT__i2s_ws_prev;
        CData/*0:0*/ SparkleTangNano9KTop__DOT__payload__DOT__i2s_ws_edge;
        CData/*4:0*/ SparkleTangNano9KTop__DOT__payload__DOT__i2s_bit_cnt_next;
        CData/*4:0*/ SparkleTangNano9KTop__DOT__payload__DOT__i2s_bit_cnt_q;
        CData/*0:0*/ SparkleTangNano9KTop__DOT__payload__DOT__i2s_valid_q;
        CData/*0:0*/ SparkleTangNano9KTop__DOT__payload__DOT____VdfgRegularize_h3c135564_0_17;
        CData/*0:0*/ SparkleTangNano9KTop__DOT__payload__DOT____VdfgRegularize_h3c135564_0_19;
        CData/*3:0*/ SparkleTangNano9KTop__DOT__payload__DOT____VdfgRegularize_h3c135564_0_20;
        CData/*0:0*/ __VstlFirstIteration;
        CData/*0:0*/ __VstlPhaseResult;
        CData/*0:0*/ __VicoFirstIteration;
        CData/*0:0*/ __VicoPhaseResult;
        CData/*0:0*/ __Vtrigprevexpr___TOP__clk__0;
        CData/*0:0*/ __Vtrigprevexpr___TOP__rst_n__0;
        CData/*0:0*/ __VactPhaseResult;
        CData/*0:0*/ __VnbaPhaseResult;
        SData/*15:0*/ SparkleTangNano9KTop__DOT__payload__DOT__phase_next;
        SData/*15:0*/ SparkleTangNano9KTop__DOT__payload__DOT__phase_q;
        SData/*9:0*/ SparkleTangNano9KTop__DOT__payload__DOT__uart_frame_load;
        SData/*9:0*/ SparkleTangNano9KTop__DOT__payload__DOT__uart_shift_next;
        SData/*9:0*/ SparkleTangNano9KTop__DOT__payload__DOT__uart_shift_q;
        IData/*24:0*/ SparkleTangNano9KTop__DOT__payload__DOT__tick_next;
        IData/*24:0*/ SparkleTangNano9KTop__DOT__payload__DOT__tick_q;
        IData/*23:0*/ SparkleTangNano9KTop__DOT__payload__DOT__i2s_shift_next;
        IData/*23:0*/ SparkleTangNano9KTop__DOT__payload__DOT__i2s_shift_q;
        IData/*23:0*/ SparkleTangNano9KTop__DOT__payload__DOT__i2s_sample_next;
        IData/*23:0*/ SparkleTangNano9KTop__DOT__payload__DOT__i2s_sample_q;
        IData/*31:0*/ __VactIterCount;
    };
    struct {
        VlUnpacked<QData/*63:0*/, 1> __VstlTriggered;
        VlUnpacked<QData/*63:0*/, 1> __VicoTriggered;
        VlUnpacked<QData/*63:0*/, 1> __VactTriggered;
        VlUnpacked<QData/*63:0*/, 1> __VnbaTriggered;
        VlUnpacked<CData/*0:0*/, 2> __Vm_traceActivity;
    };

    // INTERNAL VARIABLES
    VSparkleTangNano9KTop__Syms* vlSymsp;
    const char* vlNamep;

    // CONSTRUCTORS
    VSparkleTangNano9KTop___024root(VSparkleTangNano9KTop__Syms* symsp, const char* namep);
    ~VSparkleTangNano9KTop___024root();
    VL_UNCOPYABLE(VSparkleTangNano9KTop___024root);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
