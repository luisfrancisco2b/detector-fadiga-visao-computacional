"""
Detector de Fadiga - versão refatorada e robusta.

Melhorias em relação à versão anterior:
- Abertura da webcam com fallback entre backends do Windows.
- Carregamento dos classificadores Haar validado (erro claro se faltarem).
- Sons tocados em thread separada, sem travar o vídeo.
- Bipes intermitentes em vez de um bipe a cada frame.
- CLAHE criado uma única vez (antes era recriado a cada frame).
- Proteção contra divisão por zero no cálculo de FPS.
- Tolerância a falhas pontuais de leitura da câmera.
- Encerramento limpo com 'q', ESC ou fechando a janela.
"""

import os
import sys
import time
import threading

import cv2

try:
    import winsound  # Disponível apenas no Windows
    SOM_DISPONIVEL = True
except ImportError:
    winsound = None
    SOM_DISPONIVEL = False


# ==========================================
# CONFIGURAÇÕES
# ==========================================
INDICE_CAMERA = 0
LARGURA_CAPTURA = 1920#640
ALTURA_CAPTURA = 1080#480

TEMPO_LIMIAR_FADIGA = 1.5    # Segundos com olhos fechados para alerta crítico
MIN_FRAMES_VALIDACAO = 5     # Frames seguidos sem olhos para confirmar fechamento
INTERVALO_BIP = 0.8          # Segundos entre bipes de alerta intermediário
MAX_FALHAS_LEITURA = 30      # Falhas seguidas de leitura toleradas antes de encerrar

NOME_JANELA = "Sistema de Monitoramento de Fadiga v2.1"


# ==========================================
# UTILITÁRIOS
# ==========================================
def carregar_classificador(nome_arquivo):
    """Carrega um classificador Haar e garante que ele foi lido corretamente."""
    try:
        base = cv2.data.haarcascades
    except AttributeError:
        # Algumas instalações não expõem cv2.data; usa a pasta do próprio pacote
        base = os.path.join(os.path.dirname(cv2.__file__), "data")

    caminho = os.path.join(base, nome_arquivo)
    classificador = cv2.CascadeClassifier(caminho)

    if classificador.empty():
        raise RuntimeError(
            f"Não foi possível carregar o classificador: {caminho}\n"
            "Verifique se a instalação do opencv-python está correta."
        )
    return classificador


def abrir_camera(indice):
    """Tenta abrir a webcam com diferentes backends. Retorna None se falhar."""
    if sys.platform.startswith("win"):
        backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
    else:
        backends = [cv2.CAP_ANY]

    for backend in backends:
        cap = cv2.VideoCapture(indice, backend)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, LARGURA_CAPTURA)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, ALTURA_CAPTURA)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduz atraso entre câmera e tela
            ok, _ = cap.read()
            if ok:
                return cap
        cap.release()
    return None


class Alarme:
    """Toca sons em thread separada, para não travar o processamento do vídeo."""

    def __init__(self):
        self._ocupado = False
        self._lock = threading.Lock()

    def tocar(self, frequencia, duracao_ms):
        if not SOM_DISPONIVEL:
            return

        with self._lock:
            if self._ocupado:
                return  # Já há um som tocando; ignora este para não acumular
            self._ocupado = True

        def _executar():
            try:
                winsound.Beep(frequencia, duracao_ms)
            except RuntimeError:
                pass  # Falha de hardware de áudio não deve derrubar o programa
            finally:
                with self._lock:
                    self._ocupado = False

        threading.Thread(target=_executar, daemon=True).start()


def desenhar_texto(img, texto, posicao, cor, escala=0.8, espessura=2, fonte=cv2.FONT_HERSHEY_SIMPLEX):
    cv2.putText(img, texto, posicao, fonte, escala, cor, espessura, cv2.LINE_AA)


# ==========================================
# DETECÇÃO
# ==========================================
def detectar_olhos_no_rosto(roi_cinza, eye_cascade, w, h):
    """Detecta olhos na metade superior do rosto."""
    min_olho = (max(int(w / 10), 1), max(int(h / 10), 1))
    return eye_cascade.detectMultiScale(
        roi_cinza, scaleFactor=1.1, minNeighbors=8, minSize=min_olho
    )


