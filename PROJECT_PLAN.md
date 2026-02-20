# Alexandra Social Content Engine - Complete Guide

## What This Project Does

Uses GPT-OSS 120B (running in Ollama on your DGX Spark) to generate blog posts, Twitter/X posts, and Instagram captions that sound like you — not like AI. Posts to a Supabase blog, Twitter/X, and Instagram.

Also uses **Nano Banana MCP** (powered by Google Gemini) to auto-generate images for blog headers, Instagram posts, and tweet attachments — so the entire content pipeline (text + images) is automated.

Later, you can fine-tune GPT-OSS 120B with your personality data (text messages, personal Q&A, etc.) for an even more authentic voice.

---

## Project Structure

```
gptoss-alexandra-project/
├── PROJECT_PLAN.md                    ← YOU ARE HERE
├── .env                               ← BACKEND ENV VARS (Supabase, Gemini, model)
├── ghostpen/                          ← REACT FRONTEND (use now)
│   ├── .env.local                     # Frontend env (API URL, Supabase anon key)
│   ├── src/app/page.tsx               # Dashboard (main page)
│   ├── src/app/layout.tsx             # Root layout, fonts, theme
│   ├── src/app/globals.css            # Bougie Coffee warm earth tone theme
│   ├── src/app/blog/page.tsx          # Blog listing page (client component)
│   ├── src/app/blog/[slug]/page.tsx   # Individual blog post page (client component)
│   ├── src/components/generate/       # TopicForm, ContentCard, ImagePreview
│   ├── src/components/blog/           # BlogCard, BlogList
│   ├── src/components/shared/         # PageHero
│   ├── src/components/layout/         # Header
│   ├── src/components/status/         # PlatformStatus
│   ├── src/lib/api.ts                 # API client for backend (blog CRUD + content gen)
│   ├── src/types/index.ts             # TypeScript interfaces
│   └── package.json                   # Next.js 15 + Tailwind + Lucide
├── training/                          ← FOR LATER (fine-tuning)
│   ├── download_gptoss.py             # Download trainable model from HuggingFace
│   ├── prepare_gptoss_data.py         # Convert & clean your training data
│   └── train_gptoss_alexandra.py      # QLoRA fine-tuning with Unsloth
├── serving/                           ← FOR LATER (after fine-tuning)
│   └── serve_gptoss_alexandra.sh      # Serve fine-tuned model via vLLM
└── social-content-engine/             ← BACKEND API (use now)
    ├── requirements.txt
    ├── config.py                      # Config (Ollama endpoint, API keys, Gemini)
    ├── generator.py                   # Calls GPT-OSS via Ollama API
    ├── cli.py                         # Command-line tool
    ├── server.py                      # REST API server (port 8001)
    ├── venv/                          # Python virtual environment
    ├── prompts/
    │   └── templates.py               # Your voice/personality prompts
    └── platforms/
        ├── base.py                    # Adapter base class
        ├── blog.py                    # Supabase blog
        ├── twitter.py                 # Twitter/X via Tweepy
        └── instagram.py              # Instagram via Instagrapi
```

---

# PART 1: CONTENT ENGINE (USE NOW)

This works right now with your existing Ollama `gpt-oss:120b`.

## Step 1: Make Sure Ollama Is Running

```bash
# Check if Ollama is running
ollama list

# You should see gpt-oss:120b in the list
# If Ollama isn't running:
ollama serve &
```

## Step 2: Install Dependencies

```bash
cd /home/alexandratitus767/gptoss-alexandra-project/social-content-engine
pip install -r requirements.txt
```

This installs: httpx, fastapi, uvicorn, tweepy, instagrapi, supabase

## Step 3: Set Up Environment Variables

The `.env` file is already created at `/home/alexandratitus767/gptoss-alexandra-project/.env` with all credentials configured.

Load the env vars before running anything:

```bash
source /home/alexandratitus767/gptoss-alexandra-project/.env
```

