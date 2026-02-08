# Codex Skills Catalog

This repo uses Codex skills installed under `$CODEX_HOME/skills` (typically `~/.codex/skills`).
This file is a quick, practical index. For authoritative instructions, open each skill's `SKILL.md`.

## How To Invoke

- Name the skill in your prompt (recommended): use `$skill-name`.
- Or describe a task that clearly matches the skill; Codex may auto-apply it.

## Installed Skills (Alphabetical)

### `ab-test-setup`
- What it is: When the user wants to plan, design, or implement an A/B test or experiment. Also use when the user mentions "A/B test," "split test," "experiment," "test this change," "variant copy," "multivariate test," or "hypothesis." For tracking implementation, see analytics-tracking.
- Use when: The task matches the description above.
- Invoke: Use `$ab-test-setup` in your prompt.
- Source: `$CODEX_HOME/skills/ab-test-setup/SKILL.md`

### `agent-md-refactor`
- What it is: Refactor bloated AGENTS.md, CLAUDE.md, or similar agent instruction files to follow progressive disclosure principles. Splits monolithic files into organized, linked documentation.
- Use when: The task matches the description above.
- Invoke: Use `$agent-md-refactor` in your prompt.
- Source: `$CODEX_HOME/skills/agent-md-refactor/SKILL.md`
- License: MIT

### `analytics-tracking`
- What it is: When the user wants to set up, improve, or audit analytics tracking and measurement. Also use when the user mentions "set up tracking," "GA4," "Google Analytics," "conversion tracking," "event tracking," "UTM parameters," "tag manager," "GTM," "analytics implementation," or "tracking plan." For A/B test measurement, see ab-test-setup.
- Use when: The task matches the description above.
- Invoke: Use `$analytics-tracking` in your prompt.
- Source: `$CODEX_HOME/skills/analytics-tracking/SKILL.md`

### `async-python-patterns`
- What it is: Master Python asyncio, concurrent programming, and async/await patterns for high-performance applications. Use when building async APIs, concurrent systems, or I/O-bound applications requiring non-blocking operations.
- Use when: The task matches the description above.
- Invoke: Use `$async-python-patterns` in your prompt.
- Source: `$CODEX_HOME/skills/async-python-patterns/SKILL.md`

### `audit-website`
- What it is: Audit websites for SEO, performance, security, technical, content, and 15 other issue cateories with 230+ rules using the squirrelscan CLI. Returns LLM-optimized reports with health scores, broken links, meta tag analysis, and actionable recommendations. Use to discover and asses website or webapp issues and health.
- Use when: Analyze a website's health; Debug technical SEO issues; Fix all of the issues mentioned above; Check for broken links
- Invoke: Use `$audit-website` in your prompt.
- Source: `$CODEX_HOME/skills/audit-website/SKILL.md`
- License: See LICENSE file in repository root

### `better-auth-best-practices`
- What it is: Skill for integrating Better Auth - the comprehensive TypeScript authentication framework.
- Use when: The task matches the description above.
- Invoke: Use `$better-auth-best-practices` in your prompt.
- Source: `$CODEX_HOME/skills/better-auth-best-practices/SKILL.md`

### `brainstorming`
- What it is: You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements and design before implementation.
- Use when: The task matches the description above.
- Invoke: Use `$brainstorming` in your prompt.
- Source: `$CODEX_HOME/skills/brainstorming/SKILL.md`

### `canvas-design`
- What it is: Create beautiful visual art in .png and .pdf documents using design philosophy. You should use this skill when the user asks to create a poster, piece of art, design, or other static piece. Create original visual designs, never copying existing artists' work to avoid copyright violations.
- Use when: The task matches the description above.
- Invoke: Use `$canvas-design` in your prompt.
- Source: `$CODEX_HOME/skills/canvas-design/SKILL.md`
- License: Complete terms in LICENSE.txt

### `commit-work`
- What it is: Create high-quality git commits: review/stage intended changes, split into logical commits, and write clear commit messages (including Conventional Commits). Use when the user asks to commit, craft a commit message, stage changes, or split work into multiple commits.
- Use when: The task matches the description above.
- Invoke: Use `$commit-work` in your prompt.
- Source: `$CODEX_HOME/skills/commit-work/SKILL.md`

### `competitor-alternatives`
- What it is: When the user wants to create competitor comparison or alternative pages for SEO and sales enablement. Also use when the user mentions 'alternative page,' 'vs page,' 'competitor comparison,' 'comparison page,' '[Product] vs [Product],' '[Product] alternative,' or 'competitive landing pages.' Covers four formats: singular alternative, plural alternatives, you vs competitor, and competitor vs competitor. Emphasizes deep research, modular content architecture, and varied section types beyond feature tables.
- Use when: The task matches the description above.
- Invoke: Use `$competitor-alternatives` in your prompt.
- Source: `$CODEX_HOME/skills/competitor-alternatives/SKILL.md`

