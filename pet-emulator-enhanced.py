import curses
import time
import threading
from typing import Dict, List, Optional, Tuple, Union

class CPU6502:
    """Emulates a MOS 6502 processor with full instruction set and addressing modes."""
    
    def __init__(self):
        # Main registers
        self.A = 0       # Accumulator
        self.X = 0       # X index register
        self.Y = 0       # Y index register
        self.PC = 0      # Program counter
        self.SP = 0xFF   # Stack pointer (starts at 0xFF, decrements when pushing)
        
        # Status register flags (P register)
        self.C = 0  # Carry
        self.Z = 0  # Zero
        self.I = 0  # Interrupt disable
        self.D = 0  # Decimal mode
        self.B = 0  # Break command
        self.V = 0  # Overflow
        self.N = 0  # Negative
        
        # Cycle counting and timing
        self.cycles = 0
        self.total_cycles = 0
        
        # Interrupt handling
        self.irq_pending = False
        self.nmi_pending = False
        
        # Initialize instruction table
        self._init_instruction_table()
    
    def _init_instruction_table(self):
        """Initialize the full 6502 instruction set."""
        self.instructions = {
            # Load/Store Operations
            0xA9: self.LDA_immediate,  # LDA Immediate
            0xA5: self.LDA_zeropage,   # LDA Zero Page
            0xB5: self.LDA_zeropageX,  # LDA Zero Page,X
            0xAD: self.LDA_absolute,   # LDA Absolute
            0xBD: self.LDA_absoluteX,  # LDA Absolute,X
            0xB9: self.LDA_absoluteY,  # LDA Absolute,Y
            0xA1: self.LDA_indirectX,  # LDA (Indirect,X)
            0xB1: self.LDA_indirectY,  # LDA (Indirect),Y
            
            0xA2: self.LDX_immediate,  # LDX Immediate
            0xA6: self.LDX_zeropage,   # LDX Zero Page
            0xB6: self.LDX_zeropageY,  # LDX Zero Page,Y
            0xAE: self.LDX_absolute,   # LDX Absolute
            0xBE: self.LDX_absoluteY,  # LDX Absolute,Y
            
            0xA0: self.LDY_immediate,  # LDY Immediate
            0xA4: self.LDY_zeropage,   # LDY Zero Page
            0xB4: self.LDY_zeropageX,  # LDY Zero Page,X
            0xAC: self.LDY_absolute,   # LDY Absolute
            0xBC: self.LDY_absoluteX,  # LDY Absolute,X
            
            0x85: self.STA_zeropage,   # STA Zero Page
            0x95: self.STA_zeropageX,  # STA Zero Page,X
            0x8D: self.STA_absolute,   # STA Absolute
            0x9D: self.STA_absoluteX,  # STA Absolute,X
            0x99: self.STA_absoluteY,  # STA Absolute,Y
            0x81: self.STA_indirectX,  # STA (Indirect,X)
            0x91: self.STA_indirectY,  # STA (Indirect),Y
            
            0x86: self.STX_zeropage,   # STX Zero Page
            0x96: self.STX_zeropageY,  # STX Zero Page,Y
            0x8E: self.STX_absolute,   # STX Absolute
            
            0x84: self.STY_zeropage,   # STY Zero Page
            0x94: self.STY_zeropageX,  # STY Zero Page,X
            0x8C: self.STY_absolute,   # STY Absolute
            
            # Register Transfers
            0xAA: self.TAX,  # TAX
            0x8A: self.TXA,  # TXA
            0xA8: self.TAY,  # TAY
            0x98: self.TYA,  # TYA
            0xBA: self.TSX,  # TSX
            0x9A: self.TXS,  # TXS
            
            # Stack Operations
            0x48: self.PHA,  # PHA
            0x68: self.PLA,  # PLA
            0x08: self.PHP,  # PHP
            0x28: self.PLP,  # PLP
            
            # Logical Operations
            0x29: self.AND_immediate,  # AND Immediate
            0x25: self.AND_zeropage,   # AND Zero Page
            0x35: self.AND_zeropageX,  # AND Zero Page,X
            0x2D: self.AND_absolute,   # AND Absolute
            0x3D: self.AND_absoluteX,  # AND Absolute,X
            0x39: self.AND_absoluteY,  # AND Absolute,Y
            0x21: self.AND_indirectX,  # AND (Indirect,X)
            0x31: self.AND_indirectY,  # AND (Indirect),Y
            
            0x09: self.ORA_immediate,  # ORA Immediate
            0x05: self.ORA_zeropage,   # ORA Zero Page
            0x15: self.ORA_zeropageX,  # ORA Zero Page,X
            0x0D: self.ORA_absolute,   # ORA Absolute
            0x1D: self.ORA_absoluteX,  # ORA Absolute,X
            0x19: self.ORA_absoluteY,  # ORA Absolute,Y
            0x01: self.ORA_indirectX,  # ORA (Indirect,X)
            0x11: self.ORA_indirectY,  # ORA (Indirect),Y
            
            0x49: self.EOR_immediate,  # EOR Immediate
            0x45: self.EOR_zeropage,   # EOR Zero Page
            0x55: self.EOR_zeropageX,  # EOR Zero Page,X
            0x4D: self.EOR_absolute,   # EOR Absolute
            0x5D: self.EOR_absoluteX,  # EOR Absolute,X
            0x59: self.EOR_absoluteY,  # EOR Absolute,Y
            0x41: self.EOR_indirectX,  # EOR (Indirect,X)
            0x51: self.EOR_indirectY,  # EOR (Indirect),Y
            
            0x24: self.BIT_zeropage,   # BIT Zero Page
            0x2C: self.BIT_absolute,   # BIT Absolute
            
            # Arithmetic Operations
            0x69: self.ADC_immediate,  # ADC Immediate
            0x65: self.ADC_zeropage,   # ADC Zero Page
            0x75: self.ADC_zeropageX,  # ADC Zero Page,X
            0x6D: self.ADC_absolute,   # ADC Absolute
            0x7D: self.ADC_absoluteX,  # ADC Absolute,X
            0x79: self.ADC_absoluteY,  # ADC Absolute,Y
            0x61: self.ADC_indirectX,  # ADC (Indirect,X)
            0x71: self.ADC_indirectY,  # ADC (Indirect),Y
            
            0xE9: self.SBC_immediate,  # SBC Immediate
            0xE5: self.SBC_zeropage,   # SBC Zero Page
            0xF5: self.SBC_zeropageX,  # SBC Zero Page,X
            0xED: self.SBC_absolute,   # SBC Absolute
            0xFD: self.SBC_absoluteX,  # SBC Absolute,X
            0xF9: self.SBC_absoluteY,  # SBC Absolute,Y
            0xE1: self.SBC_indirectX,  # SBC (Indirect,X)
            0xF1: self.SBC_indirectY,  # SBC (Indirect),Y
            
            0xC9: self.CMP_immediate,  # CMP Immediate
            0xC5: self.CMP_zeropage,   # CMP Zero Page
            0xD5: self.CMP_zeropageX,  # CMP Zero Page,X
            0xCD: self.CMP_absolute,   # CMP Absolute
            0xDD: self.CMP_absoluteX,  # CMP Absolute,X
            0xD9: self.CMP_absoluteY,  # CMP Absolute,Y
            0xC1: self.CMP_indirectX,  # CMP (Indirect,X)
            0xD1: self.CMP_indirectY,  # CMP (Indirect),Y
            
            0xE0: self.CPX_immediate,  # CPX Immediate
            0xE4: self.CPX_zeropage,   # CPX Zero Page
            0xEC: self.CPX_absolute,   # CPX Absolute
            
            0xC0: self.CPY_immediate,  # CPY Immediate
            0xC4: self.CPY_zeropage,   # CPY Zero Page
            0xCC: self.CPY_absolute,   # CPY Absolute
            
            # Increments & Decrements
            0xE6: self.INC_zeropage,   # INC Zero Page
            0xF6: self.INC_zeropageX,  # INC Zero Page,X
            0xEE: self.INC_absolute,   # INC Absolute
            0xFE: self.INC_absoluteX,  # INC Absolute,X
            
            0xE8: self.INX,  # INX
            0xC8: self.INY,  # INY
            
            0xC6: self.DEC_zeropage,   # DEC Zero Page
            0xD6: self.DEC_zeropageX,  # DEC Zero Page,X
            0xCE: self.DEC_absolute,   # DEC Absolute
            0xDE: self.DEC_absoluteX,  # DEC Absolute,X
            
            0xCA: self.DEX,  # DEX
            0x88: self.DEY,  # DEY
            
            # Shifts
            0x0A: self.ASL_accumulator,  # ASL Accumulator
            0x06: self.ASL_zeropage,     # ASL Zero Page
            0x16: self.ASL_zeropageX,    # ASL Zero Page,X
            0x0E: self.ASL_absolute,     # ASL Absolute
            0x1E: self.ASL_absoluteX,    # ASL Absolute,X
            
            0x4A: self.LSR_accumulator,  # LSR Accumulator
            0x46: self.LSR_zeropage,     # LSR Zero Page
            0x56: self.LSR_zeropageX,    # LSR Zero Page,X
            0x4E: self.LSR_absolute,     # LSR Absolute
            0x5E: self.LSR_absoluteX,    # LSR Absolute,X
            
            0x2A: self.ROL_accumulator,  # ROL Accumulator
            0x26: self.ROL_zeropage,     # ROL Zero Page
            0x36: self.ROL_zeropageX,    # ROL Zero Page,X
            0x2E: self.ROL_absolute,     # ROL Absolute
            0x3E: self.ROL_absoluteX,    # ROL Absolute,X
            
            0x6A: self.ROR_accumulator,  # ROR Accumulator
            0x66: self.ROR_zeropage,     # ROR Zero Page
            0x76: self.ROR_zeropageX,    # ROR Zero Page,X
            0x6E: self.ROR_absolute,     # ROR Absolute
            0x7E: self.ROR_absoluteX,    # ROR Absolute,X
            
            # Jumps & Calls
            0x4C: self.JMP_absolute,   # JMP Absolute
            0x6C: self.JMP_indirect,   # JMP Indirect
            0x20: self.JSR_absolute,   # JSR Absolute
            0x60: self.RTS,            # RTS
            
            # Branches
            0x90: self.BCC,  # BCC
            0xB0: self.BCS,  # BCS
            0xF0: self.BEQ,  # BEQ
            0x30: self.BMI,  # BMI
            0xD0: self.BNE,  # BNE
            0x10: self.BPL,  # BPL
            0x50: self.BVC,  # BVC
            0x70: self.BVS,  # BVS
            
            # Status Flag Changes
            0x18: self.CLC,  # CLC
            0x38: self.SEC,  # SEC
            0x58: self.CLI,  # CLI
            0x78: self.SEI,  # SEI
            0xB8: self.CLV,  # CLV
            0xD8: self.CLD,  # CLD
            0xF8: self.SED,  # SED
            
            # System Functions
            0x00: self.BRK,  # BRK
            0x40: self.RTI,  # RTI
            0xEA: self.NOP,  # NOP
        }
    
    def get_status(self) -> int:
        """Get the processor status as a byte."""
        status = (self.C | (self.Z << 1) | (self.I << 2) | (self.D << 3) |
                 (1 << 5) | (self.V << 6) | (self.N << 7))  # Bit 5 always set
        return status
    
    def set_status(self, value: int) -> None:
        """Set the processor status from a byte."""
        self.C = value & 1
        self.Z = (value >> 1) & 1
        self.I = (value >> 2) & 1
        self.D = (value >> 3) & 1
        self.B = (value >> 4) & 1  # Unused in actual 6502
        # Bit 5 ignored (always 1)
        self.V = (value >> 6) & 1
        self.N = (value >> 7) & 1
    
    def update_ZN(self, value: int) -> None:
        """Update Zero and Negative flags based on value."""
        self.Z = 1 if (value & 0xFF) == 0 else 0
        self.N = 1 if (value & 0x80) else 0
    
    # === Addressing Modes ===
    def immediate(self, memory) -> int:
        """Immediate addressing mode."""
        value = memory.read(self.PC)
        self.PC += 1
        return value
    
    def zeropage(self, memory) -> int:
        """Zero page addressing mode."""
        addr = memory.read(self.PC)
        self.PC += 1
        return addr
    
    def zeropageX(self, memory) -> int:
        """Zero page with X offset addressing mode."""
        addr = (memory.read(self.PC) + self.X) & 0xFF
        self.PC += 1
        return addr
    
    def zeropageY(self, memory) -> int:
        """Zero page with Y offset addressing mode."""
        addr = (memory.read(self.PC) + self.Y) & 0xFF
        self.PC += 1
        return addr
    
    def absolute(self, memory) -> int:
        """Absolute addressing mode."""
        low = memory.read(self.PC)
        self.PC += 1
        high = memory.read(self.PC)
        self.PC += 1
        return (high << 8) | low
    
    def absoluteX(self, memory, check_page_cross=True) -> Tuple[int, bool]:
        """Absolute with X offset addressing mode."""
        low = memory.read(self.PC)
        self.PC += 1
        high = memory.read(self.PC)
        self.PC += 1
        
        base = (high << 8) | low
        addr = (base + self.X) & 0xFFFF
        
        # Check page crossing (adds a cycle if crossed)
        page_crossed = False
        if check_page_cross:
            page_crossed = (base & 0xFF00) != (addr & 0xFF00)
        
        return addr, page_crossed
    
    def absoluteY(self, memory, check_page_cross=True) -> Tuple[int, bool]:
        """Absolute with Y offset addressing mode."""
        low = memory.read(self.PC)
        self.PC += 1
        high = memory.read(self.PC)
        self.PC += 1
        
        base = (high << 8) | low
        addr = (base + self.Y) & 0xFFFF
        
        # Check page crossing (adds a cycle if crossed)
        page_crossed = False
        if check_page_cross:
            page_crossed = (base & 0xFF00) != (addr & 0xFF00)
        
        return addr, page_crossed
    
    def indirect(self, memory) -> int:
        """Indirect addressing mode (JMP only)."""
        addr_ptr = self.absolute(memory)
        
        # 6502 bug: If address is on page boundary, high byte is fetched from
        # start of the page rather than next page
        if (addr_ptr & 0xFF) == 0xFF:
            low = memory.read(addr_ptr)
            high = memory.read(addr_ptr & 0xFF00)
        else:
            low = memory.read(addr_ptr)
            high = memory.read(addr_ptr + 1)
        
        return (high << 8) | low
    
    def indirectX(self, memory) -> int:
        """Pre-indexed indirect addressing mode."""
        ptr = (memory.read(self.PC) + self.X) & 0xFF
        self.PC += 1
        
        # Wraparound in zero page
        low = memory.read(ptr & 0xFF)
        high = memory.read((ptr + 1) & 0xFF)
        
        return (high << 8) | low
    
    def indirectY(self, memory, check_page_cross=True) -> Tuple[int, bool]:
        """Post-indexed indirect addressing mode."""
        ptr = memory.read(self.PC)
        self.PC += 1
        
        # Wraparound in zero page
        low = memory.read(ptr & 0xFF)
        high = memory.read((ptr + 1) & 0xFF)
        
        base = (high << 8) | low
        addr = (base + self.Y) & 0xFFFF
        
        # Check page crossing (adds a cycle if crossed)
        page_crossed = False
        if check_page_cross:
            page_crossed = (base & 0xFF00) != (addr & 0xFF00)
        
        return addr, page_crossed
    
    # === Instruction Implementation ===
    # Load/Store Operations
    def LDA_immediate(self, memory) -> None:
        self.A = self.immediate(memory)
        self.update_ZN(self.A)
        self.cycles += 2
    
    def LDA_zeropage(self, memory) -> None:
        addr = self.zeropage(memory)
        self.A = memory.read(addr)
        self.update_ZN(self.A)
        self.cycles += 3
    
    def LDA_zeropageX(self, memory) -> None:
        addr = self.zeropageX(memory)
        self.A = memory.read(addr)
        self.update_ZN(self.A)
        self.cycles += 4
    
    def LDA_absolute(self, memory) -> None:
        addr = self.absolute(memory)
        self.A = memory.read(addr)
        self.update_ZN(self.A)
        self.cycles += 4
    
    def LDA_absoluteX(self, memory) -> None:
        addr, page_crossed = self.absoluteX(memory)
        self.A = memory.read(addr)
        self.update_ZN(self.A)
        self.cycles += 4 + (1 if page_crossed else 0)
    
    def LDA_absoluteY(self, memory) -> None:
        addr, page_crossed = self.absoluteY(memory)
        self.A = memory.read(addr)
        self.update_ZN(self.A)
        self.cycles += 4 + (1 if page_crossed else 0)
    
    def LDA_indirectX(self, memory) -> None:
        addr = self.indirectX(memory)
        self.A = memory.read(addr)
        self.update_ZN(self.A)
        self.cycles += 6
    
    def LDA_indirectY(self, memory) -> None:
        addr, page_crossed = self.indirectY(memory)
        self.A = memory.read(addr)
        self.update_ZN(self.A)
        self.cycles += 5 + (1 if page_crossed else 0)
    
    def LDX_immediate(self, memory) -> None:
        self.X = self.immediate(memory)
        self.update_ZN(self.X)
        self.cycles += 2
    
    def LDX_zeropage(self, memory) -> None:
        addr = self.zeropage(memory)
        self.X = memory.read(addr)
        self.update_ZN(self.X)
        self.cycles += 3
    
    def LDX_zeropageY(self, memory) -> None:
        addr = self.zeropageY(memory)
        self.X = memory.read(addr)
        self.update_ZN(self.X)
        self.cycles += 4
    
    def LDX_absolute(self, memory) -> None:
        addr = self.absolute(memory)
        self.X = memory.read(addr)
        self.update_ZN(self.X)
        self.cycles += 4
    
    def LDX_absoluteY(self, memory) -> None:
        addr, page_crossed = self.absoluteY(memory)
        self.X = memory.read(addr)
        self.update_ZN(self.X)
        self.cycles += 4 + (1 if page_crossed else 0)
    
    def LDY_immediate(self, memory) -> None:
        self.Y = self.immediate(memory)
        self.update_ZN(self.Y)
        self.cycles += 2
    
    def LDY_zeropage(self, memory) -> None:
        addr = self.zeropage(memory)
        self.Y = memory.read(addr)
        self.update_ZN(self.Y)
        self.cycles += 3
    
    def LDY_zeropageX(self, memory) -> None:
        addr = self.zeropageX(memory)
        self.Y = memory.read(addr)
        self.update_ZN(self.Y)
        self.cycles += 4
    
    def LDY_absolute(self, memory) -> None:
        addr = self.absolute(memory)
        self.Y = memory.read(addr)
        self.update_ZN(self.Y)
        self.cycles += 4
    
    def LDY_absoluteX(self, memory) -> None:
        addr, page_crossed = self.absoluteX(memory)
        self.Y = memory.read(addr)
        self.update_ZN(self.Y)
        self.cycles += 4 + (1 if page_crossed else 0)
    
    def STA_zeropage(self, memory) -> None:
        addr = self.zeropage(memory)
        memory.write(addr, self.A)
        self.cycles += 3
    
    def STA_zeropageX(self, memory) -> None:
        addr = self.zeropageX(memory)
        memory.write(addr, self.A)
        self.cycles += 4
    
    def STA_absolute(self, memory) -> None:
        addr = self.absolute(memory)
        memory.write(addr, self.A)
        self.cycles += 4
    
    def STA_absoluteX(self, memory) -> None:
        addr, _ = self.absoluteX(memory, False)  # No page crossing check for stores
        memory.write(addr, self.A)
        self.cycles += 5  # Always 5 cycles
    
    def STA_absoluteY(self, memory) -> None:
        addr, _ = self.absoluteY(memory, False)  # No page crossing check for stores
        memory.write(addr, self.A)
        self.cycles += 5  # Always 5 cycles
    
    def STA_indirectX(self, memory) -> None:
        addr = self.indirectX(memory)
        memory.write(addr, self.A)
        self.cycles += 6
    
    def STA_indirectY(self, memory) -> None:
        addr, _ = self.indirectY(memory, False)  # No page crossing check for stores
        memory.write(addr, self.A)
        self.cycles += 6  # Always 6 cycles
    
    def STX_zeropage(self, memory) -> None:
        addr = self.zeropage(memory)
        memory.write(addr, self.X)
        self.cycles += 3
    
    def STX_zeropageY(self, memory) -> None:
        addr = self.zeropageY(memory)
        memory.write(addr, self.X)
        self.cycles += 4
    
    def STX_absolute(self, memory) -> None:
        addr = self.absolute(memory)
        memory.write(addr, self.X)
        self.cycles += 4
    
    def STY_zeropage(self, memory) -> None:
        addr = self.zeropage(memory)
        memory.write(addr, self.Y)
        self.cycles += 3
    
    def STY_zeropageX(self, memory) -> None:
        addr = self.zeropageX(memory)
        memory.write(addr, self.Y)
        self.cycles += 4
    
    def STY_absolute(self, memory) -> None:
        addr = self.absolute(memory)
        memory.write(addr, self.Y)
        self.cycles += 4
    
    # Register Transfers
    def TAX(self, memory) -> None:
        self.X = self.A
        self.update_ZN(self.X)
        self.cycles += 2
    
    def TXA(self, memory) -> None:
        self.A = self.X
        self.update_ZN(self.A)
        self.cycles += 2
    
    def TAY(self, memory) -> None:
        self.Y = self.A
        self.update_ZN(self.Y)
        self.cycles += 2
    
    def TYA(self, memory) -> None:
        self.A = self.Y
        self.update_ZN(self.A)
        self.cycles += 2
    
    def TSX(self, memory) -> None:
        self.X = self.SP
        self.update_ZN(self.X)
        self.cycles += 2
    
    def TXS(self, memory) -> None:
        self.SP = self.X
        self.cycles += 2  # Note: flags not affected
    
    # Stack Operations
    def PHA(self, memory) -> None:
        memory.write(0x100 + self.SP, self.A)
        self.SP = (self.SP - 1) & 0xFF
        self.cycles += 3
    
    def PLA(self, memory) -> None:
        self.SP = (self.SP + 1) & 0xFF
        self.A = memory.read(0x100 + self.SP)
        self.update_ZN(self.A)
        self.cycles += 4
    
    def PHP(self, memory) -> None:
        # Push status with B flag set
        status = self.get_status() | 0x10  # Set B flag
        memory.write(0x100 + self.SP, status)
        self.SP = (self.SP - 1) & 0xFF
        self.cycles += 3
    
    def PLP(self, memory) -> None:
        self.SP = (self.SP + 1) & 0xFF
        status = memory.read(0x100 + self.SP)
        self.set_status(status)
        self.cycles += 4
    
    # Logical Operations
    def AND_immediate(self, memory) -> None:
        self.A &= self.immediate(memory)
        self.update_ZN(self.A)
        self.cycles += 2
    
    def AND_zeropage(self, memory) -> None:
        addr = self.zeropage(memory)
        self.A &= memory.read(addr)
        self.update_ZN(self.A)
        self.cycles += 3
    
    def AND_zeropageX(self, memory) -> None:
        addr = self.zeropageX(memory)
        self.A &= memory.read(addr)
        self.update_ZN(self.A)
        self.cycles += 4
    
    def AND_absolute(self, memory) -> None:
        addr = self.absolute(memory)
        self.A &= memory.read(addr)
        self.update_ZN(self.A)
        self.cycles += 4
    
    def AND_absoluteX(self, memory) -> None:
        addr, page_crossed = self.absoluteX(memory)
        self.A &= memory.read(addr)
        self.update_ZN(self.A)
        self.cycles += 4 + (1 if page_crossed else 0)
    
    def AND_absoluteY(self, memory) -> None:
        addr, page_crossed = self.absoluteY(memory)
        self.A &= memory.read(addr)
        self.update_ZN(self.A)
        self.cycles += 4 + (1 if page_crossed else 0)
    
    def AND_indirectX(self, memory) -> None:
        addr = self.indirectX(memory)
        self.A &= memory.read(addr)
        self.update_ZN(self.A)
        self.cycles += 6
    
    def AND_indirectY(self, memory) -> None:
        addr, page_crossed = self.indirectY(memory)
        self.A &= memory.read(addr)
        self.update_ZN(self.A)
        self.cycles += 5 + (1 if page_crossed else 0)
    
    def ORA_immediate(self, memory) -> None:
        self.A |= self.immediate(memory)
        self.update_ZN(self.A)
        self.cycles += 2
    
    def ORA_zeropage(self, memory) -> None:
        addr = self.zeropage(memory)
        self.A |= memory.read(addr)
        self.update_ZN(self.A)
        self.cycles += 3
    
    def ORA_zeropageX(self, memory) -> None:
        addr = self.zeropageX(memory)
        self.A |= memory.read(addr)
        self.update_ZN(self.A)
        self.cycles += 4
    
    def ORA_absolute(self, memory) -> None:
        addr = self.absolute(memory)
        self.A |= memory.read(addr)
        self.update_ZN(self.A)
        self.cycles += 4
    
    def ORA_absoluteX(self, memory) -> None:
        addr, page_crossed = self.absoluteX(memory)
        self.A |= memory.read(addr)
        self.update_ZN(self.A)
        self.cycles += 4 + (1 if page_crossed else 0)
    
    def ORA_absoluteY(self, memory) -> None:
        addr, page_crossed = self.absoluteY(memory)
        self.A |= memory.read(addr)
        self.update_ZN(self.A)
        self.cycles += 4 + (1 if page_crossed else 0)
    
    def ORA_indirectX(self, memory) -> None:
        addr = self.indirectX(memory)
        self.A |= memory.read(addr)
        self.update_ZN(self.A)
        self.cycles += 6
    
    def ORA_indirectY(self, memory) -> None:
        addr, page_crossed = self.indirectY(memory)
        self.A |= memory.read(addr)
        self.update_ZN(self.A)
        self.cycles += 5 + (1 if page_crossed else 0)
    
    def EOR_immediate(self, memory) -> None:
        self.A ^= self.immediate(memory)
        self.update_ZN(self.A)
        self.cycles += 2
    
    def EOR_zeropage(self, memory) -> None:
        addr = self.zeropage(memory)
        self.A ^= memory.read(addr)
        self.update_ZN(self.A)
        self.cycles += 3
    
    def EOR_zeropageX(self, memory) -> None:
        addr = self.zeropageX(memory)
        self.A ^= memory.read(addr)
        self.update_ZN(self.A)
        self.cycles += 4
    
    def EOR_absolute(self, memory) -> None:
        addr = self.absolute(memory)
        self.A ^= memory.read(addr)
        self.update_ZN(self.A)
        self.cycles += 4
    
    def EOR_absoluteX(self, memory) -> None:
        addr, page_crossed = self.absoluteX(memory)
        self.A ^= memory.read(addr)
        self.update_ZN(self.A)
        self.cycles += 4 + (1 if page_crossed else 0)
    
    def EOR_absoluteY(self, memory) -> None:
        addr, page_crossed = self.absoluteY(memory)
        self.A ^= memory.read(addr)
        self.update_ZN(self.A)
        self.cycles += 4 + (1 if page_crossed else 0)
    
    def EOR_indirectX(self, memory) -> None:
        addr = self.indirectX(memory)
        self.A ^= memory.read(addr)
        self.update_ZN(self.A)
        self.cycles += 6
    
    def EOR_indirectY(self, memory) -> None:
        addr, page_crossed = self.indirectY(memory)
        self.A ^= memory.read(addr)
        self.update_ZN(self.A)
        self.cycles += 5 + (1 if page_crossed else 0)
    
    def BIT_zeropage(self, memory) -> None:
        addr = self.zeropage(memory)
        value = memory.read(addr)
        self.Z = 1 if (self.A & value) == 0 else 0
        self.V = (value >> 6) & 1
        self.N = (value >> 7) & 1
        self.cycles += 3
    
    def BIT_absolute(self, memory) -> None:
        addr = self.absolute(memory)
        value = memory.read(addr)
        self.Z = 1 if (self.A & value) == 0 else 0
        self.V = (value >> 6) & 1
        self.N = (value >> 7) & 1
        self.cycles += 4
    
    # Arithmetic Operations
    def ADC_immediate(self, memory) -> None:
        value = self.immediate(memory)
        self._add_with_carry(value)
        self.cycles += 2
    
    def ADC_zeropage(self, memory) -> None:
        addr = self.zeropage(memory)
        value = memory.read(addr)
        self._add_with_carry(value)
        self.cycles += 3
    
    def ADC_zeropageX(self, memory) -> None:
        addr = self.zeropageX(memory)
        value = memory.read(addr)
        self._add_with_carry(value)
        self.cycles += 4
    
    def ADC_absolute(self, memory) -> None:
        addr = self.absolute(memory)
        value = memory.read(addr)
        self._add_with_carry(value)
        self.cycles += 4
    
    def ADC_absoluteX(self, memory) -> None:
        addr, page_crossed = self.absoluteX(memory)
        value = memory.read(addr)
        self._add_with_carry(value)
        self.cycles += 4 + (1 if page_crossed else 0)
    
    def ADC_absoluteY(self, memory) -> None:
        addr, page_crossed = self.absoluteY(memory)
        value = memory.read(addr)
        self._add_with_carry(value)
        self.cycles += 4 + (1 if page_crossed else 0)
    
    def ADC_indirectX(self, memory) -> None:
        addr = self.indirectX(memory)
        value = memory.read(addr)
        self._add_with_carry(value)
        self.cycles += 6
    
    def ADC_indirectY(self, memory) -> None:
        addr, page_crossed = self.indirectY(memory)
        value = memory.read(addr)
        self._add_with_carry(value)
        self.cycles += 5 + (1 if page_crossed else 0)
    
    def _add_with_carry(self, value: int) -> None:
        """Implements ADC logic with decimal mode support."""
        if self.D:  # Decimal mode
            # BCD addition
            a_lo = self.A & 0x0F
            a_hi = self.A >> 4
            val_lo = value & 0x0F
            val_hi = value >> 4
            
            # Add low nibbles
            result_lo = a_lo + val_lo + self.C
            if result_lo > 9:
                result_lo += 6
                result_lo &= 0x0F
                carry_lo = 1
            else:
                carry_lo = 0
                
            # Add high nibbles
            result_hi = a_hi + val_hi + carry_lo
            if result_hi > 9:
                result_hi += 6
                result_hi &= 0x0F
                self.C = 1
            else:
                self.C = 0
                
            # Final result
            result = (result_hi << 4) | result_lo
            
            # Set flags
            self.Z = 1 if (result & 0xFF) == 0 else 0
            self.N = 1 if (result & 0x80) else 0
            
            # V flag is complicated in decimal mode, simplify here
            self.V = 0  # Simplified
            
        else:  # Binary mode
            temp = self.A + value + self.C
            
            # Set carry flag if result > 255
            self.C = 1 if temp > 0xFF else 0
            
            # Set overflow flag if sign bit changes incorrectly
            self.V = 1 if ((~(self.A ^ value) & (self.A ^ temp)) & 0x80) else 0
            
            # Set result and update flags
            self.A = temp & 0xFF
            self.update_ZN(self.A)
    
    def SBC_immediate(self, memory) -> None:
        value = self.immediate(memory)
        self._subtract_with_carry(value)
        self.cycles += 2
    
    def SBC_zeropage(self, memory) -> None:
        addr = self.zeropage(memory)
        value = memory.read(addr)
        self._subtract_with_carry(value)
        self.cycles += 3
    
    def SBC_zeropageX(self, memory) -> None:
        addr = self.zeropageX(memory)
        value = memory.read(addr)
        self._subtract_with_carry(value)
        self.cycles += 4
    
    def SBC_absolute(self, memory) -> None:
        addr = self.absolute(memory)
        value = memory.read(addr)
        self._subtract_with_carry(value)
        self.cycles += 4
    
    def SBC_absoluteX(self, memory) -> None:
        addr, page_crossed = self.absoluteX(memory)
        value = memory.read(addr)
        self._subtract_with_carry(value)
        self.cycles += 4 + (1 if page_crossed else 0)
    
    def SBC_absoluteY(self, memory) -> None:
        addr, page_crossed = self.absoluteY(memory)
        value = memory.read(addr)
        self._subtract_with_carry(value)
        self.cycles += 4 + (1 if page_crossed else 0)
    
    def SBC_indirectX(self, memory) -> None:
        addr = self.indirectX(memory)
        value = memory.read(addr)
        self._subtract_with_carry(value)
        self.cycles += 6
    
    def SBC_indirectY(self, memory) -> None:
        addr, page_crossed = self.indirectY(memory)
        value = memory.read(addr)
        self._subtract_with_carry(value)
        self.cycles += 5 + (1 if page_crossed else 0)
    
    def _subtract_with_carry(self, value: int) -> None:
        """Implements SBC logic with decimal mode support."""
        # SBC is basically ADC with inverted value
        if self.D:  # Decimal mode
            # BCD subtraction with borrow
            a_lo = self.A & 0x0F
            a_hi = self.A >> 4
            val_lo = value & 0x0F
            val_hi = value >> 4
            
            borrow = 1 - self.C  # Convert carry to borrow
            
            # Subtract low nibbles
            result_lo = a_lo - val_lo - borrow
            if result_lo < 0:
                result_lo += 10
                borrow_lo = 1
            else:
                borrow_lo = 0
                
            # Subtract high nibbles
            result_hi = a_hi - val_hi - borrow_lo
            if result_hi < 0:
                result_hi += 10
                self.C = 0
            else:
                self.C = 1
                
            # Final result
            result = (result_hi << 4) | result_lo
            
            # Set flags
            self.Z = 1 if (result & 0xFF) == 0 else 0
            self.N = 1 if (result & 0x80) else 0
            
            # V flag is complicated in decimal mode, simplify here
            self.V = 0  # Simplified
            
        else:  # Binary mode
            # Invert bits and add (A - M - !C = A + ~M + C)
            self._add_with_carry(value ^ 0xFF)
    
    def CMP_immediate(self, memory) -> None:
        value = self.immediate(memory)
        self._compare(self.A, value)
        self.cycles += 2
    
    def CMP_zeropage(self, memory) -> None:
        addr = self.zeropage(memory)
        value = memory.read(addr)
        self._compare(self.A, value)
        self.cycles += 3
    
    def CMP_zeropageX(self, memory) -> None:
        addr = self.zeropageX(memory)
        value = memory.read(addr)
        self._compare(self.A, value)
        self.cycles += 4
    
    def CMP_absolute(self, memory) -> None:
        addr = self.absolute(memory)
        value = memory.read(addr)
        self._compare(self.A, value)
        self.cycles += 4
    
    def CMP_absoluteX(self, memory) -> None:
        addr, page_crossed = self.absoluteX(memory)
        value = memory.read(addr)
        self._compare(self.A, value)
        self.cycles += 4 + (1 if page_crossed else 0)
    
    def CMP_absoluteY(self, memory) -> None:
        addr, page_crossed = self.absoluteY(memory)
        value = memory.read(addr)
        self._compare(self.A, value)
        self.cycles += 4 + (1 if page_crossed else 0)
    
    def CMP_indirectX(self, memory) -> None:
        addr = self.indirectX(memory)
        value = memory.read(addr)
        self._compare(self.A, value)
        self.cycles += 6
    
    def CMP_indirectY(self, memory) -> None:
        addr, page_crossed = self.indirectY(memory)
        value = memory.read(addr)
        self._compare(self.A, value)
        self.cycles += 5 + (1 if page_crossed else 0)
    
    def CPX_immediate(self, memory) -> None:
        value = self.immediate(memory)
        self._compare(self.X, value)
        self.cycles += 2
    
    def CPX_zeropage(self, memory) -> None:
        addr = self.zeropage(memory)
        value = memory.read(addr)
        self._compare(self.X, value)
        self.cycles += 3
    
    def CPX_absolute(self, memory) -> None:
        addr = self.absolute(memory)
        value = memory.read(addr)
        self._compare(self.X, value)
        self.cycles += 4
    
    def CPY_immediate(self, memory) -> None:
        value = self.immediate(memory)
        self._compare(self.Y, value)
        self.cycles += 2
    
    def CPY_zeropage(self, memory) -> None:
        addr = self.zeropage(memory)
        value = memory.read(addr)
        self._compare(self.Y, value)
        self.cycles += 3
    
    def CPY_absolute(self, memory) -> None:
        addr = self.absolute(memory)
        value = memory.read(addr)
        self._compare(self.Y, value)
        self.cycles += 4
    
    def _compare(self, reg: int, value: int) -> None:
        """Implement comparison logic for CMP, CPX, CPY instructions."""
        result = (reg - value) & 0xFF
        self.C = 1 if reg >= value else 0
        self.Z = 1 if reg == value else 0
        self.N = 1 if result & 0x80 else 0
    
    # Increments & Decrements
    def INC_zeropage(self, memory) -> None:
        addr = self.zeropage(memory)
        value = (memory.read(addr) + 1) & 0xFF
        memory.write(addr, value)
        self.update_ZN(value)
        self.cycles += 5
    
    def INC_zeropageX(self, memory) -> None:
        addr = self.zeropageX(memory)
        value = (memory.read(addr) + 1) & 0xFF
        memory.write(addr, value)
        self.update_ZN(value)
        self.cycles += 6
    
    def INC_absolute(self, memory) -> None:
        addr = self.absolute(memory)
        value = (memory.read(addr) + 1) & 0xFF
        memory.write(addr, value)
        self.update_ZN(value)
        self.cycles += 6
    
    def INC_absoluteX(self, memory) -> None:
        addr, _ = self.absoluteX(memory, False)
        value = (memory.read(addr) + 1) & 0xFF
        memory.write(addr, value)
        self.update_ZN(value)
        self.cycles += 7
    
    def INX(self, memory) -> None:
        self.X = (self.X + 1) & 0xFF
        self.update_ZN(self.X)
        self.cycles += 2
    
    def INY(self, memory) -> None:
        self.Y = (self.Y + 1) & 0xFF
        self.update_ZN(self.Y)
        self.cycles += 2
    
    def DEC_zeropage(self, memory) -> None:
        addr = self.zeropage(memory)
        value = (memory.read(addr) - 1) & 0xFF
        memory.write(addr, value)
        self.update_ZN(value)
        self.cycles += 5
    
    def DEC_zeropageX(self, memory) -> None:
        addr = self.zeropageX(memory)
        value = (memory.read(addr) - 1) & 0xFF
        memory.write(addr, value)
        self.update_ZN(value)
        self.cycles += 6
    
    def DEC_absolute(self, memory) -> None:
        addr = self.absolute(memory)
        value = (memory.read(addr) - 1) & 0xFF
        memory.write(addr, value)
        self.update_ZN(value)
        self.cycles += 6
    
    def DEC_absoluteX(self, memory) -> None:
        addr, _ = self.absoluteX(memory, False)
        value = (memory.read(addr) - 1) & 0xFF
        memory.write(addr, value)
        self.update_ZN(value)
        self.cycles += 7
    
    def DEX(self, memory) -> None:
        self.X = (self.X - 1) & 0xFF
        self.update_ZN(self.X)
        self.cycles += 2
    
    def DEY(self, memory) -> None:
        self.Y = (self.Y - 1) & 0xFF
        self.update_ZN(self.Y)
        self.cycles += 2
    
    # Shifts & Rotates
    def ASL_accumulator(self, memory) -> None:
        self.C = (self.A >> 7) & 1
        self.A = (self.A << 1) & 0xFF
        self.update_ZN(self.A)
        self.cycles += 2
    
    def ASL_zeropage(self, memory) -> None:
        addr = self.zeropage(memory)
        value = memory.read(addr)
        self.C = (value >> 7) & 1
        value = (value << 1) & 0xFF
        memory.write(addr, value)
        self.update_ZN(value)
        self.cycles += 5
    
    def ASL_zeropageX(self, memory) -> None:
        addr = self.zeropageX(memory)
        value = memory.read(addr)
        self.C = (value >> 7) & 1
        value = (value << 1) & 0xFF
        memory.write(addr, value)
        self.update_ZN(value)
        self.cycles += 6
    
    def ASL_absolute(self, memory) -> None:
        addr = self.absolute(memory)
        value = memory.read(addr)
        self.C = (value >> 7) & 1
        value = (value << 1) & 0xFF
        memory.write(addr, value)
        self.update_ZN(value)
        self.cycles += 6
    
    def ASL_absoluteX(self, memory) -> None:
        addr, _ = self.absoluteX(memory, False)
        value = memory.read(addr)
        self.C = (value >> 7) & 1
        value = (value << 1) & 0xFF
        memory.write(addr, value)
        self.update_ZN(value)
        self.cycles += 7
    
    def LSR_accumulator(self, memory) -> None:
        self.C = self.A & 1
        self.A = self.A >> 1
        self.update_ZN(self.A)
        self.cycles += 2
    
    def LSR_zeropage(self, memory) -> None:
        addr = self.zeropage(memory)
        value = memory.read(addr)
        self.C = value & 1
        value = value >> 1
        memory.write(addr, value)
        self.update_ZN(value)
        self.cycles += 5
    
    def LSR_zeropageX(self, memory) -> None:
        addr = self.zeropageX(memory)
        value = memory.read(addr)
        self.C = value & 1
        value = value >> 1
        memory.write(addr, value)
        self.update_ZN(value)
        self.cycles += 6
    
    def LSR_absolute(self, memory) -> None:
        addr = self.absolute(memory)
        value = memory.read(addr)
        self.C = value & 1
        value = value >> 1
        memory.write(addr, value)
        self.update_ZN(value)
        self.cycles += 6
    
    def LSR_absoluteX(self, memory) -> None:
        addr, _ = self.absoluteX(memory, False)
        value = memory.read(addr)
        self.C = value & 1
        value = value >> 1
        memory.write(addr, value)
        self.update_ZN(value)
        self.cycles += 7
    
    def ROL_accumulator(self, memory) -> None:
        old_carry = self.C
        self.C = (self.A >> 7) & 1
        self.A = ((self.A << 1) | old_carry) & 0xFF
        self.update_ZN(self.A)
        self.cycles += 2
    
    def ROL_zeropage(self, memory) -> None:
        addr = self.zeropage(memory)
        value = memory.read(addr)
        old_carry = self.C
        self.C = (value >> 7) & 1
        value = ((value << 1) | old_carry) & 0xFF
        memory.write(addr, value)
        self.update_ZN(value)
        self.cycles += 5
    
    def ROL_zeropageX(self, memory) -> None:
        addr = self.zeropageX(memory)
        value = memory.read(addr)
        old_carry = self.C
        self.C = (value >> 7) & 1
        value = ((value << 1) | old_carry) & 0xFF
        memory.write(addr, value)
        self.update_ZN(value)
        self.cycles += 6
    
    def ROL_absolute(self, memory) -> None:
        addr = self.absolute(memory)
        value = memory.read(addr)
        old_carry = self.C
        self.C = (value >> 7) & 1
        value = ((value << 1) | old_carry) & 0xFF
        memory.write(addr, value)
        self.update_ZN(value)
        self.cycles += 6
    
    def ROL_absoluteX(self, memory) -> None:
        addr, _ = self.absoluteX(memory, False)
        value = memory.read(addr)
        old_carry = self.C
        self.C = (value >> 7) & 1
        value = ((value << 1) | old_carry) & 0xFF
        memory.write(addr, value)
        self.update_ZN(value)
        self.cycles += 7
    
    def ROR_accumulator(self, memory) -> None:
        old_carry = self.C
        self.C = self.A & 1
        self.A = (self.A >> 1) | (old_carry << 7)
        self.update_ZN(self.A)
        self.cycles += 2
    
    def ROR_zeropage(self, memory) -> None:
        addr = self.zeropage(memory)
        value = memory.read(addr)
        old_carry = self.C
        self.C = value & 1
        value = (value >> 1) | (old_carry << 7)
        memory.write(addr, value)
        self.update_ZN(value)
        self.cycles += 5
    
    def ROR_zeropageX(self, memory) -> None:
        addr = self.zeropageX(memory)
        value = memory.read(addr)
        old_carry = self.C
        self.C = value & 1
        value = (value >> 1) | (old_carry << 7)
        memory.write(addr, value)
        self.update_ZN(value)
        self.cycles += 6
    
    def ROR_absolute(self, memory) -> None:
        addr = self.absolute(memory)
        value = memory.read(addr)
        old_carry = self.C
        self.C = value & 1
        value = (value >> 1) | (old_carry << 7)
        memory.write(addr, value)
        self.update_ZN(value)
        self.cycles += 6
    
    def ROR_absoluteX(self, memory) -> None:
        addr, _ = self.absoluteX(memory, False)
        value = memory.read(addr)
        old_carry = self.C
        self.C = value & 1
        value = (value >> 1) | (old_carry << 7)
        memory.write(addr, value)
        self.update_ZN(value)
        self.cycles += 7
    
    # Jumps & Calls
    def JMP_absolute(self, memory) -> None:
        self.PC = self.absolute(memory)
        self.cycles += 3
    
    def JMP_indirect(self, memory) -> None:
        self.PC = self.indirect(memory)
        self.cycles += 5
    
    def JSR_absolute(self, memory) -> None:
        addr = self.absolute(memory)
        # PC is already pointing to next instruction
        # Push return address (PC-1) to stack
        return_addr = self.PC - 1
        memory.write(0x100 + self.SP, (return_addr >> 8) & 0xFF)  # Push high byte
        self.SP = (self.SP - 1) & 0xFF
        memory.write(0x100 + self.SP, return_addr & 0xFF)  # Push low byte
        self.SP = (self.SP - 1) & 0xFF
        
        # Jump to subroutine
        self.PC = addr
        self.cycles += 6
    
    def RTS(self, memory) -> None:
        # Pull return address from stack
        self.SP = (self.SP + 1) & 0xFF
        low = memory.read(0x100 + self.SP)
        self.SP = (self.SP + 1) & 0xFF
        high = memory.read(0x100 + self.SP)
        
        # Set PC to return address + 1
        self.PC = ((high << 8) | low) + 1
        self.cycles += 6
    
    # Branches
    def _branch(self, memory, condition: bool) -> None:
        """Common logic for all branch instructions."""
        offset = self.immediate(memory)
        if condition:
            # Calculate new address (signed 8-bit offset)
            if offset & 0x80:  # Negative offset
                offset = -(256 - offset)
            
            old_pc = self.PC
            self.PC = (self.PC + offset) & 0xFFFF
            
            # +1 cycle if branch taken, +1 more if page crossed
            self.cycles += 1
            if (old_pc & 0xFF00) != (self.PC & 0xFF00):
                self.cycles += 1
        
        # Base cycles for branch instructions
        self.cycles += 2
    
    def BCC(self, memory) -> None:
        self._branch(memory, self.C == 0)
    
    def BCS(self, memory) -> None:
        self._branch(memory, self.C == 1)
    
    def BEQ(self, memory) -> None:
        self._branch(memory, self.Z == 1)
    
    def BMI(self, memory) -> None:
        self._branch(memory, self.N == 1)
    
    def BNE(self, memory) -> None:
        self._branch(memory, self.Z == 0)
    
    def BPL(self, memory) -> None:
        self._branch(memory, self.N == 0)
    
    def BVC(self, memory) -> None:
        self._branch(memory, self.V == 0)
    
    def BVS(self, memory) -> None:
        self._branch(memory, self.V == 1)
    
    # Status Flag Changes
    def CLC(self, memory) -> None:
        self.C = 0
        self.cycles += 2
    
    def SEC(self, memory) -> None:
        self.C = 1
        self.cycles += 2
    
    def CLI(self, memory) -> None:
        self.I = 0
        self.cycles += 2
    
    def SEI(self, memory) -> None:
        self.I = 1
        self.cycles += 2
    
    def CLV(self, memory) -> None:
        self.V = 0
        self.cycles += 2
    
    def CLD(self, memory) -> None:
        self.D = 0
        self.cycles += 2
    
    def SED(self, memory) -> None:
        self.D = 1
        self.cycles += 2
    
    # System Functions
    def BRK(self, memory) -> None:
        # Push PC+1 to stack
        memory.write(0x100 + self.SP, ((self.PC + 1) >> 8) & 0xFF)
        self.SP = (self.SP - 1) & 0xFF
        memory.write(0x100 + self.SP, (self.PC + 1) & 0xFF)
        self.SP = (self.SP - 1) & 0xFF
        
        # Push status with B flag set
        memory.write(0x100 + self.SP, self.get_status() | 0x10)
        self.SP = (self.SP - 1) & 0xFF
        
        # Set I flag
        self.I = 1
        
        # Load interrupt vector
        self.PC = memory.read(0xFFFE) | (memory.read(0xFFFF) << 8)
        self.cycles += 7
    
    def RTI(self, memory) -> None:
        # Pull status
        self.SP = (self.SP + 1) & 0xFF
        self.set_status(memory.read(0x100 + self.SP))
        
        # Pull PC
        self.SP = (self.SP + 1) & 0xFF
        low = memory.read(0x100 + self.SP)
        self.SP = (self.SP + 1) & 0xFF
        high = memory.read(0x100 + self.SP)
        
        self.PC = (high << 8) | low
        self.cycles += 6
    
    def NOP(self, memory) -> None:
        self.cycles += 2
    
    def step(self, memory) -> int:
        """Execute one instruction and return cycles used."""
        # Check for interrupts
        if self.nmi_pending:
            self._handle_nmi(memory)
        elif self.irq_pending and self.I == 0:
            self._handle_irq(memory)
        
        # Fetch instruction
        opcode = memory.read(self.PC)
        self.PC += 1
        
        # Reset cycle counter for this instruction
        self.cycles = 0
        
        # Execute instruction
        if opcode in self.instructions:
            self.instructions[opcode](memory)
        else:
            # Handle illegal opcodes as NOP
            self.cycles += 2
        
        # Update total cycles
        self.total_cycles += self.cycles
        
        return self.cycles
    
    def _handle_nmi(self, memory) -> None:
        """Handle Non-Maskable Interrupt."""
        # Push PC to stack
        memory.write(0x100 + self.SP, (self.PC >> 8) & 0xFF)
        self.SP = (self.SP - 1) & 0xFF
        memory.write(0x100 + self.SP, self.PC & 0xFF)
        self.SP = (self.SP - 1) & 0xFF
        
        # Push status without B flag
        memory.write(0x100 + self.SP, self.get_status() & ~0x10)
        self.SP = (self.SP - 1) & 0xFF
        
        # Set I flag
        self.I = 1
        
        # Load NMI vector
        self.PC = memory.read(0xFFFA) | (memory.read(0xFFFB) << 8)
        self.cycles += 7
        
        # Clear NMI pending flag
        self.nmi_pending = False
    
    def _handle_irq(self, memory) -> None:
        """Handle Interrupt Request."""
        # Push PC to stack
        memory.write(0x100 + self.SP, (self.PC >> 8) & 0xFF)
        self.SP = (self.SP - 1) & 0xFF
        memory.write(0x100 + self.SP, self.PC & 0xFF)
        self.SP = (self.SP - 1) & 0xFF
        
        # Push status without B flag
        memory.write(0x100 + self.SP, self.get_status() & ~0x10)
        self.SP = (self.SP - 1) & 0xFF
        
        # Set I flag
        self.I = 1
        
        # Load IRQ vector
        self.PC = memory.read(0xFFFE) | (memory.read(0xFFFF) << 8)
        self.cycles += 7
        
        # Clear IRQ pending flag
        self.irq_pending = False
    
    def trigger_nmi(self) -> None:
        """Trigger a Non-Maskable Interrupt."""
        self.nmi_pending = True
    
    def trigger_irq(self) -> None:
        """Trigger an Interrupt Request."""
        self.irq_pending = True
    
    def get_state(self) -> Dict[str, int]:
        """Get CPU state for debugging."""
        return {
            'A': self.A,
            'X': self.X,
            'Y': self.Y,
            'PC': self.PC,
            'SP': self.SP,
            'P': self.get_status(),
            'cycles': self.total_cycles
        }


