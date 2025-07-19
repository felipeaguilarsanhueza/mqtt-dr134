# MQTT DR134 API

This project exposes a small REST API using **FastAPI** to serve readings stored in a SQL database. Two background workers consume MQTT messages from different meter models (`dr134` and `dr154`) and store the processed measurements.

## Installation

```bash
pip install -r requirements.txt
```

Create a `.env` file or export the following variables if needed:

- `DATABASE_URL` – Database connection string (defaults to an SQLite file `./test.db`).
- `API_KEY` – API key required to call the endpoints (defaults to `secret`).

## Running

```
uvicorn main:app --reload
```

The workers will automatically start in background threads when running the application.

## Endpoints

- `GET /data/{identifier}` – List the latest readings for a device. `identifier` can be a MAC address or an IMEI depending on the device type. Optional query parameter `limit` (default `10`). Requires header `X-API-Key`.
- `GET /current/{identifier}` – Return the most recent current measurement for a device. Also protected by API key.

Interactive documentation is available once the server is running at `/docs`.

## Notes

When adding the new `imei` column to the `devices` table you may need to recreate the database or handle the migration manually if you already have data stored.