### `content-strategy`
- What it is: When the user wants to plan a content strategy, decide what content to create, or figure out what topics to cover. Also use when the user mentions "content strategy," "what should I write about," "content ideas," "blog strategy," "topic clusters," or "content planning." For writing individual pieces, see copywriting. For SEO-specific audits, see seo-audit.
- Use when: The task matches the description above.
- Invoke: Use `$content-strategy` in your prompt.
- Source: `$CODEX_HOME/skills/content-strategy/SKILL.md`

### `copy-editing`
- What it is: When the user wants to edit, review, or improve existing marketing copy. Also use when the user mentions 'edit this copy,' 'review my copy,' 'copy feedback,' 'proofread,' 'polish this,' 'make this better,' or 'copy sweep.' This skill provides a systematic approach to editing marketing copy through multiple focused passes.
- Use when: The task matches the description above.
- Invoke: Use `$copy-editing` in your prompt.
- Source: `$CODEX_HOME/skills/copy-editing/SKILL.md`

### `create-auth-skill`
- What it is: Skill for creating auth layers in TypeScript/JavaScript apps using Better Auth.
- Use when: The task matches the description above.
- Invoke: Use `$create-auth-skill` in your prompt.
- Source: `$CODEX_HOME/skills/create-auth-skill/SKILL.md`

### `database-migration`
- What it is: Execute database migrations across ORMs and platforms with zero-downtime strategies, data transformation, and rollback procedures. Use when migrating databases, changing schemas, performing data transformations, or implementing zero-downtime deployment strategies.
- Use when: The task matches the description above.
- Invoke: Use `$database-migration` in your prompt.
- Source: `$CODEX_HOME/skills/database-migration/SKILL.md`

### `debugging-strategies`
- What it is: Master systematic debugging techniques, profiling tools, and root cause analysis to efficiently track down bugs across any codebase or technology stack. Use when investigating bugs, performance issues, or unexpected behavior.
- Use when: The task matches the description above.
- Invoke: Use `$debugging-strategies` in your prompt.
- Source: `$CODEX_HOME/skills/debugging-strategies/SKILL.md`

### `dependency-updater`
- What it is: Smart dependency management for any language. Auto-detects project type, applies safe updates automatically, prompts for major versions, diagnoses and fixes dependency issues.
- Use when: The task matches the description above.
- Invoke: Use `$dependency-updater` in your prompt.
- Source: `$CODEX_HOME/skills/dependency-updater/SKILL.md`
- License: MIT

### `deployment-pipeline-design`
- What it is: Design multi-stage CI/CD pipelines with approval gates, security checks, and deployment orchestration. Use when architecting deployment workflows, setting up continuous delivery, or implementing GitOps practices.
- Use when: Design CI/CD architecture; Implement deployment gates; Configure multi-environment pipelines; Establish deployment best practices
- Invoke: Use `$deployment-pipeline-design` in your prompt.
- Source: `$CODEX_HOME/skills/deployment-pipeline-design/SKILL.md`
- Notes: Deployment-oriented; expects project deploy config/scripts.

### `design-md`
- What it is: Analyze Stitch projects and synthesize a semantic design system into DESIGN.md files
- Use when: The task matches the description above.
- Invoke: Use `$design-md` in your prompt.
- Source: `$CODEX_HOME/skills/design-md/SKILL.md`

### `docker-expert`
- What it is: Docker containerization expert with deep knowledge of multi-stage builds, image optimization, container security, Docker Compose orchestration, and production deployment patterns. Use PROACTIVELY for Dockerfile optimization, container issues, image size problems, security hardening, networking, and orchestration challenges.
- Use when: The task matches the description above.
- Invoke: Use `$docker-expert` in your prompt.
- Source: `$CODEX_HOME/skills/docker-expert/SKILL.md`

### `e2e-testing-patterns`
- What it is: Master end-to-end testing with Playwright and Cypress to build reliable test suites that catch bugs, improve confidence, and enable fast deployment. Use when implementing E2E tests, debugging flaky tests, or establishing testing standards.
- Use when: The task matches the description above.
- Invoke: Use `$e2e-testing-patterns` in your prompt.
- Source: `$CODEX_HOME/skills/e2e-testing-patterns/SKILL.md`

### `email-sequence`
- What it is: When the user wants to create or optimize an email sequence, drip campaign, automated email flow, or lifecycle email program. Also use when the user mentions "email sequence," "drip campaign," "nurture sequence," "onboarding emails," "welcome sequence," "re-engagement emails," "email automation," or "lifecycle emails." For in-app onboarding, see onboarding-cro.
- Use when: The task matches the description above.
- Invoke: Use `$email-sequence` in your prompt.
- Source: `$CODEX_HOME/skills/email-sequence/SKILL.md`

### `executing-plans`
- What it is: Use when you have a written implementation plan to execute in a separate session with review checkpoints
- Use when: The task matches the description above.
- Invoke: Use `$executing-plans` in your prompt.
- Source: `$CODEX_HOME/skills/executing-plans/SKILL.md`

