import cv2
import time
import winsound

# ==========================================
# CONFIGURAÇÕES E CONSTANTES
# ==========================================
# Carrega os classificadores pré-treinados do OpenCV
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

# Parâmetros de calibração do detector
TEMPO_LIMIAR_FADIGA = 1.5  # Segundos de olhos fechados para disparar o alarme definitivo
MIN_FRAMES_VALIDACAO = 5   # Mínimo de frames sem olhos para confirmar o fechamento (evita ruído)

def iniciar_detector():
    # Inicializa a captura da webcam
    cap = cv2.VideoCapture(0)
    
    # Variáveis de estado e temporização
    inicio_fechado = None
    contador_frames_fechados = 0
    
    # Variáveis para cálculo de FPS (Desempenho)
    tempo_anterior = 0
    
    nome_janela = 'Sistema de Monitoramento de Fadiga v2.0'
    cv2.namedWindow(nome_janela)
    
    print("=== DETECTOR DE FADIGA ATIVADO ===")
    print("Orientações: Mantenha o rosto bem iluminado.")
    print("Para encerrar: Pressione 'q' ou clique no 'X' da janela.")
    
    while cap.isOpened():
        sucesso, frame = cap.read()
        if not sucesso:
            print("Erro: Não foi possível acessar o fluxo da câmera.")
            break
            
        # Otimização: Espelha a imagem para parecer um espelho (mais natural para o usuário)
        frame = cv2.flip(frame, 1)
        h_tela, w_tela, _ = frame.shape
        
        # Processamento digital: Conversão para escala de cinza com CLAHE
        frame_cinza_raw = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        frame_cinza = clahe.apply(frame_cinza_raw)
        
        # Detecção facial
        rostos = face_cascade.detectMultiScale(frame_cinza, scaleFactor=1.2, minNeighbors=5, minSize=(100, 100))
        olhos_detectados = False
        
        for (x, y, w, h) in rostos:
            # Desenha um retângulo suave sobre o rosto detectado
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 100, 0), 2)
            
            # Recorta a Região de Interesse (ROI) do rosto (apenas metade superior)
            roi_h = int(h / 2)
            roi_cinza = frame_cinza[y:y+roi_h, x:x+w]
            roi_cor = frame[y:y+roi_h, x:x+w]
            
            # minSize Dinâmico para os Olhos
            min_size_olhos = (int(w / 10), int(h / 10))
            
            # Detecta os olhos estritamente na metade superior da região do rosto
            olhos = eye_cascade.detectMultiScale(roi_cinza, scaleFactor=1.1, minNeighbors=8, minSize=min_size_olhos)
            
            if len(olhos) > 0:
                olhos_detectados = True
                for (ex, ey, ew, eh) in olhos:
                    # Desenha um círculo no centro de cada olho detectado
                    centro_x = int(ex + ew / 2)
                    centro_y = int(ey + eh / 2)
                    cv2.circle(roi_cor, (centro_x, centro_y), int(ew / 3), (0, 255, 255), 2)

        # LÓGICA DE TOMADA DE DECISÃO DA IA
        if len(rostos) > 0 and not olhos_detectados:
            # Incrementa o contador de estabilização
            contador_frames_fechados += 1
            
            # Só assume que o olho fechou se passar do mínimo de frames de segurança
            if contador_frames_fechados >= MIN_FRAMES_VALIDACAO:
                if inicio_fechado is None:
                    inicio_fechado = time.time()
                
                tempo_decorrido = time.time() - inicio_fechado
                
                # Alerta sonoro de teste (olhos fechados detectados no momento)
                winsound.Beep(2200, 40)
                
                # Condição de Fadiga Crítica
                if tempo_decorrido >= TEMPO_LIMIAR_FADIGA:
                    # Efeito visual: Alerta crítico piscante (Borda vermelha na tela)
                    cv2.rectangle(frame, (0, 0), (w_tela, h_tela), (0, 0, 255), 20)
                    cv2.putText(frame, "ALERTA: MOTORISTA DORMINDO!", (int(w_tela*0.1), int(h_tela*0.5)), 
                                cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 0, 255), 3)
                    
                    # Alarme sonoro grave do sistema
                    winsound.Beep(1200, 150)
                else:
                    # Status intermediário: Piscada longa ou início de sonolência
                    cv2.putText(frame, "Status: Olhos Fechados...", (30, 40), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)
        else:
            # Reseta os temporizadores e contadores se os olhos estiverem abertos
            inicio_fechado = None
            contador_frames_fechados = 0
            
            if len(rostos) > 0:
                cv2.putText(frame, "Status: Alerta (Acordado)", (30, 40), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            else:
                cv2.putText(frame, "Status: Rosto ausente", (30, 40), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (128, 128, 128), 2)

        # CÁLCULO E EXIBIÇÃO DO DESEMPENHO (FPS)
        tempo_atual = time.time()
        fps = 1 / (tempo_atual - tempo_anterior)
        tempo_anterior = tempo_atual
        cv2.putText(frame, f"FPS: {int(fps)}", (w_tela - 130, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        # Renderiza a janela final do software
        cv2.imshow(nome_janela, frame)
        
        # Mecanismos de saída seguros (evitam o travamento do Windows)
        if cv2.waitKey(20) & 0xFF == ord('q'):
            break
        if cv2.getWindowProperty(nome_janela, cv2.WND_PROP_VISIBLE) < 1:
            break
            
    # Liberação limpa de recursos de hardware e interface
    cap.release()
    cv2.destroyAllWindows()
    print("=== SISTEMA ENCERRADO COM SUCESSO ===")

if __name__ == "__main__":
    iniciar_detector()