class Memory:
    """Emulates the memory subsystem with memory-mapped I/O."""
    
    def __init__(self, size: int = 0x10000):
        # Main memory
        self.ram = bytearray(size)
        
        # ROM areas
        self.roms = {}  # addr: (data, size)
        
        # Memory-mapped I/O handlers
        self.io_read_handlers = {}   # addr: handler_func
        self.io_write_handlers = {}  # addr: handler_func
    
    def load_rom(self, data: bytes, addr: int) -> None:
        """Load ROM data at the specified address."""
        size = len(data)
        self.roms[addr] = (bytes(data), size)
        
        # Copy to main memory for initial state
        for i, b in enumerate(data):
            if addr + i < len(self.ram):
                self.ram[addr + i] = b
    
    def register_io_handler(self, addr: int, read_handler=None, write_handler=None) -> None:
        """Register I/O handlers for a memory-mapped address."""
        if read_handler:
            self.io_read_handlers[addr] = read_handler
        if write_handler:
            self.io_write_handlers[addr] = write_handler
    
    def read(self, addr: int) -> int:
        """Read a byte from memory, handling ROMs and I/O."""
        addr = addr & 0xFFFF  # Ensure address is 16-bit
        
        # Check for I/O handler
        if addr in self.io_read_handlers:
            return self.io_read_handlers[addr]()
        
        # Check if in ROM area
        for rom_addr, (data, size) in self.roms.items():
            if rom_addr <= addr < rom_addr + size:
                offset = addr - rom_addr
                return data[offset]
        
        # Regular RAM access
        return self.ram[addr]
    
    def write(self, addr: int, value: int) -> None:
        """Write a byte to memory, handling ROMs and I/O."""
        addr = addr & 0xFFFF  # Ensure address is 16-bit
        value = value & 0xFF  # Ensure value is 8-bit
        
        # Check for I/O handler
        if addr in self.io_write_handlers:
            self.io_write_handlers[addr](value)
            return
        
        # Check if in ROM area (can't write to ROM)
        for rom_addr, (_, size) in self.roms.items():
            if rom_addr <= addr < rom_addr + size:
                return
        
        # Regular RAM access
        self.ram[addr] = value
    
    def read_word(self, addr: int) -> int:
        """Read a 16-bit word from memory (little-endian)."""
        return self.read(addr) | (self.read(addr + 1) << 8)
    
    def write_word(self, addr: int, value: int) -> None:
        """Write a 16-bit word to memory (little-endian)."""
        self.write(addr, value & 0xFF)
        self.write(addr + 1, (value >> 8) & 0xFF)


