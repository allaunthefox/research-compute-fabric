// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Tracing implementation internals

#include "verilated_vcd_c.h"
#include "VSparkleTangNano9KTop__Syms.h"


VL_ATTR_COLD void VSparkleTangNano9KTop___024root__trace_init_sub__TOP__0(VSparkleTangNano9KTop___024root* vlSelf, VerilatedVcd* tracep) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root__trace_init_sub__TOP__0\n"); );
    VSparkleTangNano9KTop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    const int c = vlSymsp->__Vm_baseCode;
    tracep->pushPrefix("$rootio", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBit(c+61,0,"clk",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+62,0,"rst_n",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+63,0,"user_btn",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+64,0,"led",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 5,0);
    tracep->declBit(c+65,0,"uart_tx",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+66,0,"uart_rx",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+67,0,"i2s_sclk",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+68,0,"i2s_ws",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+69,0,"i2s_sd",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->popPrefix();
    tracep->pushPrefix("SparkleTangNano9KTop", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBit(c+61,0,"clk",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+62,0,"rst_n",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+63,0,"user_btn",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+64,0,"led",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 5,0);
    tracep->declBit(c+65,0,"uart_tx",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+66,0,"uart_rx",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+67,0,"i2s_sclk",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+68,0,"i2s_ws",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+69,0,"i2s_sd",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+70,0,"user_btn_pressed",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+71,0,"rst",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+0,0,"scalar_state",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 3,0);
    tracep->declBit(c+1,0,"s3c_emit",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+2,0,"s3c_j_score",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+3,0,"s3c_mass",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+4,0,"handleK",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 15,0);
    tracep->declBus(c+5,0,"handleA",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 15,0);
    tracep->declBus(c+6,0,"handleB",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 15,0);
    tracep->pushPrefix("payload", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBit(c+61,0,"clk",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+71,0,"rst",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+70,0,"user_btn",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+66,0,"uart_rx",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+69,0,"i2s_sd",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+64,0,"led",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 5,0);
    tracep->declBit(c+65,0,"uart_tx",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+67,0,"i2s_sclk",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+68,0,"i2s_ws",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+0,0,"scalar_state",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 3,0);
    tracep->declBit(c+1,0,"s3c_emit",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+2,0,"s3c_j_score",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+3,0,"s3c_mass",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+4,0,"handleK",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 15,0);
    tracep->declBus(c+5,0,"handleA",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 15,0);
    tracep->declBus(c+6,0,"handleB",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 15,0);
    tracep->declBus(c+7,0,"state_next",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 3,0);
    tracep->declBus(c+0,0,"state_q",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 3,0);
    tracep->declBus(c+8,0,"manual_state_next",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 3,0);
    tracep->declBus(c+9,0,"manual_state_q",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 3,0);
    tracep->declBit(c+10,0,"audio_mode_next",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+11,0,"audio_mode_q",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+12,0,"audio_state",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 3,0);
    tracep->declBit(c+13,0,"button_d1",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+14,0,"button_d2",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+15,0,"button_prev",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+16,0,"button_rise",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+17,0,"tick_next",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 24,0);
    tracep->declBus(c+18,0,"tick_q",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 24,0);
    tracep->declBit(c+19,0,"tick_wrap",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+20,0,"phase_next",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 15,0);
    tracep->declBus(c+21,0,"phase_q",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 15,0);
    tracep->declBit(c+1,0,"emit_w",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+5,0,"handle_a_w",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 15,0);
    tracep->declBus(c+6,0,"handle_b_w",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 15,0);
    tracep->declBit(c+22,0,"uart_event",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+23,0,"uart_start",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+24,0,"uart_baud_done",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+25,0,"uart_last_bit",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+26,0,"uart_busy_next",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+27,0,"uart_busy_q",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+28,0,"uart_baud_inc",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 7,0);
    tracep->declBus(c+29,0,"uart_baud_next",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 7,0);
    tracep->declBus(c+30,0,"uart_baud_q",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 7,0);
    tracep->declBus(c+31,0,"uart_bit_inc",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 3,0);
    tracep->declBus(c+32,0,"uart_bit_next",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 3,0);
    tracep->declBus(c+33,0,"uart_bit_q",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 3,0);
    tracep->declBus(c+34,0,"uart_frame",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 9,0);
    tracep->declBus(c+35,0,"uart_frame_tag",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 3,0);
    tracep->declBus(c+36,0,"uart_frame_payload",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 3,0);
    tracep->declBus(c+37,0,"uart_frame_tag_load",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 3,0);
    tracep->declBus(c+38,0,"uart_frame_payload_load",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 3,0);
    tracep->declBus(c+39,0,"uart_frame_load",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 9,0);
    tracep->declBit(c+40,0,"uart_byte_idx_next",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+41,0,"uart_byte_idx_q",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+42,0,"uart_all_done",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+43,0,"uart_shift_step",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 9,0);
    tracep->declBus(c+44,0,"uart_shift_next",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 9,0);
    tracep->declBus(c+45,0,"uart_shift_q",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 9,0);
    tracep->declBus(c+46,0,"sclk_div_next",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 2,0);
    tracep->declBus(c+47,0,"sclk_div_q",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 2,0);
    tracep->declBus(c+48,0,"ws_div_next",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 5,0);
    tracep->declBus(c+49,0,"ws_div_q",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 5,0);
    tracep->declBit(c+50,0,"i2s_sclk_prev",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+51,0,"i2s_sclk_rise",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+52,0,"i2s_ws_prev",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+53,0,"i2s_ws_q",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+54,0,"i2s_ws_edge",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+55,0,"i2s_bit_cnt_next",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 4,0);
    tracep->declBus(c+56,0,"i2s_bit_cnt_q",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 4,0);
    tracep->declBus(c+72,0,"i2s_shift_next",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 23,0);
    tracep->declBus(c+57,0,"i2s_shift_q",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 23,0);
    tracep->declBus(c+58,0,"i2s_sample_next",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 23,0);
    tracep->declBus(c+59,0,"i2s_sample_q",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 23,0);
    tracep->declBit(c+54,0,"i2s_valid_next",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+60,0,"i2s_valid_q",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->popPrefix();
    tracep->popPrefix();
}

VL_ATTR_COLD void VSparkleTangNano9KTop___024root__trace_init_top(VSparkleTangNano9KTop___024root* vlSelf, VerilatedVcd* tracep) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root__trace_init_top\n"); );
    VSparkleTangNano9KTop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    VSparkleTangNano9KTop___024root__trace_init_sub__TOP__0(vlSelf, tracep);
}

VL_ATTR_COLD void VSparkleTangNano9KTop___024root__trace_const_0(void* voidSelf, VerilatedVcd::Buffer* bufp);
VL_ATTR_COLD void VSparkleTangNano9KTop___024root__trace_full_0(void* voidSelf, VerilatedVcd::Buffer* bufp);
void VSparkleTangNano9KTop___024root__trace_chg_0(void* voidSelf, VerilatedVcd::Buffer* bufp);
void VSparkleTangNano9KTop___024root__trace_cleanup(void* voidSelf, VerilatedVcd* /*unused*/);

VL_ATTR_COLD void VSparkleTangNano9KTop___024root__trace_register(VSparkleTangNano9KTop___024root* vlSelf, VerilatedVcd* tracep) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root__trace_register\n"); );
    VSparkleTangNano9KTop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    tracep->addConstCb(&VSparkleTangNano9KTop___024root__trace_const_0, 0, vlSelf);
    tracep->addFullCb(&VSparkleTangNano9KTop___024root__trace_full_0, 0, vlSelf);
    tracep->addChgCb(&VSparkleTangNano9KTop___024root__trace_chg_0, 0, vlSelf);
    tracep->addCleanupCb(&VSparkleTangNano9KTop___024root__trace_cleanup, vlSelf);
}

VL_ATTR_COLD void VSparkleTangNano9KTop___024root__trace_const_0(void* voidSelf, VerilatedVcd::Buffer* bufp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root__trace_const_0\n"); );
    // Body
    VSparkleTangNano9KTop___024root* const __restrict vlSelf VL_ATTR_UNUSED = static_cast<VSparkleTangNano9KTop___024root*>(voidSelf);
    VSparkleTangNano9KTop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
}

VL_ATTR_COLD void VSparkleTangNano9KTop___024root__trace_full_0_sub_0(VSparkleTangNano9KTop___024root* vlSelf, VerilatedVcd::Buffer* bufp);

VL_ATTR_COLD void VSparkleTangNano9KTop___024root__trace_full_0(void* voidSelf, VerilatedVcd::Buffer* bufp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root__trace_full_0\n"); );
    // Body
    VSparkleTangNano9KTop___024root* const __restrict vlSelf VL_ATTR_UNUSED = static_cast<VSparkleTangNano9KTop___024root*>(voidSelf);
    VSparkleTangNano9KTop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VSparkleTangNano9KTop___024root__trace_full_0_sub_0((&vlSymsp->TOP), bufp);
}

VL_ATTR_COLD void VSparkleTangNano9KTop___024root__trace_full_0_sub_0(VSparkleTangNano9KTop___024root* vlSelf, VerilatedVcd::Buffer* bufp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    VSparkleTangNano9KTop___024root__trace_full_0_sub_0\n"); );
    VSparkleTangNano9KTop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    uint32_t* const oldp VL_ATTR_UNUSED = bufp->oldp(vlSymsp->__Vm_baseCode);
    bufp->fullCData(oldp+0,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q),4);
    bufp->fullBit(oldp+1,(vlSelfRef.SparkleTangNano9KTop__DOT__s3c_emit));
    bufp->fullIData(oldp+2,(((0U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                              ? 3U : ((1U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                       ? 2U : ((2U 
                                                == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                ? 3U
                                                : (
                                                   (3U 
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
    bufp->fullIData(oldp+3,(((0U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                              ? 0U : ((1U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                       ? 1U : ((2U 
                                                == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                ? 0U
                                                : (
                                                   (3U 
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
    bufp->fullSData(oldp+4,(((0U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                              ? 1U : ((1U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                       ? 1U : ((2U 
                                                == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                ? 1U
                                                : (
                                                   (3U 
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
    bufp->fullSData(oldp+5,(((0U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                              ? 0U : ((1U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                       ? 1U : ((2U 
                                                == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                ? 2U
                                                : (
                                                   (3U 
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
    bufp->fullSData(oldp+6,(((0U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                              ? 2U : ((1U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                       ? 1U : ((2U 
                                                == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_q))
                                                ? 0U
                                                : (
                                                   (3U 
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
    bufp->fullCData(oldp+7,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_next),4);
    bufp->fullCData(oldp+8,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__manual_state_next),4);
    bufp->fullCData(oldp+9,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__manual_state_q),4);
    bufp->fullBit(oldp+10,((1U & ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__button_rise)
                                   ? (~ (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__audio_mode_q))
                                   : (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__audio_mode_q)))));
    bufp->fullBit(oldp+11,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__audio_mode_q));
    bufp->fullCData(oldp+12,((0x0000000fU & (vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sample_q 
                                             >> 0x00000013U))),4);
    bufp->fullBit(oldp+13,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__button_d1));
    bufp->fullBit(oldp+14,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__button_d2));
    bufp->fullBit(oldp+15,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__button_prev));
    bufp->fullBit(oldp+16,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__button_rise));
    bufp->fullIData(oldp+17,((0x01ffffffU & ((IData)(1U) 
                                             + vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__tick_q))),25);
    bufp->fullIData(oldp+18,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__tick_q),25);
    bufp->fullBit(oldp+19,((0U == vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__tick_q)));
    bufp->fullSData(oldp+20,((0x0000ffffU & ((0U == vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__tick_q)
                                              ? ((IData)(0x9e37U) 
                                                 + (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__phase_q))
                                              : (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__phase_q)))),16);
    bufp->fullSData(oldp+21,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__phase_q),16);
    bufp->fullBit(oldp+22,(((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__button_rise) 
                            | (0U == vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__tick_q))));
    bufp->fullBit(oldp+23,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_start));
    bufp->fullBit(oldp+24,((0xe9U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_baud_q))));
    bufp->fullBit(oldp+25,((9U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_bit_q))));
    bufp->fullBit(oldp+26,((1U & ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_start) 
                                  | ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT____VdfgRegularize_h3c135564_0_17)
                                      ? (~ (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_all_done))
                                      : (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_busy_q))))));
    bufp->fullBit(oldp+27,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_busy_q));
    bufp->fullCData(oldp+28,((0x000000ffU & ((IData)(1U) 
                                             + (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_baud_q)))),8);
    bufp->fullCData(oldp+29,(((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_start)
                               ? 0U : ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_busy_q)
                                        ? ((0xe9U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_baud_q))
                                            ? 0U : 
                                           (0x000000ffU 
                                            & ((IData)(1U) 
                                               + (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_baud_q))))
                                        : 0U))),8);
    bufp->fullCData(oldp+30,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_baud_q),8);
    bufp->fullCData(oldp+31,((0x0000000fU & ((IData)(1U) 
                                             + (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_bit_q)))),4);
    bufp->fullCData(oldp+32,(((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_start)
                               ? 0U : (0x0000000fU 
                                       & ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT____VdfgRegularize_h3c135564_0_19)
                                           ? ((9U == (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_bit_q))
                                               ? 0U
                                               : ((IData)(1U) 
                                                  + (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_bit_q)))
                                           : (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_bit_q))))),4);
    bufp->fullCData(oldp+33,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_bit_q),4);
    bufp->fullSData(oldp+34,((0x00000200U | ((((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_byte_idx_q)
                                                ? 6U
                                                : 5U) 
                                              << 5U) 
                                             | (((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_byte_idx_q)
                                                  ? (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT____VdfgRegularize_h3c135564_0_20)
                                                  : (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_next)) 
                                                << 1U)))),10);
    bufp->fullCData(oldp+35,(((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_byte_idx_q)
                               ? 6U : 5U)),4);
    bufp->fullCData(oldp+36,(((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_byte_idx_q)
                               ? (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT____VdfgRegularize_h3c135564_0_20)
                               : (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_next))),4);
    bufp->fullCData(oldp+37,(((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_byte_idx_next)
                               ? 6U : 5U)),4);
    bufp->fullCData(oldp+38,(((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_byte_idx_next)
                               ? (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT____VdfgRegularize_h3c135564_0_20)
                               : (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__state_next))),4);
    bufp->fullSData(oldp+39,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_frame_load),10);
    bufp->fullBit(oldp+40,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_byte_idx_next));
    bufp->fullBit(oldp+41,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_byte_idx_q));
    bufp->fullBit(oldp+42,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_all_done));
    bufp->fullSData(oldp+43,((0x00000200U | (0x000001ffU 
                                             & ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_shift_q) 
                                                >> 1U)))),10);
    bufp->fullSData(oldp+44,(((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_start)
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
    bufp->fullSData(oldp+45,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__uart_shift_q),10);
    bufp->fullCData(oldp+46,((7U & ((IData)(1U) + (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__sclk_div_q)))),3);
    bufp->fullCData(oldp+47,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__sclk_div_q),3);
    bufp->fullCData(oldp+48,((0x0000003fU & ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__ws_div_q) 
                                             + (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sclk_rise)))),6);
    bufp->fullCData(oldp+49,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__ws_div_q),6);
    bufp->fullBit(oldp+50,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sclk_prev));
    bufp->fullBit(oldp+51,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sclk_rise));
    bufp->fullBit(oldp+52,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_ws_prev));
    bufp->fullBit(oldp+53,((1U & ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__ws_div_q) 
                                  >> 5U))));
    bufp->fullBit(oldp+54,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_ws_edge));
    bufp->fullCData(oldp+55,(((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_ws_edge)
                               ? 0U : (0x0000001fU 
                                       & ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_bit_cnt_q) 
                                          + (IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sclk_rise))))),5);
    bufp->fullCData(oldp+56,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_bit_cnt_q),5);
    bufp->fullIData(oldp+57,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_shift_q),24);
    bufp->fullIData(oldp+58,(((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_ws_edge)
                               ? vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_shift_q
                               : vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sample_q)),24);
    bufp->fullIData(oldp+59,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sample_q),24);
    bufp->fullBit(oldp+60,(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_valid_q));
    bufp->fullBit(oldp+61,(vlSelfRef.clk));
    bufp->fullBit(oldp+62,(vlSelfRef.rst_n));
    bufp->fullBit(oldp+63,(vlSelfRef.user_btn));
    bufp->fullCData(oldp+64,(vlSelfRef.led),6);
    bufp->fullBit(oldp+65,(vlSelfRef.uart_tx));
    bufp->fullBit(oldp+66,(vlSelfRef.uart_rx));
    bufp->fullBit(oldp+67,(vlSelfRef.i2s_sclk));
    bufp->fullBit(oldp+68,(vlSelfRef.i2s_ws));
    bufp->fullBit(oldp+69,(vlSelfRef.i2s_sd));
    bufp->fullBit(oldp+70,((1U & (~ (IData)(vlSelfRef.user_btn)))));
    bufp->fullBit(oldp+71,((1U & (~ (IData)(vlSelfRef.rst_n)))));
    bufp->fullIData(oldp+72,(((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_ws_edge)
                               ? vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_shift_q
                               : ((IData)(vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_sclk_rise)
                                   ? (((IData)(vlSelfRef.i2s_sd) 
                                       << 0x00000017U) 
                                      | (0x007fffffU 
                                         & (vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_shift_q 
                                            >> 1U)))
                                   : vlSelfRef.SparkleTangNano9KTop__DOT__payload__DOT__i2s_shift_q))),24);
}
