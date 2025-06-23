# Event Management API with FastAPI and PostgreSQL

A secure event management API built with FastAPI, PostgreSQL, and Docker. This application provides endpoints for managing events, user favorites, and integrates with external APIs.

## Prerequisites

- Docker (version 20.10.0+)
- Docker Compose (version 1.29.0+)


## Setup Instructions

### 1. Environment Configuration

Create a `.env` file in the project root with the following structure:


GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
DATABASE_URL=postgresql://postgres:postgres@db:5432/ticketmaster
POSTGRES_DB=ticketmaster
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
TICKETMASTER_KEY=your_ticketmaster_api_key

Replace the GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET with the appropriate values from your Google Cloud Console: https://console.cloud.google.com/
In the Google cloud console create a new project and go to APIs & Services > OAuth consent screen, choose External, click create and fill out the required information.
Go to Clients from the left sidebar and select the application type to be Web.
Add the following in the Authorized redirect URIs:
http://localhost:8000/auth/google/callback
Click create, you will get a popup containing the Google Client ID and Google Client Secret, copy them into your .env file.

For the TICKETMASTER_KEY, you must create a TicketMaster account here : https://developer-acct.ticketmaster.com/user/login
After creating the account you will receive an API key.


Now that you have your .env setup in the root directory, open your terminal inside the root directory and run the following command:
docker-compose build
docker-compose up

You should have the database and the web service both running.
You can access the backend at http://localhost:8000


###### API Usage:
**http://localhost:8000/events**

#### Pagination
| Parameter  | Type  | Default | Description |
|------------|-------|---------|-------------|
| `page`     | int   | 1       | Page number (1-based) |
| `per_page` | int   | 10      | Items per page (max 100) |

#### Filtering
| Parameter          | Type      | Example | Description |
|--------------------|-----------|---------|-------------|
| `name`             | string    | `?name=concert` | Partial name match |
| `city`             | string    | `?city=new+york` | Events in city |
| `country`          | string    | `?country=usa` | Events in country |
| `venue_name`       | string    | `?venue_name=arena` | Events at venue |
| `start_date_from`  | datetime  | `?start_date_from=2023-10-01` | Events after date |
| `start_date_to`    | datetime  | `?start_date_to=2023-12-31` | Events before date |
| `search`           | string    | `?search=music+festival` | Full-text search |

#### Sorting
| Parameter   | Type   | Default     | Example | Description |
|-------------|--------|-------------|---------|-------------|
| `sort_by`   | string | "start_date" | `?sort_by=name` | Field to sort by |
| `sort_order`| string | "asc"       | `?sort_order=desc` | Sort direction |

**http://localhost:8000/auth/login/google**
Type this in a browser, login to your google account, you will get an access token and a refresh token upon successful login.
 
**http://localhost:8000/events/{eventid}/save**
Must be authenticated to access this endpoint (have a valid Bearer token). Saves an event to user's favorite events.

**http://localhost:8000/events/favorites**
Must be authenticated to access this endpoint (have a valid Bearer Token). Retrieves user's saved events.



