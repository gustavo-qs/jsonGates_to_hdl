#!/usr/bin/env python3
"""
Exemplo de Uso: Conversão DLS → HDL
Demonstra como usar os conversores na prática
"""

import json
from advanced_converter import AdvancedConverter

# ============================================================================
# EXEMPLO 1: Conversão Básica
# ============================================================================

print("="*70)
print("EXEMPLO 1: Conversão Básica de MUX-16")
print("="*70)

# JSON do Digital Logic Sim
mux16_json = {
    "Name": "MUX-16",
    "InputPins": [
        {"Name": "A", "ID": 1, "BitCount": 8},
        {"Name": "B", "ID": 2, "BitCount": 8},
        {"Name": "SEL", "ID": 3, "BitCount": 1}
    ],
    "OutputPins": [
        {"Name": "OUT", "ID": 4, "BitCount": 8}
    ],
    "SubChips": [
        {"Name": "MUX", "ID": 100},
        {"Name": "MUX", "ID": 101},
        {"Name": "MUX", "ID": 102},
        {"Name": "MUX", "ID": 103},
        {"Name": "MUX", "ID": 104},
        {"Name": "MUX", "ID": 105},
        {"Name": "MUX", "ID": 106},
        {"Name": "MUX", "ID": 107}
    ],
    "Wires": [
        # A[0] → MUX[100].a
        {"SourcePinAddress": {"PinOwnerID": 1, "PinID": 0}, 
         "TargetPinAddress": {"PinOwnerID": 100, "PinID": 0}},
        # B[0] → MUX[100].b
        {"SourcePinAddress": {"PinOwnerID": 2, "PinID": 0}, 
         "TargetPinAddress": {"PinOwnerID": 100, "PinID": 1}},
        # SEL → MUX[100].sel
        {"SourcePinAddress": {"PinOwnerID": 3, "PinID": 0}, 
         "TargetPinAddress": {"PinOwnerID": 100, "PinID": 2}},
        # MUX[100].out → OUT[0]
        {"SourcePinAddress": {"PinOwnerID": 100, "PinID": 0}, 
         "TargetPinAddress": {"PinOwnerID": 4, "PinID": 0}}
    ]
}

converter = AdvancedConverter(mux16_json)
hdl = converter.convert()
print(hdl)
print()

# ============================================================================
# EXEMPLO 2: Análise Estrutural
# ============================================================================

print("="*70)
print("EXEMPLO 2: Análise Estrutural Detalhada")
print("="*70)

report = converter.generate_detailed_report()
print(report)
print()

# ============================================================================
# EXEMPLO 3: Processamento em Lote
# ============================================================================

print("="*70)
print("EXEMPLO 3: Processamento em Lote")
print("="*70)

# Simular múltiplos arquivos
circuits = {
    "Adder": {
        "Name": "FullAdder",
        "InputPins": [
            {"Name": "a", "ID": 1, "BitCount": 1},
            {"Name": "b", "ID": 2, "BitCount": 1},
            {"Name": "c", "ID": 3, "BitCount": 1}
        ],
        "OutputPins": [
            {"Name": "sum", "ID": 4, "BitCount": 1},
            {"Name": "carry", "ID": 5, "BitCount": 1}
        ],
        "SubChips": [
            {"Name": "XOR", "ID": 100},
            {"Name": "AND", "ID": 101}
        ],
        "Wires": []
    },
    "Register": {
        "Name": "Register8",
        "InputPins": [
            {"Name": "in", "ID": 1, "BitCount": 8},
            {"Name": "load", "ID": 2, "BitCount": 1}
        ],
        "OutputPins": [
            {"Name": "out", "ID": 3, "BitCount": 8}
        ],
        "SubChips": [
            {"Name": "DFF", "ID": 100}
        ],
        "Wires": []
    }
}

for name, circuit_json in circuits.items():
    converter = AdvancedConverter(circuit_json)
    hdl = converter.convert()
    
    filename = f"{converter.chip_name}.hdl"
    print(f"✓ Processado: {name} → {filename}")

print()

# ============================================================================
# EXEMPLO 4: Tratamento de Casos Especiais
# ============================================================================

print("="*70)
print("EXEMPLO 4: Casos Especiais")
print("="*70)

# Caso 1: Múltiplos inputs com mesmo nome
print("\nCaso 1: Inputs duplicados")
duplicate_inputs = {
    "Name": "Comparator",
    "InputPins": [
        {"Name": "IN", "ID": 1, "BitCount": 8},
        {"Name": "IN", "ID": 2, "BitCount": 8}
    ],
    "OutputPins": [
        {"Name": "EQ", "ID": 3, "BitCount": 1}
    ],
    "SubChips": [],
    "Wires": []
}

converter = AdvancedConverter(duplicate_inputs)
in_sig, out_sig = converter._generate_hdl_signature()
print(f"Assinatura gerada: IN {in_sig}; OUT {out_sig};")

# Caso 2: Barramentos de diferentes tamanhos
print("\nCaso 2: Barramentos mistos")
mixed_buses = {
    "Name": "Extender",
    "InputPins": [
        {"Name": "in", "ID": 1, "BitCount": 4}
    ],
    "OutputPins": [
        {"Name": "out", "ID": 2, "BitCount": 8}
    ],
    "SubChips": [],
    "Wires": []
}

converter = AdvancedConverter(mixed_buses)
in_sig, out_sig = converter._generate_hdl_signature()
print(f"Assinatura gerada: IN {in_sig}; OUT {out_sig};")

print()

# ============================================================================
# EXEMPLO 5: Estatísticas de Conversão
# ============================================================================

print("="*70)
print("EXEMPLO 5: Estatísticas")
print("="*70)

stats = {
    "Total de Inputs": len(mux16_json["InputPins"]),
    "Total de Outputs": len(mux16_json["OutputPins"]),
    "Total de SubChips": len(mux16_json["SubChips"]),
    "Total de Conexões": len(mux16_json["Wires"]),
    "Bits de Input": sum(p["BitCount"] for p in mux16_json["InputPins"]),
    "Bits de Output": sum(p["BitCount"] for p in mux16_json["OutputPins"])
}

for key, value in stats.items():
    print(f"  {key}: {value}")

print("\n" + "="*70)
print("Exemplos concluídos!")
print("="*70)
