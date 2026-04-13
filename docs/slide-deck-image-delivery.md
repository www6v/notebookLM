# Slide Deck Image Delivery

This project now generates three slide image variants for each deck page:

- `thumb`: small WebP for the thumbnail rail
- `preview`: medium WebP for the main detail view
- `export`: original PNG for high-quality export and fallback

All newly generated variants are uploaded to object storage with:

- `Cache-Control: public, max-age=31536000, immutable`

The detail view loads an authenticated manifest from the API, then prefers
presigned object-storage URLs for `thumb` and `preview`. If direct loading is
blocked or unavailable, the frontend falls back to the same-origin proxy route.

## Required Bucket CORS

When presigned URLs are used directly from the browser, configure the OSS
bucket to allow the notebook frontend origin to fetch slide images.

Recommended rules:

- Allowed origins: your frontend domains, such as `https://app.example.com`
- Allowed methods: `GET`, `HEAD`
- Allowed headers: `*`
- Expose headers: `Content-Type`, `Cache-Control`, `ETag`
- Max age: `3600`

Example CORS shape:

```json
[
  {
    "AllowedOrigin": [
      "https://app.example.com"
    ],
    "AllowedMethod": [
      "GET",
      "HEAD"
    ],
    "AllowedHeader": [
      "*"
    ],
    "ExposeHeader": [
      "Content-Type",
      "Cache-Control",
      "ETag"
    ],
    "MaxAgeSeconds": 3600
  }
]
```

## Runtime Behavior

- Preview requests use object-storage URLs first.
- The API proxy remains available for compatibility and old data.
- Old slide decks without uploaded variants still work through local-file
  fallback and on-the-fly proxy resizing.

## Optional Nginx Follow-up

The repository keeps `/api/` proxy caching disabled because these routes are
authenticated. If you later want shared caching for slide images, prefer doing
that at the object storage or CDN layer instead of caching authenticated API
responses in Nginx.
