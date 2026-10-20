# Domain Profiles: Market Any Company

The agent is domain agnostic. It markets whatever company you describe in a
Domain Profile: one JSON file with the company's facts, audiences, content
pillars, calls to action, hashtags, and brand colors. Generation, image
branding, and publishing all read from the profile. Nothing about any
specific company is baked into the engine.

Two ready examples ship in `services/engine-py/examples/`:

- `vo_technology_4splus.json`: an automotive ERP company.
- `nile_dental_clinic.json`: a dental clinic, deliberately a different
  industry and a different brand palette, proving the engine is generic.

## Fields

| Field | Required | What it does |
|---|---|---|
| `company_name` | yes | Shown on images, used in copy |
| `product_name` | no | Product or brand line used in copy and the image band |
| `industry` | no | Fallback headline and tagline |
| `tagline` | no | Image subline; string or `{"en": ..., "ar": ...}` |
| `key_facts` | no | Verified facts the posts are built from, per language lists |
| `value_props` | no | Benefit statements rotated into posts, per language |
| `audiences` | no | `[{name, kind: prospecting or customers, pains per language}]`; pains feed the pain pattern for that audience |
| `pillars` | no | `[{name, angle}]`; pillar names become image headlines and post themes |
| `ctas` | no | Calls to action per language; the first is used |
| `hashtags` | no | Appended to LinkedIn and Instagram variants |
| `brand` | no | Hex colors `bg, accent, text, muted`, plus optional `logo_path` |

Text fields accept a plain string, a list, or a per language object
(`{"en": [...], "ar": [...]}`). Write facts as complete, verified sentences:
posts quote them, and the claim guardrails still scan every generated post
for prohibited promises and unverified percentages.

## Run it on your machine

```bash
git clone https://github.com/AhmdArFa/AI-Marketing-Agent.git
cd AI-Marketing-Agent/services/engine-py
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

# 1) Drafts only: generates and prints the posts for your profile
python run_campaign.py --profile examples/vo_technology_4splus.json --language ar

# 2) Generate, render branded images, and export publish packages
python run_campaign.py --profile examples/vo_technology_4splus.json --language ar --approve
# packages land in outputs/<company>-post-N-<timestamp>/ with post.txt,
# variants.json and image.png

# 3) Or serve the API and use the web UI (apps/web, Campaign Studio tab,
#    paste your profile JSON there)
uvicorn app.main:app --port 8000
```

## Publishing channels

Selected with `--channel` (CLI) or the `channel` field of `POST /v1/publish`:

- `file_export` (default): writes the ready package to `outputs/`.
- `webhook`: POSTs the package (text, variants, base64 image) to
  `PUBLISH_WEBHOOK_URL`: a website CMS, a scheduler, or your own endpoint.
- `meta`: posts photo and caption to a Facebook Page via the Graph API when
  `META_PAGE_ID` and `META_ACCESS_TOKEN` are set.

Channels never fake success: missing configuration returns
`queued_missing_credentials`, provider failures return `failed` with the
provider status, and nothing is pushed anywhere without an explicit approval
(`--approve` on the CLI, `approved: true` through the orchestrator gate).
