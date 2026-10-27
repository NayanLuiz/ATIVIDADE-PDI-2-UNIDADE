# Atividade PDI - 2ª Unidade: Detecção e Contagem Automática de Sementes

Implementação do método computacional em Processamento Digital de Imagens (PDI) para detecção, filtragem e contagem de sementes sobre fundo de EVA verde.

---

## 📌 Documentação Oficial e Relatório
O relatório detalhado com a fundamentação matemática, equações, diagrama do pipeline e análise de resultados está disponível em:
👉 **[PLANO_METODO_COMPUTACIONAL.md](PLANO_METODO_COMPUTACIONAL.md)**

---

## 🔬 Pipeline de 5 Etapas

1. **Pré-processamento:** Delimitação da placa de EVA + Conversão para Tons de Cinza + Filtro Gaussiano ($5 \times 5$).
2. **Limiarização:** Segmentação binária dos objetos sobre o EVA (Otsu Invertido).
3. **Limpeza de Ruído:** Fechamento Morfológico (preenchimento de reflexos na semente) + Abertura Morfológica (eliminação de poeira do EVA).
4. **Separação de Sementes Juntas:** Erosão Morfológica (rompe conexões estreitas) + Dilatação.
5. **Contagem e Métricas:** Rotulagem por Componentes Conexos (8-vizinhança) + Filtro de Área (descarta poeira $< 35\text{ px}$, descarta moeda $> 900\text{ px}$ e decompõe aglomerados).

---

## 📊 Resultados da Validação Experimental (20 Fotos)

Validado contra o gabarito manual anotado no caderno:

| Métrica | Resultado |
| :--- | :--- |
| **Total de Sementes no Gabarito** | 477 sementes |
| **Total Contado pelo Pipeline** | 471 sementes |
| **Acurácia Geral do Sistema** | **98.74%** |
| **Fotos com Contagem 100% Exata** | **11 de 20 (55%)** |
| **Erro Médio por Foto** | **0.9 sementes** |

---

## 🚀 Como Executar

### Opção 1: Via `uv` (Sem precisar instalar Python manualmente)
```bash
uv run --with opencv-python --with numpy --with matplotlib python pipeline_sementes.py
```

### Opção 2: Via Python padrão
```bash
pip install -r requirements.txt
python pipeline_sementes.py
```

O script processará automaticamente as 20 fotos na pasta `Fotos pdi II/Fotos pdi II`, imprimirá a tabela comparativa no terminal e salvará a prancha com as 6 etapas visuais em `resultado_Foto 1.png`.
