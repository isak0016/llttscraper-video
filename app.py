import asyncio
import os
from flask import Flask, request, jsonify
from pytok.tiktok import PyTok

app = Flask(__name__)

@app.route("/video", methods=["GET"])
async def get_video_data():
    username = request.args.get("username")
    video_id = request.args.get("id")

    if not username or not video_id:
        return jsonify({"error": "username and id are required"}), 400

    last_error = None
    for attempt in range(3):
        try:
            async with PyTok(headless=True, browser_args=["--no-sandbox"]) as api:
                video = api.video(username=username, id=video_id)
                video_data = await video.info()

                comments = []
                async for comment in video.comments(count=1000):
                    comments.append({
                        "text": comment.get("text", ""),
                        "author": comment.get("user", {}).get("unique_id", "unknown")
                    })
                    for reply in comment.get("reply_comment", []) or []:
                        comments.append({
                            "text": reply.get("text", ""),
                            "author": reply.get("user", {}).get("unique_id", "unknown"),
                            "reply_to": comment.get("user", {}).get("unique_id", "unknown")
                        })

            return jsonify({
                "video_id": video_id,
                "username": username,
                "views": video_data["stats"]["playCount"],
                "likes": video_data["stats"]["diggCount"],
                "comment_count": video_data["stats"]["commentCount"],
                "comments": comments
            })

        except Exception as e:
            last_error = str(e)
            await asyncio.sleep(3)

    return jsonify({"error": last_error}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))