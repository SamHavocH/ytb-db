# Fluxo: ingest

## 1. Baixar as transcrições (determinístico)

```bash
uv run --script <dir-da-skill>/scripts/ytvault.py ingest <cofre> <url-ou-id> [<url-ou-id> ...]
```

Opções úteis:

| Opção | Uso |
|---|---|
| `--lang pt,en` | idiomas preferidos para legendas manuais (padrão `pt,en`) |
| `--whisper` | se o vídeo não tiver legenda, baixa o áudio e transcreve localmente (lento; baixa o modelo na 1ª vez) |
| `--whisper-model small` | `tiny`, `base`, `small`, `medium`, `large-v3` |
| `--limit N` | só os N primeiros vídeos de uma playlist |
| `--no-playlist` | numa URL `watch?v=..&list=..`, pega só o vídeo |
| `--force` | baixa de novo transcrições que já existem |

Prioridade de legenda: manual no idioma pedido → automática no idioma original →
manual em qualquer idioma → automática traduzida. O campo `transcript_source` da
transcrição registra a origem (`manual`, `auto`, `auto-translated`, `whisper`).

O stdout é JSON:

```json
{"playlists": [{"id": "...", "title": "...", "path": "raw/playlists/<id>.md", "videos": 12}],
 "results": [{"video_id": "...", "status": "ok|skipped|no_transcript|error", "path": "raw/transcripts/<id>.md", ...}]}
```

- `skipped`: já existia (não reprocesse a menos que o usuário peça).
- `no_transcript`: sugira `--whisper` ao usuário.
- `error`: relate a mensagem. Bloqueio do YouTube ("Sign in to confirm you're not a
  bot", HTTP 429) acontece principalmente em servidores/nuvem. Sugira rodar na máquina
  do usuário, atualizar o yt-dlp (`uv run --script --upgrade ...`) ou instalar o `deno`.
  Canais ainda não são suportados.

## 2. Escrever as notas da wiki (você)

Para cada resultado `ok` (e, se o usuário pedir, para pendências apontadas pelo `lint`):

1. Leia `raw/transcripts/<id>.md` inteiro.
2. Crie `wiki/videos/<Título>.md` seguindo `note-schema.md`: resumo, pontos-chave com
   timestamps, conceitos, citações relevantes.
3. Para cada conceito importante, crie ou **atualize** `wiki/conceitos/<Conceito>.md`
   acrescentando o que este vídeo diz (com link e timestamp). Antes de criar, procure
   uma nota existente com nome ou alias equivalente para evitar duplicatas.
4. Crie/atualize `wiki/canais/<Canal>.md` e, se houver pessoas relevantes,
   `wiki/pessoas/<Nome>.md`.
5. Se houver contradição com o que já está no cofre, registre nas duas notas numa
   seção `## Divergências` em vez de sobrescrever.
6. Atualize `index.md` (novos canais, playlists e conceitos) e adicione no topo de
   `log.md`: `- AAAA-MM-DD ingest: <n> vídeos (<títulos ou playlist>)`.

Playlists grandes: processe em lotes e informe o progresso. Se o usuário só quiser as
transcrições agora, pare após o passo 1. O `lint` mostra depois o que ficou pendente.
