# Detector de Fadiga com Visão Computacional

Protótipo de monitoramento de fadiga que usa a webcam do computador para acompanhar a presença de rosto e olhos. Quando os olhos deixam de ser detectados por um período prolongado, o programa exibe um alerta visual e emite sinais sonoros.

Projeto desenvolvido na disciplina de Visão Computacional, do curso de Sistemas de Informação (FATEPI/FAESPI).

## Como funciona

1. A webcam captura os quadros e a imagem é espelhada.
2. Cada quadro passa para escala de cinza e recebe equalização de contraste (CLAHE).
3. Um classificador Haar detecta o rosto. Na metade superior do rosto, outro classificador procura os olhos.
4. Se há rosto, mas nenhum olho detectado por 5 quadros seguidos, o sistema começa a contar o tempo.
5. Após 1,5 segundo sem olhos detectados, o alerta é disparado: borda vermelha, mensagem na tela e som.

## Requisitos

- Windows (o som usa a biblioteca `winsound`)
- Python 3.x
- Webcam

## Instalação e execução

```bash
pip install -r requirements.txt
python detector_fadiga.py
```

Para encerrar, pressione `q` ou feche a janela.

## Limitações

- A detecção de olhos é uma aproximação: o sistema não mede diretamente sonolência ou nível de consciência.
- O desempenho depende de iluminação, posição do rosto, uso de óculos e qualidade da câmera.
- Os classificadores Haar são mais simples que modelos de aprendizado profundo.
- O som funciona apenas no Windows.
- Este é um protótipo acadêmico e não substitui sistemas certificados de segurança veicular.

## Próximos passos

- Detecção de bocejos
- Cálculo de EAR (razão de aspecto dos olhos) com landmarks faciais
- Portabilidade do alerta sonoro para outros sistemas operacionais
- Testes quantitativos em diferentes condições de iluminação

## Demonstração

![Demonstração](link-do-gif-ou-print)

## Autor

Luis Francisco Bezerra Barbosa

- GitHub: [@luisfrancisco2b](https://github.com/luisfrancisco2b)
- E-mail: luisfrancisco2bdev@gmail.com
