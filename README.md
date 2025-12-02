# 🔄 Conversor DLS → Nand2tetris HDL

Ferramentas Python para converter circuitos do **Digital Logic Sim** (Sebastian Lague) para o formato **HDL do Nand2tetris**.

---

## 📦 Arquivos Incluídos

```
├── dls_to_hdl_converter.py    # Conversor básico com análise
├── advanced_converter.py       # Conversor avançado com mapeamento completo
├── exemplo_uso.py              # Exemplos práticos de uso
└── GUIA_CONVERSAO_DLS_HDL.md  # Documentação completa
```

---

## 🚀 Início Rápido

### 1. Exportar seu circuito do Digital Logic Sim

No Digital Logic Sim:
1. Abra seu circuito
2. Vá em **File → Export → JSON** (ou salve o arquivo .txt)
3. Salve como `meu_circuito.json`

### 2. Converter para HDL

**Opção A: Conversor Básico** (recomendado para começar)
```bash
python dls_to_hdl_converter.py meu_circuito.json
```

**Opção B: Conversor Avançado** (para circuitos complexos)
```bash
python advanced_converter.py meu_circuito.json
```

### 3. Resultado

O script irá gerar:
- ✅ Análise detalhada no terminal
- ✅ Arquivo `.hdl` pronto para usar no Nand2tetris

---

## 📖 Uso Detalhado

### Conversor Básico

```bash
python dls_to_hdl_converter.py circuito.json
```

**O que ele faz:**
- ✅ Analisa a estrutura do circuito
- ✅ Conta inputs, outputs e subcomponentes
- ✅ Gera a assinatura HDL (IN/OUT)
- ⚠️ Gera esqueleto do PARTS (requer ajuste manual)

**Ideal para:**
- Entender a estrutura do circuito
- Circuitos simples
- Primeiro contato com a conversão

**Exemplo de saída:**
```
=== Análise do Chip: MUX-16 ===

INPUT PINS:
  - IN: 8 bit(s) [ID: 1952408028]
  - IN: 8 bit(s) [ID: 1130506631]
  - SEL: 1 bit(s) [ID: 1871591605]

OUTPUT PINS:
  - OUT: 8 bit(s) [ID: 597175907]

SUBCHIPS (4):
  - 8-1BIT: 2 instance(s)
  - MUX: 1 instance(s)
  - 1-8BIT: 1 instance(s)

CONNECTIONS (2):
  - Input → SubChip: 2
  - SubChip → SubChip: 0
  - SubChip → Output: 0
```

### Conversor Avançado

```bash
python advanced_converter.py circuito.json
```

**O que ele faz:**
- ✅ Rastreia todas as conexões entre componentes
- ✅ Mapeia wires internos automaticamente
- ✅ Nomeia instâncias múltiplas (Mux1, Mux2, ...)
- ✅ Gera HDL com conexões completas

**Ideal para:**
- Circuitos complexos
- Conversão mais precisa
- Menos trabalho manual

**Exemplo de saída:**
```hdl
CHIP MUX16 {
    IN in0[8], in1[8], sel;
    OUT out[8];

    PARTS:
    Splitter8(in=in1, out[0]=bit0_1, out[1]=bit1_1, ...);
    Splitter8(in=in0, out[0]=bit0_0, out[1]=bit1_0, ...);
    Mux(a=bit0_0, b=bit0_1, sel=sel, out=w0);
    Mux(a=bit1_0, b=bit1_1, sel=sel, out=w1);
    ...
    Bus8(in[0]=w0, in[1]=w1, ..., out=out);
}
```

---

## 🎯 Exemplos Práticos

### Exemplo 1: Converter um MUX simples

```python
from advanced_converter import AdvancedConverter
import json

# Carregar JSON
with open('mux.json', 'r') as f:
    data = json.load(f)

# Converter
converter = AdvancedConverter(data)
hdl = converter.convert()

# Salvar
with open('Mux.hdl', 'w') as f:
    f.write(hdl)

print("✓ Conversão concluída!")
```

### Exemplo 2: Análise antes de converter

```python
converter = AdvancedConverter(data)

# Ver relatório detalhado
report = converter.generate_detailed_report()
print(report)

# Depois converter
hdl = converter.convert()
```

### Exemplo 3: Processar múltiplos arquivos

```python
import os
import glob

for json_file in glob.glob("circuits/*.json"):
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    converter = AdvancedConverter(data)
    hdl = converter.convert()
    
    output_name = f"{converter.chip_name}.hdl"
    with open(f"hdl_output/{output_name}", 'w') as f:
        f.write(hdl)
    
    print(f"✓ {json_file} → {output_name}")
```

---

