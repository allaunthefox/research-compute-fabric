// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See VSparkleTangNano9KTop.h for the primary calling header

#include "VSparkleTangNano9KTop__pch.h"

void VSparkleTangNano9KTop___024root___eval_triggers_vec__ico(VSparkleTangNano9KTop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root___eval_triggers_vec__ico\n"); );
    VSparkleTangNano9KTop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VicoTriggered[0U] = ((0xfffffffffffffffeULL 
                                      & vlSelfRef.__VicoTriggered[0U]) 
                                     | (IData)((IData)(vlSelfRef.__VicoFirstIteration)));
}

bool VSparkleTangNano9KTop___024root___trigger_anySet__ico(const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root___trigger_anySet__ico\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        if (in[n]) {
            return (1U);
        }
        n = ((IData)(1U) + n);
    } while ((1U > n));
    return (0U);
}

void VSparkleTangNano9KTop___024root___ico_sequent__TOP__0(VSparkleTangNano9KTop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root___ico_sequent__TOP__0\n"); );
    VSparkleTangNano9KTop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_shift_next 
        = ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_ws_edge)
            ? vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_shift_q
            : ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sclk_rise)
                ? (((IData)(vlSelfRef.i2s_sd) << 0x00000017U) 
                   | (0x007fffffU & (vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_shift_q 
                                     >> 1U))) : vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_shift_q));
}

void VSparkleTangNano9KTop___024root___eval_ico(VSparkleTangNano9KTop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root___eval_ico\n"); );
    VSparkleTangNano9KTop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1ULL & vlSelfRef.__VicoTriggered[0U])) {
        VSparkleTangNano9KTop___024root___ico_sequent__TOP__0(vlSelf);
    }
}

#ifdef VL_DEBUG
VL_ATTR_COLD void VSparkleTangNano9KTop___024root___dump_triggers__ico(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG

bool VSparkleTangNano9KTop___024root___eval_phase__ico(VSparkleTangNano9KTop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root___eval_phase__ico\n"); );
    VSparkleTangNano9KTop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VicoExecute;
    // Body
    VSparkleTangNano9KTop___024root___eval_triggers_vec__ico(vlSelf);
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        VSparkleTangNano9KTop___024root___dump_triggers__ico(vlSelfRef.__VicoTriggered, "ico"s);
    }
#endif
    __VicoExecute = VSparkleTangNano9KTop___024root___trigger_anySet__ico(vlSelfRef.__VicoTriggered);
    if (__VicoExecute) {
        VSparkleTangNano9KTop___024root___eval_ico(vlSelf);
    }
    return (__VicoExecute);
}

void VSparkleTangNano9KTop___024root___eval_triggers_vec__act(VSparkleTangNano9KTop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root___eval_triggers_vec__act\n"); );
    VSparkleTangNano9KTop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VactTriggered[0U] = (QData)((IData)(
                                                    ((((~ (IData)(vlSelfRef.rst_n)) 
                                                       & (IData)(vlSelfRef.__Vtrigprevexpr___TOP__rst_n__0)) 
                                                      << 1U) 
                                                     | ((IData)(vlSelfRef.clk) 
                                                        & (~ (IData)(vlSelfRef.__Vtrigprevexpr___TOP__clk__0))))));
    vlSelfRef.__Vtrigprevexpr___TOP__clk__0 = vlSelfRef.clk;
    vlSelfRef.__Vtrigprevexpr___TOP__rst_n__0 = vlSelfRef.rst_n;
}

bool VSparkleTangNano9KTop___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root___trigger_anySet__act\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        if (in[n]) {
            return (1U);
        }
        n = ((IData)(1U) + n);
    } while ((1U > n));
    return (0U);
}

