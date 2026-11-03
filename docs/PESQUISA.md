# Pesquisa: YouTube → Obsidian → base de conhecimento para Claude/Codex

> Status: pesquisa inicial (2026-11-03). Nada implementado ainda.

## Objetivo

Transformar vídeos do YouTube (e suas transcrições) em notas Markdown num cofre
Obsidian que sirva como **fundamentação** (grounding) para agentes como Claude
Code e Codex responderem com base nesse conteúdo, citando a fonte.

## Pipeline proposto

```
YouTube (URL, playlist, canal)
   │ 1. Coleta: metadados + legendas (yt-dlp) ── se não houver legenda ──► áudio + Whisper local
   ▼
raw/  (transcrição bruta, imutável, com timestamps)
   │ 2. Processamento por LLM: limpeza, resumo, conceitos, links [[...]]
   ▼
wiki/ (notas do cofre: vídeo, conceito, pessoa, canal — com frontmatter)
   │ 3. Acesso pela IA: arquivos + AGENTS.md/CLAUDE.md + busca (grep/BM25/vetorial via MCP)
   ▼
Claude Code / Codex respondem citando [[nota]] e link com timestamp
```

## 1. Coleta das transcrições

| Opção | Prós | Contras |
|---|---|---|
| `youtube-transcript-api` (Python) | Simples, retorna segmentos com timestamp | YouTube bloqueia IPs de nuvem; exige proxy residencial pago em servidor |
| `yt-dlp --write-subs --write-auto-subs --skip-download` | Mantido ativamente, pega metadados + legendas, playlists/canais | Mudanças frequentes no extrator; às vezes exige PO token / cookies |
| Áudio + Whisper local (`faster-whisper`) | Funciona sem legenda, qualidade alta | Custo de CPU/GPU, mais lento |
| APIs pagas (AssemblyAI, Deepgram) | Rápido, diarização | Custo por minuto |

**Recomendação:** rodar **localmente** (IP residencial evita a maioria dos
bloqueios), usar `yt-dlp` como fonte principal e `faster-whisper` como fallback.
Rodar isso em nuvem/CI tende a falhar por bloqueio de IP.

## 2. Estrutura do cofre (padrão "LLM Wiki")

Padrão popularizado por Karpathy (abr/2026): em vez de só fazer RAG sobre
documentos brutos, um agente mantém uma wiki Markdown estruturada e crescente.
Três camadas e três operações:

- **Camadas:** `raw/` (fontes imutáveis) · `wiki/` (mantida pelo LLM) · arquivo de
  esquema (`AGENTS.md` / `CLAUDE.md`) com as convenções.
- **Operações:** *ingest* (nova fonte → atualiza notas), *query* (responder com
  citações), *lint* (achar contradições, links quebrados, notas órfãs).

Esboço:

```
vault/
├── AGENTS.md            # convenções lidas pelo Codex (e CLAUDE.md → aponta p/ ele)
├── raw/transcripts/<video_id>.md
├── wiki/videos/<titulo>.md
├── wiki/conceitos/<conceito>.md
├── wiki/canais/<canal>.md
└── index.md             # mapa de conteúdo
```

Frontmatter sugerido da nota de vídeo:

```yaml
---
type: video
video_id: dQw4w9WgXcQ
url: https://youtu.be/dQw4w9WgXcQ
canal: "[[Nome do Canal]]"
publicado: 2026-05-01
duracao: 00:42:10
idioma: pt
fonte_transcricao: yt-dlp-auto   # manual | auto | whisper
tags: [ia, obsidian]
conceitos: ["[[RAG]]", "[[MCP]]"]
---
```

Timestamps como links (`[12:34](https://youtu.be/ID?t=754)`) permitem que a IA
cite o trecho exato.

## 3. Como Claude e Codex consomem o cofre

1. **Acesso direto a arquivos** – abrir o agente na pasta do cofre. Ambos leem
   Markdown e usam grep; `AGENTS.md` (Codex) e `CLAUDE.md` (Claude Code) explicam
   a estrutura e exigem citação. Zero infraestrutura; funciona bem até alguns
   milhares de notas.
