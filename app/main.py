import asyncio
import datetime
import logging
import logging.handlers
import os
from typing import Any

import discord
from discord import app_commands
from discord.ext import tasks
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from peewee import *
from playhouse.db_url import connect

from .enums import (
    Slot1,
    Slot2,
)
from .exceptions import HTTPException
from .template import get_html_template
from .user import User
from .wotapi import WoTAPI

load_dotenv()

app = FastAPI()
api = WoTAPI(app_id=os.getenv("APP_ID"), clan_id=os.getenv("CLAN_ID"))
db = connect(f"sqlite:///{os.path.abspath(os.path.join(__file__,  '..', '..', 'db', 'tanku.db'))}")
db.bind([User])
db.create_tables([User])
db.close()

logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setLevel(logging.INFO)

formatter = logging.Formatter("[{asctime}] [{levelname:<8}] {name}: {message}", "%Y-%m-%d %H:%M:%S", style="{")
handler.setFormatter(formatter)
logger.addHandler(handler)

TEST_GUILD = discord.Object(id=os.getenv("GUILD_ID"))
ACTING_USER = os.getenv("ALLOWED_ACCOUNT_ID")

task_run_time = datetime.time(hour=2, minute=30, tzinfo=datetime.timezone.utc)


class BotClient(discord.Client):
    def __init__(self, *, intents: discord.Intents) -> None:
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        self.extend_token_task.start()
        self.tree.copy_global_to(guild=TEST_GUILD)
        await self.tree.sync(guild=TEST_GUILD)

    @tasks.loop(time=task_run_time)
    async def extend_token_task(self) -> None:
        acting_user = get_api_user()
        if not acting_user:
            print("no user found...skipping")
        else:
            try:
                resp = api.extend_access_token(acting_user)
            except HTTPException as ex:
                print(ex)

            """
            # @TODO
            # error handling
            """
            query = User.update(access_token=resp["access_token"], updated_at=datetime.datetime.now()).where(
                User.account_id == acting_user.account_id
            )
            query.execute()

    @extend_token_task.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()


intents = discord.Intents.default()
client = BotClient(intents=intents)


@app.on_event("startup")
async def startup_event() -> None:
    asyncio.create_task(client.start(token=os.getenv("BOT_TOKEN")))


@app.get("/auth")
async def auth(
    status: str = "",
    access_token: str = "",
    nickname: str = "",
    account_id: int = 0,
    expires_at: float = 0,
) -> Any:
    if status != "ok" or ("" in [status, access_token, nickname, expires_at] or account_id == 0):
        return get_html_response(success=False)

    if not api.verify_user_token(access_token, nickname, account_id):
        print("token verification failed")
        return get_html_response(success=False)

    try:
        with db.atomic():
            print("attempting to create user")
            user = User.create(
                account_id=account_id,
                nickname=nickname,
                access_token=access_token,
                expires_at=datetime.datetime.fromtimestamp(expires_at),
                updated_at=datetime.datetime.now(),
            )
            if user:
                print("user created successfully")
                return get_html_response(success=True)
            else:
                print("user creation failed")
                return get_html_response(success=False)
    except IntegrityError as ex:
        print(ex)
        return get_html_response(success=False)


@client.event
async def on_ready() -> None:
    print(f"Logged in as {client.user} (ID: {client.user.id})")


@client.tree.command()
@app_commands.describe(bonus_code="The bonus code", reward="The rewards or None")
async def bonus_code(interaction: discord.Interaction, bonus_code: str, reward: str = None) -> None:
    await interaction.response.send_message(
        f'<https://eu.wargaming.net/shop/redeem/?bonus_mode={bonus_code}>\n{reward or "no reward specified"}'
    )


@client.tree.command()
@app_commands.describe(
    first_booster="Requires 10 online members",
    second_booster="Requires 15 online members",
)
async def booster(interaction: discord.Interaction, first_booster: Slot1, second_booster: Slot2) -> None:
    acting_user = get_api_user()

    if not acting_user:
        await interaction.response.send_message("No available account to activate boosters", ephemeral=True)
        return

    await interaction.response.defer()
    try:
        online_members = api.get_online_member_count(acting_user)
    except HTTPException as ex:
        print(ex)
        await interaction.followup.send("Something went wrong, ping snwflake")

    if online_members < 10:
        await interaction.followup.send("Not enough online members")
    elif online_members < 15:
        try:
            api.activate_clan_booster(acting_user, first_booster.value)
        except HTTPException as ex:
            print(ex)
            await interaction.followup.send("Something went wrong, ping snwflake")
        else:
            await interaction.followup.send("Booster activated!")
    else:
        try:
            api.activate_clan_booster(acting_user, first_booster.value, second_booster.value)
        except HTTPException as ex:
            print(ex)
            await interaction.followup.send("Something went wrong, ping snwflake")
        else:
            await interaction.followup.send("Booster activated!")


@client.tree.command()
async def test(interaction: discord.Interaction) -> None:
    await interaction.response.defer()
    acting_user = get_api_user()

    try:
        online_members = api.get_online_member_count(acting_user)
    except HTTPException:
        await interaction.followup.send("Something went wrong, ping snwflake", ephemeral=True)
    else:
        await interaction.followup.send(online_members, ephemeral=True)


def get_html_response(success: bool = False) -> HTMLResponse:
    return HTMLResponse(content=get_html_template(success), status_code=200)


def get_api_user() -> User | bool:
    try:
        user = User.get(User.account_id == ACTING_USER) or None
    except User.DoesNotExist:
        return None
    else:
        return user
