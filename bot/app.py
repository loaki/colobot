from flask import Flask, request, jsonify
from flask_swagger_ui import get_swaggerui_blueprint
import asyncio
from nextcord.utils import get


app = Flask(__name__)

SWAGGER_URL = "/swagger"
API_URL = "/static/swagger.json"
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL, API_URL, config={"app_name": "Message Sending API"}
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)


@app.route("/send_message", methods=["POST"])
def send_message():
    data = request.json
    guild_id = data.get("guild_id")
    channel_id = data.get("channel_id")
    member_id = data.get("member_id")
    message = data.get("message")

    if not all([all([guild_id, channel_id]) or member_id, message]):
        return (
            jsonify(
                {"error": "guild_id, channel_id, member_id or message not provided"}
            ),
            400,
        )

    try:
        bot = app.config["bot"]
        target = None
        if guild_id and channel_id:
            guild = bot.get_guild(int(guild_id))
            if guild:
                channel = get(guild.text_channels, id=int(channel_id))
                if channel:
                    target = channel
        elif member_id:
            member = bot.get_user(int(member_id))
            if member:
                target = member
        if target:

            async def send_message_async():
                try:
                    await target.send(message)
                    return {"status": "Message sent successfully"}
                except Exception as e:
                    return {"error": str(e)}

            loop = bot.loop
            response_future = asyncio.run_coroutine_threadsafe(
                send_message_async(), loop
            )

            response = response_future.result()
            return jsonify(response), 200 if "status" in response else 500
        else:
            return jsonify({"error": "Invalid data ID"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def run_flask():
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)


if __name__ == "__main__":
    run_flask()