void VSparkleTangNano9KTop___024root___nba_sequent__TOP__0(VSparkleTangNano9KTop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root___nba_sequent__TOP__0\n"); );
    VSparkleTangNano9KTop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if (vlSelfRef.rst_n) {
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_valid_q 
            = vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_ws_edge;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sclk_prev 
            = vlSelfRef.i2s_sclk;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__audio_mode_q 
            = vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__audio_mode_next;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_byte_idx_q 
            = vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_byte_idx_next;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_ws_prev 
            = ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__ws_div_q) 
               >> 5U);
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__phase_q 
            = vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__phase_next;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_bit_cnt_q 
            = vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_bit_cnt_next;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_shift_q 
            = vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_shift_next;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_shift_q 
            = vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_shift_next;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__sclk_div_q 
            = vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__sclk_div_next;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sample_q 
            = vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sample_next;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__manual_state_q 
            = vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__manual_state_next;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_baud_q 
            = vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_baud_next;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q 
            = vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_next;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__tick_q 
            = vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__tick_next;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_bit_q 
            = vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_bit_next;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__ws_div_q 
            = vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__ws_div_next;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_busy_q 
            = vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_busy_next;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__button_prev 
            = vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__button_d2;
    } else {
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_valid_q = 0U;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sclk_prev = 0U;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__audio_mode_q = 0U;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_byte_idx_q = 0U;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_ws_prev = 0U;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__phase_q = 0U;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_bit_cnt_q = 0U;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_shift_q = 0U;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_shift_q = 0x03ffU;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__sclk_div_q = 0U;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sample_q = 0U;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__manual_state_q = 0U;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_baud_q = 0U;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q = 0U;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__tick_q = 0U;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_bit_q = 0U;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__ws_div_q = 0U;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_busy_q = 0U;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__button_prev = 0U;
    }
    vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__sclk_div_next 
        = (7U & ((IData)(1U) + (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__sclk_div_q)));
    vlSelfRef.i2s_sclk = (1U & ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__sclk_div_q) 
                                >> 2U));
    vlSelfRef.SparkleTangNano9KTop__DOT__s3c_emit = 
        ((0U != (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q)) 
         & ((1U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q)) 
            | ((2U != (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q)) 
               & ((3U != (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q)) 
                  & ((4U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q)) 
                     | ((5U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q)) 
                        | ((6U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q)) 
                           | ((7U != (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q)) 
                              & ((8U != (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q)) 
                                 & ((9U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q)) 
                                    | ((0x0aU == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q)) 
                                       | ((0x0bU == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q)) 
                                          | ((0x0cU 
                                              == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q)) 
                                             | (0x0dU 
                                                == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q)))))))))))))));
    vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__tick_next 
        = (0x01ffffffU & ((IData)(1U) + vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__tick_q));
    vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__phase_next 
        = (0x0000ffffU & ((0U == vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__tick_q)
                           ? ((IData)(0x9e37U) + (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__phase_q))
                           : (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__phase_q)));
    vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_all_done 
        = ((9U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_bit_q)) 
           & (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_byte_idx_q));
    vlSelfRef.uart_tx = (1U & ((~ (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_busy_q)) 
                               | (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_shift_q)));
    vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT____VdfgRegularize_h3c135564_0_19 
        = ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_busy_q) 
           & (0xe9U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_baud_q)));
    vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT____VdfgRegularize_h3c135564_0_17 
        = ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_busy_q) 
           & ((0xe9U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_baud_q)) 
              & (9U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_bit_q))));
    vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__button_d2 
        = ((IData)(vlSelfRef.rst_n) & (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__button_d1));
    vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sclk_rise 
        = ((~ (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sclk_prev)) 
           & (IData)(vlSelfRef.i2s_sclk));
    vlSelfRef.led = ((0x00000020U & (vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__tick_q 
                                     >> 0x00000013U)) 
                     | (((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__audio_mode_q) 
                         << 4U) | (((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__s3c_emit) 
                                    << 3U) | (7U & (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q)))));
    vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT____VdfgRegularize_h3c135564_0_20 
        = (((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__audio_mode_q) 
            << 3U) | (((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__s3c_emit) 
                       << 2U) | ((0U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                  ? 1U : ((1U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                           ? 1U : (
                                                   (2U 
                                                    == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                    ? 1U
                                                    : 
                                                   ((3U 
                                                     == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                     ? 2U
                                                     : 
                                                    ((4U 
                                                      == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                      ? 2U
                                                      : 
                                                     ((5U 
                                                       == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                       ? 2U
                                                       : 
                                                      ((6U 
                                                        == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                        ? 2U
                                                        : 
                                                       ((7U 
                                                         == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                         ? 2U
                                                         : 
                                                        ((8U 
                                                          == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                          ? 3U
                                                          : 
                                                         ((9U 
                                                           == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                           ? 3U
                                                           : 
                                                          ((0x0aU 
                                                            == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                            ? 3U
                                                            : 
                                                           ((0x0bU 
                                                             == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                             ? 3U
                                                             : 
                                                            ((0x0cU 
                                                              == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                              ? 3U
                                                              : 
                                                             ((0x0dU 
                                                               == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                               ? 3U
                                                               : 
                                                              ((0x0eU 
                                                                == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                                ? 3U
                                                                : 
                                                               ((0x0fU 
                                                                 == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                                 ? 0U
                                                                 : 1U))))))))))))))))));
    vlSelfRef.i2s_ws = (1U & ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__ws_div_q) 
                              >> 5U));
    vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__ws_div_next 
        = (0x0000003fU & ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__ws_div_q) 
                          + (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sclk_rise)));
    vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_ws_edge 
        = ((1U & ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__ws_div_q) 
                  >> 5U)) != (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_ws_prev));
    vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__button_d1 
        = ((IData)(vlSelfRef.rst_n) & (~ (IData)(vlSelfRef.user_btn)));
    vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__button_rise 
        = ((~ (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__button_prev)) 
           & (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__button_d2));
    if (vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_ws_edge) {
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_bit_cnt_next = 0U;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sample_next 
            = vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_shift_q;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_shift_next 
            = vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_shift_q;
    } else {
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_bit_cnt_next 
            = (0x0000001fU & ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_bit_cnt_q) 
                              + (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sclk_rise)));
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sample_next 
            = vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sample_q;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_shift_next 
            = ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sclk_rise)
                ? (((IData)(vlSelfRef.i2s_sd) << 0x00000017U) 
                   | (0x007fffffU & (vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_shift_q 
                                     >> 1U))) : vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_shift_q);
    }
    vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__audio_mode_next 
        = (1U & ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__button_rise)
                  ? (~ (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__audio_mode_q))
                  : (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__audio_mode_q)));
    vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__manual_state_next 
        = (0x0000000fU & ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__manual_state_q) 
                          + (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__button_rise)));
    vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_start 
        = ((~ (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_busy_q)) 
           & ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__button_rise) 
              | (0U == vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__tick_q)));
    vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_next 
        = (0x0000000fU & ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__audio_mode_q)
                           ? ((0U == vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__tick_q)
                               ? (vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sample_q 
                                  >> 0x00000013U) : (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                           : (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__manual_state_next)));
    vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_busy_next 
        = (1U & ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_start) 
                 | ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT____VdfgRegularize_h3c135564_0_17)
                     ? (~ (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_all_done))
                     : (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_busy_q))));
    vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_byte_idx_next 
        = (1U & ((~ (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_start)) 
                 & ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT____VdfgRegularize_h3c135564_0_17)
                     ? (~ (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_all_done))
                     : (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_byte_idx_q))));
    vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_frame_load 
        = (0x00000200U | ((((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_byte_idx_next)
                             ? 6U : 5U) << 5U) | (((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_byte_idx_next)
                                                    ? (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT____VdfgRegularize_h3c135564_0_20)
                                                    : (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_next)) 
                                                  << 1U)));
    if (vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_start) {
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_baud_next = 0U;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_bit_next = 0U;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_shift_next 
            = vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_frame_load;
    } else {
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_baud_next 
            = ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_busy_q)
                ? ((0xe9U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_baud_q))
                    ? 0U : (0x000000ffU & ((IData)(1U) 
                                           + (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_baud_q))))
                : 0U);
        if (vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT____VdfgRegularize_h3c135564_0_19) {
            if ((9U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_bit_q))) {
                vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_bit_next 
                    = (0x0000000fU & 0U);
                vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_shift_next 
                    = ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_all_done)
                        ? (0x00000200U | (0x000001ffU 
                                          & ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_shift_q) 
                                             >> 1U)))
                        : (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_frame_load));
            } else {
                vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_bit_next 
                    = (0x0000000fU & ((IData)(1U) + (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_bit_q)));
                vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_shift_next 
                    = (0x00000200U | (0x000001ffU & 
                                      ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_shift_q) 
                                       >> 1U)));
            }
        } else {
            vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_bit_next 
                = (0x0000000fU & (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_bit_q));
            vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_shift_next 
                = vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_shift_q;
        }
    }
}

