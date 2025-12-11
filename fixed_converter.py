#!/usr/bin/env python3
"""
Conversor CORRIGIDO: Digital Logic Sim → Nand2tetris HDL
Baseado nas especificações do HDL Survival Guide

Correções principais:
- Inferência correta de pinos por ordem de conexão (não usa PinIDs como nomes)
- Remove chips inexistentes (Splitter8, Bus8)
- Validação contra API oficial do Hack chip-set
- Suporte correto a sub-busing
"""

import json
import sys
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict


class HackChipAPI:
    """API oficial do Hack chip-set do Nand2tetris"""

    # Definição completa de todos os chips disponíveis
    CHIPS = {
        "Nand": {"inputs": ["a", "b"], "outputs": ["out"]},
        "Not": {"inputs": ["in"], "outputs": ["out"]},
        "And": {"inputs": ["a", "b"], "outputs": ["out"]},
        "Or": {"inputs": ["a", "b"], "outputs": ["out"]},
        "Xor": {"inputs": ["a", "b"], "outputs": ["out"]},
        "Mux": {"inputs": ["a", "b", "sel"], "outputs": ["out"]},
        "DMux": {"inputs": ["in", "sel"], "outputs": ["a", "b"]},
        "Not16": {"inputs": ["in"], "outputs": ["out"]},
        "And16": {"inputs": ["a", "b"], "outputs": ["out"]},
        "Or16": {"inputs": ["a", "b"], "outputs": ["out"]},
        "Mux16": {"inputs": ["a", "b", "sel"], "outputs": ["out"]},
        "Or8Way": {"inputs": ["in"], "outputs": ["out"]},
        "Mux4Way16": {"inputs": ["a", "b", "c", "d", "sel"], "outputs": ["out"]},
        "Mux8Way16": {"inputs": ["a", "b", "c", "d", "e", "f", "g", "h", "sel"], "outputs": ["out"]},
        "DMux4Way": {"inputs": ["in", "sel"], "outputs": ["a", "b", "c", "d"]},
        "DMux8Way": {"inputs": ["in", "sel"], "outputs": ["a", "b", "c", "d", "e", "f", "g", "h"]},
        "HalfAdder": {"inputs": ["a", "b"], "outputs": ["sum", "carry"]},
        "Halfadder": {"inputs": ["a", "b"], "outputs": ["sum", "carry"]},  # Aceitar variação
        "FullAdder": {"inputs": ["a", "b", "c"], "outputs": ["sum", "carry"]},
        "Add16": {"inputs": ["a", "b"], "outputs": ["out"]},
        "Inc16": {"inputs": ["in"], "outputs": ["out"]},
        "ALU": {"inputs": ["x", "y", "zx", "nx", "zy", "ny", "f", "no"], "outputs": ["out", "zr", "ng"]},
        "DFF": {"inputs": ["in"], "outputs": ["out"]},
        "Bit": {"inputs": ["in", "load"], "outputs": ["out"]},
        "Register": {"inputs": ["in", "load"], "outputs": ["out"]},
        "RAM8": {"inputs": ["in", "load", "address"], "outputs": ["out"]},
        "RAM64": {"inputs": ["in", "load", "address"], "outputs": ["out"]},
        "RAM512": {"inputs": ["in", "load", "address"], "outputs": ["out"]},
        "RAM4K": {"inputs": ["in", "load", "address"], "outputs": ["out"]},
        "RAM16K": {"inputs": ["in", "load", "address"], "outputs": ["out"]},
        "PC": {"inputs": ["in", "load", "inc", "reset"], "outputs": ["out"]},
    }

    @classmethod
    def get_chip_spec(cls, chip_name: str) -> Optional[Dict]:
        """Retorna especificação do chip ou None se não existir"""
        return cls.CHIPS.get(chip_name)

    @classmethod
    def is_valid_chip(cls, chip_name: str) -> bool:
        """Verifica se o chip existe no Hack chip-set"""
        return chip_name in cls.CHIPS


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

        # Coletar PinIDs dos outputs de OutputPinColourInfo
        self.output_pin_ids = []
        for pin_info in subchip_data.get("OutputPinColourInfo", []):
            self.output_pin_ids.append(pin_info["PinID"])

        # Mapas de PinID -> lista de Wires
        self.input_wires: Dict[int, List[Wire]] = defaultdict(list)
        self.output_wires: Dict[int, List[Wire]] = defaultdict(list)

        # Mapas de PinID -> nome do pino (será preenchido depois)
        self.input_pin_names: Dict[int, str] = {}
        self.output_pin_names: Dict[int, str] = {}