The `.env` file contains:
- `MODEL_ENDPOINT` and `MODEL_NAME` — Ollama GPT-OSS 120B connection
- `SUPABASE_URL` and `SUPABASE_KEY` — Supabase project "Alexandra_GhostPen" (service_role key)
- `GEMINI_API_KEY` — Google Gemini API for image generation
- `TWITTER_*` keys — fill in when ready
- `INSTAGRAM_*` keys — fill in when ready

The frontend also has its own env at `ghostpen/.env.local`:
- `NEXT_PUBLIC_API_URL=http://192.168.1.187:8001` — backend URL (uses Spark's LAN IP so MacBook browser can reach it)
- `NEXT_PUBLIC_SUPABASE_URL` — Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` — Supabase anon key (for client-side reads)

## Step 4: Supabase Blog (DONE)

Supabase project **"Alexandra_GhostPen"** is set up and working.

- **Project URL:** `https://vngzdpwvurdehtctfbxj.supabase.co`
- **Database table:** `blog_posts` with RLS policies
- **Backend** uses the `service_role` key (full CRUD access)
- **Frontend** uses the `anon` key (read-only published posts)

The `blog_posts` table schema:

```sql
CREATE TABLE blog_posts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    content TEXT NOT NULL,
    excerpt TEXT,
    tags TEXT[] DEFAULT '{}',
    image_url TEXT,
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived')),
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Fallback:** If Supabase credentials aren't configured, the backend automatically falls back to `LocalBlogStore` (stores posts in `social-content-engine/data/blog_posts.json`).

## Step 5: Set Up Twitter/X (When Ready)

1. Go to https://developer.twitter.com
2. Sign up for developer access (Basic tier = $100/month for write access)
3. Create a Project and App
4. Set app permissions to **Read and Write**
5. Generate these 4 keys and put them in your `.env`:
   - Consumer Key (API Key)
   - Consumer Secret (API Secret)
   - Access Token
   - Access Token Secret

## Step 6: Set Up Instagram (When Ready)

Just put your Instagram username and password in the `.env` file. The app handles login and session persistence automatically.

**Important:** Instagram can be touchy with automated posting. Start slow (1-2 posts per day).

---

## HOW TO USE THE CLI

Always run from the social-content-engine directory:

```bash
cd /home/alexandratitus767/gptoss-alexandra-project/social-content-engine
source /home/alexandratitus767/gptoss-alexandra-project/.env
```

### Check Status

```bash
python cli.py status
```

Shows if the model server is reachable and which platforms are configured.

### Generate Content (Preview Only - Does NOT Post)

```bash
# Generate for ALL platforms at once
python cli.py generate "my experience building AI at home on a DGX Spark"

# Generate just a tweet
python cli.py generate "fly fishing in Pennsylvania" -p twitter

# Generate just a blog post
python cli.py generate "why I love camping in Ridgway PA" -p blog

# Generate just an Instagram caption
python cli.py generate "morning coffee and code" -p instagram

# Generate a longer blog post
python cli.py generate "my transition journey" -p blog --word-count 1000

# Generate with a specific tone
python cli.py generate "tech advice for beginners" -p blog --tone serious

# Generate Instagram with image context
python cli.py generate "sunset hike" -p instagram --image-desc "golden sunset over the Allegheny mountains"
```

### Generate AND Post

Add `--post` to actually publish:

```bash
# Generate and post a tweet
python cli.py generate "AI tip of the day" -p twitter --post

# Generate and post to blog
python cli.py generate "my first week with the DGX Spark" -p blog --post

# Generate and post to Instagram (requires --image)
python cli.py generate "beautiful day" -p instagram --image /path/to/photo.jpg --post

# Generate and post to ALL platforms (Instagram needs --image)
python cli.py generate "exciting news" --post --image /path/to/photo.jpg
```

### Post Pre-Written Content

If you wrote something yourself and just want to post it:

```bash
# Post a tweet you already wrote
python cli.py post twitter --content "Just finished training my AI model. 6 hours well spent."

# Post a blog you already wrote
python cli.py post blog --content "# My Blog Title

This is the first paragraph of my blog post.

## Section Two

More content here..." --title "My Blog Title"

# Post to Instagram
python cli.py post instagram --content "Beautiful morning in Ridgway #ridgwaypa #nature" --image /path/to/photo.jpg
```

---

## HOW TO USE THE REST API

Start the API server:

```bash
cd /home/alexandratitus767/gptoss-alexandra-project/social-content-engine
source /home/alexandratitus767/gptoss-alexandra-project/.env
python server.py
```

Server runs at **http://localhost:8001**

### API Endpoints

**Generate content:**
```bash
curl -X POST http://localhost:8001/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "AI for beginners", "platform": "all"}'
```

**Generate and auto-post:**
```bash
curl -X POST http://localhost:8001/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "morning thoughts", "platform": "twitter", "auto_post": true}'
```

**Post pre-written content to blog:**
```bash
curl -X POST http://localhost:8001/post/blog \
  -H "Content-Type: application/json" \
  -d '{"content": "# Blog Title\n\nContent here...", "title": "My Post"}'
```

**Check platform status:**
```bash
curl http://localhost:8001/platforms
```

**Health check:**
```bash
curl http://localhost:8001/health
```

---

# PART 1A: GHOSTPEN WEB UI (USE NOW)

GhostPen is a React web dashboard for generating and posting content — no command line needed.

## Tech Stack

- **Framework:** Next.js 15 + TypeScript (App Router)
- **Styling:** Tailwind CSS v4 with `@theme inline` (no tailwind.config — all in CSS)
- **Icons:** Lucide React
- **Fonts:** Playfair Display (serif headings) + Inter (body)
- **Design:** Bougie Coffee-inspired warm earth tone palette

## How to Start GhostPen

You need TWO terminals — one for the backend, one for the frontend.

### Terminal 1: Start Backend

```bash
cd /home/alexandratitus767/gptoss-alexandra-project/social-content-engine
source venv/bin/activate
source /home/alexandratitus767/gptoss-alexandra-project/.env
python server.py
```

Backend runs at **http://localhost:8001**

### Terminal 2: Start Frontend

```bash
cd /home/alexandratitus767/gptoss-alexandra-project/ghostpen
npm run dev
```

Frontend runs at **http://localhost:3000**

### Access from your MacBook

Open your browser and go to: **http://192.168.1.187:3000**

(Use the Spark's IP address since the servers run on the Spark)

## How to Use GhostPen

1. **Enter a topic** — type what you want to write about
2. **Select platforms** — Blog, X/Twitter, Instagram (select one or all)
3. **Pick a tone** — casual, reflective, technical, or humorous
4. **Set word count** — slider for blog post length (200-2000 words)
5. **Hit Generate** — GPT-OSS 120B creates content in your voice
6. **Image auto-generates** — Gemini reads your content and creates a matching image
7. **Preview everything** — edit content inline if needed
8. **Post** — click "Post to [Platform]" when you're happy with it

## Features

- **Content preview cards** for each platform with character counts
- **Blog posts** render as formatted markdown
- **Auto image generation** — AI reads your content and creates a relevant image prompt, then generates the image
- **Editable image prompt** — tweak the prompt and regenerate if the image isn't right
- **Copy button** — copy content to clipboard
- **Edit button** — edit content inline before posting
- **Delete button** — delete blog posts (with confirmation dialog) from both the blog list and individual post pages
- **Platform status** — green/red dots show which platforms are connected and if the model is reachable
- **Blog pages** — full blog listing page (`/blog`) and individual post pages (`/blog/[slug]`) with hero images, tag filters, and related posts
- **Supabase-backed** — all blog posts stored in Supabase with automatic fallback to local JSON storage

## Backend API Endpoints (for GhostPen)

These endpoints are in `server.py`:

| Endpoint | Method | What It Does |
|---|---|---|
| `/generate` | POST | Generate text content |
| `/post/{platform}` | POST | Post content to a platform |
| `/generate-image-prompt` | POST | GPT-OSS creates an image prompt from your content |
| `/generate-image` | POST | Gemini API generates an image from the prompt |
| `/images/{filename}` | GET | Serves generated images to the browser |
| `/api/blog/posts` | GET | List all published blog posts (from Supabase) |
| `/api/blog/posts/{slug}` | GET | Get a single blog post by slug |
| `/api/blog/posts/{post_id}` | DELETE | Delete a blog post by UUID |
| `/platforms` | GET | Platform connection status |
| `/health` | GET | Backend + model health check |

## Content → Image Flow

This is the key feature. When you click Generate:

1. GPT-OSS 120B generates text content for your selected platforms
2. GhostPen sends that content to `/generate-image-prompt`
3. GPT-OSS analyzes the content and writes a descriptive image prompt
4. GhostPen sends the prompt to `/generate-image`
5. Gemini API generates a matching image
6. The image displays in the preview panel
7. You can edit the prompt and regenerate if needed
8. For Instagram posts, the image auto-attaches when you click Post

## Design System (Bougie Coffee Style)

### Color Palette

| Name | Hex | CSS Variable | Usage |
|------|-----|-------------|-------|
| **Cream** | `#FAF7F2` | `--background` | Page background |
| **Espresso** | `#3C2415` | `--foreground` | Text, dark elements |
| **Terracotta** | `#C4704B` | `--terracotta` | Primary accent, CTAs, links |
| **Terracotta Dark** | `#A85D3C` | `--terracotta-dark` | Hover state for accent |
| **Sage** | `#7A8B6F` | `--sage` | Success indicators, secondary accent |
| **Red** | `#C45B4B` | `--red` | Errors, over-limit warnings |
| **White** | `#FFFFFF` | `--surface` | Cards, panels |
| **Light Cream** | `#F0EBE3` | `--surface-hover` / `--secondary` | Hover states, secondary backgrounds |
| **Warm Sand** | `#E8E0D6` | `--border` | Borders, dividers |
| **Warm Gray** | `#8B7E74` | `--muted` | Muted text, meta info |

### Typography

- **Headings:** Playfair Display (serif) — elegant, editorial feel
- **Body:** Inter (sans-serif) — clean, readable
- All `h1`-`h6` elements default to serif via CSS

### Component Patterns

- **Navbar:** Sticky, `bg-background/80 backdrop-blur-md`, rounded-full nav pills
- **Cards:** White bg (`bg-surface`), no border or `border-0`, `shadow-sm`, `hover:shadow-md`
- **Buttons:** Rounded-full pills, terracotta primary, espresso/cream toggles
- **Filter pills:** `rounded-full`, active = `bg-foreground text-background`, inactive = `bg-secondary`
- **Tags/badges:** `rounded-full`, `bg-terracotta/10 text-terracotta` or `bg-terracotta text-white`
- **Hero sections:** Full-width with image + gradient overlay (`from-foreground/80`)
- **Blog cards:** Image with scale-105 hover, serif titles, shadow elevation
- **Footer:** `bg-foreground text-background` (dark espresso with cream text)

### Layout

- **Container:** `max-w-6xl` (dashboard) / `max-w-7xl` (blog) centered with `mx-auto`
- **Section padding:** `py-12 px-4 sm:px-6 lg:px-8`
- **Grid:** `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3` for card layouts
- **Clean dashboard** — single page, everything visible at once
- **Responsive** — works on desktop and mobile

---

# PART 1B: IMAGE GENERATION (NANO BANANA MCP)

The content engine can auto-generate images using **Nano Banana MCP**, which connects Claude to Google's Gemini image generation API. This means fully automated content — text AND images — from a single command.

## How It Works

- **Nano Banana MCP** is a plugin (Model Context Protocol server) that gives Claude image generation abilities
- It uses **Google Gemini's image API** under the hood (not Nano Banana's paid plans)
- You only need a **free Google Gemini API key**
- Images are generated locally and saved to `./generated_imgs/`

