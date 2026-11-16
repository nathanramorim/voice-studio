# Aviso sobre licenças de terceiros

O `LICENSE` (MIT) cobre apenas o código deste repositório.

O motor padrão usa o modelo **XTTS-v2** (Coqui), sob a licença **Coqui Public Model License (CPML)**, que permite **somente uso não comercial**: https://coqui.ai/cpml. Os pesos do modelo **não** são distribuídos aqui; o motor os baixa na primeira geração, e o usuário aceita a CPML explicitamente (`--accept-cpml` ou `VOICE_STUDIO_ACCEPT_CPML=1`).

Para uso comercial, troque o motor por um de licença permissiva, implementando a interface `synth.Synth`.