void VSparkleTangNano9KTop___024root___eval_nba(VSparkleTangNano9KTop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root___eval_nba\n"); );
    VSparkleTangNano9KTop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((3ULL & vlSelfRef.__VnbaTriggered[0U])) {
        VSparkleTangNano9KTop___024root___nba_sequent__TOP__0(vlSelf);
        vlSelfRef.__Vm_traceActivity[1U] = 1U;
    }
}

void VSparkleTangNano9KTop___024root___trigger_orInto__act_vec_vec(VlUnpacked<QData/*63:0*/, 1> &out, const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root___trigger_orInto__act_vec_vec\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        out[n] = (out[n] | in[n]);
        n = ((IData)(1U) + n);
    } while ((0U >= n));
}

#ifdef VL_DEBUG
VL_ATTR_COLD void VSparkleTangNano9KTop___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG

bool VSparkleTangNano9KTop___024root___eval_phase__act(VSparkleTangNano9KTop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root___eval_phase__act\n"); );
    VSparkleTangNano9KTop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    VSparkleTangNano9KTop___024root___eval_triggers_vec__act(vlSelf);
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        VSparkleTangNano9KTop___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
    }
#endif
    VSparkleTangNano9KTop___024root___trigger_orInto__act_vec_vec(vlSelfRef.__VnbaTriggered, vlSelfRef.__VactTriggered);
    return (0U);
}