### `expo-api-routes`
- What it is: Guidelines for creating API routes in Expo Router with EAS Hosting
- Use when: The task matches the description above.
- Invoke: Use `$expo-api-routes` in your prompt.
- Source: `$CODEX_HOME/skills/expo-api-routes/SKILL.md`
- License: MIT

### `expo-deployment`
- What it is: Deploying Expo apps to iOS App Store, Android Play Store, web hosting, and API routes
- Use when: The task matches the description above.
- Invoke: Use `$expo-deployment` in your prompt.
- Source: `$CODEX_HOME/skills/expo-deployment/SKILL.md`
- License: MIT
- Notes: Deployment-oriented; expects project deploy config/scripts.

### `expo-tailwind-setup`
- What it is: Set up Tailwind CSS v4 in Expo with react-native-css and NativeWind v5 for universal styling
- Use when: The task matches the description above.
- Invoke: Use `$expo-tailwind-setup` in your prompt.
- Source: `$CODEX_HOME/skills/expo-tailwind-setup/SKILL.md`
- License: MIT

### `fastapi-templates`
- What it is: Create production-ready FastAPI projects with async patterns, dependency injection, and comprehensive error handling. Use when building new FastAPI applications or setting up backend API projects.
- Use when: The task matches the description above.
- Invoke: Use `$fastapi-templates` in your prompt.
- Source: `$CODEX_HOME/skills/fastapi-templates/SKILL.md`

### `finishing-a-development-branch`
- What it is: Use when implementation is complete, all tests pass, and you need to decide how to integrate the work - guides completion of development work by presenting structured options for merge, PR, or cleanup
- Use when: The task matches the description above.
- Invoke: Use `$finishing-a-development-branch` in your prompt.
- Source: `$CODEX_HOME/skills/finishing-a-development-branch/SKILL.md`

### `form-cro`
- What it is: When the user wants to optimize any form that is NOT signup/registration — including lead capture forms, contact forms, demo request forms, application forms, survey forms, or checkout forms. Also use when the user mentions "form optimization," "lead form conversions," "form friction," "form fields," "form completion rate," or "contact form." For signup/registration forms, see signup-flow-cro. For popups containing forms, see popup-cro.
- Use when: The task matches the description above.
- Invoke: Use `$form-cro` in your prompt.
- Source: `$CODEX_HOME/skills/form-cro/SKILL.md`

### `frontend-code-review`
- What it is: Trigger when the user requests a review of frontend files (e.g., `.tsx`, `.ts`, `.js`). Support both pending-change reviews and focused file reviews while applying the checklist rules.
- Use when: The task matches the description above.
- Invoke: Use `$frontend-code-review` in your prompt.
- Source: `$CODEX_HOME/skills/frontend-code-review/SKILL.md`

### `frontend-design`
- What it is: Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when the user asks to build web components, pages, artifacts, posters, or applications (examples include websites, landing pages, dashboards, React components, HTML/CSS layouts, or when styling/beautifying any web UI). Generates creative, polished code and UI design that avoids generic AI aesthetics.
- Use when: The task matches the description above.
- Invoke: Use `$frontend-design` in your prompt.
- Source: `$CODEX_HOME/skills/frontend-design/SKILL.md`
- License: Complete terms in LICENSE.txt

### `game-changing-features`
- What it is: Find 10x product opportunities and high-leverage improvements. Use when user wants strategic product thinking, mentions '10x', wants to find high-impact features, or says 'what would make this 10x better', 'product strategy', or 'what should we build next'.
- Use when: The task matches the description above.
- Invoke: Use `$game-changing-features` in your prompt.
- Source: `$CODEX_HOME/skills/game-changing-features/SKILL.md`

### `gh-address-comments`
- What it is: Help address review/issue comments on the open GitHub PR for the current branch using gh CLI; verify gh auth first and prompt the user to authenticate if not logged in.
- Use when: The task matches the description above.
- Invoke: Use `$gh-address-comments` in your prompt.
- Source: `$CODEX_HOME/skills/gh-address-comments/SKILL.md`
- Notes: Typically uses GitHub CLI (gh); may require auth.

### `gh-fix-ci`
- What it is: Use when a user asks to debug or fix failing GitHub PR checks that run in GitHub Actions; use `gh` to inspect checks and logs, summarize failure context, draft a fix plan, and implement only after explicit approval. Treat external providers (for example Buildkite) as out of scope and report only the details URL.
- Use when: The task matches the description above.
- Invoke: Use `$gh-fix-ci` in your prompt.
- Source: `$CODEX_HOME/skills/gh-fix-ci/SKILL.md`
- Notes: Typically uses GitHub CLI (gh); may require auth.

### `github-actions-templates`
- What it is: Create production-ready GitHub Actions workflows for automated testing, building, and deploying applications. Use when setting up CI/CD with GitHub Actions, automating development workflows, or creating reusable workflow templates.
- Use when: Automate testing and deployment; Build Docker images and push to registries; Deploy to Kubernetes clusters; Run security scans
- Invoke: Use `$github-actions-templates` in your prompt.
- Source: `$CODEX_HOME/skills/github-actions-templates/SKILL.md`