# ==========================================
# LOOP PRINCIPAL
# ==========================================
def iniciar_detector():
    face_cascade = carregar_classificador("haarcascade_frontalface_default.xml")
    eye_cascade = carregar_classificador("haarcascade_eye.xml")
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    alarme = Alarme()

    cap = abrir_camera(INDICE_CAMERA)
    if cap is None:
        raise RuntimeError(
            f"Não foi possível abrir a webcam (índice {INDICE_CAMERA}).\n"
            "Verifique se a câmera está conectada, se nenhum outro programa a está usando "
            "e se o Windows permite acesso à câmera (Configurações > Privacidade > Câmera)."
        )

    cv2.namedWindow(NOME_JANELA, cv2.WINDOW_AUTOSIZE)

    print("=== DETECTOR DE FADIGA ATIVADO ===")
    print("Dica: mantenha o rosto bem iluminado e de frente para a câmera.")
    print("Para encerrar: pressione 'q' ou ESC, ou feche a janela.")

    # Estado
    inicio_fechado = None
    frames_sem_olhos = 0
    ultimo_bip = 0.0
    falhas_leitura = 0
    tempo_anterior = time.time()
    fps_suavizado = 0.0

    try:
        while True:
            sucesso, frame = cap.read()
            if not sucesso:
                falhas_leitura += 1
                if falhas_leitura >= MAX_FALHAS_LEITURA:
                    print("Erro: a câmera parou de enviar imagens.")
                    break
                time.sleep(0.05)
                continue
            falhas_leitura = 0

            # Espelha a imagem para ficar mais natural
            frame = cv2.flip(frame, 1)
            altura_tela, largura_tela = frame.shape[:2]

            # Pré-processamento
            cinza = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            cinza = clahe.apply(cinza)

            # Detecção de rosto
            rostos = face_cascade.detectMultiScale(
                cinza, scaleFactor=1.2, minNeighbors=5, minSize=(100, 100)
            )

            olhos_detectados = False
            for (x, y, w, h) in rostos:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 100, 0), 2)

                roi_h = max(int(h / 2), 1)  # Metade superior do rosto
                roi_cinza = cinza[y:y + roi_h, x:x + w]
                roi_cor = frame[y:y + roi_h, x:x + w]

                olhos = detectar_olhos_no_rosto(roi_cinza, eye_cascade, w, h)
                if len(olhos) > 0:
                    olhos_detectados = True
                    for (ex, ey, ew, eh) in olhos:
                        centro = (int(ex + ew / 2), int(ey + eh / 2))
                        cv2.circle(roi_cor, centro, max(int(ew / 3), 1), (0, 255, 255), 2)

            # Lógica de decisão
            agora = time.time()

            if len(rostos) > 0 and not olhos_detectados:
                frames_sem_olhos += 1

                if frames_sem_olhos >= MIN_FRAMES_VALIDACAO:
                    if inicio_fechado is None:
                        inicio_fechado = agora

                    tempo_decorrido = agora - inicio_fechado

                    if tempo_decorrido >= TEMPO_LIMIAR_FADIGA:
                        # Alerta crítico: borda vermelha piscante + mensagem + som grave
                        if int(agora * 4) % 2 == 0:
                            cv2.rectangle(frame, (0, 0), (largura_tela - 1, altura_tela - 1),
                                          (0, 0, 255), 20)
                        desenhar_texto(frame, "ALERTA: MOTORISTA DORMINDO!",
                                       (int(largura_tela * 0.1), int(altura_tela * 0.5)),
                                       (0, 0, 255), escala=1.0, espessura=3,
                                       fonte=cv2.FONT_HERSHEY_DUPLEX)
                        alarme.tocar(1200, 300)
                    else:
                        # Estado intermediário: bipes espaçados, não contínuos
                        desenhar_texto(frame, "Status: Olhos Fechados...", (30, 40), (0, 165, 255))
                        if agora - ultimo_bip >= INTERVALO_BIP:
                            alarme.tocar(2200, 60)
                            ultimo_bip = agora
            else:
                # Olhos abertos ou rosto ausente: reseta o estado
                inicio_fechado = None
                frames_sem_olhos = 0

                if len(rostos) > 0:
                    desenhar_texto(frame, "Status: Alerta (Acordado)", (30, 40), (0, 255, 0))
                else:
                    desenhar_texto(frame, "Status: Rosto ausente", (30, 40), (128, 128, 128))

            # FPS suavizado, protegido contra divisão por zero
            dt = max(agora - tempo_anterior, 1e-6)
            fps_suavizado = 0.9 * fps_suavizado + 0.1 * (1.0 / dt) if fps_suavizado else 1.0 / dt
            tempo_anterior = agora
            desenhar_texto(frame, f"FPS: {int(fps_suavizado)}",
                           (largura_tela - 130, 40), (255, 255, 255), escala=0.6, espessura=1)

            cv2.imshow(NOME_JANELA, frame)

            tecla = cv2.waitKey(1) & 0xFF
            if tecla in (ord("q"), 27):  # 'q' ou ESC
                break

            try:
                if cv2.getWindowProperty(NOME_JANELA, cv2.WND_PROP_VISIBLE) < 1:
                    break
            except cv2.error:
                break  # Janela foi fechada

    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("=== SISTEMA ENCERRADO ===")


if __name__ == "__main__":
    try:
        iniciar_detector()
    except Exception as erro:
        print(f"\nERRO: {erro}")
        if sys.platform.startswith("win"):
            input("\nPressione Enter para sair...")
        sys.exit(1)