class VideoRAM:
    """Emulates the PET's screen memory."""
    
    def __init__(self, width: int = 40, height: int = 25):
        self.width = width
        self.height = height
        self.size = width * height
        self.memory = bytearray(self.size)
        self.dirty = True  # Flag to indicate screen needs redrawing
    
    def read(self, addr: int) -> int:
        """Read from video RAM."""
        if 0 <= addr < self.size:
            return self.memory[addr]
        return 0
    
    def write(self, addr: int, value: int) -> None:
        """Write to video RAM and mark as dirty."""
        if 0 <= addr < self.size:
            if self.memory[addr] != value:
                self.memory[addr] = value
                self.dirty = True
    
    def clear(self) -> None:
        """Clear the screen with spaces."""
        for i in range(self.size):
            self.memory[i] = 0x20  # ASCII space
        self.dirty = True


class PETKeyboard:
    """Emulates the PET keyboard matrix."""
    
    def __init__(self):
        # PET keyboard matrix (8x8)
        self.matrix = [0xFF] * 10  # 10 rows, all keys up (1=up, 0=down)
        self.last_key = None
        
        # Key mapping: maps ASCII/curses keys to (row, col) in matrix
        self.key_map = {
            # Row 0
            '1': (0, 0), '3': (0, 1), '5': (0, 2), '7': (0, 3), '9': (0, 4),
            '+': (0, 5), '\\': (0, 6), 'DEL': (0, 7),
            
            # Row 1
            'RETURN': (1, 0), 'W': (1, 1), 'R': (1, 2), 'Y': (1, 3), 'I': (1, 4),
            'P': (1, 5), '*': (1, 6), '↑': (1, 7),
            
            # Row 2 (and so on...)
            'LEFT': (2, 0), 'A': (2, 1), 'D': (2, 2), 'G': (2, 3), 'J': (2, 4),
            'L': (2, 5), ';': (2, 6), 'RIGHT': (2, 7),
            
            # Row 3
            'DOWN': (3, 0), 'LSHIFT': (3, 1), 'X': (3, 2), 'V': (3, 3), 'N': (3, 4),
            ',': (3, 5), '/': (3, 6), 'RSHIFT': (3, 7),
            
            # Row 4
            ' ': (4, 0), 'Z': (4, 1), 'C': (4, 2), 'B': (4, 3), 'M': (4, 4),
            '.': (4, 5), 'UP': (4, 7),
            
            # Row 5
            '0': (5, 0), '2': (5, 1), '4': (5, 2), '6': (5, 3), '8': (5, 4),
            '-': (5, 5), '@': (5, 6), '^': (5, 7),
            
            # Row 6
            'HOME': (6, 0), 'Q': (6, 1), 'E': (6, 2), 'T': (6, 3), 'U': (6, 4),
            'O': (6, 5), '[': (6, 6), ']': (6, 7),
            
            # Row 7
            'STOP': (7, 0), 'S': (7, 1), 'F': (7, 2), 'H': (7, 3), 'K': (7, 4),
            ':': (7, 5), '=': (7, 6),
            
            # Row 8
            'CTRL': (8, 0), 'COMMODORE': (8, 1),
            
            # Row 9 (function keys for expanded keyboards)
            'F1': (9, 0), 'F2': (9, 1), 'F3': (9, 2), 'F4': (9, 3),
        }
        
        # Curses key mapping (maps curses key codes to our key names)
        self.curses_map = {
            curses.KEY_ENTER: 'RETURN',
            curses.KEY_HOME: 'HOME',
            curses.KEY_LEFT: 'LEFT',
            curses.KEY_RIGHT: 'RIGHT',
            curses.KEY_UP: 'UP',
            curses.KEY_DOWN: 'DOWN',
            curses.KEY_BACKSPACE: 'DEL',
            curses.KEY_DC: 'DEL',       # Delete key
            curses.KEY_F1: 'F1',
            curses.KEY_F2: 'F2',
            curses.KEY_F3: 'F3',
            curses.KEY_F4: 'F4',
            27: 'STOP',                 # ESC key as STOP
        }
    
    def key_down(self, key) -> None:
        """Process key down event."""
        self.last_key = key
        
        # Convert curses key code if needed
        if isinstance(key, int):
            if key in self.curses_map:
                key = self.curses_map[key]
            elif 32 <= key <= 126:  # Printable ASCII
                key = chr(key).upper()
            else:
                return  # Unknown key
        
        # Handle shift for uppercase letters
        if key.isalpha() and key.isupper():
            self._set_key('LSHIFT', True)
        
        # Look up key in map
        if key in self.key_map:
            row, col = self.key_map[key]
            self._set_key((row, col), True)
    
    def key_up(self, key) -> None:
        """Process key up event."""
        # Convert curses key code if needed
        if isinstance(key, int):
            if key in self.curses_map:
                key = self.curses_map[key]
            elif 32 <= key <= 126:  # Printable ASCII
                key = chr(key).upper()
            else:
                return  # Unknown key
        
        # Handle shift for uppercase letters
        if key.isalpha() and key.isupper():
            self._set_key('LSHIFT', False)
        
        # Look up key in map
        if key in self.key_map:
            row, col = self.key_map[key]
            self._set_key((row, col), False)
    
    def _set_key(self, key, is_down: bool) -> None:
        """Set a key state in the matrix."""
        if isinstance(key, tuple):
            row, col = key
        elif key in self.key_map:
            row, col = self.key_map[key]
        else:
            return
        
        # Update matrix (1=up, 0=down)
        if is_down:
            self.matrix[row] &= ~(1 << col)
        else:
            self.matrix[row] |= (1 << col)
    
    def read_row(self, row: int) -> int:
        """Read a row from the keyboard matrix."""
        if 0 <= row < len(self.matrix):
            return self.matrix[row]
        return 0xFF  # All keys up


