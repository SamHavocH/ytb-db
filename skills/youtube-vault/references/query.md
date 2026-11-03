# Fluxo: query (responder com base no cofre)

1. **Comece pela wiki.** Leia `index.md` e busque na `wiki/` (rg/grep por termos,
   sinônimos e variações em pt/en; `tags:` e `conceitos:` no frontmatter).
2. **Desça à fonte quando precisar de precisão.** Para citações literais, números ou
   detalhes, abra a transcrição em `raw/transcripts/<video_id>.md` e localize o trecho.
   O timestamp do parágrafo já é um link.
3. **Se houver um servidor MCP de busca** configurado sobre o cofre (ex.: `qmd`), prefira-o
   para perguntas semânticas amplas, e confirme lendo as notas retornadas.
4. **Responda citando:**
   - nota: `[[Título do vídeo]]` ou `[[Conceito]]`
   - trecho: `[12:34](https://youtu.be/ID?t=754)`
   - diferencie o que o vídeo afirma do que é sua síntese ou inferência.
5. **Lacunas:** se o cofre não cobre a pergunta (ou só parcialmente), diga
   claramente. Só então complemente com conhecimento geral, sinalizado como tal.
6. **Opcional — compor conhecimento:** se a resposta gerou uma síntese útil (comparação
   entre vídeos, linha do tempo), ofereça salvá-la como nota em `wiki/conceitos/` com
   links para as fontes.