class FixedConverter:
    def __init__(self, json_data: dict):
        self.data = json_data

        # Warnings - inicializar ANTES de chamar _normalize_chip_name
        self.warnings: List[str] = []

        self.chip_name = self._normalize_chip_name(json_data.get("Name", "UnknownChip"))

        # Indexar inputs e outputs do chip principal
        self.input_pins = {pin["ID"]: pin for pin in json_data.get("InputPins", [])}
        self.output_pins = {pin["ID"]: pin for pin in json_data.get("OutputPins", [])}

        # Componentes indexados por ID
        self.components: Dict[int, Component] = {}
        for subchip_data in json_data.get("SubChips", []):
            comp = Component(subchip_data)
            self.components[comp.id] = comp

        # Processar conexões
        self.wires = [Wire(w) for w in json_data.get("Wires", [])]
        self._map_wires_to_components()
        self._infer_pin_names()

        # Contador de wires internos
        self.wire_counter = 0
        self.wire_name_map: Dict[Tuple[int, int], str] = {}  # (comp_id, pin_id) -> nome

    def _normalize_chip_name(self, name: str) -> str:
        """Normaliza nomes de chips DLS para nomes HDL válidos"""
        # Remover caracteres especiais e espaços
        # Converter para CamelCase se tiver espaços
        if " " in name:
            # "HALF ADDER" -> "HalfAdder"
            parts = name.split()
            name = "".join(part.capitalize() for part in parts)

        name = name.replace("-", "").replace("_", "")

        # Mapear chips DLS específicos para chips Hack
        name_map = {
            "NAND": "Nand",
            "NOT": "Not",
            "AND": "And",
            "OR": "Or",
            "XOR": "Xor",
            "MUX": "Mux",
            "DMUX": "DMux",
            # Chips que NÃO EXISTEM no Hack (remover)
            "8-1BIT": None,  # ❌ Splitter - usar sub-busing
            "1-8BIT": None,  # ❌ Bus - usar sub-busing
            "Splitter8": None,
            "Bus8": None,
        }

        mapped = name_map.get(name, name)

        if mapped is None:
            self.warnings.append(f"WARNING: Chip '{name}' nao existe no Hack chip-set. Sera ignorado.")
            return None

        # Validar contra API do Hack
        if not HackChipAPI.is_valid_chip(mapped):
            self.warnings.append(f"WARNING: Chip '{mapped}' nao encontrado na API do Hack chip-set.")

        return mapped

    def _map_wires_to_components(self):
        """Mapeia wires para componentes"""
        for wire in self.wires:
            # Wire conecta A ENTRADA de um componente
            if wire.target_owner_id in self.components:
                comp = self.components[wire.target_owner_id]
                comp.input_wires[wire.target_pin_id].append(wire)

            # Wire conecta A SAÍDA de um componente
            if wire.source_owner_id in self.components:
                comp = self.components[wire.source_owner_id]
                comp.output_wires[wire.source_pin_id].append(wire)

    def _infer_pin_names(self):
        """
        Inferir nomes de pinos baseado na ordem e na API do Hack.

        CORREÇÃO PRINCIPAL: Não usa PinIDs diretamente como nomes,
        mas mapeia pela ordem de conexão.
        """
        for comp_id, comp in self.components.items():
            normalized_name = self._normalize_chip_name(comp.name)

            if normalized_name is None:
                continue  # Chip inexistente, pular

            chip_spec = HackChipAPI.get_chip_spec(normalized_name)

            if not chip_spec:
                # Chip customizado ou desconhecido - usar nomes genéricos
                self._infer_generic_pin_names(comp)
                continue

            # CRÍTICO: Mapear inputs pela ORDEM DE INSERÇÃO (não ordenar numericamente!)
            # Preservar ordem exata do JSON para manter circuito fiel ao original
            input_pin_ids = list(comp.input_wires.keys())  # Mantém ordem de inserção
            expected_inputs = chip_spec["inputs"]

            if len(input_pin_ids) > len(expected_inputs):
                self.warnings.append(
                    f"WARNING: {comp.name} (ID {comp.id}): "
                    f"Tem {len(input_pin_ids)} inputs, mas API espera {len(expected_inputs)}"
                )

            for idx, pin_id in enumerate(input_pin_ids):
                if idx < len(expected_inputs):
                    comp.input_pin_names[pin_id] = expected_inputs[idx]
                else:
                    comp.input_pin_names[pin_id] = f"in{idx}"

            # CRÍTICO: Mapear outputs usando OutputPinColourInfo (ordem correta!)
            # OutputPinColourInfo contém os PinIDs na ordem real dos outputs do chip
            expected_outputs = chip_spec["outputs"]

            if comp.output_pin_ids:  # Usar OutputPinColourInfo se disponível
                for idx, pin_id in enumerate(comp.output_pin_ids):
                    if idx < len(expected_outputs):
                        comp.output_pin_names[pin_id] = expected_outputs[idx]
                    else:
                        comp.output_pin_names[pin_id] = f"out{idx}"
            else:
                # Fallback: usar ordem de inserção dos wires
                output_pin_ids = list(comp.output_wires.keys())

                if len(output_pin_ids) > len(expected_outputs):
                    self.warnings.append(
                        f"WARNING: {comp.name} (ID {comp.id}): "
                        f"Tem {len(output_pin_ids)} outputs, mas API espera {len(expected_outputs)}"
                    )

                for idx, pin_id in enumerate(output_pin_ids):
                    if idx < len(expected_outputs):
                        comp.output_pin_names[pin_id] = expected_outputs[idx]
                    else:
                        comp.output_pin_names[pin_id] = f"out{idx}"

    def _infer_generic_pin_names(self, comp: Component):
        """Gera nomes genéricos para chips desconhecidos"""
        # Preservar ordem de inserção (não ordenar!)
        for idx, pin_id in enumerate(comp.input_wires.keys()):
            comp.input_pin_names[pin_id] = f"in{idx}" if idx > 0 else "in"

        for idx, pin_id in enumerate(comp.output_wires.keys()):
            comp.output_pin_names[pin_id] = f"out{idx}" if idx > 0 else "out"

    def _get_or_create_wire_name(self, comp_id: int, pin_id: int) -> str:
        """Cria ou retorna nome de wire interno"""
        key = (comp_id, pin_id)
        if key not in self.wire_name_map:
            self.wire_counter += 1
            self.wire_name_map[key] = f"w{self.wire_counter}"
        return self.wire_name_map[key]

    def _get_wire_source_name(self, wire: Wire) -> str:
        """Obtém o nome da fonte de um wire"""
        # Fonte é um input pin do chip principal
        if wire.source_owner_id in self.input_pins:
            pin = self.input_pins[wire.source_owner_id]
            name = pin["Name"].lower()
            bit_count = pin["BitCount"]

            # Identificar qual input é (pode haver múltiplos com mesmo nome)
            same_name_pins = [p for p in self.input_pins.values() if p["Name"] == pin["Name"]]
            if len(same_name_pins) > 1:
                # Adicionar índice numérico
                pin_ids = sorted([p["ID"] for p in same_name_pins])
                idx = pin_ids.index(pin["ID"])
                if idx > 0:
                    name = f"{name}{idx}"

            # Sub-busing para barramentos
            if bit_count > 1 and wire.source_pin_id < bit_count:
                return f"{name}[{wire.source_pin_id}]"

            return name

        # Fonte é output de um componente interno
        elif wire.source_owner_id in self.components:
            return self._get_or_create_wire_name(wire.source_owner_id, wire.source_pin_id)

        return "unknown"

    def _generate_hdl_signature(self) -> Tuple[str, str]:
        """Gera a assinatura IN/OUT do chip"""
        in_parts = []
        seen_names = {}

        for pin_id, pin in self.input_pins.items():
            name = pin["Name"].lower()
            bit_count = pin["BitCount"]

            # Tratar inputs duplicados
            if name in seen_names:
                seen_names[name] += 1
                name = f"{name}{seen_names[name] - 1}"
            else:
                seen_names[name] = 1

            if bit_count > 1:
                in_parts.append(f"{name}[{bit_count}]")
            else:
                in_parts.append(name)

        out_parts = []
        for pin_id, pin in self.output_pins.items():
            name = pin["Name"].lower().replace(" ", "")  # Remover espaços
            bit_count = pin["BitCount"]

            if bit_count > 1:
                out_parts.append(f"{name}[{bit_count}]")
            else:
                out_parts.append(name)

        return ", ".join(in_parts), ", ".join(out_parts)

    def convert(self) -> str:
        """Converte para HDL com todas as correções aplicadas"""
        in_sig, out_sig = self._generate_hdl_signature()

        hdl = []
        hdl.append("// Converted from Digital Logic Sim (Sebastian Lague)")
        hdl.append(f"// Original chip: {self.data['Name']}")
        hdl.append("// Fixed converter - compliant with Nand2tetris HDL specification")
        hdl.append("")
        hdl.append(f"CHIP {self.chip_name} {{")
        hdl.append(f"    IN {in_sig};")
        hdl.append(f"    OUT {out_sig};")
        hdl.append("")
        hdl.append("    PARTS:")

        # Gerar instâncias de componentes
        for comp_id, comp in self.components.items():
            normalized_name = self._normalize_chip_name(comp.name)

            if normalized_name is None:
                # Chip inexistente - adicionar comentário
                hdl.append(f"    // SKIPPED: {comp.name} (não existe no Hack chip-set)")
                continue

            # Construir conexões
            connections = []

            # Inputs do componente - PRESERVAR ORDEM DE INSERÇÃO!
            for pin_id in comp.input_wires.keys():
                wires = comp.input_wires[pin_id]
                if wires:
                    # Usar o primeiro wire (geralmente só há um)
                    wire = wires[0]
                    source_name = self._get_wire_source_name(wire)
                    param_name = comp.input_pin_names.get(pin_id, f"in{pin_id}")
                    connections.append(f"{param_name}={source_name}")

            # Outputs do componente - USAR ORDEM CORRETA (OutputPinColourInfo)!
            # Iterar na mesma ordem que OutputPinColourInfo para manter ordem correta
            if comp.output_pin_ids:
                output_pin_ids_ordered = comp.output_pin_ids
            else:
                output_pin_ids_ordered = list(comp.output_wires.keys())

            for pin_id in output_pin_ids_ordered:
                if pin_id not in comp.output_wires:
                    continue  # Pino sem conexões

                wires = comp.output_wires[pin_id]

                # Verificar se conecta diretamente ao output do chip
                connects_to_output = any(
                    w.target_owner_id in self.output_pins
                    for w in wires
                )

                if connects_to_output:
                    # Conecta ao output do chip principal
                    # Usar nomes da API do Hack para outputs
                    chip_spec = HackChipAPI.get_chip_spec(self.chip_name)

                    output_pin = None
                    for w in wires:
                        if w.target_owner_id in self.output_pins:
                            output_pin = self.output_pins[w.target_owner_id]
                            break

                    if chip_spec and output_pin:
                        # Encontrar índice do output
                        output_pins_list = list(self.output_pins.values())
                        idx = output_pins_list.index(output_pin)
                        if idx < len(chip_spec["outputs"]):
                            wire_name = chip_spec["outputs"][idx]
                        else:
                            wire_name = self._get_or_create_wire_name(comp_id, pin_id)
                    elif output_pin:
                        wire_name = output_pin["Name"].lower().replace(" ", "")
                    else:
                        wire_name = self._get_or_create_wire_name(comp_id, pin_id)
                else:
                    # Wire interno
                    wire_name = self._get_or_create_wire_name(comp_id, pin_id)

                param_name = comp.output_pin_names.get(pin_id, f"out{pin_id}")
                connections.append(f"{param_name}={wire_name}")

            # Adicionar linha do componente
            if connections:
                conn_str = ", ".join(connections)
                hdl.append(f"    {normalized_name}({conn_str});")
            else:
                hdl.append(f"    // WARNING: {normalized_name} has no connections")

        hdl.append("}")

        return "\n".join(hdl)

    def generate_report(self) -> str:
        """Gera relatório de conversão"""
        lines = []
        lines.append("=" * 70)
        lines.append(f"RELATÓRIO DE CONVERSÃO: {self.data['Name']}")
        lines.append("=" * 70)
        lines.append("")

        # Warnings
        if self.warnings:
            lines.append("WARNING:")
            for warning in self.warnings:
                lines.append(f"  {warning}")
            lines.append("")

        # Inputs
        lines.append("ENTRADAS:")
        for pin_id, pin in self.input_pins.items():
            lines.append(f"  {pin['Name']}: {pin['BitCount']} bit(s) [ID: {pin_id}]")

        # Outputs
        lines.append("\nSAÍDAS:")
        for pin_id, pin in self.output_pins.items():
            lines.append(f"  {pin['Name']}: {pin['BitCount']} bit(s) [ID: {pin_id}]")

        # Componentes
        lines.append(f"\nCOMPONENTES ({len(self.components)}):")
        for comp_id, comp in self.components.items():
            normalized = self._normalize_chip_name(comp.name)
            status = "[OK]" if normalized else "[SKIP]"
            lines.append(f"  {status} {comp.name} -> {normalized or 'SKIPPED'} [ID: {comp_id}]")

            # Mostrar mapeamento de pinos
            if normalized and comp.input_pin_names:
                lines.append("    Inputs:")
                for pin_id, pin_name in comp.input_pin_names.items():
                    lines.append(f"      PinID {pin_id} -> {pin_name}")

            if normalized and comp.output_pin_names:
                lines.append("    Outputs:")
                for pin_id, pin_name in comp.output_pin_names.items():
                    lines.append(f"      PinID {pin_id} -> {pin_name}")

        lines.append("\n" + "=" * 70)
        return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Uso: python fixed_converter.py <arquivo.json>")
        print("\nEste conversor está em conformidade com as especificações do HDL Survival Guide.")
        sys.exit(1)

    with open(sys.argv[1], 'r') as f:
        data = json.load(f)

    converter = FixedConverter(data)

    # Relatório
    print(converter.generate_report())
    print()

    # HDL
    hdl = converter.convert()
    print(hdl)
    print()

    # Salvar
    output_file = f"{converter.chip_name}.hdl"
    with open(output_file, 'w') as f:
        f.write(hdl)

    print(f"[OK] Arquivo salvo: {output_file}")

    if converter.warnings:
        print(f"\nWARNING: {len(converter.warnings)} aviso(s) encontrado(s). Revise o relatorio acima.")


if __name__ == "__main__":
    main()
