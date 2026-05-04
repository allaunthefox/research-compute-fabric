// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See VSparkleTangNano9KTop.h for the primary calling header

#include "VSparkleTangNano9KTop__pch.h"

void VSparkleTangNano9KTop___024root___ctor_var_reset(VSparkleTangNano9KTop___024root* vlSelf);

VSparkleTangNano9KTop___024root::VSparkleTangNano9KTop___024root(VSparkleTangNano9KTop__Syms* symsp, const char* namep)
 {
    vlSymsp = symsp;
    vlNamep = strdup(namep);
    // Reset structure values
    VSparkleTangNano9KTop___024root___ctor_var_reset(this);
}

void VSparkleTangNano9KTop___024root::__Vconfigure(bool first) {
    (void)first;  // Prevent unused variable warning
}

VSparkleTangNano9KTop___024root::~VSparkleTangNano9KTop___024root() {
    VL_DO_DANGLING(std::free(const_cast<char*>(vlNamep)), vlNamep);
}
