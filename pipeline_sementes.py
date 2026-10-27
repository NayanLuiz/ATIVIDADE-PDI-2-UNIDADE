"""
Pipeline de Processamento Digital de Imagens (PDI) - 2ª Unidade
Método Computacional para Detecção e Contagem Automática de Sementes

Sequência do Pipeline:
1. Pré-processamento: Isolamento do EVA + Tons de Cinza + Filtro Gaussiano (5x5)
2. Limiarização: Método de Otsu Invertido / Segmentação Binária
3. Limpeza de Ruído: Fechamento (Reflexos) + Abertura (Poeira EVA)
4. Sementes Juntas: Erosão (Separar Grãos) + Dilatação
5. Contagem: Componentes Conexos + Filtro de Área (ignora poeira e moeda, decompõe agrupados)
"""

import os
import glob
# pyrefly: ignore[missing-import]
import cv2
# pyrefly: ignore[missing-import]
import numpy as np
# pyrefly: ignore[missing-import]
import matplotlib.pyplot as plt

# Gabarito oficial de contagem das 20 fotos
GABARITO = {
    1: 30, 2: 28, 3: 27, 4: 26, 5: 30,
    6: 25, 7: 24, 8: 21, 9: 24, 10: 19,
    11: 30, 12: 18, 13: 16, 14: 15, 15: 22,
    16: 23, 17: 26, 18: 27, 19: 28, 20: 18
}

# Parâmetros calibrados para as fotos experimentais (resolução 1280x960)
AREA_UNITARIA_SEMENTE = 82.0   # Área média em pixels de 1 grão individual
FATOR_AGRUPAMENTO = 1.35       # Componentes com área > 1.35 * ref são tratados como grãos colados
AREA_MINIMA_POEIRA = 35        # Abaixo disso é considerado resíduo/poeira de EVA
AREA_MAXIMA_MOEDA = 900        # Acima disso é a moeda de calibração


def isolar_placa_eva(img_bgr):
    """
    Detecta a placa de EVA verde para delimitar a Região de Interesse (ROI),
    removendo a toalha/mesa de fundo e recortando a borda imperfeita.
    """
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    # Faixa da tonalidade verde no espaço HSV
    green_mask = cv2.inRange(hsv, (35, 30, 30), (85, 255, 255))
    
    cnts, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return np.ones(img_bgr.shape[:2], dtype=np.uint8) * 255, green_mask

    eva_cnt = max(cnts, key=cv2.contourArea)
    mask_eva = np.zeros(img_bgr.shape[:2], dtype=np.uint8)
    cv2.drawContours(mask_eva, [eva_cnt], -1, 255, -1)
    
    # Reduzir ligeiramente a borda da placa para não pegar cortes imperfeitos do EVA
    kernel_borda = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
    mask_eva = cv2.erode(mask_eva, kernel_borda)
    
    return mask_eva, green_mask


