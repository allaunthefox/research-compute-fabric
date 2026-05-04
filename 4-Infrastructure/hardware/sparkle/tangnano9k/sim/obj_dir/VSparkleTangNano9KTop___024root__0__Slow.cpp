// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See VSparkleTangNano9KTop.h for the primary calling header

#include "VSparkleTangNano9KTop__pch.h"

VL_ATTR_COLD void VSparkleTangNano9KTop___024root___eval_static(VSparkleTangNano9KTop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root___eval_static\n"); );
    VSparkleTangNano9KTop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__Vtrigprevexpr___TOP__clk__0 = vlSelfRef.clk;
    vlSelfRef.__Vtrigprevexpr___TOP__rst_n__0 = vlSelfRef.rst_n;
}

VL_ATTR_COLD void VSparkleTangNano9KTop___024root___eval_initial(VSparkleTangNano9KTop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root___eval_initial\n"); );
    VSparkleTangNano9KTop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

VL_ATTR_COLD void VSparkleTangNano9KTop___024root___eval_final(VSparkleTangNano9KTop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root___eval_final\n"); );
    VSparkleTangNano9KTop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

#ifdef VL_DEBUG
VL_ATTR_COLD void VSparkleTangNano9KTop___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG
VL_ATTR_COLD bool VSparkleTangNano9KTop___024root___eval_phase__stl(VSparkleTangNano9KTop___024root* vlSelf);

VL_ATTR_COLD void VSparkleTangNano9KTop___024root___eval_settle(VSparkleTangNano9KTop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root___eval_settle\n"); );
    VSparkleTangNano9KTop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VstlIterCount;
    // Body
    __VstlIterCount = 0U;
    vlSelfRef.__VstlFirstIteration = 1U;
    do {
        if (VL_UNLIKELY(((0x00000064U < __VstlIterCount)))) {
#ifdef VL_DEBUG
            VSparkleTangNano9KTop___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
#endif
            VL_FATAL_MT("../SparkleTangNano9KTop.v", 9, "", "DIDNOTCONVERGE: Settle region did not converge after '--converge-limit' of 100 tries");
        }
        __VstlIterCount = ((IData)(1U) + __VstlIterCount);
        vlSelfRef.__VstlPhaseResult = VSparkleTangNano9KTop___024root___eval_phase__stl(vlSelf);
        vlSelfRef.__VstlFirstIteration = 0U;
    } while (vlSelfRef.__VstlPhaseResult);
}

VL_ATTR_COLD void VSparkleTangNano9KTop___024root___eval_triggers_vec__stl(VSparkleTangNano9KTop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root___eval_triggers_vec__stl\n"); );
    VSparkleTangNano9KTop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VstlTriggered[0U] = ((0xfffffffffffffffeULL 
                                      & vlSelfRef.__VstlTriggered[0U]) 
                                     | (IData)((IData)(vlSelfRef.__VstlFirstIteration)));
}

VL_ATTR_COLD bool VSparkleTangNano9KTop___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 1> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void VSparkleTangNano9KTop___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root___dump_triggers__stl\n"); );
    // Body
    if ((1U & (~ (IData)(VSparkleTangNano9KTop___024root___trigger_anySet__stl(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: Internal 'stl' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD bool VSparkleTangNano9KTop___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root___trigger_anySet__stl\n"); );
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

VL_ATTR_COLD void VSparkleTangNano9KTop___024root___stl_sequent__TOP__0(VSparkleTangNano9KTop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root___stl_sequent__TOP__0\n"); );
    VSparkleTangNano9KTop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.i2s_ws = (1U & ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__ws_div_q) 
                              >> 5U));
    vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__tick_next 
        = (0x01ffffffU & ((IData)(1U) + vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__tick_q));
    vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__sclk_div_next 
        = (7U & ((IData)(1U) + (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__sclk_div_q)));
    vlSelfRef.uart_tx = (1U & ((~ (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_busy_q)) 
                               | (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_shift_q)));
    vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__phase_next 
        = (0x0000ffffU & ((0U == vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__tick_q)
                           ? ((IData)(0x9e37U) + (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__phase_q))
                           : (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__phase_q)));
    vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT____VdfgRegularize_h3c135564_0_19 
        = ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_busy_q) 
           & (0xe9U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_baud_q)));
    vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_ws_edge 
        = ((1U & ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__ws_div_q) 
                  >> 5U)) != (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_ws_prev));
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
    vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT____VdfgRegularize_h3c135564_0_17 
        = ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_busy_q) 
           & ((0xe9U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_baud_q)) 
              & (9U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_bit_q))));
    vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_all_done 
        = ((9U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_bit_q)) 
           & (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_byte_idx_q));
    vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__button_rise 
        = ((~ (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__button_prev)) 
           & (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__button_d2));
    vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sclk_rise 
        = ((~ (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sclk_prev)) 
           & (IData)(vlSelfRef.i2s_sclk));
    if (vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_ws_edge) {
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sample_next 
            = vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_shift_q;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_bit_cnt_next = 0U;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_shift_next 
            = vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_shift_q;
    } else {
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sample_next 
            = vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sample_q;
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_bit_cnt_next 
            = (0x0000001fU & ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_bit_cnt_q) 
                              + (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sclk_rise)));
        vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_shift_next 
            = ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sclk_rise)
                ? (((IData)(vlSelfRef.i2s_sd) << 0x00000017U) 
                   | (0x007fffffU & (vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_shift_q 
                                     >> 1U))) : vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_shift_q);
    }
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
    vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__ws_div_next 
        = (0x0000003fU & ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__ws_div_q) 
                          + (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sclk_rise)));
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

