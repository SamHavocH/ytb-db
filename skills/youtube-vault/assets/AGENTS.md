# Convenções deste cofre

Este é um cofre Obsidian gerado pela skill `youtube-vault`. Ele é a base de
conhecimento para respostas fundamentadas em vídeos do YouTube.

## Estrutura

- `raw/transcripts/<video_id>.md`: transcrições brutas com timestamps. Imutáveis: não edite.
- `raw/playlists/<playlist_id>.md`: lista de vídeos de cada playlist importada.
- `wiki/videos/`: uma nota por vídeo (resumo, pontos-chave, citações, conceitos).
- `wiki/conceitos/`: uma nota por conceito, agregando o que cada vídeo diz.
- `wiki/canais/`, `wiki/pessoas/`: autores e pessoas citadas.
- `index.md`: mapa do conteúdo. `log.md`: histórico de ingestões e revisões.

## Ao responder perguntas

1. Busque primeiro em `wiki/`; vá a `raw/transcripts/` para detalhes e citações literais.
2. Cite sempre: `[[nota]]` e o timestamp `[mm:ss](https://youtu.be/ID?t=S)`.
3. Separe o que as fontes dizem da sua própria síntese.
4. Se o cofre não cobre o assunto, diga isso antes de usar conhecimento geral.

## Ao editar

- Siga o esquema de notas da skill `youtube-vault` (`references/note-schema.md`).
- Atualize notas existentes em vez de criar duplicatas; use `aliases:` para sinônimos.
- Contradições entre fontes vão para uma seção `## Divergências` e não são apagadas.
- Registre ingestões e revisões no topo de `log.md`.