## Setup (Already Done)

The MCP config is already set up at `~/.mcp.json`:

```json
{
  "mcpServers": {
    "nano-banana": {
      "command": "npx",
      "args": ["nano-banana-mcp"],
      "env": {
        "GEMINI_API_KEY": "your-gemini-key-here"
      }
    }
  }
}
```

**Gemini API Key:** Get a free key at https://aistudio.google.com/app/apikey

**Requirements:** Node.js 18+ (already installed on your Spark)

## What You Can Do

When working with Claude Code, just ask:

### Generate New Images
```
"Generate an image of a mountain sunset for my blog header"
"Create a tech-themed banner with circuit board patterns"
"Make a cozy cabin photo for my camping blog post"
```

### Edit Existing Images
```
"Edit /path/to/image.png — make the sky more dramatic"
"Take this photo and add a vintage filter look"
```

### Iterative Refinement
```
"Make the colors warmer"
"Add more detail to the foreground"
"Change the sky to sunset colors"
```

## Available MCP Tools

| Tool | What It Does |
|---|---|
| `generate_image` | Create a brand new image from a text description |
| `edit_image` | Modify an existing image file with a text prompt |
| `continue_editing` | Refine the last generated/edited image |
| `get_last_image_info` | Check what image is currently in the editing buffer |
| `configure_gemini_token` | Update your Gemini API key |
| `get_configuration_status` | Check if the API key is configured |

