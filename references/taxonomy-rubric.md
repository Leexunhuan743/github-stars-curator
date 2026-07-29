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
- [Formal rules for publishing lists](#formal-rules-for-publishing-lists)
- [Formal rules for deployment and network lists](#formal-rules-for-deployment-and-network-lists)
- [Formal rules for fallback lists](#formal-rules-for-fallback-lists)

## Starter lists

- `downloaders`: download managers, media downloaders, torrent clients, stream grabbers, and automated download tools
- `cloud-drive-transfer-sync`: cloud drives, WebDAV and storage browsers, file transfer, device sending, remote copy, and folder sync tools
- `clipboard-tools`: clipboard managers, clipboard history, pasteboard tools, cross-device copy/paste, and clipboard synchronization utilities
- `music-players`: music players, streaming music clients, lyric-focused players, and music listening apps
- `image-viewers`: image viewers, photo browsers, comic/image browsing apps, gallery clients, and image preview tools
- `video-players`: video players, streaming video clients, danmu viewers, and watch-focused apps
- `agent-harnesses`: agent harnesses, coding runtimes, ADEs, and multi-agent workspaces
- `agent-skills-mcp`: agent skills, MCP servers, plugins, code intelligence, repo knowledge graphs, and AI content-generation tools
- `ai-agents`: AI agents, agent platforms, autonomous workflows, and agent-oriented applications
- `dev-tools`: developer tools, editors, local engineering utilities, and coding workflow tools
- `terminal`: terminal apps, TUIs, CLI-first utilities, SSH clients, and remote shell tools
- `windows-tools`: Windows utilities, shell extensions, Explorer integrations, keymaps, thumbnails, and system tools
- `desktop-apps`: general user-facing desktop apps, clipboard managers, chat export and archive tools, native utilities, and everyday GUI software
- `reading-apps`: RSS readers, desktop reading apps, document readers, and subscription-based reading workflows
- `pdf-document-tools`: PDF and document readers, editors, converters, OCR/compression tools, document viewers, and document-to-Markdown or AI-prep utilities
- `note-software`: note-taking apps, markdown knowledge tools, PKM systems, scratchpads, and personal knowledge software
- `selfhosted-reading-bookmarks`: self-hosted reading libraries, read-later services, bookmark archives, and manga or ebook servers
- `references-guides`: reference collections, awesome lists, guides, tutorials, datasets, books, and learning resources
- `publishing-site-pipelines`: doc-to-site, book-generation, static publishing, content-to-website, and automated publication pipelines
- `self-hosted`: deployable self-hosted services, home-lab apps, private web tools, APIs, and personal server software
- `cloudflare-network-proxy`: Cloudflare Workers, tunnels, reverse proxies, subscription and proxy panels, edge gateways, relays, and proxy-network clients
- `general-software`: broad useful software that is understandable but not better captured by a stable specialized bucket
- `misc-explore`: temporary holding list for ambiguous, under-read, experimental, or still-learning repos that need later review

## Core front-rank buckets

These twenty-three buckets are the front rank of this skill's taxonomy. When a repo fits one of them cleanly, prefer assigning it there before reaching for ad hoc or legacy buckets. The last two buckets are still formal, but they are controlled fallbacks rather than preferred destinations.

1. `downloaders`
2. `cloud-drive-transfer-sync`
3. `clipboard-tools`
4. `music-players`
5. `image-viewers`
6. `video-players`
7. `agent-harnesses`
8. `agent-skills-mcp`
9. `ai-agents`
10. `dev-tools`
11. `terminal`
12. `windows-tools`
13. `desktop-apps`
14. `reading-apps`
15. `pdf-document-tools`
16. `note-software`
17. `selfhosted-reading-bookmarks`
18. `references-guides`
19. `publishing-site-pipelines`
20. `self-hosted`
21. `cloudflare-network-proxy`
22. `general-software`
23. `misc-explore`

Ordering principle:

1. File movement, acquisition, and clipboard flow: `downloaders`, `cloud-drive-transfer-sync`, `clipboard-tools`.
2. Media consumption: `music-players`, `image-viewers`, `video-players`.
3. AI, development, terminal, local system, and desktop app workflows: `agent-harnesses`, `agent-skills-mcp`, `ai-agents`, `dev-tools`, `terminal`, `windows-tools`, `desktop-apps`.
4. Reading, document tooling, notes, self-hosted reading libraries, and reference material: `reading-apps`, `pdf-document-tools`, `note-software`, `selfhosted-reading-bookmarks`, `references-guides`.
5. Publishing, self-hosted services, and network infrastructure: `publishing-site-pipelines`, `self-hosted`, `cloudflare-network-proxy`.
6. Controlled fallbacks: `general-software`, then `misc-explore`.

## How to choose lists

Use the smallest set of lists that makes the repo easy to find later.

Good questions:

- What is this repo mainly for?
- What workflow would make me go looking for it again?
- Is it a product, a library, a dataset, a reading list, a service, or a desktop tool?
- Does it belong to a special retrieval lane like `self-hosted`, `reading-apps`, or `desktop-apps`?

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

If still unsure, place it in `misc-explore` and record the uncertainty in the ledger.

## Formal rules for development-related lists

Do not create a separate `editors-ide` bucket. Traditional editors and local coding tools should be handled inside the existing development taxonomy.

### `agent-harnesses`

Definition:

`Agent harnesses, coding runtimes, ADEs, and multi-agent workspaces.`

Use this when the repository is mainly the environment for running or supervising coding agents.

Belongs here:

- coding-agent harnesses,
- ADEs and agent workspaces,
- agent runtimes and agent shells,
- multi-agent execution environments,
- coding terminals designed around agent loops.

Do not put these here:

- MCP servers,
- skills or plugin packs,
- ordinary editors,
- general local dev utilities.

Common confusions:

- if it mainly adds capabilities to another agent, use `agent-skills-mcp`,
- if it is mainly a traditional developer utility, use `dev-tools`,
- if it is mainly an agent-facing product or workflow app rather than the runtime itself, consider `ai-agents`.

### `agent-skills-mcp`

Definition:

`Agent skills, MCP servers, plugins, code intelligence, repo knowledge graphs, and AI content-generation tools.`

Use this when the repository mainly extends what an agent can do rather than acting as the primary runtime, when it provides code intelligence or repo knowledge capabilities, or when it is primarily an AI content-generation capability.

Belongs here:

- MCP servers,
- skills,
- agent plugins,
- capability bridges,
- tool integrations for Codex, Claude Code, Cursor, and similar clients.
- code graphs, graph RAG, repo knowledge graphs, and codebase indexing tools,
- repository understanding, code search, and knowledge retrieval systems designed for AI or agent workflows,
- AI tools for PPT, image, writing, research, report, and content generation.

Do not put these here:

- full agent harnesses,
- standard editors,
- general-purpose engineering tools with no agent-facing integration layer.

Common confusions:

- runtime shells and ADEs belong in `agent-harnesses`,
- non-agent developer tools belong in `dev-tools`,
- broad end-user agent products can belong in `ai-agents`.

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

- runtimes and coding harnesses belong in `agent-harnesses`,
- capabilities and integrations belong in `agent-skills-mcp`,
- AI content-generation tools belong in `agent-skills-mcp`.

### `dev-tools`

Use this as the default bucket for traditional development tools. This is where editors, documentation browsers, code-processing tools, and local engineering helpers should go when they are not primarily AI-agent infrastructure.

Belongs here:

- editors and editor-adjacent tools,
- offline documentation browsers,
- code and text processing tools,
- local workflow helpers for engineering work,
- developer-facing utilities that are not primarily note-taking products.

If a repo is development-related, classify it in this order:

1. If it is mainly an environment for running agents, use `agent-harnesses`.
2. If it mainly extends agent capabilities, use `agent-skills-mcp`.
3. Otherwise, default to `dev-tools`.

For text editors, use this rule:

- development-oriented text editors go to `dev-tools`,
- note-taking or markdown knowledge editors go to `note-software`,
- general desktop writing tools go to `desktop-apps`.

Common confusions:

- if the product is really a note system, use `note-software`,
- if the product is a broad desktop app with no clear dev workflow focus, use `desktop-apps`,
- if the repo is clearly agent-runtime or MCP related, use the AI buckets above.

## Formal rules for reading and document lists

Use four reading and document-oriented lanes:

1. `reading-apps` for subscription reading and ordinary desktop reading tools,
2. `pdf-document-tools` for PDF/document editing, conversion, OCR, compression, viewing components, and document-to-Markdown or AI-prep pipelines,
3. `note-software` for notes, markdown knowledge, and PKM-style tools,
4. `selfhosted-reading-bookmarks` for self-hosted reading libraries, read-later services, and bookmark archives.

Do not create a broad catch-all reading bucket beyond these lanes.

### `reading-apps`

Definition:

`RSS readers, desktop reading apps, document readers, and subscription-based reading workflows.`

Use this when the main workflow is reading content rather than writing notes or managing a personal knowledge base.

Belongs here:

- RSS and feed readers,
- newsletter and subscription readers,
- ebook readers and document-reading apps,
- desktop reading apps,
- single-user manga or novel readers when the main experience is simply reading.

Do not use this for note-taking systems, PKM tools, PDF/document processing suites, or self-hosted reading archives unless reading is clearly the primary standalone desktop workflow.

Common confusions:

- if the main workflow is collecting or structuring personal knowledge, use `note-software`,
- if the main workflow is editing, converting, OCR-ing, compressing, preparing, or programmatically viewing PDF/document files, use `pdf-document-tools`,
- if the main value is self-hosted read-later, archive, or library management, use `selfhosted-reading-bookmarks`,
- if it is a writing-first tool rather than a reading-first tool, do not force it here.

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

Use this alongside `reading-apps` when the app is both a user-facing document reader and a PDF/document toolkit. Use it alongside `dev-tools` when the repo is a developer-facing document conversion library.

Do not use this for general note-taking, plain Markdown editors, static-site publishing systems, or ordinary ebook/RSS readers unless PDF/document handling is the main retrieval intent.

Common confusions:

- if the main workflow is simply reading ebooks, feeds, or articles, use `reading-apps`,
- if the main workflow is capturing notes or managing knowledge, use `note-software`,
- if the main workflow is publishing documents to a website, book, deck, or public report, use `publishing-site-pipelines`,
- if the main workflow is downloading files and document handling is incidental, use `downloaders`.

### `note-software`

Definition:

`Note-taking apps, markdown knowledge tools, PKM systems, scratchpads, and personal knowledge software.`

Use this when the main workflow is capturing, organizing, linking, or managing knowledge.

Belongs here:

- note-taking apps,
- markdown knowledge tools,
- PKM systems,
- memo and scratchpad apps,
- personal knowledge bases.

Use this bucket for markdown-first knowledge tools as well as broader note-taking and PKM systems.

Common confusions:

- if the main experience is reading rather than capturing and organizing knowledge, use `reading-apps`,
- if the main workflow is PDF/document conversion, OCR, compression, or repair, use `pdf-document-tools`,
- if the repo is a self-hosted reading archive rather than a note system, use `selfhosted-reading-bookmarks`,
- if it is mainly a developer editor or documentation browser, use `dev-tools`.

### `selfhosted-reading-bookmarks`

Definition:

`Self-hosted reading libraries, read-later services, bookmark archives, and manga or ebook servers.`

Use this when the repo is mainly a self-hosted archive or library for reading-oriented content.

Belongs here:

- self-hosted read-later services,
- bookmark archives,
- manga, comic, and ebook servers,
- self-hosted reading libraries and bookshelf apps.

Do not use this for ordinary desktop readers or note-taking tools unless self-hosting and archive management are the primary value.

Common confusions:

- single-user desktop readers usually belong in `reading-apps`,
- PKM and note tools belong in `note-software`,
- generic self-hosted services with no reading/archive workflow should stay in `self-hosted`.

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

- if the main product is listening, use `music-players`,
- if the main product is watching, use `video-players`,
- if the main product is a cloud-drive, transfer, or sync manager, use `cloud-drive-transfer-sync`.

### `music-players`

Definition:

`Music players, streaming music clients, lyric-focused players, and music listening apps.`

Use this when the main workflow is listening to music.

Belongs here:

- local music players,
- streaming music clients,
- desktop lyric players,
- self-hosted music playback clients,
- album, playlist, and library-oriented music apps.

Do not use this for music tag editors, sync/download tools, or media services unless playback is the main product surface.

Common confusions:

- if download is the real value, use `downloaders`,
- if the main workflow is browsing photos, illustrations, galleries, or image files, use `image-viewers`,
- if the app is a broader file, cloud-media, transfer, or sync hub, consider pairing or preferring `cloud-drive-transfer-sync`,
- if it is mainly a tag editor or library utility without a real listening surface, do not force it here.

### `image-viewers`

Definition:

`Image viewers, photo browsers, comic/image browsing apps, gallery clients, and image preview tools.`

Use this when the main workflow is browsing, previewing, or viewing image-first content.

Belongs here:

- local image viewers and photo browsers,
- comic, manga, archive, or folder image viewers when image browsing is the main app experience,
- gallery and illustration clients such as Pixiv-style browsers,
- image preview tools and lightweight image format viewers,
- apps whose video support is secondary to an image-viewing product.

Do not use this for full image editors, drawing tools, prompt collections, image-generation skills, or gallery/media downloaders unless viewing is the primary user intent.

Common confusions:

- if the main workflow is editing or creating images, use `desktop-apps`, `general-software`, or a more specific future bucket,
- if the main workflow is downloading galleries/media, use `downloaders`,
- if the main workflow is reading ebooks, PDFs, or text-heavy documents, use `reading-apps`,
- if the app is primarily a watch-focused video player with optional image support, use `video-players`.

### `video-players`

Definition:

`Video players, streaming video clients, danmu viewers, and watch-focused apps.`

Use this when the main workflow is watching video.

Belongs here:

- local video players,
- streaming video clients,
- danmu players,
- watch-first anime, Bilibili, or media frontends,
- playback-focused apps with subtitles, tracks, and watch history.

Do not use this for pure download tools, resource aggregators, or general-purpose site helpers unless watching is the primary user intent.

Common confusions:

- if the real workflow is acquisition or scraping, use `downloaders`,
- if the product is primarily an image/photo/comic viewer with optional video support, use `image-viewers`,
- if the app is mainly a site helper or utility, use a more fitting broad bucket such as `general-software`,
- if the product mainly manages storage, transfer, or sync rather than playback, use `cloud-drive-transfer-sync`.

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

- if the repo is primarily a coding-agent runtime, use `agent-harnesses`,
- if the repo is primarily a broad remote-management or network product rather than a terminal workflow, consider `general-software` or a more specific networking bucket,
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
- if it is mainly notes, markdown knowledge, or PKM, use `note-software`,
- if it is useful software but not specifically a desktop app or native GUI utility, use `general-software`.

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

- if it is a tool for writing, publishing, or hosting docs, use `publishing-site-pipelines`,
- if it is a note-taking or PKM product, use `note-software`,
- if it is a developer utility with reference features, use `dev-tools`,
- if the repo is the knowledge itself rather than a tool that manages knowledge, use `references-guides`.

## Formal rules for publishing lists

### `publishing-site-pipelines`

Definition:

`Doc-to-site, book-generation, static publishing, content-to-website, and automated publication pipelines.`

Use this when the repository's main workflow is turning source material into a publishable site, book, documentation portal, generated report, or recurring public content feed.

Belongs here:

- doc-to-site and markdown-to-site pipelines,
- book, ebook, PDF, or long-form publication generators,
- static-site publishing workflows,
- content-to-website systems,
- automated news, report, or knowledge-site publication pipelines,
- tools that prepare parsed documents, notes, or generated content for web publishing.

Do not use this for raw reference material, ordinary note-taking apps, coding-agent harnesses, or general CMS-like apps unless publishing is the main retrieval intent.

Common confusions:

- if the repo is mainly the content itself, use `references-guides`,
- if the repo is mainly a personal note or PKM app, use `note-software`,
- if the repo is mainly an agent or research product that can produce reports, use `ai-agents` or `agent-skills-mcp`,
- if the repo is a deployable web service with publishing as only one feature, use `self-hosted` plus the closest functional bucket.

## Formal rules for deployment and network lists

### `self-hosted`

Definition:

`Deployable self-hosted services, home-lab apps, private web tools, APIs, and personal server software.`

Use this when the repository is mainly something the user can run as their own service, server, API, private web app, NAS app, or home-lab tool, and no more specific front-rank bucket captures the core workflow better.

Belongs here:

- self-hosted web services,
- home-lab and NAS-friendly apps,
- private APIs and backend services,
- personal dashboards and server-side tools,
- deployable utilities intended to replace a hosted SaaS,
- Docker-ready or single-binary services where the service itself is the product.

Do not use this merely because a project supports Docker, Vercel, Cloudflare Workers, or server deployment. Use the repo's primary user intent first.

Common confusions:

- self-hosted RSS readers and ordinary feed readers belong in `reading-apps`,
- self-hosted read-later, bookmark, manga, comic, or ebook libraries belong in `selfhosted-reading-bookmarks`,
- self-hosted note or PKM systems belong in `note-software`,
- self-hosted cloud drives, WebDAV tools, file sharing, R2/S3 browsers, and transfer tools belong in `cloud-drive-transfer-sync`,
- Cloudflare tunnel, proxy, relay, edge gateway, and proxy subscription projects belong in `cloudflare-network-proxy`,
- AI-agent services belong first in the relevant AI bucket if agent behavior is the main product.

### `cloudflare-network-proxy`

Definition:

`Cloudflare Workers, tunnels, reverse proxies, subscription and proxy panels, edge gateways, relays, and proxy-network clients.`

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
- Cloudflare-hosted news or publication projects belong in `publishing-site-pipelines` when publishing is the main workflow,
- terminal or SSH clients belong in `terminal`,
- Windows-only proxy clients can use `windows-tools` as a secondary list only when Windows integration is a major retrieval reason.

## Formal rules for fallback lists

### `general-software`

Definition:

`Broad useful software that is understandable but not better captured by a stable specialized bucket.`

Use this as the final normal bucket for usable software whose purpose is clear, but whose workflow does not justify a dedicated list and does not fit an existing specialized list.

Belongs here:

- useful apps or utilities with a clear purpose but no stable specialist home,
- cross-domain tools that would make several specific buckets noisier,
- small products where the main retrieval question is simply "useful software",
- libraries or utilities that are not primarily developer workflow tools.

Do not use this when any specific bucket fits. It should be rare after the README has been read.

Common confusions:

- ordinary desktop GUI apps belong in `desktop-apps`,
- developer tools belong in `dev-tools`,
- Windows system utilities belong in `windows-tools`,
- deployable services belong in `self-hosted`,
- unclear repos belong in `misc-explore`, not `general-software`.

### `misc-explore`

Definition:

`Temporary holding list for ambiguous, under-read, experimental, or still-learning repos that need later review.`

Use this only when the repository cannot be classified confidently after reading the README and available metadata, or when it exposes a possible future taxonomy concept that has not yet earned a stable list.

Belongs here:

- ambiguous repos with incomplete or misleading READMEs,
- experimental projects whose main workflow is unclear,
- repos that appear to span many domains without a clear primary retrieval intent,
- one-off concepts being watched for future taxonomy growth,
- projects that require manual user judgment before final placement.

Do not use this as a convenience bucket for low-confidence work. If the repo has a clear function, choose the closest specific bucket and record uncertainty in the ledger.

Common confusions:

- use `general-software` when the repo is understandable but broad,
- use `misc-explore` when the repo is not yet understood well enough,
- revisit every `misc-explore` entry during maintenance passes before syncing list changes.