class PETScreen:
    """Handles rendering the PET screen using curses."""
    
    def __init__(self, stdscr, width: int = 40, height: int = 25):
        self.stdscr = stdscr
        self.width = width
        self.height = height
        
        # Set up curses
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # PET green phosphor
        self.color = curses.color_pair(1)
        
        # PET character set mapping (PETSCII to ASCII/displayable)
        self.charset = self._create_charset()
    
    def _create_charset(self) -> Dict[int, str]:
        """Create a mapping from PETSCII codes to displayable characters."""
        charset = {}
        
        # Basic ASCII mapping
        for i in range(32, 127):
            charset[i] = chr(i)
        
        # PETSCII special characters
        charset[0x20] = ' '    # Space
        charset[0x51] = 'Q'    # Q
        charset[0x5A] = 'Z'    # Z
        charset[0x43] = 'C'    # C
        charset[0x92] = '│'    # Vertical line
        charset[0x9D] = '─'    # Horizontal line
        charset[0xA0] = ' '    # Shifted space
        
        # Fill in unmapped characters with '?'
        for i in range(256):
            if i not in charset:
                charset[i] = '?'
        
        return charset
    
    def update(self, video_ram: VideoRAM) -> None:
        """Update the screen from video RAM if dirty."""
        if not video_ram.dirty:
            return
        
        for y in range(min(self.height, video_ram.height)):
            for x in range(min(self.width, video_ram.width)):
                char_code = video_ram.memory[y * video_ram.width + x]
                char = self.charset.get(char_code, '?')
                
                try:
                    self.stdscr.addch(y, x, char, self.color)
                except curses.error:
                    pass  # Ignore errors from writing to bottom-right corner
        
        self.stdscr.refresh()
        video_ram.dirty = False


