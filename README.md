# Restaurant Menu Admin Full Stack App

A Flask full stack app mangin restaurants and their menu items. Following feaures are demonstrated.

* Flask
  * Routing
  * Request
  * Templates
  * Message Flashing
  * REST API Endpoints
* Data Driven and ORM
  * SQLite
  * SQL Alchemy
  * Bleach
* Front End
  * Multi-page
  * Bootstrap
  * Templating
* Authentication
  * Google OAuth2 sign in
  * Facebook sign in

## Running the app

```bash
$> python ./flask-server.py
```

Then open [localhost:8000](http://localhost:8000/) in your browser.

## Dependencies

Following dependencies are required

* PostgreSQL 10.6
* SQL Alchemy
* Bleach
* OAuth2Client
* HttpLib2
* Requests

### Todos

* OAuth
* Cookies
* User passwords
* Demonstrate above in another project

#### Bugs

* Facebook login does not work. Probably due to HTTP and not HTTPS.