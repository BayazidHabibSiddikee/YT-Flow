# Social Media API Keys — How to Get Them

## YouTube (Already Done ✓)

You already have:
- `Client_ID_IZUKU`
- `Client_SECRET_IZUKU`
- `YOUTUBE_REFRESH_TOKEN_IZUKU`

To upload videos, use the YouTube Data API v3.

---

## Facebook Pages API

### Step 1: Create a Facebook App
1. Go to https://developers.facebook.com/
2. Click **My Apps** → **Create App**
3. Select **Business** type
4. Fill in app name (e.g., "Izuku Midoriya Bot")
5. Create the app

### Step 2: Get Page Access Token
1. Go to **Graph API Explorer** (https://developers.facebook.com/tools/explorer/)
2. Select your app from dropdown
3. Click **Generate Access Token**
4. Select pages: `pages_manage_posts`, `pages_read_engagement`, `pages_show_list`
5. Copy the access token

### Step 3: Get Long-Lived Token
```bash
# Exchange short-lived token for long-lived token
curl "https://graph.facebook.com/v19.0/oauth/access_token?\
grant_type=fb_exchange_token&\
client_id=YOUR_APP_ID&\
client_secret=YOUR_APP_SECRET&\
fb_exchange_token=YOUR_SHORT_TOKEN"
```

### Step 4: Get Page Token
```bash
# Get page access token (never expires)
curl "https://graph.facebook.com/v19.0/me/accounts?access_token=YOUR_LONG_TOKEN"
```

### Add to .env:
```
FB_PAGE_TOKEN=your_page_access_token
FB_PAGE_ID=your_page_id
```

---

## Instagram Business API

### Requirements:
- Facebook Page connected to Instagram Business account
- Facebook App with Instagram Basic Display

### Step 1: Connect Instagram to Facebook Page
1. Go to your Facebook Page settings
2. Click **Instagram** → **Connect Account**
3. Switch to **Business** account if not already

### Step 2: Add Instagram Product
1. Go to Facebook Developer Dashboard
2. Add **Instagram Basic Display** product to your app

### Step 3: Get Access Token
1. Go to **Graph API Explorer**
2. Select your app
3. Add permissions: `instagram_basic`, `instagram_content_publish`
4. Generate token

### Step 4: Get Long-Lived Token
```bash
curl "https://graph.facebook.com/v19.0/oauth/access_token?\
grant_type=fb_exchange_token&\
client_id=YOUR_APP_ID&\
client_secret=YOUR_APP_SECRET&\
fb_exchange_token=YOUR_SHORT_TOKEN"
```

### Add to .env:
```
IG_ACCESS_TOKEN=your_instagram_token
IG_BUSINESS_ID=your_instagram_business_id
```

---

## TikTok API

### Step 1: Create TikTok Developer Account
1. Go to https://developers.tiktok.com/
2. Sign up / Log in
3. Create a new app

### Step 2: Get API Credentials
1. Go to your app dashboard
2. Note your **Client Key** and **Client Secret**
3. Add **Login Kit** and **Video Kit** products

### Step 3: OAuth Flow
```bash
# 1. Redirect user to authorize
https://www.tiktok.com/v2/auth/authorize/?\
client_key=YOUR_CLIENT_KEY&\
scope=user.info.basic,video.publish&\
response_type=code&\
redirect_uri=YOUR_REDIRECT_URI

# 2. Exchange code for access token
curl -X POST "https://open.tiktokapis.com/v2/oauth/token/" \
  -d "client_key=YOUR_KEY" \
  -d "client_secret=YOUR_SECRET" \
  -d "code=AUTH_CODE" \
  -d "grant_type=authorization_code" \
  -d "redirect_uri=YOUR_URI"
```

### Add to .env:
```
TIKTOK_CLIENT_KEY=your_key
TIKTOK_CLIENT_SECRET=your_secret
TIKTOK_ACCESS_TOKEN=your_token
```

---

## Twitter/X API

### Step 1: Create Twitter Developer Account
1. Go to https://developer.twitter.com/
2. Apply for developer account
3. Create a **Project** and **App**

### Step 2: Get API Keys
1. Go to **Keys and Tokens** tab
2. Generate:
   - API Key
   - API Secret
   - Access Token
   - Access Token Secret

### Step 3: Set Permissions
- Set app permissions to **Read and Write**

### Add to .env:
```
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_SECRET=your_access_secret
```

---

## Pinterest API (for image sourcing)

### Step 1: Create Pinterest Developer Account
1. Go to https://developers.pinterest.com/
2. Create an app

### Step 2: Get Access Token
1. Go to app settings
2. Generate access token with `read_public` scope

### Add to .env:
```
PINTEREST_ACCESS_TOKEN=your_token
```

---

## Environment Variables Summary

Add to `.env`:
```bash
# Social Media APIs
FB_PAGE_TOKEN=
FB_PAGE_ID=
IG_ACCESS_TOKEN=
IG_BUSINESS_ID=
TIKTOK_CLIENT_KEY=
TIKTOK_CLIENT_SECRET=
TIKTOK_ACCESS_TOKEN=
TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_SECRET=
PINTEREST_ACCESS_TOKEN=
```

---

## Easiest APIs to Start With

1. **YouTube** — Already done ✓
2. **Twitter/X** — Free tier, easy to post
3. **Facebook Pages** — Free, good for video
4. **Instagram** — Needs Facebook setup
5. **TikTok** — Hardest to get approved

**Recommendation:** Start with YouTube + Twitter. Add Facebook/Instagram later.
