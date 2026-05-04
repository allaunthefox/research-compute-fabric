// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Tracing implementation internals

#include "verilated_vcd_c.h"
#include "VSparkleTangNano9KTop__Syms.h"


void VSparkleTangNano9KTop___024root__trace_chg_0_sub_0(VSparkleTangNano9KTop___024root* vlSelf, VerilatedVcd::Buffer* bufp);

void VSparkleTangNano9KTop___024root__trace_chg_0(void* voidSelf, VerilatedVcd::Buffer* bufp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root__trace_chg_0\n"); );
    // Body
    VSparkleTangNano9KTop___024root* const __restrict vlSelf VL_ATTR_UNUSED = static_cast<VSparkleTangNano9KTop___024root*>(voidSelf);
    VSparkleTangNano9KTop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    if (VL_UNLIKELY(!vlSymsp->__Vm_activity)) return;
    VSparkleTangNano9KTop___024root__trace_chg_0_sub_0((&vlSymsp->TOP), bufp);
}

void VSparkleTangNano9KTop___024root__trace_chg_0_sub_0(VSparkleTangNano9KTop___024root* vlSelf, VerilatedVcd::Buffer* bufp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root__trace_chg_0_sub_0\n"); );
    VSparkleTangNano9KTop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    uint32_t* const oldp VL_ATTR_UNUSED = bufp->oldp(vlSymsp->__Vm_baseCode + 0);
    if (VL_UNLIKELY((vlSelfRef.__Vm_traceActivity[1U]))) {
        bufp->chgCData(oldp+0,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q),4);
        bufp->chgBit(oldp+1,(vlSelfRef.SparkleTangNano9KTop__DOT__s3c_emit));
        bufp->chgIData(oldp+2,(((0U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                 ? 3U : ((1U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                          ? 2U : ((2U 
                                                   == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                   ? 3U
                                                   : 
                                                  ((3U 
                                                    == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                    ? 6U
                                                    : 
                                                   ((4U 
                                                     == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                     ? 7U
                                                     : 
                                                    ((5U 
                                                      == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                      ? 6U
                                                      : 
                                                     ((6U 
                                                       == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                       ? 7U
                                                       : 
                                                      ((7U 
                                                        == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                        ? 6U
                                                        : 
                                                       ((8U 
                                                         == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                         ? 9U
                                                         : 
                                                        ((9U 
                                                          == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                          ? 0x0000000cU
                                                          : 
                                                         ((0x0aU 
                                                           == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                           ? 0x0000000dU
                                                           : 
                                                          ((0x0bU 
                                                            == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                            ? 0x0000000cU
                                                            : 
                                                           ((0x0cU 
                                                             == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                             ? 0x0000000dU
                                                             : 
                                                            ((0x0dU 
                                                              == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                              ? 0x0000000cU
                                                              : 
                                                             ((0x0eU 
                                                               == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                               ? 9U
                                                               : 
                                                              ((0x0fU 
                                                                == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                                ? 0x0000000cU
                                                                : 3U))))))))))))))))),32);
        bufp->chgIData(oldp+3,(((0U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                 ? 0U : ((1U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                          ? 1U : ((2U 
                                                   == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                   ? 0U
                                                   : 
                                                  ((3U 
                                                    == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                    ? 0U
                                                    : 
                                                   ((4U 
                                                     == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                     ? 3U
                                                     : 
                                                    ((5U 
                                                      == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                      ? 4U
                                                      : 
                                                     ((6U 
                                                       == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                       ? 3U
                                                       : 
                                                      ((7U 
                                                        == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                        ? 0U
                                                        : 
                                                       ((8U 
                                                         == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                         ? 0U
                                                         : 
                                                        ((9U 
                                                          == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                          ? 5U
                                                          : 
                                                         ((0x0aU 
                                                           == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                           ? 8U
                                                           : 
                                                          ((0x0bU 
                                                            == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                            ? 9U
                                                            : 
                                                           ((0x0cU 
                                                             == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                             ? 8U
                                                             : 
                                                            ((0x0dU 
                                                              == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                              ? 5U
                                                              : 0U))))))))))))))),32);
        bufp->chgSData(oldp+4,(((0U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                 ? 1U : ((1U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                          ? 1U : ((2U 
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
                                                                ? 4U
                                                                : 1U))))))))))))))))),16);
        bufp->chgSData(oldp+5,(((0U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                 ? 0U : ((1U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                          ? 1U : ((2U 
                                                   == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                   ? 2U
                                                   : 
                                                  ((3U 
                                                    == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                    ? 0U
                                                    : 
                                                   ((4U 
                                                     == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                     ? 1U
                                                     : 
                                                    ((5U 
                                                      == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                      ? 2U
                                                      : 
                                                     ((6U 
                                                       == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                       ? 3U
                                                       : 
                                                      ((7U 
                                                        == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                        ? 4U
                                                        : 
                                                       ((8U 
                                                         == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                         ? 0U
                                                         : 
                                                        ((9U 
                                                          == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                          ? 1U
                                                          : 
                                                         ((0x0aU 
                                                           == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                           ? 2U
                                                           : 
                                                          ((0x0bU 
                                                            == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                            ? 3U
                                                            : 
                                                           ((0x0cU 
                                                             == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                             ? 4U
                                                             : 
                                                            ((0x0dU 
                                                              == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                              ? 5U
                                                              : 
                                                             ((0x0eU 
                                                               == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                               ? 6U
                                                               : 0U)))))))))))))))),16);
        bufp->chgSData(oldp+6,(((0U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                 ? 2U : ((1U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                          ? 1U : ((2U 
                                                   == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                   ? 0U
                                                   : 
                                                  ((3U 
                                                    == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                    ? 4U
                                                    : 
                                                   ((4U 
                                                     == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                     ? 3U
                                                     : 
                                                    ((5U 
                                                      == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                      ? 2U
                                                      : 
                                                     ((6U 
                                                       == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                       ? 1U
                                                       : 
                                                      ((7U 
                                                        == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                        ? 0U
                                                        : 
                                                       ((8U 
                                                         == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                         ? 6U
                                                         : 
                                                        ((9U 
                                                          == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                          ? 5U
                                                          : 
                                                         ((0x0aU 
                                                           == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                           ? 4U
                                                           : 
                                                          ((0x0bU 
                                                            == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                            ? 3U
                                                            : 
                                                           ((0x0cU 
                                                             == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                             ? 2U
                                                             : 
                                                            ((0x0dU 
                                                              == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                              ? 1U
                                                              : 
                                                             ((0x0eU 
                                                               == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                               ? 0U
                                                               : 
                                                              ((0x0fU 
                                                                == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                                ? 8U
                                                                : 2U))))))))))))))))),16);
        bufp->chgCData(oldp+7,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_next),4);
        bufp->chgCData(oldp+8,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__manual_state_next),4);
        bufp->chgCData(oldp+9,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__manual_state_q),4);
        bufp->chgBit(oldp+10,((1U & ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__button_rise)
                                      ? (~ (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__audio_mode_q))
                                      : (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__audio_mode_q)))));
        bufp->chgBit(oldp+11,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__audio_mode_q));
        bufp->chgCData(oldp+12,((0x0000000fU & (vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sample_q 
                                                >> 0x00000013U))),4);
        bufp->chgBit(oldp+13,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__button_d1));
        bufp->chgBit(oldp+14,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__button_d2));
        bufp->chgBit(oldp+15,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__button_prev));
        bufp->chgBit(oldp+16,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__button_rise));
        bufp->chgIData(oldp+17,((0x01ffffffU & ((IData)(1U) 
                                                + vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__tick_q))),25);
        bufp->chgIData(oldp+18,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__tick_q),25);
        bufp->chgBit(oldp+19,((0U == vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__tick_q)));
        bufp->chgSData(oldp+20,((0x0000ffffU & ((0U 
                                                 == vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__tick_q)
                                                 ? 
                                                ((IData)(0x9e37U) 
                                                 + (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__phase_q))
                                                 : (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__phase_q)))),16);
        bufp->chgSData(oldp+21,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__phase_q),16);
        bufp->chgBit(oldp+22,(((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__button_rise) 
                               | (0U == vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__tick_q))));
        bufp->chgBit(oldp+23,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_start));
        bufp->chgBit(oldp+24,((0xe9U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_baud_q))));
        bufp->chgBit(oldp+25,((9U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_bit_q))));
        bufp->chgBit(oldp+26,((1U & ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_start) 
                                     | ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT____VdfgRegularize_h3c135564_0_17)
                                         ? (~ (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_all_done))
                                         : (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_busy_q))))));
        bufp->chgBit(oldp+27,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_busy_q));
        bufp->chgCData(oldp+28,((0x000000ffU & ((IData)(1U) 
                                                + (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_baud_q)))),8);
        bufp->chgCData(oldp+29,(((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_start)
                                  ? 0U : ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_busy_q)
                                           ? ((0xe9U 
                                               == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_baud_q))
                                               ? 0U
                                               : (0x000000ffU 
                                                  & ((IData)(1U) 
                                                     + (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_baud_q))))
                                           : 0U))),8);
        bufp->chgCData(oldp+30,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_baud_q),8);
        bufp->chgCData(oldp+31,((0x0000000fU & ((IData)(1U) 
                                                + (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_bit_q)))),4);
        bufp->chgCData(oldp+32,(((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_start)
                                  ? 0U : (0x0000000fU 
                                          & ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT____VdfgRegularize_h3c135564_0_19)
                                              ? ((9U 
                                                  == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_bit_q))
                                                  ? 0U
                                                  : 
                                                 ((IData)(1U) 
                                                  + (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_bit_q)))
                                              : (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_bit_q))))),4);
        bufp->chgCData(oldp+33,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_bit_q),4);
        bufp->chgSData(oldp+34,((0x00000200U | ((((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_byte_idx_q)
                                                   ? 6U
                                                   : 5U) 
                                                 << 5U) 
                                                | (((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_byte_idx_q)
                                                     ? (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT____VdfgRegularize_h3c135564_0_20)
                                                     : (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_next)) 
                                                   << 1U)))),10);
        bufp->chgCData(oldp+35,(((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_byte_idx_q)
                                  ? 6U : 5U)),4);
        bufp->chgCData(oldp+36,(((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_byte_idx_q)
                                  ? (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT____VdfgRegularize_h3c135564_0_20)
                                  : (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_next))),4);
        bufp->chgCData(oldp+37,(((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_byte_idx_next)
                                  ? 6U : 5U)),4);
        bufp->chgCData(oldp+38,(((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_byte_idx_next)
                                  ? (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT____VdfgRegularize_h3c135564_0_20)
                                  : (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_next))),4);
        bufp->chgSData(oldp+39,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_frame_load),10);
        bufp->chgBit(oldp+40,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_byte_idx_next));
        bufp->chgBit(oldp+41,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_byte_idx_q));
        bufp->chgBit(oldp+42,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_all_done));
        bufp->chgSData(oldp+43,((0x00000200U | (0x000001ffU 
                                                & ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_shift_q) 
                                                   >> 1U)))),10);
        bufp->chgSData(oldp+44,(((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_start)
                                  ? (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_frame_load)
                                  : ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT____VdfgRegularize_h3c135564_0_19)
                                      ? ((9U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_bit_q))
                                          ? ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_all_done)
                                              ? (0x00000200U 
                                                 | (0x000001ffU 
                                                    & ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_shift_q) 
                                                       >> 1U)))
                                              : (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_frame_load))
                                          : (0x00000200U 
                                             | (0x000001ffU 
                                                & ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_shift_q) 
                                                   >> 1U))))
                                      : (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_shift_q)))),10);
        bufp->chgSData(oldp+45,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_shift_q),10);
        bufp->chgCData(oldp+46,((7U & ((IData)(1U) 
                                       + (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__sclk_div_q)))),3);
        bufp->chgCData(oldp+47,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__sclk_div_q),3);
        bufp->chgCData(oldp+48,((0x0000003fU & ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__ws_div_q) 
                                                + (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sclk_rise)))),6);
        bufp->chgCData(oldp+49,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__ws_div_q),6);
        bufp->chgBit(oldp+50,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sclk_prev));
        bufp->chgBit(oldp+51,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sclk_rise));
        bufp->chgBit(oldp+52,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_ws_prev));
        bufp->chgBit(oldp+53,((1U & ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__ws_div_q) 
                                     >> 5U))));
        bufp->chgBit(oldp+54,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_ws_edge));
        bufp->chgCData(oldp+55,(((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_ws_edge)
                                  ? 0U : (0x0000001fU 
                                          & ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_bit_cnt_q) 
                                             + (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sclk_rise))))),5);
        bufp->chgCData(oldp+56,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_bit_cnt_q),5);
        bufp->chgIData(oldp+57,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_shift_q),24);
        bufp->chgIData(oldp+58,(((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_ws_edge)
                                  ? vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_shift_q
                                  : vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sample_q)),24);
        bufp->chgIData(oldp+59,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sample_q),24);
        bufp->chgBit(oldp+60,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_valid_q));
    }
    bufp->chgBit(oldp+61,(vlSelfRef.clk));
    bufp->chgBit(oldp+62,(vlSelfRef.rst_n));
    bufp->chgBit(oldp+63,(vlSelfRef.user_btn));
    bufp->chgCData(oldp+64,(vlSelfRef.led),6);
    bufp->chgBit(oldp+65,(vlSelfRef.uart_tx));
    bufp->chgBit(oldp+66,(vlSelfRef.uart_rx));
    bufp->chgBit(oldp+67,(vlSelfRef.i2s_sclk));
    bufp->chgBit(oldp+68,(vlSelfRef.i2s_ws));
    bufp->chgBit(oldp+69,(vlSelfRef.i2s_sd));
    bufp->chgBit(oldp+70,((1U & (~ (IData)(vlSelfRef.user_btn)))));
    bufp->chgBit(oldp+71,((1U & (~ (IData)(vlSelfRef.rst_n)))));
    bufp->chgIData(oldp+72,(((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_ws_edge)
                              ? vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_shift_q
                              : ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sclk_rise)
                                  ? (((IData)(vlSelfRef.i2s_sd) 
                                      << 0x00000017U) 
                                     | (0x007fffffU 
                                        & (vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_shift_q 
                                           >> 1U)))
                                  : vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_shift_q))),24);
}

void VSparkleTangNano9KTop___024root__trace_cleanup(void* voidSelf, VerilatedVcd* /*unused*/) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root__trace_cleanup\n"); );
    // Body
    VSparkleTangNano9KTop___024root* const __restrict vlSelf VL_ATTR_UNUSED = static_cast<VSparkleTangNano9KTop___024root*>(voidSelf);
    VSparkleTangNano9KTop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    vlSymsp->__Vm_activity = false;
    vlSymsp->TOP.__Vm_traceActivity[0U] = 0U;
    vlSymsp->TOP.__Vm_traceActivity[1U] = 0U;
}
