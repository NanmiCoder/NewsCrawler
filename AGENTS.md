# Repository Guidelines

This repository bundles Python crawlers, a FastAPI service, and a Vue-based UI. Keep updates modular, align with existing platform adapters, and document assumptions so other agents can continue your work quickly.

## Project Structure & Module Organization
- Core crawlers live in `news_crawler/` with platform-specific packages (`wechat_news/`, `toutiao_news/`, etc.); mirror existing adapter patterns when adding a site.
- Shared automation helpers live in `libs/` and are reused by both news and video modules.
- Web assets sit under `news-extractor-ui/`: `backend/app/` hosts FastAPI adapters and services, while `frontend/src/` contains Vue components, stores, and TypeScript types.
- Video downloaders live in `video_crawler/`, and generated artifacts land in `data/`. Keep static screenshots and docs under `static/`.

## Build, Test, and Development Commands
- `uv sync` — install Python dependencies defined in the root `pyproject.toml`.
- `uv run call_example.py` — execute the end-to-end crawler sample; update when adding new platforms.
- `cd news-extractor-ui/backend && uv sync && uv run run.py` — start the FastAPI backend on port 8000.
- `cd news-extractor-ui/frontend && npm install && npm run dev` — launch the Vue dev server (port 3000); `npm run build` performs a production build.
- `uv run pytest` — run Python tests; scope with `-k` to target a single platform module.

## Coding Style & Naming Conventions
Use PEP 8 with 4-space indentation for Python, keeping crawler classes named `*Crawler` and aligning method names with the verbs already in each module (e.g., `fetch_detail`). Reuse existing dataclass or Pydantic models where possible. For the frontend, follow the Vue `<script setup lang="ts">` pattern, use PascalCase component filenames in `src/components/`, and camelCase composables/services. Keep configuration values in `.env` files and document new keys in the README.

## Testing Guidelines
Prefer `pytest` for backend and crawler coverage; place new tests beside the module (e.g., `news_crawler/naver_news/test/test_parser.py`) and name functions `test_<behavior>()`. For the API, add lightweight integration checks under `news-extractor-ui/backend/tests/` if you introduce new endpoints. Frontend changes that affect rendering should include a `npm run build` sanity check and, when practical, a screenshot in the PR to confirm UI output.

## Commit & Pull Request Guidelines
Follow the existing Conventional Commit style (`feat:`, `fix:`, `docs:`, etc.) in present tense and keep messages under ~72 characters. Each pull request should link to related issues, outline reproduction steps or crawler targets exercised, and attach before/after evidence for UI or output changes. Ensure the branch is rebased onto the latest `main`, note any skipped tests with rationale, and request review from maintainers responsible for the touched platform or service.

## Security & Configuration Tips
Never commit API keys or cookies; load them via environment variables and reference them through configuration helpers. When scraping, respect rate limits defined in adapters and add sensible defaults for new platforms. Confirm that new dependencies are pinned in the relevant `pyproject.toml` or `package.json` so reproducible builds remain intact.
