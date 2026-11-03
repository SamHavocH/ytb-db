# Esquema das notas

Nomes de arquivo da wiki são legíveis (título do vídeo, nome do conceito), sem os
caracteres `\ / : * ? " < > | # ^ [ ]`. As transcrições em `raw/` usam o `video_id`
como nome de arquivo, então `[[<video_id>]]` sempre aponta para a fonte bruta.

## raw/transcripts/<video_id>.md (gerada pelo script — não editar)

Frontmatter: `type: transcript`, `video_id`, `url`, `title`, `channel`, `channel_url`,
`published`, `duration`, `language`, `transcript_source`, `fetched`, `yt_tags`.
Corpo: descrição do vídeo, depois a transcrição em parágrafos que começam com um link
de timestamp; os capítulos do vídeo viram títulos `###`.

## wiki/videos/<Título>.md

```markdown
---
type: video
video_id: "dQw4w9WgXcQ"
url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
canal: "[[Nome do Canal]]"
publicado: 2026-05-01
duracao: "42:10"
idioma: pt
fonte: "[[dQw4w9WgXcQ]]"
transcript_source: auto
conceitos: ["[[RAG]]", "[[MCP]]"]
pessoas: ["[[Fulano]]"]
tags: [ia, obsidian]
---

# <Título>

## Resumo
3–6 frases: tese central e conclusões.

## Pontos-chave
- Afirmação objetiva. [12:34](https://youtu.be/dQw4w9WgXcQ?t=754)

## Citações
> "Trecho literal relevante." — [12:34](https://youtu.be/dQw4w9WgXcQ?t=754)

## Conceitos
- [[RAG]]: como o vídeo usa/define o conceito.

## Divergências
(opcional) contradições com outras notas, com links.
```

## wiki/conceitos/<Conceito>.md

```markdown
---
type: conceito
aliases: ["Retrieval-Augmented Generation"]
tags: [ia]
---

# RAG

Definição curta, sintetizada a partir das fontes.

## O que os vídeos dizem
- [[Título do vídeo A]]: posição/explicação. [05:10](https://youtu.be/ID?t=310)
- [[Título do vídeo B]]: ...

## Relacionados
[[MCP]], [[Embeddings]]
```

## wiki/canais/<Canal>.md e wiki/pessoas/<Nome>.md

Frontmatter `type: canal` (com `url`) ou `type: pessoa`; corpo com uma descrição curta
e uma lista dos vídeos/menções com links.