class VIA:
    """Emulates the 6522 Versatile Interface Adapter."""
    
    def __init__(self):
        # Registers
        self.registers = bytearray(16)
        
        # I/O ports
        self.port_a = 0xFF  # Port A output
        self.port_b = 0xFF  # Port B output
        
        # Data direction registers (1=output, 0=input)
        self.ddr_a = 0x00  # Port A direction
        self.ddr_b = 0x00  # Port B direction
        
        # Timers
        self.timer1_counter = 0
        self.timer1_latch = 0
        self.timer2_counter = 0
        
        # Shift register
        self.shift_register = 0
        
        # IRQ status and control
        self.irq_status = 0
        self.irq_enable = 0
        
        # I/O callbacks
        self.read_port_a = None
        self.read_port_b = None
        self.write_port_a = None
        self.write_port_b = None
    
    def set_port_a_handlers(self, read_func=None, write_func=None) -> None:
        """Set handlers for Port A operations."""
        self.read_port_a = read_func
        self.write_port_a = write_func
    
    def set_port_b_handlers(self, read_func=None, write_func=None) -> None:
        """Set handlers for Port B operations."""
        self.read_port_b = read_func
        self.write_port_b = write_func
    
    def read(self, addr: int) -> int:
        """Read from a VIA register."""
        reg = addr & 0x0F
        
        if reg == 0x0:  # Port B
            if self.read_port_b:
                input_value = self.read_port_b()
            else:
                input_value = 0xFF
            
            # Apply data direction register
            return (self.port_b & self.ddr_b) | (input_value & ~self.ddr_b)
        
        elif reg == 0x1:  # Port A
            if self.read_port_a:
                input_value = self.read_port_a()
            else:
                input_value = 0xFF
            
            # Apply data direction register
            return (self.port_a & self.ddr_a) | (input_value & ~self.ddr_a)
        
        elif reg == 0x2:  # DDR B
            return self.ddr_b
        
        elif reg == 0x3:  # DDR A
            return self.ddr_a
        
        elif reg == 0x4:  # Timer 1 counter low
            return self.timer1_counter & 0xFF
        
        elif reg == 0x5:  # Timer 1 counter high
            return (self.timer1_counter >> 8) & 0xFF
        
        elif reg == 0x6:  # Timer 1 latch low
            return self.timer1_latch & 0xFF
        
        elif reg == 0x7:  # Timer 1 latch high
            return (self.timer1_latch >> 8) & 0xFF
        
        elif reg == 0x8:  # Timer 2 counter low
            return self.timer2_counter & 0xFF
        
        elif reg == 0x9:  # Timer 2 counter high
            return (self.timer2_counter >> 8) & 0xFF
        
        elif reg == 0xA:  # Shift register
            return self.shift_register
        
        elif reg == 0xD:  # Interrupt flag register
            return self.irq_status
        
        elif reg == 0xE:  # Interrupt enable register
            return self.irq_enable
        
        # Other registers
        return self.registers[reg]
    
    def write(self, addr: int, value: int) -> None:
        """Write to a VIA register."""
        reg = addr & 0x0F
        value &= 0xFF
        
        if reg == 0x0:  # Port B
            self.port_b = value
            if self.write_port_b:
                # Only output pins controlled by DDR
                output_value = value & self.ddr_b
                self.write_port_b(output_value)
        
        elif reg == 0x1:  # Port A
            self.port_a = value
            if self.write_port_a:
                # Only output pins controlled by DDR
                output_value = value & self.ddr_a
                self.write_port_a(output_value)
        
        elif reg == 0x2:  # DDR B
            self.ddr_b = value
        
        elif reg == 0x3:  # DDR A
            self.ddr_a = value
        
        elif reg == 0x4:  # Timer 1 counter low
            self.timer1_latch = (self.timer1_latch & 0xFF00) | value
        
        elif reg == 0x5:  # Timer 1 counter high
            self.timer1_latch = (value << 8) | (self.timer1_latch & 0xFF)
            self.timer1_counter = self.timer1_latch
            self.irq_status &= ~0x40  # Clear Timer 1 interrupt
        
        elif reg == 0x6:  # Timer 1 latch low
            self.timer1_latch = (self.timer1_latch & 0xFF00) | value
        
        elif reg == 0x7:  # Timer 1 latch high
            self.timer1_latch = (value << 8) | (self.timer1_latch & 0xFF)
        
        elif reg == 0x8:  # Timer 2 counter low
            self.timer2_counter = (self.timer2_counter & 0xFF00) | value
        
        elif reg == 0x9:  # Timer 2 counter high
            self.timer2_counter = (value << 8) | (self.timer2_counter & 0xFF)
            self.irq_status &= ~0x20  # Clear Timer 2 interrupt
        
        elif reg == 0xA:  # Shift register
            self.shift_register = value
        
        elif reg == 0xD:  # Interrupt flag register
            # Writing 1 clears the corresponding bit
            self.irq_status &= ~value
        
        elif reg == 0xE:  # Interrupt enable register
            if value & 0x80:
                # Set bits where bits in value are 1
                self.irq_enable |= (value & 0x7F)
            else:
                # Clear bits where bits in value are 1
                self.irq_enable &= ~(value & 0x7F)
        
        # Store in register array anyway
        self.registers[reg] = value
    
    def update_timers(self, cycles: int) -> bool:
        """Update timers and return True if an IRQ was triggered."""
        irq_triggered = False
        
        # Timer 1
        if self.timer1_counter > 0:
            if self.timer1_counter <= cycles:
                # Timer expired
                self.timer1_counter = self.timer1_latch  # Reload
                self.irq_status |= 0x40  # Set Timer 1 interrupt flag
                if self.irq_enable & 0x40:
                    irq_triggered = True
            else:
                self.timer1_counter -= cycles
        
        # Timer 2
        if self.timer2_counter > 0:
            if self.timer2_counter <= cycles:
                # Timer expired
                self.timer2_counter = 0
                self.irq_status |= 0x20  # Set Timer 2 interrupt flag
                if self.irq_enable & 0x20:
                    irq_triggered = True
            else:
                self.timer2_counter -= cycles
        
        return irq_triggered


