// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Model implementation (design independent parts)

#include "VSparkleTangNano9KTop__pch.h"
#include "verilated_vcd_c.h"

//============================================================
// Constructors

VSparkleTangNano9KTop::VSparkleTangNano9KTop(VerilatedContext* _vcontextp__, const char* _vcname__)
    : VerilatedModel{*_vcontextp__}
    , vlSymsp{new VSparkleTangNano9KTop__Syms(contextp(), _vcname__, this)}
    , clk{vlSymsp->TOP.clk}
    , rst_n{vlSymsp->TOP.rst_n}
    , user_btn{vlSymsp->TOP.user_btn}
    , led{vlSymsp->TOP.led}
    , uart_tx{vlSymsp->TOP.uart_tx}
    , uart_rx{vlSymsp->TOP.uart_rx}
    , i2s_sclk{vlSymsp->TOP.i2s_sclk}
    , i2s_ws{vlSymsp->TOP.i2s_ws}
    , i2s_sd{vlSymsp->TOP.i2s_sd}
    , rootp{&(vlSymsp->TOP)}
{
    // Register model with the context
    contextp()->addModel(this);
    contextp()->traceBaseModelCbAdd(
        [this](VerilatedTraceBaseC* tfp, int levels, int options) { traceBaseModel(tfp, levels, options); });
}

VSparkleTangNano9KTop::VSparkleTangNano9KTop(const char* _vcname__)
    : VSparkleTangNano9KTop(Verilated::threadContextp(), _vcname__)
{
}

//============================================================
// Destructor

VSparkleTangNano9KTop::~VSparkleTangNano9KTop() {
    delete vlSymsp;
}

//============================================================
// Evaluation function

#ifdef VL_DEBUG
void VSparkleTangNano9KTop___024root___eval_debug_assertions(VSparkleTangNano9KTop___024root* vlSelf);
#endif  // VL_DEBUG
void VSparkleTangNano9KTop___024root___eval_static(VSparkleTangNano9KTop___024root* vlSelf);
void VSparkleTangNano9KTop___024root___eval_initial(VSparkleTangNano9KTop___024root* vlSelf);
void VSparkleTangNano9KTop___024root___eval_settle(VSparkleTangNano9KTop___024root* vlSelf);
void VSparkleTangNano9KTop___024root___eval(VSparkleTangNano9KTop___024root* vlSelf);

void VSparkleTangNano9KTop::eval_step() {
    VL_DEBUG_IF(VL_DBG_MSGF("+++++TOP Evaluate VSparkleTangNano9KTop::eval_step\n"); );
#ifdef VL_DEBUG
    // Debug assertions
    VSparkleTangNano9KTop___024root___eval_debug_assertions(&(vlSymsp->TOP));
#endif  // VL_DEBUG
    vlSymsp->__Vm_activity = true;
    vlSymsp->__Vm_deleter.deleteAll();
    if (VL_UNLIKELY(!vlSymsp->__Vm_didInit)) {
        VL_DEBUG_IF(VL_DBG_MSGF("+ Initial\n"););
        VSparkleTangNano9KTop___024root___eval_static(&(vlSymsp->TOP));
        VSparkleTangNano9KTop___024root___eval_initial(&(vlSymsp->TOP));
        VSparkleTangNano9KTop___024root___eval_settle(&(vlSymsp->TOP));
        vlSymsp->__Vm_didInit = true;
    }
    VL_DEBUG_IF(VL_DBG_MSGF("+ Eval\n"););
    VSparkleTangNano9KTop___024root___eval(&(vlSymsp->TOP));
    // Evaluate cleanup
    Verilated::endOfEval(vlSymsp->__Vm_evalMsgQp);
}

//============================================================
// Events and timing
bool VSparkleTangNano9KTop::eventsPending() { return false; }

uint64_t VSparkleTangNano9KTop::nextTimeSlot() {
    VL_FATAL_MT(__FILE__, __LINE__, "", "No delays in the design");
    return 0;
}

//============================================================
// Utilities

const char* VSparkleTangNano9KTop::name() const {
    return vlSymsp->name();
}

//============================================================
// Invoke final blocks

void VSparkleTangNano9KTop___024root___eval_final(VSparkleTangNano9KTop___024root* vlSelf);

VL_ATTR_COLD void VSparkleTangNano9KTop::final() {
    VSparkleTangNano9KTop___024root___eval_final(&(vlSymsp->TOP));
}

//============================================================
// Implementations of abstract methods from VerilatedModel

const char* VSparkleTangNano9KTop::hierName() const { return vlSymsp->name(); }
const char* VSparkleTangNano9KTop::modelName() const { return "VSparkleTangNano9KTop"; }
unsigned VSparkleTangNano9KTop::threads() const { return 1; }
void VSparkleTangNano9KTop::prepareClone() const { contextp()->prepareClone(); }
void VSparkleTangNano9KTop::atClone() const {
    contextp()->threadPoolpOnClone();
}
std::unique_ptr<VerilatedTraceConfig> VSparkleTangNano9KTop::traceConfig() const {
    return std::unique_ptr<VerilatedTraceConfig>{new VerilatedTraceConfig{false, false, false}};
};

//============================================================
// Trace configuration

void VSparkleTangNano9KTop___024root__trace_decl_types(VerilatedVcd* tracep);

void VSparkleTangNano9KTop___024root__trace_init_top(VSparkleTangNano9KTop___024root* vlSelf, VerilatedVcd* tracep);

VL_ATTR_COLD static void trace_init(void* voidSelf, VerilatedVcd* tracep, uint32_t code) {
    // Callback from tracep->open()
    VSparkleTangNano9KTop___024root* const __restrict vlSelf VL_ATTR_UNUSED = static_cast<VSparkleTangNano9KTop___024root*>(voidSelf);
    VSparkleTangNano9KTop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    if (!vlSymsp->_vm_contextp__->calcUnusedSigs()) {
        VL_FATAL_MT(__FILE__, __LINE__, __FILE__,
            "Turning on wave traces requires Verilated::traceEverOn(true) call before time 0.");
    }
    vlSymsp->__Vm_baseCode = code;
    tracep->pushPrefix(vlSymsp->name(), VerilatedTracePrefixType::SCOPE_MODULE);
    VSparkleTangNano9KTop___024root__trace_decl_types(tracep);
    VSparkleTangNano9KTop___024root__trace_init_top(vlSelf, tracep);
    tracep->popPrefix();
}

VL_ATTR_COLD void VSparkleTangNano9KTop___024root__trace_register(VSparkleTangNano9KTop___024root* vlSelf, VerilatedVcd* tracep);

VL_ATTR_COLD void VSparkleTangNano9KTop::traceBaseModel(VerilatedTraceBaseC* tfp, int levels, int options) {
    (void)levels; (void)options;
    VerilatedVcdC* const stfp = dynamic_cast<VerilatedVcdC*>(tfp);
    if (VL_UNLIKELY(!stfp)) {
        vl_fatal(__FILE__, __LINE__, __FILE__,"'VSparkleTangNano9KTop::trace()' called on non-VerilatedVcdC object;"
            " use --trace-fst with VerilatedFst object, and --trace-vcd with VerilatedVcd object");
    }
    stfp->spTrace()->addModel(this);
    stfp->spTrace()->addInitCb(&trace_init, &(vlSymsp->TOP), name(), false, 73);
    VSparkleTangNano9KTop___024root__trace_register(&(vlSymsp->TOP), stfp->spTrace());
}