### `humanizer-zh`
- What it is: |
- Use when: The task matches the description above.
- Invoke: Use `$humanizer-zh` in your prompt.
- Source: `$CODEX_HOME/skills/humanizer-zh/SKILL.md`

### `launch-strategy`
- What it is: When the user wants to plan a product launch, feature announcement, or release strategy. Also use when the user mentions 'launch,' 'Product Hunt,' 'feature release,' 'announcement,' 'go-to-market,' 'beta launch,' 'early access,' 'waitlist,' or 'product update.' This skill covers phased launches, channel strategy, and ongoing launch momentum.
- Use when: The task matches the description above.
- Invoke: Use `$launch-strategy` in your prompt.
- Source: `$CODEX_HOME/skills/launch-strategy/SKILL.md`

### `marketing-ideas`
- What it is: When the user needs marketing ideas, inspiration, or strategies for their SaaS or software product. Also use when the user asks for 'marketing ideas,' 'growth ideas,' 'how to market,' 'marketing strategies,' 'marketing tactics,' 'ways to promote,' or 'ideas to grow.' This skill provides 139 proven marketing approaches organized by category.
- Use when: The task matches the description above.
- Invoke: Use `$marketing-ideas` in your prompt.
- Source: `$CODEX_HOME/skills/marketing-ideas/SKILL.md`

### `marketing-psychology`
- What it is: When the user wants to apply psychological principles, mental models, or behavioral science to marketing. Also use when the user mentions 'psychology,' 'mental models,' 'cognitive bias,' 'persuasion,' 'behavioral science,' 'why people buy,' 'decision-making,' or 'consumer behavior.' This skill provides 70+ mental models organized for marketing application.
- Use when: The task matches the description above.
- Invoke: Use `$marketing-psychology` in your prompt.
- Source: `$CODEX_HOME/skills/marketing-psychology/SKILL.md`

### `naming-analyzer`
- What it is: Suggest better variable, function, and class names based on context and conventions.
- Use when: The task matches the description above.
- Invoke: Use `$naming-analyzer` in your prompt.
- Source: `$CODEX_HOME/skills/naming-analyzer/SKILL.md`

### `native-data-fetching`
- What it is: Use when implementing or debugging ANY network request, API call, or data fetching. Covers fetch API, axios, React Query, SWR, error handling, caching strategies, offline support.
- Use when: Implementing API requests; Setting up data fetching (React Query, SWR); Debugging network failures; Implementing caching strategies
- Invoke: Use `$native-data-fetching` in your prompt.
- Source: `$CODEX_HOME/skills/native-data-fetching/SKILL.md`
- License: MIT

### `page-cro`
- What it is: When the user wants to optimize, improve, or increase conversions on any marketing page — including homepage, landing pages, pricing pages, feature pages, or blog posts. Also use when the user says "CRO," "conversion rate optimization," "this page isn't converting," "improve conversions," or "why isn't this page working." For signup/registration flows, see signup-flow-cro. For post-signup activation, see onboarding-cro. For forms outside of signup, see form-cro. For popups/modals, see popup-cro.
- Use when: The task matches the description above.
- Invoke: Use `$page-cro` in your prompt.
- Source: `$CODEX_HOME/skills/page-cro/SKILL.md`

### `paid-ads`
- What it is: When the user wants help with paid advertising campaigns on Google Ads, Meta (Facebook/Instagram), LinkedIn, Twitter/X, or other ad platforms. Also use when the user mentions 'PPC,' 'paid media,' 'ad copy,' 'ad creative,' 'ROAS,' 'CPA,' 'ad campaign,' 'retargeting,' or 'audience targeting.' This skill covers campaign strategy, ad creation, audience targeting, and optimization.
- Use when: The task matches the description above.
- Invoke: Use `$paid-ads` in your prompt.
- Source: `$CODEX_HOME/skills/paid-ads/SKILL.md`

### `paywall-upgrade-cro`
- What it is: When the user wants to create or optimize in-app paywalls, upgrade screens, upsell modals, or feature gates. Also use when the user mentions "paywall," "upgrade screen," "upgrade modal," "upsell," "feature gate," "convert free to paid," "freemium conversion," "trial expiration screen," "limit reached screen," "plan upgrade prompt," or "in-app pricing." Distinct from public pricing pages (see page-cro) — this skill focuses on in-product upgrade moments where the user has already experienced value.
- Use when: The task matches the description above.
- Invoke: Use `$paywall-upgrade-cro` in your prompt.
- Source: `$CODEX_HOME/skills/paywall-upgrade-cro/SKILL.md`

### `popup-cro`
- What it is: When the user wants to create or optimize popups, modals, overlays, slide-ins, or banners for conversion purposes. Also use when the user mentions "exit intent," "popup conversions," "modal optimization," "lead capture popup," "email popup," "announcement banner," or "overlay." For forms outside of popups, see form-cro. For general page conversion optimization, see page-cro.
- Use when: The task matches the description above.
- Invoke: Use `$popup-cro` in your prompt.
- Source: `$CODEX_HOME/skills/popup-cro/SKILL.md`