2. **Busca via MCP** – quando crescer:
   - [`qmd`](https://github.com/tobi/qmd): BM25 + vetorial + rerank, 100% local,
     servidor MCP pronto. Forte candidato.
   - Servidores MCP de RAG para Obsidian (`obsidian-rag-mcp`, `mcp-obsidianRAG`):
     embeddings via OpenAI ou Ollama.
   - MCP é suportado tanto por Claude Code quanto por Codex.
3. **Skills** – uma Agent Skill de "ingest de vídeo" reutilizável nos dois agentes.

## 4. O que já existe (para não reinventar)

Plugins Obsidian: *YouTube Transcript Fetcher*, *YTranscript*, *TubeSage*,
*YouTube Transcript Notes*, *Video Caption Fetch* (com fallback de ASR e fila).
Resolvem "um vídeo → uma nota" manualmente, mas **não** fazem ingest em lote de
canais/playlists, nem mantêm a wiki interligada, nem são pensados como base para
agentes. Esse é o espaço para o projeto.

## 4b. Reaproveitamento (a validar: licença e manutenção não verificadas)

| Camada | Reaproveitar | Observação |
|---|---|---|
| Estrutura do cofre + skill do agente | `oh-my-wiki` (dandacompany), `sdyckjq-lab/llm-wiki-skill` | Padrão LLM Wiki pronto p/ Claude Code e Codex; oh-my-wiki já busca transcrição do YouTube para `raw/` |
| Coleta em lote (canal) | `dparedesi/YTScribe` | CLI Python, arquivo por canal, Markdown + frontmatter |
| Transcrição sem legenda | `anyscribecli`, `faster-whisper` | Saída em Markdown para Obsidian |
| Skill de um vídeo | `glebis/claude-skills` (youtube-transcript) | yt-dlp → nota no cofre |
| Busca | `tobi/qmd` | MCP local |

Código próprio fica restrito à "cola": ingest em lote de canais e playlists com
deduplicação por `video_id`, esquema de frontmatter/timestamps e regras no `AGENTS.md`.

## 4c. Formato de entrega: skill instalável via `npx`

- Padrão aberto **Agent Skills**: diretório com `SKILL.md` (frontmatter `name` +
  `description`) + `scripts/` e `references/` opcionais. Mesmo formato no Claude
  Code (`~/.claude/skills`) e no Codex (`~/.codex/skills`).
- Instalação: `npx skills add SamHavocH/ytb-db` (CLI `skills` da Vercel, suporta
  `-a claude-code -a codex`, `-g` global, `--skill <nome>`). Alternativas:
  marketplace de plugins do Claude Code e `$skill-installer` no Codex.
- O repositório vira o pacote: `skills/<nome>/SKILL.md` na raiz do repo.

Esboço:

```
skills/
├── youtube-vault-ingest/      # URL/playlist/canal → raw/ + nota em wiki/
│   ├── SKILL.md
│   ├── scripts/fetch.py       # yt-dlp + fallback faster-whisper (rodar via `uv run`)
│   └── references/note-schema.md
├── youtube-vault-query/       # responder com citações [[nota]] + timestamp
└── youtube-vault-lint/        # links quebrados, duplicados, órfãs
templates/AGENTS.md            # copiado para a raiz do cofre no init
```

Pontos de atenção:
- **Dependências:** a skill não instala nada sozinha. O `yt-dlp` é Python, então
  o mais simples é scripts Python com dependências inline (PEP 723) rodando via
  `uv run`, ou exigir o `yt-dlp` no PATH. Scripts em Node evitariam o Python, mas
  continuariam chamando o binário `yt-dlp`.
- **Codex roda sem rede por padrão:** a coleta precisa de aprovação/rede
  liberada; deixar isso explícito no `SKILL.md`.
- O LLM do agente faz o trabalho de resumo/ligação de notas; os scripts só fazem
  a parte determinística (download, parsing, frontmatter, dedupe por `video_id`).
  Assim não precisa de chave de API própria.

## 5. Questões em aberto (decidir antes de desenvolver)

1. Volume: quantos vídeos/canais? (define se basta grep ou se precisa de `qmd`/vetorial)
2. Idioma dos vídeos (pt, en, ambos?) e se as notas devem ser traduzidas.
3. Onde roda: máquina local (recomendado) ou servidor?
4. Quem gera resumos/conceitos: Claude via API, o próprio Claude Code/Codex no
   modo agente, ou modelo local (Ollama)? Impacta custo.
5. Guardar transcrição integral no cofre ou só resumo + link? (integral = melhor
   grounding, cofre maior)
6. Atualização: manual por URL, ou monitorar canais/playlists periodicamente?
7. Linguagem do projeto: Python (ecossistema yt-dlp/whisper) parece o natural.

## Fontes

- youtube-transcript-api e bloqueio de IPs de nuvem: https://github.com/jdepoix/youtube-transcript-api , https://github.com/jdepoix/youtube-transcript-api/issues/593
- yt-dlp / PO tokens: https://src.opensuse.org/pool/yt-dlp/pulls/4/files
- qmd: https://github.com/tobi/qmd
- Obsidian RAG MCP: https://pypi.org/project/obsidian-rag-mcp/ , https://lobehub.com/mcp/ernestkoe-mcp-obsidianrag
- LLM Wiki (Karpathy): https://venturebeat.com/data/karpathy-shares-llm-knowledge-base-architecture-that-bypasses-rag-with-an , https://blog.starmorph.com/blog/karpathy-llm-wiki-knowledge-base-guide
- Plugins Obsidian: https://community.obsidian.md/plugins/youtube-transcript-fetcher , https://community.obsidian.md/plugins/tubesage , https://community.obsidian.md/plugins/video-transcript-fetch
