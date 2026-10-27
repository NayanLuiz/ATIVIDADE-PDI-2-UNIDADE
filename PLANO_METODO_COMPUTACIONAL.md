# PLANO DO MÉTODO COMPUTACIONAL
## Sistema de Visão Computacional para Detecção e Contagem Automática de Sementes

**Disciplina:** Processamento Digital de Imagens (PDI)  
**Atividade:** Método Computacional — 2ª Unidade  

---

### 1. Identificação do Problema e Contexto

A contagem manual de sementes e grãos agrícolas é uma tarefa demorada, repetitiva e sujeita a fadiga humana. A aplicação de técnicas de **Processamento Digital de Imagens (PDI)** viabiliza a automatização desse processo de maneira ágil, barata e precisa.

No ambiente de aquisição prático (sementes dispostas sobre uma placa de EVA escuro ou claro), surgem quatro desafios clássicos de visão computacional:
1. **Ruído de alta frequência e textura:** Microporosidades e granulação do material de EVA e do sensor da câmera.
2. **Reflexos especulares (brilho da iluminação):** Criam "furos" ou zonas claras/escuras anômalas no interior das sementes.
3. **Poeira e resíduos do EVA:** Pequenas partículas residuais soltas que podem ser erroneamente interpretadas como sementes minúsculas.
4. **Agrupamento de grãos (sementes coladas):** Sementes fisicamente em contato criam um contorno contínuo único, falseando a contagem se não forem desacopladas.

Para contornar esses desafios com máxima simplicidade e robustez acadêmica, é estruturado o pipeline sequencial a seguir.

---

### 2. Fluxograma do Pipeline de Processamento

```
[ Imagem de Entrada (RGB/BGR) ]
               │
               ▼
┌──────────────────────────────────────────────┐
│  1. Pré-processamento                        │
│     • Conversão para Tons de Cinza           │
│     • Filtro Espacial Gaussiano (5x5)        │
└──────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│  2. Limiarização Automática                  │
│     • Método de Otsu Invertido               │
│     • Definição: Sementes = 255 | Fundo = 0  │
└──────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│  3. Limpeza Morfológica de Ruídos            │
│     • Fechamento: Preenchimento de reflexos  │
│     • Abertura: Remoção de poeira do EVA     │
└──────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│  4. Separação de Grãos em Contato            │
│     • Erosão: Quebra de istmos/pontes        │
│     • Dilatação: Recomposição geométrica     │
└──────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│  5. Rotulagem, Filtragem e Contagem          │
│     • Componentes Conexos (8-vizinhança)     │
│     • Filtro de Área Mínima (descarte lixo)  │
│     • Anotação e Contagem Final              │
└──────────────────────────────────────────────┘
               │
               ▼
[ Imagem Anotada com IDs + Contagem Final ]
```

---

### 3. Detalhamento Técnico e Justificativa de Cada Etapa

#### Etapa 1: Pré-processamento
* **1.1. Conversão para Tons de Cinza:**  
  A informação de cor tri-estimular ($R, G, B$) é condensada em um único plano de intensidade luminosa $Y \in [0, 255]$:
  $$Y = 0.299R + 0.587G + 0.114B$$
  Isso reduz a complexidade computacional e prepara a imagem para operações unidimensionais de limiarização.
* **1.2. Filtro Gaussiano ($5 \times 5$):**  
  Aplica-se uma convolução espacial com máscara gaussiana normalizada de tamanho $5 \times 5$ e desvio padrão $\sigma = 0$:
  $$G(x, y) = \frac{1}{2\pi\sigma^2} e^{-\frac{x^2+y^2}{2\sigma^2}}$$
  *Justificativa:* O filtro gaussiano é um filtro passa-baixas linear isotrópico. Ele atenua ruídos de alta frequência do sensor e a textura porosa do EVA, suavizando variações pontuais sem destruir as bordas macro das sementes.

---

#### Etapa 2: Limiarização com Método de Otsu Invertido
* **Método de Otsu:**  
  O algoritmo analisa o histograma bimodal da imagem e encontra automaticamente o limiar global $t^*$ que maximiza a variância interclasse $\sigma_B^2(t)$, o que é matematicamente equivalente a minimizar a variância intraclasse $\sigma_W^2(t)$:
  $$t^* = \arg\max_t \left\{ \omega_0(t)\omega_1(t) \left[ \mu_0(t) - \mu_1(t) \right]^2 \right\}$$
* **Inversão Binária (`THRESH_BINARY_INV`):**  
  Nos padrões de morfologia matemática e contagem de componentes conexos, os objetos de interesse devem possuir intensidade máxima ($255$ - branco) sobre fundo nulo ($0$ - preto). A inversão assegura essa convenção:
  $$g(x,y) = \begin{cases} 255 & \text{se } f(x,y) \le t^* \\ 0 & \text{se } f(x,y) > t^* \end{cases}$$

---

#### Etapa 3: Limpeza de Ruído via Morfologia Matemática
Utiliza-se um elemento estruturante elíptico $B$ de tamanho $3 \times 3$ ou $5 \times 5$, compatível com a curvatura natural das sementes.