## ⚙️ Opções de Linha de Comando

### Conversor Básico

```bash
# Uso básico
python dls_to_hdl_converter.py arquivo.json

# Com redirecionamento de saída
python dls_to_hdl_converter.py arquivo.json > analise.txt
```

### Conversor Avançado

```bash
# Uso básico
python advanced_converter.py arquivo.json

# Salvar apenas o HDL
python advanced_converter.py arquivo.json | tail -n +20 > Chip.hdl
```

---

## 🔧 Personalização

### Adicionar novos tipos de chip

Edite o método `_normalize_chip_name()`:

```python
def _normalize_chip_name(self, name: str) -> str:
    name_map = {
        "8-1BIT": "Splitter8",
        "1-8BIT": "Bus8",
        "MUX": "Mux",
        # Adicione seus mapeamentos aqui:
        "MEU-CHIP": "MeuChipHDL",
    }
    return name_map.get(name, name)
```

### Alterar formato de saída

Modifique o método `convert()` em qualquer conversor:

```python
def convert(self) -> str:
    # Seu formato customizado aqui
    hdl = []
    hdl.append("// Meu formato customizado")
    # ...
    return "\n".join(hdl)
```

---

## 🐛 Problemas Comuns

### 1. "No such file or directory"

**Problema:** Arquivo JSON não encontrado

**Solução:**
```bash
# Verifique o caminho
ls -la meu_circuito.json

# Use caminho absoluto
python dls_to_hdl_converter.py /caminho/completo/circuito.json
```

### 2. "Invalid JSON"

**Problema:** Arquivo JSON corrompido ou incompleto

**Solução:**
```bash
# Valide o JSON online: https://jsonlint.com/
# Ou use Python:
python -m json.tool circuito.json
```

### 3. "Unknown chip type"

**Problema:** DLS usa um chip que não está mapeado

**Solução:**
- Adicione o mapeamento em `_normalize_chip_name()`
- Ou implemente o chip manualmente no HDL

### 4. Conexões incompletas

**Problema:** Alguns wires não são mapeados corretamente

**Solução:**
- Use o conversor avançado
- Revise manualmente as conexões no HDL gerado
- Consulte o relatório detalhado

---

## 📊 Limitações Conhecidas

### Não Suportado (ainda)
- ❌ Chips com feedback loops
- ❌ Componentes tri-state
- ❌ Memória sequencial complexa
- ❌ Subcircuitos aninhados profundamente

### Suporte Parcial
- ⚠️ Barramentos de largura variável
- ⚠️ Componentes com múltiplos outputs
- ⚠️ Conexões ponto-a-ponto complexas

### Totalmente Suportado
- ✅ Lógica combinacional
- ✅ Multiplexadores
- ✅ Portas lógicas básicas
- ✅ Barramentos de 1-16 bits

---

## 🤝 Contribuindo

Melhorias são bem-vindas! Áreas que precisam de trabalho:

1. **Mapeamento de PinIDs**: Inferir nomes corretos de pinos
2. **Otimização**: Eliminar wires redundantes
3. **Validação**: Verificar circuitos antes de converter
4. **Templates**: Reconhecer padrões comuns (ALU, etc)
5. **GUI**: Interface gráfica para conversão

---

## 📚 Recursos

- [Digital Logic Sim](https://sebastian.itch.io/digital-logic-sim) - Simulador original
- [Nand2tetris](https://www.nand2tetris.org/) - Curso e plataforma
- [HDL Survival Guide](https://www.nand2tetris.org/hdl-survival-guide) - Referência HDL

---

## 📄 Licença

Estes scripts são fornecidos "como estão" para uso educacional.

---

## 🎓 Dicas de Uso

### Para Iniciantes

1. Comece com circuitos **muito simples** (AND, OR, NOT)
2. Use o conversor básico primeiro para entender a estrutura
3. Compare o HDL gerado com exemplos do Nand2tetris
4. Ajuste manualmente quando necessário

### Para Usuários Avançados

1. Use o conversor avançado diretamente
2. Crie scripts batch para processar muitos arquivos
3. Customize os mapeamentos de chips
4. Integre com seu workflow de build

### Para Desenvolvimento

1. Fork os scripts e adicione funcionalidades
2. Teste com seus próprios circuitos
3. Compartilhe melhorias com a comunidade

---

## 📞 Suporte

Para dúvidas ou problemas:

1. Leia o `GUIA_CONVERSAO_DLS_HDL.md` completo
2. Veja os exemplos em `exemplo_uso.py`
3. Teste com circuitos mais simples primeiro
4. Revise manualmente o HDL gerado

---

**Boa sorte com suas conversões! 🚀**