void VSparkleTangNano9KTop___024root___trigger_clear__act(VlUnpacked<QData/*63:0*/, 1> &out) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root___trigger_clear__act\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        out[n] = 0ULL;
        n = ((IData)(1U) + n);
    } while ((1U > n));
}

bool VSparkleTangNano9KTop___024root___eval_phase__nba(VSparkleTangNano9KTop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root___eval_phase__nba\n"); );
    VSparkleTangNano9KTop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VnbaExecute;
    // Body
    __VnbaExecute = VSparkleTangNano9KTop___024root___trigger_anySet__act(vlSelfRef.__VnbaTriggered);
    if (__VnbaExecute) {
        VSparkleTangNano9KTop___024root___eval_nba(vlSelf);
        VSparkleTangNano9KTop___024root___trigger_clear__act(vlSelfRef.__VnbaTriggered);
    }
    return (__VnbaExecute);
}

void VSparkleTangNano9KTop___024root___eval(VSparkleTangNano9KTop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root___eval\n"); );
    VSparkleTangNano9KTop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VicoIterCount;
    IData/*31:0*/ __VnbaIterCount;
    // Body
    __VicoIterCount = 0U;
    vlSelfRef.__VicoFirstIteration = 1U;
    do {
        if (VL_UNLIKELY(((0x00000064U < __VicoIterCount)))) {
#ifdef VL_DEBUG
            VSparkleTangNano9KTop___024root___dump_triggers__ico(vlSelfRef.__VicoTriggered, "ico"s);
#endif
            VL_FATAL_MT("../SparkleTangNano9KTop.v", 9, "", "DIDNOTCONVERGE: Input combinational region did not converge after '--converge-limit' of 100 tries");
        }
        __VicoIterCount = ((IData)(1U) + __VicoIterCount);
        vlSelfRef.__VicoPhaseResult = VSparkleTangNano9KTop___024root___eval_phase__ico(vlSelf);
        vlSelfRef.__VicoFirstIteration = 0U;
    } while (vlSelfRef.__VicoPhaseResult);
    __VnbaIterCount = 0U;
    do {
        if (VL_UNLIKELY(((0x00000064U < __VnbaIterCount)))) {
#ifdef VL_DEBUG
            VSparkleTangNano9KTop___024root___dump_triggers__act(vlSelfRef.__VnbaTriggered, "nba"s);
#endif
            VL_FATAL_MT("../SparkleTangNano9KTop.v", 9, "", "DIDNOTCONVERGE: NBA region did not converge after '--converge-limit' of 100 tries");
        }
        __VnbaIterCount = ((IData)(1U) + __VnbaIterCount);
        vlSelfRef.__VactIterCount = 0U;
        do {
            if (VL_UNLIKELY(((0x00000064U < vlSelfRef.__VactIterCount)))) {
#ifdef VL_DEBUG
                VSparkleTangNano9KTop___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
#endif
                VL_FATAL_MT("../SparkleTangNano9KTop.v", 9, "", "DIDNOTCONVERGE: Active region did not converge after '--converge-limit' of 100 tries");
            }
            vlSelfRef.__VactIterCount = ((IData)(1U) 
                                         + vlSelfRef.__VactIterCount);
            vlSelfRef.__VactPhaseResult = VSparkleTangNano9KTop___024root___eval_phase__act(vlSelf);
        } while (vlSelfRef.__VactPhaseResult);
        vlSelfRef.__VnbaPhaseResult = VSparkleTangNano9KTop___024root___eval_phase__nba(vlSelf);
    } while (vlSelfRef.__VnbaPhaseResult);
}

#ifdef VL_DEBUG
void VSparkleTangNano9KTop___024root___eval_debug_assertions(VSparkleTangNano9KTop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root___eval_debug_assertions\n"); );
    VSparkleTangNano9KTop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if (VL_UNLIKELY(((vlSelfRef.clk & 0xfeU)))) {
        Verilated::overWidthError("clk");
    }
    if (VL_UNLIKELY(((vlSelfRef.rst_n & 0xfeU)))) {
        Verilated::overWidthError("rst_n");
    }
    if (VL_UNLIKELY(((vlSelfRef.user_btn & 0xfeU)))) {
        Verilated::overWidthError("user_btn");
    }
    if (VL_UNLIKELY(((vlSelfRef.uart_rx & 0xfeU)))) {
        Verilated::overWidthError("uart_rx");
    }
    if (VL_UNLIKELY(((vlSelfRef.i2s_sd & 0xfeU)))) {
        Verilated::overWidthError("i2s_sd");
    }
}
#endif  // VL_DEBUG
