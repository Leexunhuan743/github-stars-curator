# Taxonomy Rubric

This rubric starts from a practical, retrieval-oriented taxonomy that has already worked for a large starred-repo set. Treat it as a baseline, not a prison.

`references/taxonomy-template.yaml` is the bundled machine-readable source for list names, order, descriptions, and max list count. A workspace can override it with `<workspace>/taxonomy.yaml`. If prose in this rubric drifts from the YAML, use the YAML for script behavior and update the prose before changing the reusable skill.

## Table of Contents

- [Starter lists](#starter-lists)
- [Core front-rank buckets](#core-front-rank-buckets)
- [How to choose lists](#how-to-choose-lists)
- [Ledger dimensions](#ledger-dimensions)
- [When to add a new list](#when-to-add-a-new-list)
- [When to merge lists](#when-to-merge-lists)
- [Ambiguity policy](#ambiguity-policy)
- [Formal rules for development-related lists](#formal-rules-for-development-related-lists)
- [Formal rules for reading and document lists](#formal-rules-for-reading-and-document-lists)
- [Formal rules for media and download lists](#formal-rules-for-media-and-download-lists)
- [Formal rules for cloud, transfer, and sync lists](#formal-rules-for-cloud-transfer-and-sync-lists)
- [Formal rules for clipboard lists](#formal-rules-for-clipboard-lists)
- [Formal rules for terminal lists](#formal-rules-for-terminal-lists)
- [Formal rules for Windows lists](#formal-rules-for-windows-lists)
- [Formal rules for user-facing software lists](#formal-rules-for-user-facing-software-lists)
- [Formal rules for reference and learning lists](#formal-rules-for-reference-and-learning-lists)
- [Formal rules for deployment and network lists](#formal-rules-for-deployment-and-network-lists)
- [Formal rules for languages, frameworks, and data lists](#formal-rules-for-languages-frameworks-and-data-lists)
- [Formal rules for creative, business, scraping, and security lists](#formal-rules-for-creative-business-scraping-and-security-lists)
- [Formal rules for fallback lists](#formal-rules-for-fallback-lists)

## Starter lists

- `downloaders`: download managers, media downloaders, torrent clients, stream grabbers, and automated download tools
- `cloud-drive-transfer-sync`: cloud drives, WebDAV and storage browsers, file transfer, device sending, remote copy, and folder sync tools
- `clipboard-tools`: clipboard managers, clipboard history, pasteboard tools, cross-device copy/paste, and clipboard synchronization utilities
- `media-players`: music, image, and video players: local players, streaming clients, gallery and comic browsers, danmu viewers, and watch-focused apps
- `agent-tools`: agent harnesses, coding runtimes, agent skills, MCP servers, plugins, and agent-adjacent developer tooling
- `ai-agents`: AI agents, agent platforms, autonomous workflows, and agent-oriented applications
- `dev-tools`: developer tools, editors, local engineering utilities, coding workflow tools, and static-site or publishing pipelines
- `terminal`: terminal apps, TUIs, CLI-first utilities, SSH clients, and remote shell tools
- `windows-tools`: Windows utilities, shell extensions, Explorer integrations, keymaps, thumbnails, and system tools
- `desktop-apps`: general user-facing desktop apps, chat export and archive tools, native utilities, and everyday GUI software
- `reading-notes`: RSS readers, desktop reading apps, document readers, read-later and ebook/manga/library servers, note-taking apps, markdown knowledge tools, and PKM systems
- `pdf-document-tools`: PDF and document readers, editors, converters, OCR/compression tools, document viewers, and document-to-Markdown or AI-prep utilities
- `references-guides`: reference collections, awesome lists, guides, tutorials, datasets, books, and learning resources
- `self-hosted`: deployable self-hosted services, home-lab apps, private web tools, APIs, personal server software, containers and orchestration, cloud-native infrastructure, and self-hosted chat platforms
- `cloudflare-network-proxy`: Cloudflare Workers and tunnels plus general proxy-network tooling: reverse proxies, subscription and proxy panels, edge gateways, relays, and proxy-network clients
- `frameworks-libraries`: web and application frameworks, UI/component libraries, front-end libraries, programming languages, compilers, runtimes, and developer libraries
- `data-ml-tools`: data science and ML frameworks, model inference infrastructure, databases, search engines, key-value and vector stores, ORMs, and data libraries
- `game-3d-creative`: games, game engines and SDKs, 3D modeling and rendering, emulators, firmware, and generative creative tools
- `design-assets`: fonts, icon sets, color themes, and reusable design resources
- `business-apps`: business and industry software: CMS, invoicing, scheduling, e-commerce, BI, and support platforms
- `web-scraping-data-collection`: scrapers, data collection APIs, and browser automation for data acquisition
- `security-pentest-tools`: security tooling: OSINT, penetration testing, reverse engineering, and exploit frameworks
- `everything-else`: fallback bucket for repos that fit no specialized list, including ambiguous repos still awaiting review

## Core front-rank buckets

These twenty-three buckets are the front rank of this skill's taxonomy. When a repo fits one of them cleanly, prefer assigning it there before reaching for ad hoc or legacy buckets. The last bucket is still formal, but it is the controlled fallback rather than a preferred destination.

1. `downloaders`
2. `cloud-drive-transfer-sync`
3. `clipboard-tools`
4. `media-players`
5. `agent-tools`
6. `ai-agents`
7. `dev-tools`
8. `terminal`
9. `windows-tools`
10. `desktop-apps`
11. `reading-notes`
12. `pdf-document-tools`
13. `references-guides`
14. `self-hosted`
15. `cloudflare-network-proxy`
16. `frameworks-libraries`
17. `data-ml-tools`
18. `game-3d-creative`
19. `design-assets`
20. `business-apps`
21. `web-scraping-data-collection`
22. `security-pentest-tools`
23. `everything-else`

Ordering principle:

1. File movement, acquisition, and clipboard flow: `downloaders`, `cloud-drive-transfer-sync`, `clipboard-tools`.
2. Media consumption: `media-players`.
3. AI, development, terminal, local system, and desktop app workflows: `agent-tools`, `ai-agents`, `dev-tools`, `terminal`, `windows-tools`, `desktop-apps`.
4. Reading, documents, notes, and reference material: `reading-notes`, `pdf-document-tools`, `references-guides`.
5. Self-hosted services and network infrastructure: `self-hosted`, `cloudflare-network-proxy`.
6. Languages, frameworks, libraries, and data tooling: `frameworks-libraries`, `data-ml-tools`.
7. Creative, business, scraping, and security tooling: `game-3d-creative`, `design-assets`, `business-apps`, `web-scraping-data-collection`, `security-pentest-tools`.
8. Controlled fallback: `everything-else`.

## How to choose lists

Use the smallest set of lists that makes the repo easy to find later.

Good questions:

- What is this repo mainly for?
- What workflow would make me go looking for it again?
- Is it a product, a library, a dataset, a reading list, a service, or a desktop tool?
- Does it belong to a special retrieval lane like `self-hosted`, `reading-notes`, or `desktop-apps`?

## Ledger dimensions

Keep classification reasoning more structured than GitHub lists themselves:

- `primaryFunction`: exactly one short functional label that states the repo's main job, such as `download`, `play-music`, `agent-runtime`, `note-taking`, `reference`, or `network-proxy`.
- `facets`: optional secondary dimensions such as `windows`, `self-hosted`, `cli`, `desktop`, `cloudflare`, `mcp`, or `ai`.
- `finalLists`: the GitHub lists selected from the loaded taxonomy. These can be generated from `primaryFunction` and `facets`, then manually adjusted after reading the README.

Use `primaryFunction` to prevent platform, deployment style, and product shape from overwhelming the main purpose. Use `facets` to preserve useful secondary retrieval signals without inventing a new primary bucket for every combination.

## When to add a new list

Create a new list only if all are true:

1. The concept is stable and easy to name.
2. At least a few repos belong there now or clearly will soon.
3. Existing lists would become less useful if forced to absorb it.
4. The total managed list count remains within GitHub's current limit.

## When to merge lists

Merge if any are true:

- two lists are routinely assigned together,
- users would not remember the distinction later,
- one list has too few repos and no clear growth path,
- the GitHub list cap is under pressure.

## Ambiguity policy

If a repo spans several areas, use:

1. one primary functional list,
2. one secondary workflow list if it adds retrieval value,
3. a broad fallback only when needed.

If still unsure, place it in `everything-else` and record the uncertainty in the ledger.

## Formal rules for development-related lists

Do not create a separate `editors-ide` bucket. Traditional editors and local coding tools should be handled inside the existing development taxonomy.

### `agent-tools`

Definition:

`Agent harnesses, coding runtimes, agent skills, MCP servers, plugins, and agent-adjacent developer tooling.`

Use this when the repository is part of the toolchain around coding agents — whether it is the environment that runs them or the capabilities that extend them.

Belongs here:

- coding-agent harnesses, ADEs, agent runtimes, and multi-agent workspaces,
- MCP servers, skills, agent plugins, and capability bridges for Codex, Claude Code, Cursor, and similar clients,
- code intelligence, repo knowledge graphs, codebase indexing, and code-search tools,
- AI tools for content generation (PPT, image, writing, research, report).

Do not put these here:

- ordinary editors and local dev utilities — use `dev-tools`,
- broad end-user agent products — use `ai-agents`.

Common confusions:

- if it is mainly a traditional developer utility, use `dev-tools`,
- if it is mainly an agent-facing product or workflow app rather than toolchain infrastructure, use `ai-agents`.

### `ai-agents`

Definition:

`AI agents, agent platforms, autonomous workflows, and agent-oriented applications.`

Use this when the repository is mainly an agent product, agent application, or agent workflow system rather than the runtime layer or capability extension layer.

Belongs here:

- agent products and platforms,
- autonomous workflow systems,
- agent dashboards and orchestration apps,
- end-user applications centered on agent behavior.

Do not put these here:

- harnesses and ADEs,
- MCP servers and skill packs,
- ordinary developer tools with no agent-centric product surface.

Common confusions:

- runtimes and coding harnesses belong in `agent-tools`,
- capabilities and integrations belong in `agent-tools`,
- AI content-generation tools belong in `agent-tools`.

### `dev-tools`

Definition:

`Developer tools, editors, local engineering utilities, coding workflow tools, and static-site or publishing pipelines.`

Use this as the default bucket for traditional development tools. This is where editors, documentation browsers, code-processing tools, local engineering helpers, and static-site or publishing pipelines should go when they are not primarily AI-agent infrastructure.

Belongs here:

- editors and editor-adjacent tools,
- offline documentation browsers,
- code and text processing tools,
- local workflow helpers for engineering work,
- static-site generators, doc-to-site tools, and publishing pipelines (hugo, docs builders),
- developer-facing utilities that are not primarily note-taking products.

If a repo is development-related, classify it in this order:

1. If it is part of the agent toolchain, use `agent-tools`.
2. Otherwise, default to `dev-tools`.

For text editors, use this rule:

- development-oriented text editors go to `dev-tools`,
- note-taking or markdown knowledge editors go to `reading-notes`,
- general desktop writing tools go to `desktop-apps`.

Common confusions:

- if the product is really a note system, use `reading-notes`,
- if the product is a broad desktop app with no clear dev workflow focus, use `desktop-apps`,
- if the repo is clearly agent-runtime or MCP related, use `agent-tools`.

## Formal rules for reading and document lists

Use two reading and document-oriented lanes:

1. `reading-notes` for reading workflows (subscription readers, desktop reading apps, self-hosted read-later and ebook/manga/library servers) and knowledge workflows (notes, markdown knowledge, PKM),
2. `pdf-document-tools` for PDF/document editing, conversion, OCR, compression, viewing components, and document-to-Markdown or AI-prep pipelines.

Do not create a broad catch-all reading bucket beyond these lanes.

### `reading-notes`

Definition:

`RSS readers, desktop reading apps, document readers, read-later and ebook/manga/library servers, note-taking apps, markdown knowledge tools, and PKM systems.`

Use this when the main workflow is consuming content (reading, subscribing, archiving reading material) or capturing and organizing knowledge (notes, PKM). Reading and note tools are one lane because they are frequently the same product and the same retrieval question: "where do I consume and keep content?".

Belongs here:

- RSS and feed readers, newsletter and subscription readers,
- ebook readers and document-reading apps, single-user manga or novel readers,
- self-hosted read-later services, bookmark archives, ebook/manga servers, and reading libraries,
- note-taking apps, markdown knowledge tools, PKM systems, memo and scratchpad apps, personal knowledge bases.

Do not use this for PDF/document processing suites, generic deployable services without a reading/archive workflow, or developer editors.

Common confusions:

- if the main workflow is PDF/document conversion, OCR, compression, or repair, use `pdf-document-tools`,
- if the repo is a generic deployable service with no reading or knowledge workflow, use `self-hosted`,
- if it is mainly a developer editor or documentation browser, use `dev-tools`,
- if it is a writing-first general desktop tool, use `desktop-apps`.

### `pdf-document-tools`

Definition:

`PDF and document readers, editors, converters, OCR/compression tools, document viewers, and document-to-Markdown or AI-prep utilities.`

Use this when the main workflow is opening, editing, converting, compressing, OCR-ing, extracting, repairing, viewing, or preparing PDF/document files.

Belongs here:

- PDF readers and editors,
- PDF merge, split, compression, signing, annotation, form, or password tools,
- OCR, scanned-document cleanup, and document repair tools,
- Office/PDF/CAD/document viewer components,
- document-to-Markdown, document-to-HTML, or document-to-AI-prep converters,
- download helpers only when the durable retrieval intent is PDF/document handling rather than general downloading.

Use this alongside `reading-notes` when the app is both a user-facing document reader and a PDF/document toolkit. Use it alongside `dev-tools` when the repo is a developer-facing document conversion library.

Do not use this for general note-taking, plain Markdown editors, static-site publishing systems, or ordinary ebook/RSS readers unless PDF/document handling is the main retrieval intent.

Common confusions:

- if the main workflow is simply reading ebooks, feeds, or articles, use `reading-notes`,
- if the main workflow is capturing notes or managing knowledge, use `reading-notes`,
- if the main workflow is publishing documents to a website, book, deck, or public report, use `dev-tools`,
- if the main workflow is downloading files and document handling is incidental, use `downloaders`.

## Formal rules for media and download lists

### `downloaders`

Definition:

`Download managers, media downloaders, torrent clients, stream grabbers, and automated download tools.`

Use this when the core value of the repo is getting files or media onto disk, whether interactively or automatically.

Belongs here:

- download managers,
- torrent and BT clients,
- audio and video downloaders,
- m3u8, HLS, and stream grabbers,
- gallery and media fetchers,
- subscription or rule-based auto-download tools,
- remote or offline download clients.

Treat this as the primary bucket for both general download tools and media extraction tools.

Do not use this as the primary bucket for players, cloud-drive managers, or general media libraries unless downloading is clearly the main workflow.

Common confusions:

- if the main product is media playback of any kind (listening, watching, browsing), use `media-players`,
- if the main product is a cloud-drive, transfer, or sync manager, use `cloud-drive-transfer-sync`.

### `media-players`

Definition:

`Music, image, and video players: local players, streaming clients, gallery and comic browsers, danmu viewers, and watch-focused apps.`

Use this when the main workflow is consuming media — listening to music, watching video, or browsing image-first content. Playback or browsing is the product surface.

Belongs here:

- local music players, streaming music clients, lyric players,
- video players, streaming video clients, danmu players, watch-first anime/Bilibili/media frontends,
- image viewers, photo browsers, comic/manga/archive/folder viewers, gallery clients (Pixiv-style), image preview tools,
- album, playlist, and library-oriented media apps.

Do not use this for downloaders, tag editors, media servers without a playback surface, image editors, or content-generation tools.

Common confusions:

- if the real workflow is acquisition, scraping, or downloading media, use `downloaders`,
- if the main workflow is editing or creating images, use `desktop-apps` or `game-3d-creative` for generative tools,
- if the product mainly manages storage, transfer, or sync rather than playback, use `cloud-drive-transfer-sync`,
- if it is a self-hosted media library server (Plex/Jellyfin-style), use `self-hosted`.

## Formal rules for cloud, transfer, and sync lists

### `cloud-drive-transfer-sync`

Definition:

`Cloud drives, WebDAV and storage browsers, file transfer, device sending, remote copy, and folder sync tools.`

Use this as the unified bucket for moving, syncing, browsing, or managing files across cloud drives, local devices, folders, remote servers, and storage backends.

Belongs here:

- cloud-drive clients and storage browsers,
- WebDAV, S3, object-storage, and remote filesystem tools,
- file transfer and send/receive tools,
- device-to-device and LAN transfer apps,
- folder sync, backup sync, and remote copy tools,
- cross-device file hubs and file-management apps centered on storage or transfer.

Do not use this for media downloaders, torrent clients, stream grabbers, or site/gallery scraping tools unless storage sync or cloud-drive management is the main product.

Common confusions:

- if the main workflow is getting media or web resources from a platform onto disk, use `downloaders`,
- if the main workflow is browsing or managing a cloud drive, storage backend, or WebDAV filesystem, use `cloud-drive-transfer-sync`,
- if the main workflow is sending, receiving, copying, or synchronizing files between endpoints, use `cloud-drive-transfer-sync`,
- if the main object being captured, stored, or synchronized is clipboard history or pasteboard content, use `clipboard-tools`,
- if it is a broad self-hosted service with storage as only one feature, consider `self-hosted` plus the closest functional bucket.

## Formal rules for clipboard lists

### `clipboard-tools`

Definition:

`Clipboard managers, clipboard history, pasteboard tools, cross-device copy/paste, and clipboard synchronization utilities.`

Use this when the main workflow is capturing, searching, organizing, syncing, or reusing clipboard and pasteboard content.

Belongs here:

- clipboard managers and clipboard history tools,
- pasteboard utilities,
- cross-device copy/paste tools,
- local-first or encrypted clipboard sync tools,
- screenshot/text clipboard capture tools when clipboard flow is the main product,
- software KVM tools when clipboard sharing is a major retrieval reason.

Use this alongside `cloud-drive-transfer-sync` when the product is specifically cross-device clipboard sync. Use it alongside `windows-tools` when Windows shell or system integration is the main reason to find it later.

Do not use this for generic file transfer, cloud drives, password managers, ordinary text editors, or broad desktop productivity apps where clipboard is only a minor feature.

Common confusions:

- if the main workflow is file transfer, folder sync, cloud storage, or WebDAV/S3 browsing, use `cloud-drive-transfer-sync`,
- if the app is a broad desktop organizer with clipboard as only one panel, use `desktop-apps` and add `clipboard-tools` only when clipboard is a major feature,
- if the tool is Windows-only but clipboard-centered, use both `clipboard-tools` and `windows-tools`,
- if it is a text expander rather than a clipboard history/pasteboard tool, use `desktop-apps` unless clipboard reuse is central.

## Formal rules for terminal lists

### `terminal`

Definition:

`Terminal apps, TUIs, CLI-first utilities, SSH clients, and remote shell tools.`

Use this as the unified bucket for terminal-centric software, whether the main workflow is local command-line work or remote shell access.

Belongs here:

- terminal emulators,
- TUI applications,
- CLI-first utilities,
- shell workspaces and multiplexers,
- SSH and remote shell clients,
- terminal tools that combine local shell and remote session workflows.

Do not use this for ordinary developer editors, general desktop tools, or network utilities whose main value is not a terminal or shell workflow.

Common confusions:

- if the repo is primarily a coding-agent runtime, use `agent-tools`,
- if the repo is primarily a broad remote-management or network product rather than a terminal workflow, consider `everything-else` or a more specific networking bucket,
- classify SSH clients and remote shell tools directly in `terminal`.

## Formal rules for Windows lists

### `windows-tools`

Definition:

`Windows utilities, shell extensions, Explorer integrations, keymaps, thumbnails, and system tools.`

Use this as the unified bucket for Windows-specific utilities, including both ordinary Windows productivity tools and system-layer integrations.

Belongs here:

- Windows productivity utilities,
- system management and tweaking tools,
- Explorer extensions and shell integrations,
- context menu managers,
- thumbnail, preview, and file association tools,
- keymaps, input-method helpers, and hotkey tools,
- Windows-only desktop helpers that primarily improve the OS workflow.

Do not use this for generic cross-platform desktop apps unless the Windows integration is the main reason to retrieve it later.

Common confusions:

- if it is a broad desktop app that merely happens to run on Windows, use `desktop-apps`,
- if it is mainly a developer tool, use `dev-tools`,
- if it is mainly a terminal or SSH workflow, use `terminal`,
- all Windows shell, Explorer, context menu, thumbnail, keymap, and system-layer utilities belong here.

## Formal rules for user-facing software lists

### `desktop-apps`

Definition:

`General user-facing desktop apps, chat export and archive tools, native utilities, and everyday GUI software.`

When a repo is a candidate for `desktop-apps` and any specialized front-rank bucket also fits (image viewers, clipboard tools, terminal/SSH, note/PKM, media players, downloaders, Windows system tools), assign the specialized bucket instead or alongside it — never `desktop-apps` alone. A specialized list earns the repo its own retrieval path; `desktop-apps` alone buries it in the largest bucket.

Use this for ordinary desktop software that users open directly, especially when it is not better captured by a more specific front-rank bucket.

Belongs here:

- general user-facing desktop apps,
- cross-platform native GUI utilities,
- chat export, chat archive, conversation history analysis, and chat report tools,
- screenshot, OCR, tray, launcher, and everyday productivity utilities,
- general desktop writing tools that are not note-taking or PKM systems.

Use `desktop-apps` as the broad home for ordinary GUI software that is not better captured by a specialized bucket. Clipboard-centered tools now belong in `clipboard-tools`; chat export/archive workflows remain in `desktop-apps` unless a future stable social-platform bucket is created.

Common confusions:

- if the main value is Windows shell, Explorer, context menu, thumbnail, keymap, or system-layer integration, use `windows-tools`,
- if the main value is clipboard history, pasteboard management, or cross-device copy/paste, use `clipboard-tools`,
- if the app is primarily a developer utility, use `dev-tools`,
- if it is mainly notes, markdown knowledge, or PKM, use `reading-notes`,
- if it is useful software but not specifically a desktop app or native GUI utility, use `everything-else`.

## Formal rules for reference and learning lists

### `references-guides`

Definition:

`Reference collections, awesome lists, guides, tutorials, datasets, books, and learning resources.`

Use this when the repository's main value is knowledge, curated references, or reusable learning material rather than runnable software.

Belongs here:

- awesome lists and curated resource indexes,
- guides, tutorials, books, and learning tracks,
- datasets, dictionaries, corpora, and benchmark collections,
- prompt collections and reusable reference examples,
- documentation collections that are valuable as standalone reference material.

Do not use this for runnable applications, developer tools, note-taking software, publishing pipelines, or AI-agent infrastructure unless the repo is primarily a reference collection.

Common confusions:

- if it is a tool for writing, publishing, or hosting docs, use `dev-tools`,
- if it is a note-taking or PKM product, use `reading-notes`,
- if it is a developer utility with reference features, use `dev-tools`,
- if the repo is the knowledge itself rather than a tool that manages knowledge, use `references-guides`.

## Formal rules for deployment and network lists

### `self-hosted`

Definition:

`Deployable self-hosted services, home-lab apps, private web tools, APIs, personal server software, containers and orchestration, cloud-native infrastructure, and self-hosted chat platforms.`

Use this when the repository is mainly something the user can run as their own service, server, API, private web app, NAS app, home-lab tool, or infrastructure component, and no more specific front-rank bucket captures the core workflow better.

Belongs here:

- self-hosted web services,
- home-lab and NAS-friendly apps,
- private APIs and backend services,
- personal dashboards and server-side tools,
- deployable utilities intended to replace a hosted SaaS,
- Docker-ready or single-binary services where the service itself is the product,
- containers, orchestration, and cloud-native infrastructure (kubernetes, ingress controllers, terraform, observability operators),
- self-hosted chat/IM/VoIP platforms (Rocket.Chat, Matrix servers).

Do not use this merely because a project supports Docker, Vercel, Cloudflare Workers, or server deployment. Use the repo's primary user intent first.

Common confusions:

- self-hosted RSS readers, read-later, ebook/manga, and reading libraries belong in `reading-notes`,
- self-hosted note or PKM systems belong in `reading-notes`,
- self-hosted cloud drives, WebDAV tools, file sharing, R2/S3 browsers, and transfer tools belong in `cloud-drive-transfer-sync`,
- Cloudflare tunnel, proxy, relay, edge gateway, and proxy subscription projects belong in `cloudflare-network-proxy`,
- AI-agent services belong first in the relevant AI bucket if agent behavior is the main product,
- self-hosted media library servers (Plex/Jellyfin-style) belong in `self-hosted`; player clients and front-ends belong in `media-players`.

### `cloudflare-network-proxy`

Definition:

`Cloudflare Workers and tunnels plus general proxy-network tooling: reverse proxies, subscription and proxy panels, edge gateways, relays, and proxy-network clients.`

The bucket name is historical: it kept the name it launched with, but the definition is the general proxy-network lane, not a Cloudflare-exclusive one. Do not read the name as a scope limit — proxy clients, tunnels, and subscription panels belong here whether or not they touch Cloudflare.

Use this when the repository is mainly about network transport, proxying, tunneling, edge gateways, subscription conversion, acceleration, mirror gateways, or operating Cloudflare as a network layer.

Belongs here:

- Cloudflare Worker or Pages proxy projects,
- Cloudflare Tunnel managers and dashboards,
- reverse proxies and edge gateways,
- VLESS, Trojan, Shadowsocks, Clash, Mihomo, Xray, and subscription-panel tools,
- network relay, mirror, acceleration, and transparent proxy clients,
- Cloudflare-oriented DNS, gateway, or edge transport utilities.

Do not use this for every project that happens to deploy on Cloudflare. Cloudflare as a hosting platform is not enough.

Common confusions:

- Cloudflare-hosted file managers, R2 browsers, WebDAV, and storage tools belong in `cloud-drive-transfer-sync`,
- Cloudflare-hosted ordinary web apps belong in `self-hosted` or their functional bucket,
- Cloudflare-hosted news or publication projects belong in `dev-tools` when publishing is the main workflow,
- terminal or SSH clients belong in `terminal`,
- Windows-only proxy clients can use `windows-tools` as a secondary list only when Windows integration is a major retrieval reason.

## Formal rules for fallback lists

### `everything-else`

Definition:

`Fallback bucket for repos that fit no specialized list: clear-purpose software with no specialist home, and ambiguous or under-read repos still awaiting review.`

Use this as the single final bucket when no specialized list fits after reading the README. There is no separate holding list: repos that are not yet understood and repos that are understood-but-unspecialized both land here, and the ledger `reason` records which case applies.

Belongs here:

- useful apps or utilities with a clear purpose but no stable specialist home,
- cross-domain tools that would make several specific buckets noisier,
- ambiguous, experimental, or under-read repos needing later review,
- small products where the main retrieval question is simply "useful software".

Do not use this as a convenience bucket for low-confidence work on repos with a clear function — choose the closest specific bucket and record uncertainty in the ledger.

Common confusions:

- ordinary desktop GUI apps belong in `desktop-apps`,
- developer tools belong in `dev-tools`,
- Windows system utilities belong in `windows-tools`,
- deployable services belong in `self-hosted`,
- revisit `everything-else` entries during maintenance passes; classify repos that have become understandable since the last pass.

## Formal rules for languages, frameworks, and data lists

### `frameworks-libraries`

Definition:

`Web and application frameworks, UI/component libraries, front-end libraries, programming languages, compilers, runtimes, and developer libraries.`

Use this when the repo is a building block developers depend on — a framework, library, language, or runtime — rather than an end-user tool or a workflow utility.

Belongs here:

- web front- and back-end frameworks (react, vue, bootstrap, django, gin, next.js),
- UI/component libraries, CSS frameworks, template engines,
- chart, map, whiteboard, and data-visualization libraries (d3, mermaid, Leaflet),
- programming languages, compilers, runtimes, and language toolchains (go, TypeScript, rust, node, bun).

Do not use this for developer utilities that ship as tools (editors, CLIs) — those belong in `dev-tools` or `terminal`.

Common confusions:

- if it is a tool that ships as a product (editor, CLI, local utility), use `dev-tools` or `terminal`,
- if it is an AI end-user application built on a framework, use `ai-agents`,
- if it is data or model infrastructure (databases, ML engines), use `data-ml-tools`.

### `data-ml-tools`

Definition:

`Data science and machine learning frameworks, model inference infrastructure, databases, search engines, key-value and vector stores, ORMs, and data libraries.`

Use this when the repo is data or model infrastructure: frameworks, inference engines, model releases, or data stores.

Belongs here:

- ML frameworks and model weights (tensorflow, transformers, DeepSeek-R1),
- inference engines and local model runners (vllm, ollama, llama.cpp, exo),
- data science libraries (pandas, sktime, pyod),
- databases, search engines, key-value/vector stores, ORMs, and drivers (redis, elasticsearch, ClickHouse, milvus, prisma).

Do not use this for AI end-user apps (use `ai-agents`) or data pipelines that ship as deployable services (use `self-hosted`).

Common confusions:

- if it is an end-user AI application or agent product, use `ai-agents`,
- if it is a deployable data pipeline or database service the user runs, use `self-hosted`,
- if it is a general web/app framework rather than data or ML infrastructure, use `frameworks-libraries`.

## Formal rules for creative, business, scraping, and security lists

### `game-3d-creative`

Definition:

`Games, game engines and SDKs, 3D modeling and rendering, emulators, firmware, and generative creative tools.`

Use this when the repo is a game, engine, 3D/creative tool, emulator, custom firmware, or generative creative application.

Belongs here:

- games and game source releases (DOOM),
- game engines and SDKs (godot, bevy, source-sdk),
- 3D modeling/rendering (blender, openscad), emulators (RPCS3), custom firmware (Atmosphere),
- generative creative tools (stable-diffusion-webui, manim, freemocap).

Common confusions:

- if the main workflow is consuming media (watching, listening, browsing), use `media-players`,
- if it is a design asset (font, icon, theme) rather than an application, use `design-assets`,
- if it is a general desktop editing application, use `desktop-apps`.

### `design-assets`

Definition:

`Fonts, icon sets, color themes, and reusable design resources.`

Use this for assets designers and developers drop into their work (FiraCode, Inter, Font-Awesome, catppuccin). Not for design applications — those belong in `desktop-apps` or `game-3d-creative`.

Common confusions:

- if it is an application that makes or edits designs, use `desktop-apps` or `game-3d-creative`,
- if it is a developer tool that happens to include assets, use `dev-tools`.

### `business-apps`

Definition:

`Business and industry software: CMS, invoicing, scheduling, e-commerce, BI, and support platforms.`

Use this for software built around a business workflow (keystonejs, invoiceninja, cal.diy, discourse, metabase, mall). Desktop clients of such platforms stay in `desktop-apps`; deployable instances can pair `self-hosted`.

Common confusions:

- if it is the desktop client of a business platform rather than the platform itself, use `desktop-apps`,
- if the deployable instance is the product, pair or prefer `self-hosted`.

### `web-scraping-data-collection`

Definition:

`Scrapers, data collection APIs, and browser automation for data acquisition.`

Use this when the repo acquires data from the web (firecrawl, crawl4ai, instagrapi). Do not put security tooling here — it belongs in `security-pentest-tools`.

Common confusions:

- if the tool is for downloading media files rather than harvesting data, use `downloaders`,
- if it is security/OSINT/penetration tooling, use `security-pentest-tools`,
- if it is a client library/SDK whose main job is fetching data from a platform API (instagrapi, goinsta), it belongs here — `frameworks-libraries` is for general-purpose building blocks, not platform-data clients.

### `security-pentest-tools`

Definition:

`Security tooling: OSINT, penetration testing, reverse engineering, and exploit frameworks.`

Use this when the repo is security research or offensive tooling (sherlock, bettercap, x64dbg, cutter, PayloadsAllTheThings). Separated from scraping because the two retrieval questions differ.

Common confusions:

- if it acquires data without a security intent, use `web-scraping-data-collection`,
- if it is a developer debugger or analysis tool without offensive intent, use `dev-tools`.
