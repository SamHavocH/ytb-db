# ytb-db — skill `youtube-vault`

Usa vídeos e playlists do YouTube (transcrições) para alimentar um cofre Obsidian, que
serve de base de conhecimento para respostas fundamentadas de agentes como Claude Code
e Codex, com citação da nota e do timestamp.

## Instalação

```bash
npx skills add SamHavocH/ytb-db -a claude-code -a codex      # adicione -g para instalar globalmente
```

Requisitos na máquina:

- [`uv`](https://docs.astral.sh/uv/getting-started/installation/), que roda os scripts e instala as dependências Python sozinho
- recomendado: [`deno`](https://deno.com/), runtime JS usado pelo yt-dlp para o YouTube

Rode na sua máquina: o YouTube costuma bloquear IPs de servidores e nuvem.

## Uso (conversando com o agente)

- "Cria um cofre do YouTube em ~/Obsidian/YT"
- "Adiciona esta playlist ao cofre: https://www.youtube.com/playlist?list=..."
- "Com base nos vídeos do cofre, o que dizem sobre RAG?"
- "Revisa o cofre e me diz o que está pendente"

Dica: defina `YTVAULT_PATH` com o caminho do cofre para não precisar repetir.

## Como funciona

```
URL de vídeo/playlist ─► scripts/ytvault.py ingest ─► raw/transcripts/<id>.md  (legendas + timestamps)
                                                  └─► raw/playlists/<id>.md
o agente lê raw/ ─────► escreve wiki/videos, wiki/conceitos, wiki/canais, index.md, log.md
perguntas ────────────► o agente busca em wiki/ e raw/, cita [[nota]] e [mm:ss](link)
```

- Legendas via `yt-dlp`. Prioridade: manual no idioma pedido, depois automática no
  idioma original, depois traduzida. Com `--whisper`, transcreve o áudio localmente
  (`faster-whisper`) quando não há legenda.
- Os scripts fazem só a parte determinística. Resumos e ligações entre notas são feitos
  pelo próprio agente, sem chave de API extra.

Uso direto do script:

```bash
S=skills/youtube-vault/scripts/ytvault.py
uv run --script $S init  ~/Obsidian/YT
uv run --script $S ingest ~/Obsidian/YT "https://www.youtube.com/playlist?list=..." --lang pt,en
uv run --script $S lint  ~/Obsidian/YT
```

## Estrutura do repositório

```
skills/youtube-vault/
├── SKILL.md                 # ponto de entrada da skill
├── scripts/ytvault.py       # init | ingest | lint
├── scripts/transcribe.py    # fallback faster-whisper
├── references/              # fluxos ingest/query/lint e esquema das notas
└── assets/AGENTS.md         # convenções copiadas para o cofre no init
tests/                       # testes offline: uv run --with pytest pytest -q
docs/PESQUISA.md             # pesquisa que embasou o projeto
```

## Roadmap

- [ ] Canais inteiros (com acompanhamento de vídeos novos)
- [ ] Busca semântica via MCP (`qmd`) para cofres grandes
- [ ] Atualização incremental de playlists