## Integration with Content Engine

When generating content, you can ask Claude to:

1. **Blog post + header image:** "Generate a blog post about fly fishing and create a header image for it"
2. **Instagram caption + photo:** "Write an Instagram caption about camping and generate the photo to go with it"
3. **Tweet + image attachment:** "Write a tweet about AI and create an image to attach"

The workflow:
1. GPT-OSS 120B (via Ollama) generates the text in your voice
2. Nano Banana MCP (via Gemini) generates the matching image
3. You review and post (or auto-post with `--post`)

## Image Output

- Images save to `./generated_imgs/` in the current working directory
- Supports up to 4K resolution
- Multiple aspect ratios: 1:1, 16:9, 9:16, 4:3, 3:4
- Can combine up to 14 reference images for style transfer

## Troubleshooting

### "Nano Banana MCP not connected"
- Restart Claude Code — MCP servers load on startup
- Check config: `cat ~/.mcp.json`
- Make sure Node.js is installed: `node --version` (need 18+)

### "Gemini API key invalid"
- Get a new key at https://aistudio.google.com/app/apikey
- Update `~/.mcp.json` with the new key

### Images look wrong or low quality
- Be more specific in your prompt (describe style, lighting, composition)
- Use `continue_editing` to iteratively refine
- Specify aspect ratio if needed (e.g., "16:9 landscape for blog header")