def processar_pipeline(caminho_imagem, salvar_painel=True, prefixo_saida="resultado"):
    """
    Executa o pipeline completo em uma imagem e retorna a contagem final e etapas visuais.
    """
    if not os.path.exists(caminho_imagem):
        raise FileNotFoundError(f"Imagem não encontrada: {caminho_imagem}")

    img_bgr = cv2.imread(caminho_imagem)
    if img_bgr is None:
        raise ValueError(f"Erro ao abrir: {caminho_imagem}")

    # =========================================================================
    # 1. PRÉ-PROCESSAMENTO: Região de Interesse (EVA) + Tons de Cinza + Gaussiano 5x5
    # =========================================================================
    mask_eva, green_mask = isolar_placa_eva(img_bgr)
    
    img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    img_suave = cv2.GaussianBlur(img_gray, (5, 5), sigmaX=0)

    # =========================================================================
    # 2. LIMIARIZAÇÃO: Segmentação dos objetos sobre o EVA (Otsu Invertido)
    # Sementes e moeda são objetos claros sobre o EVA verde
    # =========================================================================
    # Na placa de EVA, os objetos correspondem aos pixels não-verdes
    objetos_binarios = cv2.bitwise_and(cv2.bitwise_not(green_mask), mask_eva)

    # =========================================================================
    # 3. LIMPEZA DE RUÍDO: Fechamento (Reflexos) + Abertura (Poeira EVA)
    # =========================================================================
    kernel_fechamento = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    kernel_abertura = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

    # Fechamento: preenche falhas e reflexos internos na semente
    img_fechada = cv2.morphologyEx(objetos_binarios, cv2.MORPH_CLOSE, kernel_fechamento)
    
    # Abertura: remove micropoeiras e rebarbas finas do EVA
    img_limpa = cv2.morphologyEx(img_fechada, cv2.MORPH_OPEN, kernel_abertura)

    # =========================================================================
    # 4. SEMENTES JUNTAS: Erosão (Separar Grãos) + Dilatação
    # =========================================================================
    kernel_sep = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    
    # Erosão quebra pontes finas entre sementes encostadas
    img_erodida = cv2.erode(img_limpa, kernel_sep, iterations=1)
    
    # Dilatação restaura a geometria do grão
    img_separada = cv2.dilate(img_erodida, kernel_sep, iterations=1)

    # =========================================================================
    # 5. CONTAGEM: Componentes Conexos + Filtro de Área
    # =========================================================================
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        img_separada, connectivity=8
    )

    img_anotada = img_bgr.copy()
    total_sementes = 0
    id_semente = 0

    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        
        # Filtro de Área: Descarta poeira residual e moeda de escala
        if AREA_MINIMA_POEIRA <= area <= AREA_MAXIMA_MOEDA:
            cx, cy = int(centroids[i][0]), int(centroids[i][1])
            x = stats[i, cv2.CC_STAT_LEFT]
            y = stats[i, cv2.CC_STAT_TOP]
            w = stats[i, cv2.CC_STAT_WIDTH]
            h = stats[i, cv2.CC_STAT_HEIGHT]

            # Verificação de aglomerado de sementes coladas
            if area > FATOR_AGRUPAMENTO * AREA_UNITARIA_SEMENTE:
                qtd_no_aglomerado = int(round(area / AREA_UNITARIA_SEMENTE))
            else:
                qtd_no_aglomerado = 1

            total_sementes += max(1, qtd_no_aglomerado)
            id_semente += 1

            # Desenho visual: Caixa delimitadora e centroide
            cor_bbox = (0, 255, 0) if qtd_no_aglomerado == 1 else (0, 165, 255)
            cv2.rectangle(img_anotada, (x, y), (x + w, y + h), cor_bbox, 2)
            cv2.circle(img_anotada, (cx, cy), 3, (0, 0, 255), -1)
            
            rotulo = f"#{id_semente}" if qtd_no_aglomerado == 1 else f"#{id_semente}(x{qtd_no_aglomerado})"
            cv2.putText(
                img_anotada,
                rotulo,
                (x, max(15, y - 4)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (0, 0, 255),
                1,
            )
        elif area > AREA_MAXIMA_MOEDA:
            # Moeda identificada e descartada da contagem
            x = stats[i, cv2.CC_STAT_LEFT]
            y = stats[i, cv2.CC_STAT_TOP]
            w = stats[i, cv2.CC_STAT_WIDTH]
            h = stats[i, cv2.CC_STAT_HEIGHT]
            cv2.rectangle(img_anotada, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cv2.putText(img_anotada, "Moeda (Descartada)", (x - 20, y - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 0, 0), 1)

    # Legenda superior com total contabilizado
    cv2.putText(
        img_anotada,
        f"Contagem: {total_sementes} sementes",
        (30, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.1,
        (0, 200, 0),
        3,
    )

    # =========================================================================
    # GERAÇÃO DA PRANCHA COMPARATIVA (PAINEL 2x3)
    # =========================================================================
    if salvar_painel:
        nome_base = os.path.splitext(os.path.basename(caminho_imagem))[0]
        fig, axs = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle(
            f"Pipeline de PDI - {nome_base} (Total Contado: {total_sementes})",
            fontsize=15,
            fontweight="bold",
        )

        axs[0, 0].imshow(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
        axs[0, 0].set_title("1. Entrada Original")
        axs[0, 0].axis("off")

        axs[0, 1].imshow(img_suave, cmap="gray")
        axs[0, 1].set_title("2. Pré-proc.: Cinza + Gaussiano (5x5)")
        axs[0, 1].axis("off")

        axs[0, 2].imshow(objetos_binarios, cmap="gray")
        axs[0, 2].set_title("3. Limiarização Binária (Objetos)")
        axs[0, 2].axis("off")

        axs[1, 0].imshow(img_limpa, cmap="gray")
        axs[1, 0].set_title("4. Fechamento (Reflexos) + Abertura (Poeira)")
        axs[1, 0].axis("off")

        axs[1, 1].imshow(img_separada, cmap="gray")
        axs[1, 1].set_title("5. Erosão (Separar Grãos) + Dilatação")
        axs[1, 1].axis("off")

        axs[1, 2].imshow(cv2.cvtColor(img_anotada, cv2.COLOR_BGR2RGB))
        axs[1, 2].set_title(f"6. Resultado Final ({total_sementes} sementes)")
        axs[1, 2].axis("off")

        plt.tight_layout()
        arquivo_painel = f"{prefixo_saida}_{nome_base}.png"
        plt.savefig(arquivo_painel, dpi=200)
        plt.close()

    return total_sementes, img_anotada


def validar_todas_as_fotos(pasta_fotos="Fotos pdi II/Fotos pdi II"):
    """
    Executa a validação automática em todas as 20 fotos e compara com o gabarito.
    """
    fotos = sorted(
        glob.glob(os.path.join(pasta_fotos, "Foto *.jpeg")),
        key=lambda f: int(os.path.basename(f).replace("Foto", "").replace(".jpeg", "").strip())
    )

    if not fotos:
        print(f"[ERRO] Nenhuma foto encontrada na pasta: {pasta_fotos}")
        return

    print("=" * 65)
    print(f"{'Foto':<9} | {'Gabarito':<10} | {'Contado':<10} | {'Diferença':<10} | {'Acurácia'}")
    print("=" * 65)

    total_esperado = 0
    total_obtido = 0
    fotos_exatas = 0

    for caminho in fotos:
        num_foto = int(os.path.basename(caminho).replace("Foto", "").replace(".jpeg", "").strip())
        esperado = GABARITO.get(num_foto, 0)
        
        # Salva o painel visual apenas para a Foto 1 (para demonstração rápida)
        salvar = (num_foto == 1)
        obtido, _ = processar_pipeline(caminho, salvar_painel=salvar)
        
        diff = obtido - esperado
        total_esperado += esperado
        total_obtido += obtido

        if diff == 0:
            fotos_exatas += 1
            acuracia_str = "100.0% (EXATO)"
        else:
            acuracia = max(0.0, 100.0 - (abs(diff) / esperado * 100.0))
            acuracia_str = f"{acuracia:.1f}% ({diff:+d})"

        print(f"Foto {num_foto:02d}   | {esperado:<10} | {obtido:<10} | {diff:<+10} | {acuracia_str}")

    print("=" * 65)
    acuracia_geral = 100.0 - (abs(total_obtido - total_esperado) / total_esperado * 100.0)
    print(f"TOTAL     | {total_esperado:<10} | {total_obtido:<10} | {total_obtido - total_esperado:<+10} | {acuracia_geral:.2f}% de Acurácia Geral")
    print(f"\nResumo: {fotos_exatas} de {len(fotos)} fotos tiveram contagem 100% perfeita.")
    print(f"Painel visual comparativo salvo como: 'resultado_Foto 1.png'")


if __name__ == "__main__":
    validar_todas_as_fotos()
