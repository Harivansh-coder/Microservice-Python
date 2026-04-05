## Service Interaction Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    API GATEWAY (Port 8000)                  │
│  config.py │ http_client.py │ cache.py │ dependencies.py    │
│                      routes.py (all /api/v1/*)              │
└──────────────┬──────────────────────┬──────────────────┬────┘
               │                      │                  │
       JWT Validation          Rate Limiting        Caching
               │                      │                  │
     ┌─────────▼────────┐  ┌──────────▼─────┐  ┌─────────▼──────┐
     │  AUTH SERVICE    │  │  UPLOAD        │  │  DOWNLOAD      │
     │  (Port 8001)     │  │  (Port 8002)   │  │  (Port 8003)   │
     │                  │  │                │  │                │
     │ PostgreSQL       │  │ MongoDB + RMQ  │  │ MongoDB        │
     │ JWT Tokens       │  │ GridFS Storage │  │ GridFS Stream  │
     └──────────────────┘  └────────┬───────┘  └────────────────┘
                                    │
                                    │ Job Queue
                                    │ (RabbitMQ)
                                    │
                           ┌────────▼─────────┐
                           │ CONVERSION       │
                           │ (Port 8004)      │
                           │                  │
                           │ MP4 → MP3        │
                           │ FFmpeg           │
                           └────────┬─────────┘
                                    │
                                    │ Event Queue
                                    │ (RabbitMQ)
                                    │
                           ┌────────▼─────────┐
                           │ NOTIFICATION     │
                           │ (Port 8005)      │
                           │                  │
                           │ Event Consumer   │
                           │ Logging/Email    │
                           └──────────────────┘
```

## Data Flow

```
USER REQUEST
     │
     ▼
┌─────────────────────────┐
│  API GATEWAY            │
│  • Rate Limit Check     │
│  • Cache Check          │
│  • JWT Validation       │
└────────────┬────────────┘
             │
      ┌──────┴───────┬──────────┐
      │              │          │
      ▼              ▼          ▼
   [AUTH]      [UPLOAD]    [DOWNLOAD]
      │              │          │
      │         GridFS Store    │
      │              │          │
      │         ┌─────▼─────┐   │
      │         │ RabbitMQ  │   │
      │         │ Job Queue │   │
      │         └─────┬─────┘   │
      │               │         │
      │         ┌─────▼──────┐  │
      │         │ CONVERSION │  │
      │         │ Worker     │  │
      │         │ (FFmpeg)   │  │
      │         └─────┬──────┘  │
      │               │         │
      │         ┌─────▼──────┐  │
      │         │ RabbitMQ   │  │
      │         │ Event Queue│  │
      │         └─────┬──────┘  │
      │               │         │
      │         ┌─────▼──────┐  │
      │         │NOTIFICATION│  │
      │         │Worker      │  │
      │         └──────┬─────┘  │
      │                │        │
      │            Log/Email    │
      │                         │
      └──────────┬──────────────┘
                 │
            RESPONSE
```