### `pricing-strategy`
- What it is: When the user wants help with pricing decisions, packaging, or monetization strategy. Also use when the user mentions 'pricing,' 'pricing tiers,' 'freemium,' 'free trial,' 'packaging,' 'price increase,' 'value metric,' 'Van Westendorp,' 'willingness to pay,' or 'monetization.' This skill covers pricing research, tier structure, and packaging strategy.
- Use when: The task matches the description above.
- Invoke: Use `$pricing-strategy` in your prompt.
- Source: `$CODEX_HOME/skills/pricing-strategy/SKILL.md`

### `product-marketing-context`
- What it is: When the user wants to create or update their product marketing context document. Also use when the user mentions 'product context,' 'marketing context,' 'set up context,' 'positioning,' or wants to avoid repeating foundational information across marketing tasks. Creates `.claude/product-marketing-context.md` that other marketing skills reference.
- Use when: The task matches the description above.
- Invoke: Use `$product-marketing-context` in your prompt.
- Source: `$CODEX_HOME/skills/product-marketing-context/SKILL.md`

### `programmatic-seo`
- What it is: When the user wants to create SEO-driven pages at scale using templates and data. Also use when the user mentions "programmatic SEO," "template pages," "pages at scale," "directory pages," "location pages," "[keyword] + [city] pages," "comparison pages," "integration pages," or "building many pages for SEO." For auditing existing SEO issues, see seo-audit.
- Use when: The task matches the description above.
- Invoke: Use `$programmatic-seo` in your prompt.
- Source: `$CODEX_HOME/skills/programmatic-seo/SKILL.md`

### `prompt-engineering-patterns`
- What it is: Master advanced prompt engineering techniques to maximize LLM performance, reliability, and controllability in production. Use when optimizing prompts, improving LLM outputs, or designing production prompt templates.
- Use when: The task matches the description above.
- Invoke: Use `$prompt-engineering-patterns` in your prompt.
- Source: `$CODEX_HOME/skills/prompt-engineering-patterns/SKILL.md`

### `python-performance-optimization`
- What it is: Profile and optimize Python code using cProfile, memory profilers, and performance best practices. Use when debugging slow Python code, optimizing bottlenecks, or improving application performance.
- Use when: The task matches the description above.
- Invoke: Use `$python-performance-optimization` in your prompt.
- Source: `$CODEX_HOME/skills/python-performance-optimization/SKILL.md`

### `python-testing-patterns`
- What it is: Implement comprehensive testing strategies with pytest, fixtures, mocking, and test-driven development. Use when writing Python tests, setting up test suites, or implementing testing best practices.
- Use when: The task matches the description above.
- Invoke: Use `$python-testing-patterns` in your prompt.
- Source: `$CODEX_HOME/skills/python-testing-patterns/SKILL.md`

### `ralph-tui-prd`
- What it is: Generate a Product Requirements Document (PRD) for ralph-tui task orchestration. Creates PRDs with user stories that can be converted to beads issues or prd.json for automated execution. Triggers on: create a prd, write prd for, plan this feature, requirements for, spec out.
- Use when: The task matches the description above.
- Invoke: Use `$ralph-tui-prd` in your prompt.
- Source: `$CODEX_HOME/skills/ralph-tui-prd/SKILL.md`

### `react-native-best-practices`
- What it is: Provides React Native performance optimization guidelines for FPS, TTI, bundle size, memory leaks, re-renders, and animations. Applies to tasks involving Hermes optimization, JS thread blocking, bridge overhead, FlashList, native modules, or debugging jank and frame drops.
- Use when: Debugging slow/janky UI or animations; Investigating memory leaks (JS or native); Optimizing app startup time (TTI); Reducing bundle or app size
- Invoke: Use `$react-native-best-practices` in your prompt.
- Source: `$CODEX_HOME/skills/react-native-best-practices/SKILL.md`
- License: MIT

### `react:components`
- What it is: Converts Stitch designs into modular Vite and React components using system-level networking and AST-based validation.
- Use when: The task matches the description above.
- Invoke: Use `$react:components` in your prompt.
- Source: `$CODEX_HOME/skills/react:components/SKILL.md`

### `receiving-code-review`
- What it is: Use when receiving code review feedback, before implementing suggestions, especially if feedback seems unclear or technically questionable - requires technical rigor and verification, not performative agreement or blind implementation
- Use when: The task matches the description above.
- Invoke: Use `$receiving-code-review` in your prompt.
- Source: `$CODEX_HOME/skills/receiving-code-review/SKILL.md`

### `reducing-entropy`
- What it is: Manual-only skill for minimizing total codebase size. Only activate when explicitly requested by user. Measures success by final code amount, not effort. Bias toward deletion.
- Use when: The task matches the description above.
- Invoke: Use `$reducing-entropy` in your prompt.
- Source: `$CODEX_HOME/skills/reducing-entropy/SKILL.md`