VL_ATTR_COLD void VSparkleTangNano9KTop___024root____Vm_traceActivitySetAll(VSparkleTangNano9KTop___024root* vlSelf);

VL_ATTR_COLD void VSparkleTangNano9KTop___024root___eval_stl(VSparkleTangNano9KTop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root___eval_stl\n"); );
    VSparkleTangNano9KTop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1ULL & vlSelfRef.__VstlTriggered[0U])) {
        VSparkleTangNano9KTop___024root___stl_sequent__TOP__0(vlSelf);
        VSparkleTangNano9KTop___024root____Vm_traceActivitySetAll(vlSelf);
    }
}

VL_ATTR_COLD bool VSparkleTangNano9KTop___024root___eval_phase__stl(VSparkleTangNano9KTop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root___eval_phase__stl\n"); );
    VSparkleTangNano9KTop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VstlExecute;
    // Body
    VSparkleTangNano9KTop___024root___eval_triggers_vec__stl(vlSelf);
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        VSparkleTangNano9KTop___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
    }
#endif
    __VstlExecute = VSparkleTangNano9KTop___024root___trigger_anySet__stl(vlSelfRef.__VstlTriggered);
    if (__VstlExecute) {
        VSparkleTangNano9KTop___024root___eval_stl(vlSelf);
    }
    return (__VstlExecute);
}

