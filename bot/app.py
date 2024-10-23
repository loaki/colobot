import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse
from nextcord.utils import get
import uvicorn
from typing import Optional

app = FastAPI()


class MessageRequest(BaseModel):
    guild_id: Optional[int] = Field(None, description="The ID of the guild")
    channel_id: Optional[int] = Field(None, description="The ID of the channel")
    member_id: Optional[int] = Field(None, description="The ID of the member")
    message: str = Field(..., description="The message to send")


@app.post("/send_message")
async def send_message(request: MessageRequest):
    guild_id = request.guild_id
    channel_id = request.channel_id
    member_id = request.member_id
    message = request.message

    try:
        bot = app.state.bot
        target = None

        if guild_id and channel_id:
            guild = bot.get_guild(guild_id)
            if not guild:
                raise HTTPException(status_code=404, detail="Guild not found")
            channel = get(guild.text_channels, id=channel_id)
            if not channel:
                raise HTTPException(status_code=404, detail="Channel not found")
            target = channel
        elif member_id:
            member = bot.get_user(member_id)
            if not member:
                raise HTTPException(status_code=404, detail="Member not found")
            target = member
        else:
            raise HTTPException(status_code=400, detail="Invalid request data")

        future = asyncio.run_coroutine_threadsafe(target.send(message), bot.loop)
        response = future.result()
        return JSONResponse(content={"status": "success", "message": response.content})

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def run_fastapi():
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")


if __name__ == "__main__":
    run_fastapi()