### `release-skills`
- What it is: Universal release workflow. Auto-detects version files and changelogs. Supports Node.js, Python, Rust, Claude Plugin, and generic projects. Use when user says "release", "发布", "new version", "bump version", "push", "推送".
- Use when: "release", "发布", "create release", "new version", "新版本"; "bump version", "update version", "更新版本"; "prepare release"; "push to remote" (with uncommitted changes)
- Invoke: Use `$release-skills` in your prompt.
- Source: `$CODEX_HOME/skills/release-skills/SKILL.md`

### `requesting-code-review`
- What it is: Use when completing tasks, implementing major features, or before merging to verify work meets requirements
- Use when: The task matches the description above.
- Invoke: Use `$requesting-code-review` in your prompt.
- Source: `$CODEX_HOME/skills/requesting-code-review/SKILL.md`

### `responsive-design`
- What it is: Implement modern responsive layouts using container queries, fluid typography, CSS Grid, and mobile-first breakpoint strategies. Use when building adaptive interfaces, implementing fluid layouts, or creating component-level responsive behavior.
- Use when: The task matches the description above.
- Invoke: Use `$responsive-design` in your prompt.
- Source: `$CODEX_HOME/skills/responsive-design/SKILL.md`

### `security-best-practices`
- What it is: Perform language and framework specific security best-practice reviews and suggest improvements. Trigger only when the user explicitly requests security best practices guidance, a security review/report, or secure-by-default coding help. Trigger only for supported languages (python, javascript/typescript, go). Do not trigger for general code review, debugging, or non-security tasks.
- Use when: The task matches the description above.
- Invoke: Use `$security-best-practices` in your prompt.
- Source: `$CODEX_HOME/skills/security-best-practices/SKILL.md`
- Notes: Use only for explicitly security-focused requests.

### `security-ownership-map`
- What it is: Analyze git repositories to build a security ownership topology (people-to-file), compute bus factor and sensitive-code ownership, and export CSV/JSON for graph databases and visualization. Trigger only when the user explicitly wants a security-oriented ownership or bus-factor analysis grounded in git history (for example: orphaned sensitive code, security maintainers, CODEOWNERS reality checks for risk, sensitive hotspots, or ownership clusters). Do not trigger for general maintainer lists or non-security ownership questions.
- Use when: The task matches the description above.
- Invoke: Use `$security-ownership-map` in your prompt.
- Source: `$CODEX_HOME/skills/security-ownership-map/SKILL.md`
- Notes: Use only for explicitly security-focused requests.

### `security-threat-model`
- What it is: Repository-grounded threat modeling that enumerates trust boundaries, assets, attacker capabilities, abuse paths, and mitigations, and writes a concise Markdown threat model. Trigger only when the user explicitly asks to threat model a codebase or path, enumerate threats/abuse paths, or perform AppSec threat modeling. Do not trigger for general architecture summaries, code review, or non-security design work.
- Use when: The task matches the description above.
- Invoke: Use `$security-threat-model` in your prompt.
- Source: `$CODEX_HOME/skills/security-threat-model/SKILL.md`
- Notes: Use only for explicitly security-focused requests.

### `seo-audit`
- What it is: When the user wants to audit, review, or diagnose SEO issues on their site. Also use when the user mentions "SEO audit," "technical SEO," "why am I not ranking," "SEO issues," "on-page SEO," "meta tags review," or "SEO health check." For building pages at scale to target keywords, see programmatic-seo. For adding structured data, see schema-markup.
- Use when: The task matches the description above.
- Invoke: Use `$seo-audit` in your prompt.
- Source: `$CODEX_HOME/skills/seo-audit/SKILL.md`

### `seo-geo`
- What it is: |
- Use when: The task matches the description above.
- Invoke: Use `$seo-geo` in your prompt.
- Source: `$CODEX_HOME/skills/seo-geo/SKILL.md`

### `session-handoff`
- What it is: Creates comprehensive handoff documents for seamless AI agent session transfers. Triggered when: (1) user requests handoff/memory/context save, (2) context window approaches capacity, (3) major task milestone completed, (4) work session ending, (5) user says 'save state', 'create handoff', 'I need to pause', 'context is getting full', (6) resuming work with 'load handoff', 'resume from', 'continue where we left off'. Proactively suggests handoffs after substantial work (multiple file edits, complex debugging, architecture decisions). Solves long-running agent context exhaustion by enabling fresh agents to continue with zero ambiguity.
- Use when: The task matches the description above.
- Invoke: Use `$session-handoff` in your prompt.
- Source: `$CODEX_HOME/skills/session-handoff/SKILL.md`

### `shadcn-ui`
- What it is: Complete shadcn/ui component library guide including installation, configuration, and implementation of accessible React components. Use when setting up shadcn/ui, installing components, building forms with React Hook Form and Zod, customizing themes with Tailwind CSS, or implementing UI patterns like buttons, dialogs, dropdowns, tables, and complex form layouts.
- Use when: Setting up a new project with shadcn/ui; Installing or configuring individual components; Building forms with React Hook Form and Zod validation; Creating accessible UI components (buttons, dialogs, dropdowns, sheets)
- Invoke: Use `$shadcn-ui` in your prompt.
- Source: `$CODEX_HOME/skills/shadcn-ui/SKILL.md`
- License: MIT