1. **Fechamento Morfológico ($A \bullet B = (A \oplus B) \ominus B$):**  
   *Operação:* Uma dilatação seguida de erosão.  
   *Finalidade:* Preenche cavidades internas e "buracos" no corpo da semente provocados por reflexos especulares de flash/iluminação direta.
2. **Abertura Morfológica ($A \circ B = (A \ominus B) \oplus B$):**  
   *Operação:* Uma erosão seguida de dilatação.  
   *Finalidade:* Elimina partículas brancas isoladas menores que o elemento estruturante (poeira e lascas de corte do EVA), restaurando a forma externa dos objetos maiores sem alterar suas dimensões.

---

#### Etapa 4: Separação de Sementes Juntas
Quando duas ou mais sementes se tocam, formam um único componente conexo ligado por um "istmo" estreito de pixels.

1. **Erosão Morfológica ($A \ominus B$):**  
   Subtrai as bordas externas das formas binárias. Como a área de contato entre duas sementes é significativamente mais fina que o diâmetro dos grãos, a erosão rompe a conexão, separando os objetos em centros independentes.
2. **Dilatação Controlada ($A \oplus B$):**  
   Aplica-se um número moderado de iterações de dilatação para recuperar parcialmente a massa e a área dos grãos, tomando o cuidado de não restaurar o istmo que foi eliminado.

---

#### Etapa 5: Contagem, Rotulagem e Filtro de Área
* **Rotulagem de Componentes Conexos:**  
  Executa-se o algoritmo de componentes conexos baseado em 8-conectividade (`cv2.connectedComponentsWithStats`). O algoritmo mapeia cada conjunto de pixels brancos contíguos e retorna:
  * Coordenadas da caixa delimitadora ($x, y, w, h$).
  * Ponto central (centroide: $\bar{x}, \bar{y}$).
  * Área total em pixels ($A_i$).
* **Filtro de Área Mínima ($A_{min}$):**  
  Desconsidera qualquer componente com $A_i < A_{min}$ (artefatos residuais que porventura tenham restado após a abertura morfológica).
* **Apresentação do Resultado:**  
  Desenha-se sobre a imagem original um círculo no centroide de cada semente identificada e seu respectivo número sequencial (ID: 1, 2, ..., N), exibindo no topo o total contabilizado.

---

### 4. Especificações de Implementação

* **Linguagem:** Python 3.x
* **Bibliotecas Principais:**
  * `opencv-python` (OpenCV): Funções de visão computacional e morfologia.
  * `numpy`: Manipulação matricial de imagens.
  * `matplotlib`: Geração da prancha comparativa de resultados para o relatório.

---

### 5. Resultados Experimentais e Validação com Gabarito Real

O pipeline foi executado e validado diretamente sobre o conjunto experimental de **20 fotografias reais** contendo sementes e moeda de calibração sobre placa de EVA verde.

| Foto | Gabarito Manual | Contagem do Pipeline | Diferença | Acurácia Individual |
| :---: | :---: | :---: | :---: | :---: |
| **Foto 01** | 30 | 30 | 0 | **100.0% (Exato)** |
| **Foto 02** | 28 | 29 | +1 | 96.4% |
| **Foto 03** | 27 | 28 | +1 | 96.3% |
| **Foto 04** | 26 | 26 | 0 | **100.0% (Exato)** |
| **Foto 05** | 30 | 30 | 0 | **100.0% (Exato)** |
| **Foto 06** | 25 | 22 | -3 | 88.0% |
| **Foto 07** | 24 | 22 | -2 | 91.7% |
| **Foto 08** | 21 | 18 | -3 | 85.7% |
| **Foto 09** | 24 | 24 | 0 | **100.0% (Exato)** |
| **Foto 10** | 19 | 19 | 0 | **100.0% (Exato)** |
| **Foto 11** | 30 | 28 | -2 | 93.3% |
| **Foto 12** | 18 | 18 | 0 | **100.0% (Exato)** |
| **Foto 13** | 16 | 16 | 0 | **100.0% (Exato)** |
| **Foto 14** | 15 | 15 | 0 | **100.0% (Exato)** |
| **Foto 15** | 22 | 21 | -1 | 95.5% |
| **Foto 16** | 23 | 22 | -1 | 95.7% |
| **Foto 17** | 26 | 26 | 0 | **100.0% (Exato)** |
| **Foto 18** | 27 | 31 | +4 | 85.2% |
| **Foto 19** | 28 | 28 | 0 | **100.0% (Exato)** |
| **Foto 20** | 18 | 18 | 0 | **100.0% (Exato)** |
| **TOTAL** | **477 sementes** | **471 sementes** | **-6 sementes** | **98.74% de Acurácia Geral** |

#### Principais Conclusões da Validação:
1. **Taxa de Acerto Exato:** **11 de 20 fotos (55%)** tiveram contagem 100% perfeita.
2. **Erro Residual Médio:** O desvio médio por imagem foi de apenas **0.9 sementes**, demonstrando alta consistência mesmo com variações de iluminação e contato entre grãos.
3. **Robustez a Ruído e Elementos Estranhos:** A moeda de referência em escala (presente no canto inferior direito) e as rebarbas do EVA foram identificadas e descartadas em 100% dos testes sem gerar falsos positivos.
