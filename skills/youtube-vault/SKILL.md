---
name: youtube-vault
description: Transforma vídeos e playlists do YouTube em um cofre Obsidian (Markdown interligado) que serve de base de conhecimento para respostas fundamentadas com citação e timestamp. Use quando o usuário pedir para ingerir/importar/salvar/transcrever um vídeo ou playlist do YouTube no cofre ou vault, para responder perguntas "com base nos vídeos" ou "no cofre", ou para revisar (lint) o cofre. Turns YouTube videos/playlists into an Obsidian knowledge vault and answers questions grounded in it.
---

# youtube-vault

Cofre Obsidian alimentado por transcrições do YouTube, no padrão "LLM Wiki":

- `raw/` — fontes imutáveis geradas pelo script (transcrições e playlists). **Nunca edite.**
- `wiki/` — notas que **você** escreve e mantém (vídeos, conceitos, canais, pessoas).
- `AGENTS.md` / `CLAUDE.md` na raiz do cofre — convenções do cofre. Leia antes de trabalhar nele.

Os scripts ficam em `scripts/` **dentro do diretório desta skill**. Rode-os com `uv`
(as dependências são instaladas automaticamente):

```bash
uv run --script <dir-da-skill>/scripts/ytvault.py <comando> <cofre> ...
```

## Requisitos

- [`uv`](https://docs.astral.sh/uv/) no PATH. Recomendado: `deno` no PATH (o yt-dlp usa
  um runtime JS para o YouTube).
- Acesso à rede para `ingest`. No Codex a rede vem desligada por padrão: peça
  aprovação/rede ao usuário antes de rodar.
- Localização do cofre: use o caminho que o usuário indicar; senão `$YTVAULT_PATH`;
  senão pergunte. Se o cofre não tiver `raw/transcripts/`, rode `init` primeiro.

## Fluxos

Escolha o fluxo e leia a referência correspondente antes de executar:

| Pedido do usuário | Fluxo | Referência |
|---|---|---|
| "cria/prepara o cofre" | `init` | — (só rode o comando) |
| "adiciona este vídeo/playlist", "importa", "transcreve" | ingest | `references/ingest.md` |
| "o que os vídeos dizem sobre X?", qualquer pergunta sobre o conteúdo | query | `references/query.md` |
| "revisa/arruma o cofre", "o que está pendente?" | lint | `references/lint.md` |

Formato das notas: `references/note-schema.md`.

## Regras essenciais

1. Toda afirmação tirada do cofre cita a nota (`[[nota]]`) e, quando possível, o
   timestamp (`[12:34](https://youtu.be/ID?t=754)`).
2. Se o cofre não cobre a pergunta, diga isso explicitamente antes de usar
   conhecimento próprio.
3. Transcrições automáticas têm erros (nomes próprios, termos técnicos). Corrija nas
   notas da wiki, nunca em `raw/`.
4. Ao terminar um ingest ou lint, registre uma linha no topo de `log.md`.
