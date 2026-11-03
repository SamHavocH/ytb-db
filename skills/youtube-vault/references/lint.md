# Fluxo: lint (saúde do cofre)

```bash
uv run --script <dir-da-skill>/scripts/ytvault.py lint <cofre>
```

Saída JSON e como agir:

| Campo | Significado | Ação |
|---|---|---|
| `pending_transcripts` | transcrição em `raw/` sem nota em `wiki/` | oferecer processar (fluxo ingest, passo 2) |
| `wiki_without_transcript` | nota de vídeo cujo `video_id` não tem transcrição | rodar `ingest` para o ID, ou corrigir o `video_id` |
| `duplicate_video_notes` | mais de uma nota para o mesmo vídeo | mesclar numa só e atualizar os links |
| `broken_links` | `[[link]]` sem nota de destino | criar a nota (se for conceito relevante) ou corrigir o link |
| `orphan_notes` | nota da wiki sem nenhum link de entrada | ligar a partir de conceito, canal ou `index.md` |

Verificações que o script não faz e você deve fazer por amostragem:

- conceitos duplicados com nomes diferentes (ex.: "RAG" e "Retrieval-Augmented
  Generation"): mesclar e manter `aliases:`;
- afirmações contraditórias entre notas: registrar em `## Divergências`;
- nomes próprios ou termos errados vindos da legenda automática.

Ao terminar, registre no topo de `log.md`: `- AAAA-MM-DD lint: <resumo>`.
