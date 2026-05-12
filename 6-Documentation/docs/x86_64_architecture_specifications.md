# x86_64 Architecture Specifications Comparison

## Overview
This document catalogs the official x86_64 (AMD64/Intel 64) architecture specifications from both Intel and AMD, and provides a comparison of their implementations.

## Official Specification Sources

### Intel Specifications
- **Intel® 64 and IA-32 Architectures Software Developer's Manual**
  - URL: https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html
  - Available as:
    - Combined volume (all 4 volumes in one)
    - Four-volume set
    - Ten-volume set
  - Volume 1: Basic Architecture
  - Volume 2: Instruction Set Reference (A-M)
  - Volume 2: Instruction Set Reference (N-Z)
  - Volume 3: System Programming Guide
  - Volume 4: Model-Specific Registers

### AMD Specifications
- **AMD64 Architecture Programmer's Manual**
  - Combined Volumes 1-5: https://kib.kiev.ua/x86docs/AMD/AMD64/40332-r4.00.pdf (Rev 4.00, April 2020)
  - Volume 1: Application Programming (Pub 24592)
  - Volume 2: System Programming (Pub 24593)
  - Volume 3: General-Purpose and System Instructions (Pub 24594)
  - Volume 4: 128-Bit Media and x87 Floating-Point Instructions (Pub 26568)
  - Volume 5: 64-Bit Media and x87 Floating-Point Instructions (Pub 26569)
- **AMD64 Technology Documentation Portal**: https://docs.amd.com/

## Key Architectural Differences

### Origin and Naming
- **AMD64**: Originally developed by AMD as an extension to x86 architecture
- **Intel 64**: Intel's implementation of AMD64 (formerly called EM64T)
- Both are binary compatible at the instruction set level

### Register Extensions
Both implementations extend the x86 architecture with:
- 64-bit general-purpose registers (RAX, RBX, RCX, RDX, RSI, RDI, RBP, RSP)
- 8 additional 64-bit registers (R8-R15)
- 64-bit instruction pointer (RIP)
- 64-bit flags register (RFLAGS)

### Mode of Operation
- **Legacy Mode**: Runs existing 16-bit and 32-bit x86 applications
- **Long Mode**:
  - 64-bit mode (native 64-bit operation)
  - Compatibility mode (runs 32-bit protected mode applications)

### Memory Addressing
- **Virtual Address**: 48 bits (current implementations)
- **Physical Address**: Up to 52 bits (varies by implementation)
- **Canonical Addressing**: Address bits 48-63 must be sign-extended

## Implementation-Specific Features

### Intel-Specific Extensions
- Intel Virtualization Technology (Intel VT-x)
- Intel Trusted Execution Technology (TXT)
- Intel SGX (Software Guard Extensions)
- Intel MPX (Memory Protection Extensions)
- Intel TSX (Transactional Synchronization Extensions)

### AMD-Specific Extensions
- AMD-V (AMD Virtualization)
- AMD Secure Processor / Platform Security Processor (PSP)
- AMD SME (Secure Memory Encryption)
- AMD SEV (Secure Encrypted Virtualization)
- CLZERO (Cache Line Zero instruction)

## Research Stack Status
The research stack does not currently contain local copies of these specification documents. The specifications must be accessed from the official vendor URLs above.

## References
- Intel SDM: https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html
- AMD64 Manuals: https://kib.kiev.ua/x86docs/AMD/AMD64/
