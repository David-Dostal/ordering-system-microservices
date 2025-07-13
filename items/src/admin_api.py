from fastapi import FastAPI
from starlette.config import Config
from starlette.requests import Request
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import HTMLResponse, RedirectResponse
from authlib.integrations.starlette_client import OAuth, OAuthError
from authlib.integrations.starlette_client import OAuth
from fastapi.templating import Jinja2Templates
import os
from .admin_routes import router
from starlette.config import Config


# OAuth settings
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="!secret")
app.include_router(router)



# Set up OAuth
config_data = {
    'GOOGLE_CLIENT_ID': GOOGLE_CLIENT_ID, 
    'GOOGLE_CLIENT_SECRET': GOOGLE_CLIENT_SECRET
}

starlette_config = Config(environ=config_data)
oauth = OAuth(starlette_config)

CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url=CONF_URL,
    client_kwargs={
        'scope': 'openid email profile'
    }
)

templates = Jinja2Templates(directory="templates")

@app.get('/', response_class=HTMLResponse)
async def admin_homepage(request: Request):
    user = request.session.get('user')
    return templates.TemplateResponse("admin_homepage.html", {"request": request, "user": user})



@app.get('/login')
async def login(request: Request):
    redirect_uri = request.url_for('auth')
    return await oauth.google.authorize_redirect(request, redirect_uri)


@app.get('/auth')
async def auth(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as error:
        return HTMLResponse(f'<h1>{error.error}</h1>')
    user_info = token.get('userinfo')
    if user_info:
        request.session['user'] = user_info  # Storing user info in session
    return RedirectResponse(url='/')


@app.get('/logout')
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url='/')