---

# PART 2: FINE-TUNING (DO LATER)

When you're ready to fine-tune GPT-OSS 120B with your personality data for an even more authentic voice. Do this when your coding LoRA training is finished and the Spark has resources free.

## Your Training Data

All located at `/home/alexandratitus767/ai-clone-training/data/`:

| File | Size | Examples | What It Is |
|---|---|---|---|
| `alexandra_texts.json` | 285KB | 1,269 | **Your actual text messages** (highest value) |
| `alexandra_training_cleaned.json` | 24MB | ~9,644 | Cleaned personality data |
| `alexandra_personal.json` | 97KB | ~202 | Personal identity Q&A |
| `alexandra_personal_expanded.json` | 37KB | - | Expanded identity data |

The data prep script (`prepare_gptoss_data.py`) will:
- Combine all 4 files
- Convert to GPT-OSS messages format
- Strip out all LOLs and emojis
- Filter out AI-sounding phrases ("Certainly!", "As an AI", etc.)
- Oversample your text messages 6x and identity data 8x

## Fine-Tuning Steps

### Step 1: Download the Trainable Model

Ollama's GGUF format can't be fine-tuned. You need the HuggingFace version:

```bash
cd /home/alexandratitus767/gptoss-alexandra-project
python training/download_gptoss.py
```

This downloads `unsloth/gpt-oss-120b-bnb-4bit` to `/home/alexandratitus767/models/gpt-oss-120b/`

**Note:** This is a separate download from your Ollama model. You need both — Ollama for inference now, HuggingFace for training.

### Step 2: Prepare Training Data

```bash
python training/prepare_gptoss_data.py
```

