# Fluxos — voice-studio

## Narração a partir de texto digitado
```
amostra (áudio do usuário) + texto + idioma/perfil
  ↓ consent (voz própria, licença)
  ↓ vocabulário de pronúncia (só no texto da voz)
  ↓ N variações no motor local
  ↓ guarda de duração -> melhor variação -> corte de silêncio nas pontas
  ↓ fala em WAV + relatório (ok/suspeita)
```

## Dublagem para outro idioma
```
áudio ou vídeo + idioma de destino
  ↓ transcrição local (whisper.cpp) -> segmentos com tempo
  ↓ agente traduz o texto (só texto)
  ↓ fala por segmento (fluxo de narração)
  ↓ encaixe no tempo (atempo até 1,25x) -> mixagem
  ↓ vídeo/áudio dublado + relatório (overflow)
```

## Ouvir e aprovar
```
fala gerada -> usuário ouve -> ajusta grafia falada/perfil -> regera
```
A transcrição não prova a pronúncia (`VOZ-07`).
