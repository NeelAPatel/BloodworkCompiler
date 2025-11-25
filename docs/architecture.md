flowchart LR
  U[Next.js] -->|HTTPS Upload| API[FastAPI]
  API --> DB[(Postgres)]
  API -->|enqueue (later)| Q[(Redis/SQS)]
  Q --> WRK[Parser Worker]
  WRK --> DB
  WRK --> S3[(S3 - optional)]
  API --> RLS[(RLS policies)]
