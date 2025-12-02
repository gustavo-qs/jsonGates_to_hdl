#!/usr/bin/env python3
"""
Conversor de Digital Logic Sim (Sebastian Lague) para Nand2tetris HDL
"""

import json
import sys
from typing import Dict, List, Set, Tuple
from collections import defaultdict


class DLSToHDLConverter:
    def __init__(self, json_data: dict):
        self.data = json_data
        self.chip_name = json_data.get("Name", "UnknownChip")
        self.input_pins = json_data.get("InputPins", [])
        self.output_pins = json_data.get("OutputPins", [])
        self.subchips = json_data.get("SubChips", [])
        self.wires = json_data.get("Wires", [])
        
        # Mapeamentos para facilitar a conversão
        self.subchip_by_id: Dict[int, dict] = {}
        self.pin_by_id: Dict[int, dict] = {}
        self.connections: Dict[int, List[dict]] = defaultdict(list)
        
        self._build_mappings()
    
    def _build_mappings(self):
        """Constrói índices para acesso rápido aos componentes"""
        # Mapear SubChips por ID
        for subchip in self.subchips:
            self.subchip_by_id[subchip["ID"]] = subchip
        
        # Mapear Input/Output Pins por ID
        for pin in self.input_pins + self.output_pins:
            self.pin_by_id[pin["ID"]] = pin
        
        # Organizar conexões por componente de destino
        for wire in self.wires:
            target_id = wire["TargetPinAddress"]["PinOwnerID"]
            self.connections[target_id].append(wire)
    
    def _normalize_chip_name(self, name: str) -> str:
        """Converte nomes do DLS para convenção do Nand2tetris"""
        # Mapeamentos comuns
        name_map = {
            "8-1BIT": "Bus8To1",  # Separador de barramento 8-bit para bits individuais
            "1-8BIT": "Bus1To8",  # Combinador de bits individuais para barramento 8-bit
            "MUX": "Mux",
            "AND": "And",
            "OR": "Or",
            "NOT": "Not",
            "NAND": "Nand",
            "NOR": "Nor",
            "XOR": "Xor",
        }
        return name_map.get(name, name)
    
    def _get_hdl_signature(self) -> str:
        """Gera a assinatura do chip (IN/OUT)"""
        # Processar inputs
        in_parts = []
        for pin in self.input_pins:
            name = pin["Name"].lower()
            bit_count = pin["BitCount"]
            if bit_count > 1:
                in_parts.append(f"{name}[{bit_count}]")
            else:
                in_parts.append(name)
        
        # Processar outputs
        out_parts = []
        for pin in self.output_pins:
            name = pin["Name"].lower()
            bit_count = pin["BitCount"]
            if bit_count > 1:
                out_parts.append(f"{name}[{bit_count}]")
            else:
                out_parts.append(name)
        
        in_signature = ", ".join(in_parts) if in_parts else ""
        out_signature = ", ".join(out_parts) if out_parts else ""
        
        return in_signature, out_signature
    
    def _trace_connections(self, subchip_id: int) -> Dict[str, str]:
        """Rastreia as conexões de um subchip específico"""
        connections = {}
        
        for wire in self.wires:
            target_owner = wire["TargetPinAddress"]["PinOwnerID"]
            source_owner = wire["SourcePinAddress"]["PinOwnerID"]
            
            if target_owner == subchip_id:
                # Este subchip é o destino
                source_pin_id = wire["SourcePinAddress"]["PinID"]
                target_pin_id = wire["TargetPinAddress"]["PinID"]
                
                # Verificar se a fonte é um InputPin
                if source_owner in self.pin_by_id:
                    source_name = self.pin_by_id[source_owner]["Name"].lower()
                    connections[f"in_{target_pin_id}"] = source_name
        
        return connections
    
    def _generate_parts_section(self) -> List[str]:
        """Gera a seção PARTS do HDL"""
        parts_lines = []
        
        # Contador para instâncias múltiplas do mesmo tipo
        chip_counters = defaultdict(int)
        
        for subchip in self.subchips:
            chip_type = self._normalize_chip_name(subchip["Name"])
            chip_id = subchip["ID"]
            
            # Nome da instância (para chips repetidos)
            chip_counters[chip_type] += 1
            instance_suffix = chip_counters[chip_type] if chip_counters[chip_type] > 1 else ""
            
            # Rastrear conexões deste subchip
            connections = self._trace_connections(chip_id)
            
            # Gerar linha de instanciação
            # Nota: Esta é uma simplificação - conexões reais precisam de análise mais profunda
            parts_lines.append(f"    // {chip_type} instance (ID: {chip_id})")
            parts_lines.append(f"    {chip_type}(...);  // TODO: mapear conexões corretamente")
        
        return parts_lines
    
    def convert(self) -> str:
        """Converte o JSON completo para HDL"""
        in_sig, out_sig = self._get_hdl_signature()
        
        hdl = []
        hdl.append(f"// Converted from Digital Logic Sim")
        hdl.append(f"// Original chip: {self.chip_name}")
        hdl.append(f"")
        hdl.append(f"CHIP {self.chip_name} {{")
        hdl.append(f"    IN {in_sig};")
        hdl.append(f"    OUT {out_sig};")
        hdl.append(f"")
        hdl.append(f"    PARTS:")
        
        # Adicionar análise detalhada
        hdl.append(f"    // Analysis:")
        hdl.append(f"    // - {len(self.input_pins)} input pin(s)")
        hdl.append(f"    // - {len(self.output_pins)} output pin(s)")
        hdl.append(f"    // - {len(self.subchips)} subchip(s)")
        hdl.append(f"    // - {len(self.wires)} wire connection(s)")
        hdl.append(f"")
        
        # Adicionar seção PARTS
        parts = self._generate_parts_section()
        hdl.extend(parts)
        
        hdl.append(f"}}")
        
        return "\n".join(hdl)
    
    def analyze(self) -> str:
        """Gera análise detalhada da estrutura do chip"""
        analysis = []
        analysis.append(f"=== Análise do Chip: {self.chip_name} ===\n")
        
        # Input Pins
        analysis.append("INPUT PINS:")
        for pin in self.input_pins:
            analysis.append(f"  - {pin['Name']}: {pin['BitCount']} bit(s) [ID: {pin['ID']}]")
        
        # Output Pins
        analysis.append("\nOUTPUT PINS:")
        for pin in self.output_pins:
            analysis.append(f"  - {pin['Name']}: {pin['BitCount']} bit(s) [ID: {pin['ID']}]")
        
        # SubChips
        analysis.append(f"\nSUBCHIPS ({len(self.subchips)}):")
        chip_types = defaultdict(int)
        for subchip in self.subchips:
            chip_types[subchip['Name']] += 1
        
        for chip_type, count in chip_types.items():
            analysis.append(f"  - {chip_type}: {count} instance(s)")
        
        # Wires/Connections
        analysis.append(f"\nCONNECTIONS ({len(self.wires)}):")
        
        # Agrupar conexões por tipo
        input_to_subchip = []
        subchip_to_subchip = []
        subchip_to_output = []
        
        for wire in self.wires:
            source_id = wire["SourcePinAddress"]["PinOwnerID"]
            target_id = wire["TargetPinAddress"]["PinOwnerID"]
            
            source_is_input = source_id in self.pin_by_id
            target_is_output = target_id in self.pin_by_id
            
            if source_is_input and not target_is_output:
                input_to_subchip.append(wire)
            elif not source_is_input and target_is_output:
                subchip_to_output.append(wire)
            elif not source_is_input and not target_is_output:
                subchip_to_subchip.append(wire)
        
        analysis.append(f"  - Input → SubChip: {len(input_to_subchip)}")
        analysis.append(f"  - SubChip → SubChip: {len(subchip_to_subchip)}")
        analysis.append(f"  - SubChip → Output: {len(subchip_to_output)}")
        
        return "\n".join(analysis)


def main():
    if len(sys.argv) < 2:
        print("Uso: python dls_to_hdl_converter.py <arquivo.json>")
        print("\nOu use no código:")
        print("  converter = DLSToHDLConverter(json_data)")
        print("  hdl = converter.convert()")
        sys.exit(1)
    
    # Carregar JSON
    with open(sys.argv[1], 'r') as f:
        data = json.load(f)
    
    # Converter
    converter = DLSToHDLConverter(data)
    
    # Mostrar análise
    print(converter.analyze())
    print("\n" + "="*60 + "\n")
    
    # Gerar HDL
    hdl = converter.convert()
    print(hdl)
    
    # Salvar arquivo HDL
    output_file = f"{converter.chip_name}.hdl"
    with open(output_file, 'w') as f:
        f.write(hdl)
    
    print(f"\n✓ Arquivo HDL salvo em: {output_file}")


if __name__ == "__main__":
    main()