Output: `/home/alexandratitus767/ai-clone-training/data/gptoss_alexandra_training.json`

### Step 3: Start Docker Container

```bash
# Pull the NVIDIA PyTorch container (if not already pulled)
docker pull nvcr.io/nvidia/pytorch:25.11-py3

# Launch it
docker run --gpus all \
    --ulimit memlock=-1 \
    -it \
    --ulimit stack=67108864 \
    -v /home/alexandratitus767:/workspace/host \
    --entrypoint /usr/bin/bash \
    nvcr.io/nvidia/pytorch:25.11-py3
```

### Step 4: Install Training Dependencies (Inside Docker)

```bash
pip install transformers peft hf_transfer "datasets==4.3.0" "trl==0.26.1"
pip install --no-deps unsloth unsloth_zoo bitsandbytes
```

### Step 5: Flush Memory & Run Training

```bash
# Free up memory
sudo sh -c 'sync; echo 3 > /proc/sys/vm/drop_caches'

# Make sure Ollama and other models are stopped first!
# On the host (not inside Docker): ollama stop gpt-oss:120b

# Run training
cd /workspace/host/gptoss-alexandra-project
python training/train_gptoss_alexandra.py
```

### Training Details

| Setting | Value |
|---|---|
| Model | GPT-OSS 120B (4-bit quantized) |
| Method | QLoRA via Unsloth |
| LoRA rank | 32 |
| LoRA alpha | 64 |
| Batch size | 1 (x16 gradient accumulation = effective 16) |
| Learning rate | 1e-4 |
| Epochs | 2 |
| Max sequence length | 4096 |
| Memory needed | ~65GB of 128GB available |
| Estimated time | ~6-11 hours |
| Checkpoints | Every 500 steps, keeps last 3 |

### Step 6: After Training Completes

The script automatically:
1. Saves the LoRA adapter to `gptoss-alexandra-lora-final/`
2. Tries to merge it into a standalone model at `models/gptoss-alexandra-merged/`

### Step 7: Switch Content Engine to Fine-Tuned Model

**Option A: Serve with vLLM (recommended for fine-tuned model)**

```bash
bash serving/serve_gptoss_alexandra.sh
```

Then update your `.env`:
```bash
export MODEL_ENDPOINT="http://localhost:8000"
export MODEL_NAME="alexandra"
```

**Option B: Keep using Ollama**

Create a Modelfile to import the fine-tuned model into Ollama:
```
FROM /home/alexandratitus767/models/gptoss-alexandra-merged
```

```bash
ollama create alexandra -f Modelfile
```

Then update your `.env`:
```bash
export MODEL_NAME="alexandra"
```

---

# PART 3: ADDING NEW PLATFORMS

The system uses an adapter pattern — adding a new platform is straightforward.

### Example: Adding LinkedIn

1. Create `social-content-engine/platforms/linkedin.py`:

```python
from .base import PlatformAdapter, PostResult

class LinkedInAdapter(PlatformAdapter):

    @property
    def platform_name(self) -> str:
        return "linkedin"

    @property
    def max_content_length(self) -> int:
        return 3000

    async def post(self, content: str, **kwargs) -> PostResult:
        # Your LinkedIn API posting logic here
        pass

    async def validate_credentials(self) -> bool:
        # Check credentials
        pass
```

2. Add a prompt template in `prompts/templates.py`:

```python
PLATFORM_PROMPTS["linkedin"] = {
    "system": ALEXANDRA_VOICE + "\n\nYou are writing a LinkedIn post...",
    "template": "Write a LinkedIn post about: {topic}",
    "max_tokens": 1024,
    "temperature": 0.8,
}
```

3. Register it in `cli.py` (add to `get_platforms()`) and `server.py` (add to `startup()`)

---

# QUICK REFERENCE

## Daily Workflow (Web UI)

```bash
# 1. Start backend (Terminal 1)
cd /home/alexandratitus767/gptoss-alexandra-project/social-content-engine
source venv/bin/activate
source /home/alexandratitus767/gptoss-alexandra-project/.env
python server.py

# 2. Start frontend (Terminal 2)
cd /home/alexandratitus767/gptoss-alexandra-project/ghostpen
npm run dev

# 3. Open http://192.168.1.187:3000 in your browser
# 4. Enter a topic, generate, review, post!
```

