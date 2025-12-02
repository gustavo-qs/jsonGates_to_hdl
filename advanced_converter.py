#!/usr/bin/env python3
"""
Conversor Avançado: Digital Logic Sim → Nand2tetris HDL
Mapeia conexões completas entre componentes
"""

import json
import sys
from typing import Dict, List, Optional
from collections import defaultdict


class Wire:
    """Representa uma conexão entre pinos"""
    def __init__(self, wire_data: dict):
        self.source_pin_id = wire_data["SourcePinAddress"]["PinID"]
        self.source_owner_id = wire_data["SourcePinAddress"]["PinOwnerID"]
        self.target_pin_id = wire_data["TargetPinAddress"]["PinID"]
        self.target_owner_id = wire_data["TargetPinAddress"]["PinOwnerID"]


class Component:
    """Representa um componente (SubChip)"""
    def __init__(self, subchip_data: dict):
        self.name = subchip_data["Name"]
        self.id = subchip_data["ID"]
        self.label = subchip_data.get("Label", "")
        self.input_connections: Dict[int, Wire] = {}
        self.output_connections: Dict[int, List[Wire]] = defaultdict(list)


class AdvancedConverter:
    def __init__(self, json_data: dict):
        self.data = json_data
        self.chip_name = json_data.get("Name", "UnknownChip").replace("-", "")
        self.input_pins = {pin["ID"]: pin for pin in json_data.get("InputPins", [])}
        self.output_pins = {pin["ID"]: pin for pin in json_data.get("OutputPins", [])}

        # Componentes indexados por ID
        self.components: Dict[int, Component] = {}
        for subchip_data in json_data.get("SubChips", []):
            comp = Component(subchip_data)
            self.components[comp.id] = comp

        # Processar conexões
        self.wires = [Wire(w) for w in json_data.get("Wires", [])]
        self._map_connections()

        # Contador de wires internos para nomes sequenciais
        self.wire_counter = 0
        self.wire_name_map: Dict[tuple, str] = {}  # (comp_id, pin_id) -> nome do wire

    def _map_connections(self):
        """Mapeia todas as conexões para os componentes"""
        for wire in self.wires:
            # Conexão de entrada para o componente de destino
            if wire.target_owner_id in self.components:
                self.components[wire.target_owner_id].input_connections[wire.target_pin_id] = wire

            # Conexão de saída do componente de origem
            if wire.source_owner_id in self.components:
                self.components[wire.source_owner_id].output_connections[wire.source_pin_id].append(wire)

    def _normalize_chip_name(self, name: str) -> str:
        """Normaliza nomes de chips para HDL"""
        name_map = {
            "8-1BIT": "Splitter8",
            "1-8BIT": "Bus8",
            "MUX": "Mux",
            "AND": "And",
            "OR": "Or",
            "NOT": "Not",
            "NAND": "Nand",
            "XOR": "Xor",
        }
        return name_map.get(name, name)

    def _get_chip_pin_mapping(self, chip_name: str) -> Dict[str, Dict[int, str]]:
        """Retorna o mapeamento de pinos para cada tipo de chip"""
        mappings = {
            "NAND": {
                "in": {0: "a", 1: "b"},
                "out": {2: "out"}
            },
            "AND": {
                "in": {0: "a", 1: "b"},
                "out": {2: "out"}
            },
            "OR": {
                "in": {0: "a", 1: "b"},
                "out": {2: "out"}
            },
            "NOT": {
                "in": {0: "in"},
                "out": {1: "out"}
            },
            "XOR": {
                "in": {0: "a", 1: "b"},
                "out": {2: "out"}
            },
            "MUX": {
                "in": {0: "a", 1: "b", 2: "sel"},
                "out": {3: "out"}
            },
        }
        return mappings.get(chip_name, {"in": {}, "out": {}})

    def _get_component_pin_name(self, comp: Component, pin_id: int, is_output: bool) -> str:
        """Retorna o nome do pino de um componente"""
        pin_map = self._get_chip_pin_mapping(comp.name)
        direction = "out" if is_output else "in"

        if pin_id in pin_map[direction]:
            return pin_map[direction][pin_id]

        # Fallback para nomes genéricos
        if is_output:
            return "out" if pin_id == 0 else f"out{pin_id}"
        else:
            return "in" if pin_id == 0 else f"in{pin_id}"

    def _get_or_create_wire_name(self, comp_id: int, pin_id: int) -> str:
        """Cria ou retorna nome de wire interno existente"""
        key = (comp_id, pin_id)
        if key not in self.wire_name_map:
            self.wire_counter += 1
            self.wire_name_map[key] = f"w{self.wire_counter}"
        return self.wire_name_map[key]

    def _get_wire_source_name(self, wire: Wire) -> str:
        """Obtém o nome da fonte de um wire"""
        if wire.source_owner_id in self.input_pins:
            # Fonte é um input pin do chip principal
            pin = self.input_pins[wire.source_owner_id]
            name = pin["Name"].lower()
            bit_count = pin["BitCount"]

            # Identificar qual input é (pode haver múltiplos com mesmo nome)
            same_name = [p for p in self.input_pins.values() if p["Name"] == pin["Name"]]
            if len(same_name) > 1:
                idx = [p["ID"] for p in self.input_pins.values()].index(pin["ID"])
                name = f"{name}{idx}"

            # Se for barramento, especificar bit
            if bit_count > 1 and wire.source_pin_id < bit_count:
                return f"{name}[{wire.source_pin_id}]"
            return name

        elif wire.source_owner_id in self.components:
            # Fonte é output de um componente interno
            return self._get_or_create_wire_name(wire.source_owner_id, wire.source_pin_id)

        return "unknown"

    def _generate_hdl_signature(self) -> tuple[str, str]:
        """Gera a assinatura IN/OUT do chip"""
        in_parts = []
        seen_names = {}

        for pin_id, pin in self.input_pins.items():
            name = pin["Name"].lower()
            bit_count = pin["BitCount"]

            # Tratar inputs duplicados
            if name in seen_names:
                seen_names[name] += 1
                name = f"{name}{seen_names[name]-1}"
            else:
                seen_names[name] = 1

            if bit_count > 1:
                in_parts.append(f"{name}[{bit_count}]")
            else:
                in_parts.append(name)

        out_parts = []
        for pin_id, pin in self.output_pins.items():
            name = pin["Name"].lower()
            bit_count = pin["BitCount"]

            if bit_count > 1:
                out_parts.append(f"{name}[{bit_count}]")
            else:
                out_parts.append(name)

        return ", ".join(in_parts), ", ".join(out_parts)

    def convert(self) -> str:
        """Converte para HDL com mapeamento de conexões"""
        in_sig, out_sig = self._generate_hdl_signature()

        hdl = []
        hdl.append("// Converted from Digital Logic Sim (Sebastian Lague)")
        hdl.append(f"// Original chip: {self.data['Name']}")
        hdl.append("")
        hdl.append(f"CHIP {self.chip_name} {{")
        hdl.append(f"    IN {in_sig};")
        hdl.append(f"    OUT {out_sig};")
        hdl.append("")
        hdl.append("    PARTS:")

        # Gerar instâncias de componentes com conexões
        chip_instances = defaultdict(int)

        for comp_id, comp in self.components.items():
            chip_type = self._normalize_chip_name(comp.name)
            chip_instances[chip_type] += 1

            # Construir parâmetros de conexão
            connections = []

            # Inputs do componente
            for pin_id, wire in comp.input_connections.items():
                source_name = self._get_wire_source_name(wire)
                param_name = self._get_component_pin_name(comp, pin_id, is_output=False)
                connections.append(f"{param_name}={source_name}")

            # Outputs do componente
            for pin_id, wires_list in comp.output_connections.items():
                # Verificar se conecta ao output final do chip
                connects_to_output = any(
                    w.target_owner_id in self.output_pins
                    for w in wires_list
                )

                if connects_to_output:
                    # Conecta diretamente ao output do chip
                    output_pin = None
                    for w in wires_list:
                        if w.target_owner_id in self.output_pins:
                            output_pin = self.output_pins[w.target_owner_id]
                            break

                    if output_pin:
                        wire_name = output_pin["Name"].lower()
                    else:
                        wire_name = self._get_or_create_wire_name(comp_id, pin_id)
                else:
                    # Wire interno
                    wire_name = self._get_or_create_wire_name(comp_id, pin_id)

                param_name = self._get_component_pin_name(comp, pin_id, is_output=True)
                connections.append(f"{param_name}={wire_name}")

            # Adicionar linha do componente
            if connections:
                conn_str = ", ".join(connections)
                hdl.append(f"    {chip_type}({conn_str});")
            else:
                hdl.append(f"    {chip_type}(...);  // TODO: map connections")

        hdl.append("}")

        return "\n".join(hdl)

    def generate_detailed_report(self) -> str:
        """Gera relatório detalhado da conversão"""
        lines = []
        lines.append("=" * 70)
        lines.append(f"RELATÓRIO DE CONVERSÃO: {self.data['Name']}")
        lines.append("=" * 70)
        lines.append("")

        # Inputs
        lines.append("ENTRADAS:")
        for pin_id, pin in self.input_pins.items():
            lines.append(f"  [{pin_id}] {pin['Name']}: {pin['BitCount']} bit(s)")

        # Outputs
        lines.append("\nSAÍDAS:")
        for pin_id, pin in self.output_pins.items():
            lines.append(f"  [{pin_id}] {pin['Name']}: {pin['BitCount']} bit(s)")

        # Componentes
        lines.append(f"\nCOMPONENTES ({len(self.components)}):")
        for comp_id, comp in self.components.items():
            lines.append(f"  [{comp_id}] {comp.name}")

            # Inputs do componente
            if comp.input_connections:
                lines.append("    Inputs:")
                for pin_id, wire in comp.input_connections.items():
                    source = self._get_wire_source_name(wire)
                    pin_name = self._get_component_pin_name(comp, pin_id, is_output=False)
                    lines.append(f"      {pin_name} ← {source}")

            # Outputs do componente
            if comp.output_connections:
                lines.append("    Outputs:")
                for pin_id, wires in comp.output_connections.items():
                    targets = []
                    for w in wires:
                        if w.target_owner_id in self.output_pins:
                            targets.append("OUTPUT")
                        elif w.target_owner_id in self.components:
                            target_comp = self.components[w.target_owner_id]
                            pin_name = self._get_component_pin_name(target_comp, w.target_pin_id, is_output=False)
                            targets.append(f"{target_comp.name}#{w.target_owner_id}.{pin_name}")
                    pin_name = self._get_component_pin_name(comp, pin_id, is_output=True)
                    lines.append(f"      {pin_name} → {', '.join(targets)}")

        lines.append("\n" + "=" * 70)
        return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Uso: python advanced_converter.py <arquivo.json>")
        sys.exit(1)

    with open(sys.argv[1], 'r') as f:
        data = json.load(f)

    converter = AdvancedConverter(data)

    # Relatório
    print(converter.generate_detailed_report())
    print()

    # HDL
    hdl = converter.convert()
    print(hdl)
    print()

    # Salvar
    output_file = f"{converter.chip_name}.hdl"
    with open(output_file, 'w') as f:
        f.write(hdl)

    print(f"✓ Arquivo salvo: {output_file}")


if __name__ == "__main__":
    main()
