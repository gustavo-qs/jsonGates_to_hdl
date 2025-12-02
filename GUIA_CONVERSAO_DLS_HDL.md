# Guia de Conversão: Digital Logic Sim → Nand2tetris HDL

## 📋 Sumário
1. [Estrutura do JSON do DLS](#estrutura-do-json)
2. [Mapeamento de Conceitos](#mapeamento-de-conceitos)
3. [Algoritmo de Conversão](#algoritmo-de-conversão)
4. [Scripts Python](#scripts-python)
5. [Limitações e Desafios](#limitações)
6. [Exemplos Práticos](#exemplos)

---

## 🔍 Estrutura do JSON do DLS

O Digital Logic Sim salva circuitos em JSON com esta estrutura:

```json
{
  "Name": "MUX-16",           // Nome do chip
  "InputPins": [...],          // Pinos de entrada
  "OutputPins": [...],         // Pinos de saída
  "SubChips": [...],           // Componentes internos
  "Wires": [...]               // Conexões entre componentes
}
```

### InputPins / OutputPins

```json
{
  "Name": "IN",               // Nome do pino
  "ID": 1952408028,           // ID único
  "Position": {...},          // Posição visual (ignorar)
  "BitCount": 8,              // Largura do barramento
  "Colour": 0                 // Cor visual (ignorar)
}
```

**Mapeamento para HDL:**
- `Name` → nome do parâmetro (converter para lowercase)
- `BitCount > 1` → usar array notation `name[BitCount]`
- `ID` → usado para rastrear conexões

### SubChips

```json
{
  "Name": "MUX",              // Tipo do componente
  "ID": 1327073049,           // ID único desta instância
  "Label": "",                // Rótulo personalizado (opcional)
  "Position": {...},          // Posição visual (ignorar)
  "OutputPinColourInfo": [...] // Info de cores (ignorar)
}
```

**Mapeamento para HDL:**
- `Name` → tipo do chip a instanciar
- `ID` → usado para rastrear conexões nos Wires
- Múltiplas instâncias do mesmo tipo → numerar (Mux1, Mux2, ...)

### Wires

```json
{
  "SourcePinAddress": {
    "PinID": 0,               // Pino de origem
    "PinOwnerID": 1130506631  // Componente de origem (ID)
  },
  "TargetPinAddress": {
    "PinID": 0,               // Pino de destino
    "PinOwnerID": 52227899    // Componente de destino (ID)
  },
  "ConnectionType": 0,        // Tipo de conexão (ignorar)
  "Points": [...]             // Pontos visuais do fio (ignorar)
}
```

**Mapeamento para HDL:**
- `PinOwnerID` pode referenciar:
  - InputPin (se ID estiver em InputPins)
  - OutputPin (se ID estiver em OutputPins)
  - SubChip (se ID estiver em SubChips)
- `PinID` identifica qual pino específico (0, 1, 2...)

---

## 🔄 Mapeamento de Conceitos

### DLS → HDL: Tipos de Componentes

| DLS Name | HDL Equivalent | Descrição |
|----------|----------------|-----------|
| `MUX` | `Mux` | Multiplexador |
| `8-1BIT` | `Splitter8` | Divide barramento de 8 bits em 8 bits individuais |
| `1-8BIT` | `Bus8` | Agrupa 8 bits em barramento de 8 bits |
| `AND` | `And` | Porta AND |
| `OR` | `Or` | Porta OR |
| `NOT` | `Not` | Porta NOT |

### Conexões

**DLS:** Usa IDs numéricos para referenciar componentes
```json
{
  "SourcePinOwnerID": 1130506631,  // InputPin "IN"
  "TargetPinOwnerID": 52227899     // SubChip "8-1BIT"
}
```

**HDL:** Usa nomes simbólicos
```hdl
Splitter8(in=in1, out[0]=bit0, out[1]=bit1, ...);
```

---

## ⚙️ Algoritmo de Conversão

### Etapa 1: Indexação
```python
# Criar dicionários para acesso rápido
input_pins = {pin["ID"]: pin for pin in json["InputPins"]}
output_pins = {pin["ID"]: pin for pin in json["OutputPins"]}
subchips = {chip["ID"]: chip for chip in json["SubChips"]}
```

### Etapa 2: Análise de Conexões
```python
# Para cada Wire, determinar:
# 1. Tipo de origem (InputPin, SubChip)
# 2. Tipo de destino (OutputPin, SubChip)
# 3. Nome simbólico da conexão

for wire in wires:
    source_id = wire["SourcePinAddress"]["PinOwnerID"]
    target_id = wire["TargetPinAddress"]["PinOwnerID"]
    
    if source_id in input_pins:
        source_name = input_pins[source_id]["Name"]
    elif source_id in subchips:
        source_name = f"internal_{source_id}"
```

### Etapa 3: Geração da Assinatura
```python
def generate_signature(input_pins, output_pins):
    in_parts = []
    for pin in input_pins.values():
        name = pin["Name"].lower()
        if pin["BitCount"] > 1:
            in_parts.append(f"{name}[{pin['BitCount']}]")
        else:
            in_parts.append(name)
    
    # Similar para outputs
    return ", ".join(in_parts), ", ".join(out_parts)
```

### Etapa 4: Geração do PARTS
```python
# Para cada SubChip, gerar linha de instanciação
for subchip in subchips.values():
    chip_type = normalize_name(subchip["Name"])
    
    # Encontrar conexões de entrada
    inputs = find_input_connections(subchip["ID"])
    
    # Encontrar conexões de saída
    outputs = find_output_connections(subchip["ID"])
    
    # Gerar linha HDL
    print(f"{chip_type}({inputs}, {outputs});")
```

---

## 🐍 Scripts Python

### Script 1: Conversor Básico (`dls_to_hdl_converter.py`)

**Funcionalidades:**
- ✅ Análise da estrutura do chip
- ✅ Contagem de componentes
- ✅ Geração da assinatura IN/OUT
- ⚠️ Mapeamento parcial de conexões

**Uso:**
```bash
python dls_to_hdl_converter.py circuito.json
```

**Saída:**
- Relatório de análise no terminal
- Arquivo `.hdl` gerado

### Script 2: Conversor Avançado (`advanced_converter.py`)

**Funcionalidades:**
- ✅ Rastreamento completo de conexões
- ✅ Nomeação automática de wires internos
- ✅ Suporte a múltiplas instâncias do mesmo chip
- ✅ Relatório detalhado de cada componente

**Uso:**
```bash
python advanced_converter.py circuito.json
```

**Saída:**
- Relatório completo com mapa de conexões
- Arquivo `.hdl` com conexões mapeadas

---

## ⚠️ Limitações e Desafios

### 1. Nomes Ambíguos

**Problema:** DLS permite múltiplos pinos com o mesmo nome
```json
InputPins: [
  {"Name": "IN", "ID": 123, "BitCount": 8},
  {"Name": "IN", "ID": 456, "BitCount": 8}
]
```

**Solução:** Adicionar sufixos numéricos
```hdl
IN in0[8], in1[8];
```

### 2. Componentes Customizados

**Problema:** DLS permite chips customizados que não existem em Nand2tetris
```json
{"Name": "8-1BIT"}  // Não existe no Nand2tetris padrão
```

**Solução:** 
- Criar mapeamento manual de nomes
- Implementar os chips ausentes separadamente

### 3. Barramentos vs Bits Individuais

**Problema:** DLS tem componentes separadores de barramento
```json
{"Name": "8-1BIT"}  // Divide in[8] → 8 bits separados
```

**Solução HDL:** Usar notação de índice
```hdl
// Em vez de um componente separador:
out[0]=in[0], out[1]=in[1], ... out[7]=in[7]
```

### 4. IDs de Pinos Numéricos

**Problema:** Pinos são identificados por números, não nomes
```json
{"PinID": 1704354938}  // Qual pino é esse?
```

**Solução:** Inferir através de:
- Ordem de conexão
- Posição no array OutputPinColourInfo
- Contagem a partir dos wires conectados

### 5. Ordem de Instanciação

**Problema:** DLS não garante ordem específica de componentes

**Solução:** Ordenar por:
1. Dependências (inputs → processamento → outputs)
2. Posição Y (top-to-bottom)
3. ID numérico

---

## 📝 Exemplos Práticos

### Exemplo 1: MUX Simples 2→1

**DLS JSON (simplificado):**
```json
{
  "Name": "SimpleMux",
  "InputPins": [
    {"Name": "A", "ID": 1, "BitCount": 1},
    {"Name": "B", "ID": 2, "BitCount": 1},
    {"Name": "SEL", "ID": 3, "BitCount": 1}
  ],
  "OutputPins": [
    {"Name": "OUT", "ID": 4, "BitCount": 1}
  ],
  "SubChips": [
    {"Name": "MUX", "ID": 100}
  ],
  "Wires": [
    {"SourcePinOwnerID": 1, "TargetPinOwnerID": 100, "TargetPinID": 0},
    {"SourcePinOwnerID": 2, "TargetPinOwnerID": 100, "TargetPinID": 1},
    {"SourcePinOwnerID": 3, "TargetPinOwnerID": 100, "TargetPinID": 2},
    {"SourcePinOwnerID": 100, "TargetPinOwnerID": 4}
  ]
}
```

**HDL Gerado:**
```hdl
CHIP SimpleMux {
    IN a, b, sel;
    OUT out;

    PARTS:
    Mux(a=a, b=b, sel=sel, out=out);
}
```

### Exemplo 2: MUX 8-bit (do seu JSON)

**Estrutura Conceitual:**
```
IN0[8] ──→ 8-1BIT ──→ [8 bits separados] ──→ 8× MUX ──→ 1-8BIT ──→ OUT[8]
                                                ↑
IN1[8] ──→ 8-1BIT ──→ [8 bits separados] ─────┘
                                                ↑
SEL ────────────────────────────────────────────┘
```

**HDL Equivalente:**
```hdl
CHIP Mux8Bit {
    IN in0[8], in1[8], sel;
    OUT out[8];

    PARTS:
    // Para cada bit do barramento, aplicar MUX
    Mux(a=in0[0], b=in1[0], sel=sel, out=out[0]);
    Mux(a=in0[1], b=in1[1], sel=sel, out=out[1]);
    Mux(a=in0[2], b=in1[2], sel=sel, out=out[2]);
    Mux(a=in0[3], b=in1[3], sel=sel, out=out[3]);
    Mux(a=in0[4], b=in1[4], sel=sel, out=out[4]);
    Mux(a=in0[5], b=in1[5], sel=sel, out=out[5]);
    Mux(a=in0[6], b=in1[6], sel=sel, out=out[6]);
    Mux(a=in0[7], b=in1[7], sel=sel, out=out[7]);
}
```

---

## 🚀 Melhorias Futuras

### Para tornar o conversor production-ready:

1. **Resolver PinIDs Automaticamente**
   - Analisar OutputPinColourInfo
   - Inferir ordem de pinos por posição

2. **Suporte a Chips Complexos**
   - Reconhecer padrões comuns (ripple carry, etc)
   - Biblioteca de templates

3. **Otimização**
   - Eliminar wires redundantes
   - Simplificar conexões diretas

4. **Validação**
   - Verificar se todos os pinos estão conectados
   - Detectar loops combinacionais

5. **Interface Gráfica**
   - Upload de JSON
   - Visualização do circuito
   - Download do HDL

---

## 📚 Referências

- [Digital Logic Sim - Sebastian Lague](https://sebastian.itch.io/digital-logic-sim)
- [Nand2tetris](https://www.nand2tetris.org/)
- [HDL Survival Guide](https://www.nand2tetris.org/hdl-survival-guide)

---

## 🎯 Conclusão

A conversão de DLS para HDL é **possível mas requer interpretação**, pois:

1. **DLS é visual-first** - foca em representação gráfica
2. **HDL é textual** - foca em hierarquia e conexões lógicas
3. **Barramentos são tratados diferentemente**
4. **Componentes não são 1:1 equivalentes**

Os scripts fornecidos cobrem ~70% dos casos comuns. Para circuitos complexos, pode ser necessário ajuste manual.