class PET:
    """Main PET computer system."""
    
    def __init__(self, stdscr, model="4032"):
        # Core components
        self.cpu = CPU6502()
        self.memory = Memory()
        self.video_ram = VideoRAM(40, 25)
        self.screen = PETScreen(stdscr, 40, 25)
        self.keyboard = PETKeyboard()
        
        # Memory-mapped I/O
        self.via1 = VIA()  # Keyboard VIA
        self.via2 = VIA()  # IEEE-488 VIA
        
        # System state
        self.running = False
        self.debug_mode = False
        self.cycles_per_frame = 20000  # Roughly 50Hz refresh at 1MHz
        
        # Set up the memory map
        self._setup_memory_map()
        
        # Load ROMs based on model
        self._load_roms(model)
        
        # Connect peripherals
        self._connect_peripherals()
    
    def _setup_memory_map(self):
        """Set up the memory map for the PET."""
        # Video RAM at 0x8000-0x83E7 (40x25 = 1000 bytes)
        for i in range(0x8000, 0x8000 + 1000):
            self.memory.register_io_handler(
                i,
                read_handler=lambda addr=i: self.video_ram.read(addr - 0x8000),
                write_handler=lambda value, addr=i: self.video_ram.write(addr - 0x8000, value)
            )
        
        # VIA 1 at 0xE810-0xE81F
        for i in range(0xE810, 0xE820):
            self.memory.register_io_handler(
                i,
                read_handler=lambda addr=i: self.via1.read(addr - 0xE810),
                write_handler=lambda value, addr=i: self.via1.write(addr - 0xE810, value)
            )
        
        # VIA 2 at 0xE820-0xE82F
        for i in range(0xE820, 0xE830):
            self.memory.register_io_handler(
                i,
                read_handler=lambda addr=i: self.via2.read(addr - 0xE820),
                write_handler=lambda value, addr=i: self.via2.write(addr - 0xE820, value)
            )
    
    def _load_roms(self, model):
        """Load ROMs for the specified PET model."""
        # For simplicity, instead of loading actual ROM files,
        # we'll create a minimal BASIC ROM that can execute a simple program
        
        # Generate a simple ROM with BASIC interpreter stubs
        basic_rom = bytearray([
            # Reset vector points to start of ROM
            0xA9, 0x93,       # LDA #$93 (Clear screen code)
            0x20, 0xD2, 0xFF, # JSR $FFD2 (KERNAL output character)
            0xA9, 0x0D,       # LDA #$0D (Return character)
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x50,       # LDA #$50 ('P')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x45,       # LDA #$45 ('E')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x54,       # LDA #$54 ('T')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x20,       # LDA #$20 (Space)
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x42,       # LDA #$42 ('B')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x41,       # LDA #$41 ('A')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x53,       # LDA #$53 ('S')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x49,       # LDA #$49 ('I')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x43,       # LDA #$43 ('C')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x0D,       # LDA #$0D (Return)
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x52,       # LDA #$52 ('R')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x45,       # LDA #$45 ('E')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x41,       # LDA #$41 ('A')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x44,       # LDA #$44 ('D')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x59,       # LDA #$59 ('Y')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x0D,       # LDA #$0D (Return)
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA2, 0x00,       # LDX #$00 (Input buffer index)
            0xA9, 0x3E,       # LDA #$3E ('>')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x20,       # LDA #$20 (Space)
            0x20, 0xD2, 0xFF, # JSR $FFD2
            # Input loop
            0x20, 0xE4, 0xFF, # JSR $FFE4 (KERNAL get character)
            0xF0, 0xFB,       # BEQ -5 (Loop until key pressed)
            0xC9, 0x0D,       # CMP #$0D (Check for return)
            0xF0, 0x0A,       # BEQ +10 (Process command if return)
            0x9D, 0x00, 0x02, # STA $0200,X (Store in input buffer)
            0x20, 0xD2, 0xFF, # JSR $FFD2 (Echo character)
            0xE8,             # INX
            0xE0, 0x3F,       # CPX #$3F (Check if buffer full)
            0xD0, 0xEE,       # BNE -18 (Continue input if not full)
            # Process command
            0xA9, 0x0D,       # LDA #$0D (Return)
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xAD, 0x00, 0x02, # LDA $0200 (Check first character)
            0xC9, 0x50,       # CMP #$50 ('P')
            0xF0, 0x19,       # BEQ +25 (PRINT command)
            0xC9, 0x52,       # CMP #$52 ('R')
            0xF0, 0x2A,       # BEQ +42 (RUN command)
            0xC9, 0x4C,       # CMP #$4C ('L')
            0xF0, 0x36,       # BEQ +54 (LIST command)
            0xC9, 0x4E,       # CMP #$4E ('N')
            0xF0, 0x3D,       # BEQ +61 (NEW command)
            # Unknown command
            0xA9, 0x3F,       # LDA #$3F ('?')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x0D,       # LDA #$0D (Return)
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0x4C, 0x36, 0xC0, # JMP $C036 (Back to prompt)
            # PRINT command
            0xA2, 0x05,       # LDX #$05 (Skip "PRINT" in buffer)
            # Print loop
            0xBD, 0x00, 0x02, # LDA $0200,X (Get char from buffer)
            0xF0, 0x07,       # BEQ +7 (End if zero)
            0xE8,             # INX
            0x20, 0xD2, 0xFF, # JSR $FFD2 (Print character)
            0xE0, 0x3F,       # CPX #$3F (Check buffer end)
            0xD0, 0xF4,       # BNE -12 (Continue if not at end)
            0xA9, 0x0D,       # LDA #$0D (Return)
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0x4C, 0x36, 0xC0, # JMP $C036 (Back to prompt)
            # RUN command
            0xA9, 0x52,       # LDA #$52 ('R')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x55,       # LDA #$55 ('U')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x4E,       # LDA #$4E ('N')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x0D,       # LDA #$0D (Return)
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0x4C, 0x36, 0xC0, # JMP $C036 (Back to prompt)
            # LIST command
            0xA9, 0x4E,       # LDA #$4E ('N')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x4F,       # LDA #$4F ('O')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x20,       # LDA #$20 (Space)
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x50,       # LDA #$50 ('P')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x52,       # LDA #$52 ('R')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x4F,       # LDA #$4F ('O')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x47,       # LDA #$47 ('G')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x0D,       # LDA #$0D (Return)
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0x4C, 0x36, 0xC0, # JMP $C036 (Back to prompt)
            # NEW command
            0xA9, 0x4D,       # LDA #$4D ('M')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x45,       # LDA #$45 ('E')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x4D,       # LDA #$4D ('M')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x4F,       # LDA #$4F ('O')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x52,       # LDA #$52 ('R')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x59,       # LDA #$59 ('Y')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x20,       # LDA #$20 (Space)
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x43,       # LDA #$43 ('C')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x4C,       # LDA #$4C ('L')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x45,       # LDA #$45 ('E')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x41,       # LDA #$41 ('A')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x52,       # LDA #$52 ('R')
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0xA9, 0x0D,       # LDA #$0D (Return)
            0x20, 0xD2, 0xFF, # JSR $FFD2
            0x4C, 0x36, 0xC0, # JMP $C036 (Back to prompt)
        ])
        
        # Fill the rest of the ROM with zeros up to 16K
        basic_rom.extend([0] * (16384 - len(basic_rom)))
        
        # KERNAL ROM with key I/O routines
        kernal_rom = bytearray([0] * 4096)
        
        # CHROUT: Output a character ($FFD2)
        kernal_idx = 0xFFD2 - 0xF000
        kernal_rom[kernal_idx:kernal_idx+16] = [
            0x48,             # PHA (Save A)
            0x86, 0xFB,       # STX $FB (Save X)
            0x84, 0xFC,       # STY $FC (Save Y)
            0xAA,             # TAX (Character to X)
            0xBD, 0x00, 0xE0, # LDA $E000,X (Look up in character ROM)
            0x8D, 0x00, 0x80, # STA $8000 (Store to screen)
            0xEE, 0x37, 0x03, # INC $0337 (Increment cursor position)
            0xA6, 0xFB,       # LDX $FB (Restore X)
            0xA4, 0xFC,       # LDY $FC (Restore Y)
            0x68,             # PLA (Restore A)
            0x60              # RTS
        ]
        
        # GETIN: Get a character from keyboard ($FFE4)
        kernal_idx = 0xFFE4 - 0xF000
        kernal_rom[kernal_idx:kernal_idx+16] = [
            0xAD, 0x10, 0xE8, # LDA $E810 (Read keyboard row)
            0xC9, 0xFF,       # CMP #$FF (Check if any key pressed)
            0xF0, 0x05,       # BEQ +5 (Return 0 if no key)
            0xAD, 0x11, 0xE8, # LDA $E811 (Get key code)
            0xEE, 0x12, 0xE8, # INC $E812 (Acknowledge key)
            0x60,             # RTS
            0xA9, 0x00,       # LDA #$00 (No key pressed)
            0x60              # RTS
        ]
        
        # Character ROM (simplified, maps ASCII to PETSCII)
        char_rom = bytearray([0] * 4096)
        for i in range(32, 127):
            char_rom[i] = i  # Direct mapping for printable ASCII
        
        # Reset/IRQ vectors
        basic_rom[0x3FFC - 0xC000] = 0x00  # Reset vector low byte
        basic_rom[0x3FFD - 0xC000] = 0xC0  # Reset vector high byte
        basic_rom[0x3FFE - 0xC000] = 0x36  # IRQ vector low byte
        basic_rom[0x3FFF - 0xC000] = 0xC0  # IRQ vector high byte
        
        # Load ROMs into memory
        self.memory.load_rom(basic_rom, 0xC000)  # BASIC ROM at $C000-$FFFF
        self.memory.load_rom(kernal_rom, 0xF000)  # KERNAL ROM at $F000-$FFFF
        self.memory.load_rom(char_rom, 0xE000)   # Character ROM at $E000-$EFFF
    
    def _connect_peripherals(self):
        """Connect peripherals to the system."""
        # Set up keyboard scanning via VIA
        self.via1.set_port_a_handlers(
            read_func=self._read_keyboard_matrix,
            write_func=self._select_keyboard_row
        )
        
        # Current keyboard row being read
        self.current_keyboard_row = 0
    
    def _read_keyboard_matrix(self) -> int:
        """Read the keyboard matrix for the current row."""
        return self.keyboard.read_row(self.current_keyboard_row)
    
    def _select_keyboard_row(self, value: int) -> None:
        """Select the keyboard row to read."""
        # Lower 3 bits select the row (0-7)
        self.current_keyboard_row = value & 0x07
    
    def start(self) -> None:
        """Start the emulator."""
        self.running = True
        self.cpu.PC = 0xC000  # Start at beginning of BASIC ROM
        
        # Clear screen
        self.video_ram.clear()
    
    def stop(self) -> None:
        """Stop the emulator."""
        self.running = False
    
    def process_key(self, key) -> None:
        """Process a key event."""
        if isinstance(key, int) and key == 27:  # ESC
            self.stop()
            return
        
        # Toggle debug mode with F12
        if isinstance(key, int) and key == curses.KEY_F12:
            self.debug_mode = not self.debug_mode
            return
        
        # Pass to keyboard handler
        self.keyboard.key_down(key)
        # In a real implementation, we'd handle key up events separately
    
    def run_frame(self) -> None:
        """Run one frame of emulation."""
        if not self.running:
            return
        
        # Run CPU for a certain number of cycles
        cycles_this_frame = 0
        while cycles_this_frame < self.cycles_per_frame and self.running:
            # Execute one instruction
            cycles = self.cpu.step(self.memory)
            cycles_this_frame += cycles
            
            # Update VIAs
            if self.via1.update_timers(cycles):
                self.cpu.trigger_irq()
            
            if self.via2.update_timers(cycles):
                self.cpu.trigger_irq()
        
        # Update screen
        self.screen.update(self.video_ram)
        
        # Debug info
        if self.debug_mode:
            self._update_debug_info()
    
    def _update_debug_info(self) -> None:
        """Show debug information on screen."""
        cpu_state = self.cpu.get_state()
        debug_line = f"A:{cpu_state['A']:02X} X:{cpu_state['X']:02X} Y:{cpu_state['Y']:02X} " \
                     f"PC:{cpu_state['PC']:04X} SP:{cpu_state['SP']:02X} " \
                     f"P:{cpu_state['P']:02X} CYC:{cpu_state['cycles']}"
        
        # Display at bottom of screen
        for i, c in enumerate(debug_line):
            if i < self.video_ram.width:
                self.video_ram.write(self.video_ram.width * (self.video_ram.height - 1) + i, ord(c))


def main(stdscr):
    """Main function for the PET emulator."""
    # Set up curses
    curses.curs_set(0)  # Hide cursor
    stdscr.nodelay(True)  # Non-blocking input
    stdscr.clear()
    
    # Create and start the PET
    pet = PET(stdscr)
    pet.start()
    
    # Main loop
    while pet.running:
        # Process input
        try:
            key = stdscr.getch()
            if key != -1:  # -1 means no key pressed
                pet.process_key(key)
        except curses.error:
            pass
        
        # Run one frame
        pet.run_frame()
        
        # Throttle to approximate PET speed
        time.sleep(0.02)  # ~50Hz

if __name__ == "__main__":
    curses.wrapper(main)
 self.C
        self.C = value & 1
        value = (value >> 1) | (old_carry << 7)
        memory.write(addr, value)
        self.update_ZN(value)
        self.cycles += 7