### `signup-flow-cro`
- What it is: When the user wants to optimize signup, registration, account creation, or trial activation flows. Also use when the user mentions "signup conversions," "registration friction," "signup form optimization," "free trial signup," "reduce signup dropoff," or "account creation flow." For post-signup onboarding, see onboarding-cro. For lead capture forms (not account creation), see form-cro.
- Use when: The task matches the description above.
- Invoke: Use `$signup-flow-cro` in your prompt.
- Source: `$CODEX_HOME/skills/signup-flow-cro/SKILL.md`

### `skill-creator`
- What it is: Guide for creating effective skills. This skill should be used when users want to create a new skill (or update an existing skill) that extends Codex's capabilities with specialized knowledge, workflows, or tool integrations.
- Use when: The task matches the description above.
- Invoke: Use `$skill-creator` in your prompt.
- Source: `$CODEX_HOME/skills/.system/skill-creator/SKILL.md`
- Notes: System skill used to manage Codex skills.

### `skill-installer`
- What it is: Install Codex skills into $CODEX_HOME/skills from a curated list or a GitHub repo path. Use when a user asks to list installable skills, install a curated skill, or install a skill from another repo (including private repos).
- Use when: The task matches the description above.
- Invoke: Use `$skill-installer` in your prompt.
- Source: `$CODEX_HOME/skills/.system/skill-installer/SKILL.md`
- Notes: System skill used to manage Codex skills.

### `social-content`
- What it is: When the user wants help creating, scheduling, or optimizing social media content for LinkedIn, Twitter/X, Instagram, TikTok, Facebook, or other platforms. Also use when the user mentions 'LinkedIn post,' 'Twitter thread,' 'social media,' 'content calendar,' 'social scheduling,' 'engagement,' or 'viral content.' This skill covers content creation, repurposing, and platform-specific strategies.
- Use when: The task matches the description above.
- Invoke: Use `$social-content` in your prompt.
- Source: `$CODEX_HOME/skills/social-content/SKILL.md`

### `sql-optimization-patterns`
- What it is: Master SQL query optimization, indexing strategies, and EXPLAIN analysis to dramatically improve database performance and eliminate slow queries. Use when debugging slow queries, designing database schemas, or optimizing application performance.
- Use when: The task matches the description above.
- Invoke: Use `$sql-optimization-patterns` in your prompt.
- Source: `$CODEX_HOME/skills/sql-optimization-patterns/SKILL.md`

### `stripe-integration`
- What it is: Implement Stripe payment processing for robust, PCI-compliant payment flows including checkout, subscriptions, and webhooks. Use when integrating Stripe payments, building subscription systems, or implementing secure checkout flows.
- Use when: The task matches the description above.
- Invoke: Use `$stripe-integration` in your prompt.
- Source: `$CODEX_HOME/skills/stripe-integration/SKILL.md`

### `subagent-driven-development`
- What it is: Use when executing implementation plans with independent tasks in the current session
- Use when: vs. Executing Plans (parallel session):**; Same session (no context switch); Fresh subagent per task (no context pollution); Two-stage review after each task: spec compliance first, then code quality
- Invoke: Use `$subagent-driven-development` in your prompt.
- Source: `$CODEX_HOME/skills/subagent-driven-development/SKILL.md`

### `supabase-postgres-best-practices`
- What it is: Postgres performance optimization and best practices from Supabase. Use this skill when writing, reviewing, or optimizing Postgres queries, schema designs, or database configurations.
- Use when: Writing SQL queries or designing schemas; Implementing indexes or query optimization; Reviewing database performance issues; Configuring connection pooling or scaling
- Invoke: Use `$supabase-postgres-best-practices` in your prompt.
- Source: `$CODEX_HOME/skills/supabase-postgres-best-practices/SKILL.md`
- License: MIT

### `systematic-debugging`
- What it is: Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes
- Use when: Test failures; Bugs in production; Unexpected behavior; Performance problems
- Invoke: Use `$systematic-debugging` in your prompt.
- Source: `$CODEX_HOME/skills/systematic-debugging/SKILL.md`

### `test-driven-development`
- What it is: Use when implementing any feature or bugfix, before writing implementation code
- Use when: Always:**; New features; Bug fixes; Refactoring
- Invoke: Use `$test-driven-development` in your prompt.
- Source: `$CODEX_HOME/skills/test-driven-development/SKILL.md`

### `theme-factory`
- What it is: Toolkit for styling artifacts with a theme. These artifacts can be slides, docs, reportings, HTML landing pages, etc. There are 10 pre-set themes with colors/fonts that you can apply to any artifact that has been creating, or can generate a new theme on-the-fly.
- Use when: The task matches the description above.
- Invoke: Use `$theme-factory` in your prompt.
- Source: `$CODEX_HOME/skills/theme-factory/SKILL.md`
- License: Complete terms in LICENSE.txt