## Daily Workflow (CLI)

```bash
# 1. Load env vars
source /home/alexandratitus767/gptoss-alexandra-project/.env

# 2. Go to the engine
cd /home/alexandratitus767/gptoss-alexandra-project/social-content-engine

# 3. Generate content (text)
python cli.py generate "your topic here"

# 4. If it looks good, generate and post
python cli.py generate "your topic here" --post

# 5. For images, ask Claude Code directly:
#    "Generate a header image for a blog post about fly fishing"
#    "Create an Instagram photo of a mountain sunrise"
```

## All CLI Commands at a Glance

```bash
python cli.py status                                    # Check connections
python cli.py generate "topic"                          # All platforms, preview
python cli.py generate "topic" -p twitter               # Twitter only
python cli.py generate "topic" -p blog                  # Blog only
python cli.py generate "topic" -p instagram             # Instagram only
python cli.py generate "topic" -p blog --tone serious   # Set tone
python cli.py generate "topic" -p blog --word-count 800 # Set length
python cli.py generate "topic" --post                   # Generate + publish
python cli.py generate "topic" -p instagram --image photo.jpg --post  # Instagram
python cli.py post twitter --content "your tweet"       # Post existing text
python cli.py post blog --content "# Title\n\nBody"     # Post existing blog
python cli.py post instagram --content "caption" --image photo.jpg    # Post existing
```

## Key File Locations

| What | Where |
|---|---|
| Project folder | `/home/alexandratitus767/gptoss-alexandra-project/` |
| GhostPen frontend | `ghostpen/` (Next.js, port 3000) |
| Content engine backend | `social-content-engine/` (FastAPI, port 8001) |
| Training scripts | `training/` |
| Personality prompts | `social-content-engine/prompts/templates.py` |
| Platform adapters | `social-content-engine/platforms/` |
| Config | `social-content-engine/config.py` |
| Backend env vars | `.env` (configured with Supabase, Gemini, model) |
| Frontend env vars | `ghostpen/.env.local` (API URL, Supabase anon key) |
| Supabase project | "Alexandra_GhostPen" at `vngzdpwvurdehtctfbxj.supabase.co` |
| Your training data | `/home/alexandratitus767/ai-clone-training/data/` |
| Your text messages | `/home/alexandratitus767/ai-clone-training/data/alexandra_texts.json` |
| Ollama model | `gpt-oss:120b` (already installed) |
| Trainable model (later) | `/home/alexandratitus767/models/gpt-oss-120b/` |
| Nano Banana MCP config | `~/.mcp.json` |
| Generated images | `~/generated_imgs/` |
| Gemini API key setup | https://aistudio.google.com/app/apikey |

---

## Troubleshooting

### "Model server not reachable"
- Make sure Ollama is running: `ollama serve &`
- Check it's working: `ollama list`
- Test manually: `curl http://localhost:11434/v1/models`

### Content sounds too AI-like
- Edit `social-content-engine/prompts/templates.py` to adjust the personality rules
- Increase temperature (0.9-1.0) for more creative/varied output
- Fine-tune the model later with your real text messages for best results

### Platform not configured
- Run `python cli.py status` to see what's connected
- Make sure you ran `source .env` to load your API keys
- Check that the API keys are correct

### Instagram blocks/challenges
- Space posts at least 4+ hours apart
- Don't post more than 2-3 times per day
- The session file at `~/.instagram_session.json` is auto-managed

### Twitter rate limits
- Basic tier: 1,500 tweets/month
- Don't post more than ~50/day

### Out of Memory during fine-tuning (later)
- Stop Ollama first: `ollama stop gpt-oss:120b`
- Stop Jarvis and any other running models
- Flush caches: `sudo sh -c 'sync; echo 3 > /proc/sys/vm/drop_caches'`
- If still OOM: reduce `MAX_SEQ_LENGTH` to 2048 in the training script
