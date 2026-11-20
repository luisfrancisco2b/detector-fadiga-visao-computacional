# 👁️ Detector de Fadiga com Visão Computacional

Protótipo de monitoramento de fadiga que usa a webcam do computador para acompanhar rosto e olhos em tempo real. Quando os olhos deixam de ser detectados por um período prolongado, o sistema exibe um alerta visual e emite sinais sonoros.

Projeto desenvolvido na disciplina de Visão Computacional, do curso de Sistemas de Informação (FATEPI/FAESPI).

## ✨ Funcionalidades

- ✅ Captura de vídeo em tempo real pela webcam
- ✅ Detecção de rosto com classificador Haar
- ✅ Detecção de olhos na metade superior do rosto
- ✅ Melhoria de contraste com CLAHE para lidar com iluminação irregular
- ✅ Alerta só após 5 quadros seguidos sem olhos, para evitar falsos alarmes
- ✅ Alerta crítico após 1,5 segundo sem olhos detectados (borda vermelha, mensagem na tela e som)
- ✅ Exibição do estado atual e do FPS na tela
- ✅ Processamento local, sem gravar nem transmitir imagens

## 🛠️ Tecnologias

- Python
- OpenCV
- Classificadores Haar pré-treinados
- winsound (sons no Windows)

## 🚀 Como executar

**Requisitos:** Windows, Python 3.x e webcam.

1. Clone o repositório
   ```bash
   git clone https://github.com/luisfrancisco2b/detector-fadiga-visao-computacional.git
   ```
2. Entre na pasta do projeto
   ```bash
   cd detector-fadiga-visao-computacional
   ```
3. Instale as dependências
   ```bash
   pip install -r requirements.txt
   ```
4. Execute o programa
   ```bash
   python detector_fadiga.py
   ```

Para encerrar, pressione `q` ou feche a janela.

## ⚠️ Limitações

- A detecção de olhos é uma aproximação: o sistema não mede diretamente sonolência nem nível de consciência.
- O desempenho depende de iluminação, posição do rosto, uso de óculos e qualidade da câmera.
- Os classificadores Haar são mais simples que modelos de aprendizado profundo.
- O som funciona apenas no Windows.
- Este é um protótipo acadêmico e não substitui sistemas certificados de segurança veicular.

## 🔮 Próximos passos

- [ ] Detecção de bocejos
- [ ] Cálculo de EAR (razão de aspecto dos olhos) com landmarks faciais
- [ ] Alerta sonoro compatível com outros sistemas operacionais
- [ ] Testes quantitativos em diferentes condições de iluminação
- [ ] Borda de alerta piscante, como indicado no código

---

## 👨‍💻 Autor

Luis Francisco Bezerra Barbosa

- GitHub: [@luisfrancisco2b](https://github.com/luisfrancisco2b)
- E-mail: luisfrancisco2bdev@gmail.com