### `typescript-advanced-types`
- What it is: Master TypeScript's advanced type system including generics, conditional types, mapped types, template literals, and utility types for building type-safe applications. Use when implementing complex type logic, creating reusable type utilities, or ensuring compile-time type safety in TypeScript projects.
- Use when: The task matches the description above.
- Invoke: Use `$typescript-advanced-types` in your prompt.
- Source: `$CODEX_HOME/skills/typescript-advanced-types/SKILL.md`

### `ui-ux-pro-max`
- What it is: UI/UX design intelligence. 50 styles, 21 palettes, 50 font pairings, 20 charts, 9 stacks (React, Next.js, Vue, Svelte, SwiftUI, React Native, Flutter, Tailwind, shadcn/ui). Actions: plan, build, create, design, implement, review, fix, improve, optimize, enhance, refactor, check UI/UX code. Projects: website, landing page, dashboard, admin panel, e-commerce, SaaS, portfolio, blog, mobile app, .html, .tsx, .vue, .svelte. Elements: button, modal, navbar, sidebar, card, table, form, chart. Styles: glassmorphism, claymorphism, minimalism, brutalism, neumorphism, bento grid, dark mode, responsive, skeuomorphism, flat design. Topics: color palette, accessibility, animation, layout, typography, font pairing, spacing, hover, shadow, gradient. Integrations: shadcn/ui MCP for component search and examples.
- Use when: Designing new UI components or pages; Choosing color palettes and typography; Reviewing code for UX issues; Building landing pages or dashboards
- Invoke: Use `$ui-ux-pro-max` in your prompt.
- Source: `$CODEX_HOME/skills/ui-ux-pro-max/SKILL.md`

### `using-git-worktrees`
- What it is: Use when starting feature work that needs isolation from current workspace or before executing implementation plans - creates isolated git worktrees with smart directory selection and safety verification
- Use when: The task matches the description above.
- Invoke: Use `$using-git-worktrees` in your prompt.
- Source: `$CODEX_HOME/skills/using-git-worktrees/SKILL.md`

### `using-superpowers`
- What it is: Use when starting any conversation - establishes how to find and use skills, requiring Skill tool invocation before ANY response including clarifying questions
- Use when: The task matches the description above.
- Invoke: Use `$using-superpowers` in your prompt.
- Source: `$CODEX_HOME/skills/using-superpowers/SKILL.md`

### `vercel-deploy`
- What it is: Deploy applications and websites to Vercel using the bundled `scripts/deploy.sh` claimable-preview flow. Use when the user asks to deploy to Vercel, wants a preview URL, or says to push a project live on Vercel.
- Use when: The task matches the description above.
- Invoke: Use `$vercel-deploy` in your prompt.
- Source: `$CODEX_HOME/skills/vercel-deploy/SKILL.md`
- Notes: Deployment-oriented; expects project deploy config/scripts.

### `vercel-react-best-practices`
- What it is: React and Next.js performance optimization guidelines from Vercel Engineering. This skill should be used when writing, reviewing, or refactoring React/Next.js code to ensure optimal performance patterns. Triggers on tasks involving React components, Next.js pages, data fetching, bundle optimization, or performance improvements.
- Use when: Writing new React components or Next.js pages; Implementing data fetching (client or server-side); Reviewing code for performance issues; Refactoring existing React/Next.js code
- Invoke: Use `$vercel-react-best-practices` in your prompt.
- Source: `$CODEX_HOME/skills/vercel-react-best-practices/SKILL.md`
- License: MIT

### `web-artifacts-builder`
- What it is: Suite of tools for creating elaborate, multi-component claude.ai HTML artifacts using modern frontend web technologies (React, Tailwind CSS, shadcn/ui). Use for complex artifacts requiring state management, routing, or shadcn/ui components - not for simple single-file HTML/JSX artifacts.
- Use when: The task matches the description above.
- Invoke: Use `$web-artifacts-builder` in your prompt.
- Source: `$CODEX_HOME/skills/web-artifacts-builder/SKILL.md`
- License: Complete terms in LICENSE.txt

### `webapp-testing`
- What it is: Toolkit for interacting with and testing local web applications using Playwright. Supports verifying frontend functionality, debugging UI behavior, capturing browser screenshots, and viewing browser logs.
- Use when: The task matches the description above.
- Invoke: Use `$webapp-testing` in your prompt.
- Source: `$CODEX_HOME/skills/webapp-testing/SKILL.md`
- License: Complete terms in LICENSE.txt

### `writing-plans`
- What it is: Use when you have a spec or requirements for a multi-step task, before touching code
- Use when: The task matches the description above.
- Invoke: Use `$writing-plans` in your prompt.
- Source: `$CODEX_HOME/skills/writing-plans/SKILL.md`

### `yeet`
- What it is: Use only when the user explicitly asks to stage, commit, push, and open a GitHub pull request in one flow using the GitHub CLI (`gh`).
- Use when: The task matches the description above.
- Invoke: Use `$yeet` in your prompt.
- Source: `$CODEX_HOME/skills/yeet/SKILL.md`