bool VSparkleTangNano9KTop___024root___trigger_anySet__ico(const VlUnpacked<QData/*63:0*/, 1> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void VSparkleTangNano9KTop___024root___dump_triggers__ico(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root___dump_triggers__ico\n"); );
    // Body
    if ((1U & (~ (IData)(VSparkleTangNano9KTop___024root___trigger_anySet__ico(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: Internal 'ico' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

bool VSparkleTangNano9KTop___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void VSparkleTangNano9KTop___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root___dump_triggers__act\n"); );
    // Body
    if ((1U & (~ (IData)(VSparkleTangNano9KTop___024root___trigger_anySet__act(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @(posedge clk)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 1U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 1 is active: @(negedge rst_n)\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD void VSparkleTangNano9KTop___024root____Vm_traceActivitySetAll(VSparkleTangNano9KTop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root____Vm_traceActivitySetAll\n"); );
    VSparkleTangNano9KTop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__Vm_traceActivity[0U] = 1U;
    vlSelfRef.__Vm_traceActivity[1U] = 1U;
}

VL_ATTR_COLD void VSparkleTangNano9KTop___024root___ctor_var_reset(VSparkleTangNano9KTop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root___ctor_var_reset\n"); );
    VSparkleTangNano9KTop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    const uint64_t __VscopeHash = VL_MURMUR64_HASH(vlSelf->vlNamep);
    vlSelf->clk = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16707436170211756652ull);
    vlSelf->rst_n = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1638864771569018232ull);
    vlSelf->user_btn = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1773744718480251498ull);
    vlSelf->led = VL_SCOPED_RAND_RESET_I(6, __VscopeHash, 14009161575225144129ull);
    vlSelf->uart_tx = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1761512799854230840ull);
    vlSelf->uart_rx = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 2399467654730215438ull);
    vlSelf->i2s_sclk = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 17913508762189998967ull);
    vlSelf->i2s_ws = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 11941430048040003142ull);
    vlSelf->i2s_sd = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6560961560033025047ull);
    vlSelf->SparkleTangNano9KTop__DOT__s3c_emit = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1424760439982459582ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__state_next = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 3666975911428191505ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__state_q = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 4787922459064522808ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__manual_state_next = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 3074556251838679224ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__manual_state_q = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 6448021804015411149ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__audio_mode_next = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16737507586291114379ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__audio_mode_q = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 10752427176266081584ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__button_d1 = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1325024016380017903ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__button_d2 = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 3821005362490127898ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__button_prev = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 7007399088329538383ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__button_rise = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 10192477481194017518ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__tick_next = VL_SCOPED_RAND_RESET_I(25, __VscopeHash, 2324208658799791966ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__tick_q = VL_SCOPED_RAND_RESET_I(25, __VscopeHash, 999520266990590547ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__phase_next = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 5505402551237400122ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__phase_q = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 17342668295482480767ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__uart_start = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 7816037629605942917ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__uart_busy_next = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 15810661313162923944ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__uart_busy_q = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 11978113101284670288ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__uart_baud_next = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 2746889699153873855ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__uart_baud_q = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 7511882197771851030ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__uart_bit_next = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 12396684711589733403ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__uart_bit_q = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 289080531598277876ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__uart_frame_load = VL_SCOPED_RAND_RESET_I(10, __VscopeHash, 10032498661425589045ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__uart_byte_idx_next = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6370863725639201433ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__uart_byte_idx_q = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 17257055071232200103ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__uart_all_done = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 13038861383704931010ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__uart_shift_next = VL_SCOPED_RAND_RESET_I(10, __VscopeHash, 2141810169638186810ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__uart_shift_q = VL_SCOPED_RAND_RESET_I(10, __VscopeHash, 5639726643544776011ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__sclk_div_next = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 4531615939322216218ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__sclk_div_q = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 11107770347832166629ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__ws_div_next = VL_SCOPED_RAND_RESET_I(6, __VscopeHash, 12799217425300880822ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__ws_div_q = VL_SCOPED_RAND_RESET_I(6, __VscopeHash, 16917713915727073280ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__i2s_sclk_prev = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 426698709047061660ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__i2s_sclk_rise = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 11974303288976494514ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__i2s_ws_prev = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16163669165123777976ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__i2s_ws_edge = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 8971603199915722301ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__i2s_bit_cnt_next = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 2467893287615492049ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__i2s_bit_cnt_q = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 11179835675367877745ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__i2s_shift_next = VL_SCOPED_RAND_RESET_I(24, __VscopeHash, 8020082034083129914ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__i2s_shift_q = VL_SCOPED_RAND_RESET_I(24, __VscopeHash, 15795993537969487144ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__i2s_sample_next = VL_SCOPED_RAND_RESET_I(24, __VscopeHash, 7284258329499268173ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__i2s_sample_q = VL_SCOPED_RAND_RESET_I(24, __VscopeHash, 11189583537586410639ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT__i2s_valid_q = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 13994522475903438322ull);
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT____VdfgRegularize_h3c135564_0_17 = 0;
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT____VdfgRegularize_h3c135564_0_19 = 0;
    vlSelf->SparkleTangNano9KTop__DOT__payload__DOT____VdfgRegularize_h3c135564_0_20 = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VstlTriggered[__Vi0] = 0;
    }
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VicoTriggered[__Vi0] = 0;
    }
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VactTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__clk__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__rst_n__0 = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VnbaTriggered[__Vi0] = 0;
    }
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->__Vm_traceActivity[__Vi0] = 0;
    }
}
