import re, os
import googleapiclient.discovery


def build_youtube_client():
    """
    Create a YouTube Data API client using the API key from the environment.
    Raises a helpful error if the key is missing.
    """
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "Missing YOUTUBE_API_KEY environment variable. "
            "Set it to a valid YouTube Data API v3 key."
        )
    return googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)


def extract_channel_name(url):
    """
    Extract a channel name from various YouTube URL formats or a bare name:
    - https://www.youtube.com/@handle -> handle
    - https://www.youtube.com/c/CustomName -> CustomName
    - https://www.youtube.com/user/LegacyUser -> LegacyUser
    - "SomeName" (bare string) -> SomeName
    Returns None if nothing is found.
    """
    # @handle
    match = re.search(r"@([A-Za-z0-9_.-]+)", url)
    if match:
        return match.group(1)
    # /c/CustomName
    match = re.search(r"/c/([^/?]+)", url)
    if match:
        return match.group(1)
    # /user/LegacyUser
    match = re.search(r"/user/([^/?]+)", url)
    if match:
        return match.group(1)
    # If it's not a URL, treat as a bare name
    if not re.search(r"https?://", url):
        return url.strip()
    return None


def extract_channel_id_from_url(url):
    """
    Extract the channel ID from a URL like:
    - https://www.youtube.com/channel/UCxxxxxxxxxxxxxxxxxxxxxx
    Returns the ID if present, else None.
    """
    match = re.search(r"/channel/([A-Za-z0-9_-]+)", url)
    if match:
        return match.group(1)
    return None


def get_channel_id_by_name(channel_name):
    """
    Get the channel ID from the channel name.
    """
    if not channel_name:
        raise ValueError("Channel name is required to look up a channel ID.")
    youtube = build_youtube_client()
    request = youtube.search().list(
        part="snippet", q=channel_name, type="channel", maxResults=1
    )
    response = request.execute()
    if response["items"]:
        return response["items"][0]["id"]["channelId"]
    else:
        raise ValueError(f"No channel found with the name: {channel_name}")


def get_channel_videos_stats(channel_id):
    """
    Get total videos count, details of the last 15 videos,
    and average views and likes for all videos.
    """
    youtube = build_youtube_client()

    # Fetch channel statistics for the total video count
    channel_request = youtube.channels().list(part="statistics", id=channel_id)
    channel_response = channel_request.execute()
    total_videos = int(channel_response["items"][0]["statistics"]["videoCount"])
    subscriber_count = int(
        channel_response["items"][0]["statistics"]["subscriberCount"]
    )

    # Fetch the last 15 videos
    video_ids = []
    videos_request = youtube.search().list(
        part="id,snippet",
        channelId=channel_id,
        maxResults=15,
        order="date",  # Sort by date to get the latest videos
    )
    videos_response = videos_request.execute()

    videos_data = []
    for item in videos_response["items"]:
        if item["id"]["kind"] == "youtube#video":
            video_ids.append(item["id"]["videoId"])
            videos_data.append(
                {
                    "title": item["snippet"]["title"],
                    "description": item["snippet"]["description"],
                    "published_at": item["snippet"]["publishedAt"],
                }
            )

    # Fetch statistics (views, likes, etc.) for all videos
    all_video_ids = []
    page_token = None
    while True:
        search_request = youtube.search().list(
            part="id", channelId=channel_id, maxResults=50, pageToken=page_token
        )
        search_response = search_request.execute()

        all_video_ids += [
            item["id"]["videoId"]
            for item in search_response["items"]
            if item["id"]["kind"] == "youtube#video"
        ]

        # Check for more pages
        page_token = search_response.get("nextPageToken")
        if not page_token:
            break

    # Divide video IDs into chunks of 50 (API limit)
    video_chunks = [all_video_ids[i : i + 50] for i in range(0, len(all_video_ids), 50)]
    total_views, total_likes, stats_count = 0, 0, 0

    for chunk in video_chunks:
        stats_request = youtube.videos().list(part="statistics", id=",".join(chunk))
        stats_response = stats_request.execute()

        for item in stats_response["items"]:
            stats = item["statistics"]
            total_views += int(stats.get("viewCount", 0))
            total_likes += int(stats.get("likeCount", 0))
            stats_count += 1

    # Calculate averages
    avg_views = total_views / stats_count if stats_count > 0 else 0
    avg_likes = total_likes / stats_count if stats_count > 0 else 0

    return {
        "total_videos": total_videos,
        "subscriber_count": subscriber_count,
        "last_15_videos": videos_data,
        "average_views": avg_views,
        "average_likes": avg_likes,
    }


def get_youtube_stats(channel_url):
    # Attempt to extract a channel ID directly from URL
    channel_id = extract_channel_id_from_url(channel_url)
    if not channel_id:
        # Fallback to extracting a channel name/handle/custom name
        channel_name = extract_channel_name(channel_url)
        if not channel_name:
            raise ValueError(
                "Could not extract a channel ID or name from the provided input."
            )
        channel_id = get_channel_id_by_name(channel_name)
    result = get_channel_videos_stats(channel_id)

    last_15_videos_str = "\n".join(
        [
            f"- {video['title']} (Published: {video['published_at']})"
            for video in result["last_15_videos"]
        ]
    )

    # Now format the full message
    youtube_data = f"""
    Total Videos: {result['total_videos']}
    Number of Subscribers: {result['subscriber_count']}
    Average Views: {result['average_views']}
    Average Likes: {result['average_likes']}
    Last 15 Videos:
    {last_15_videos_str}
    """
    return youtube_data


if __name__ == "__main__":
    print(get_youtube_stats("https://www.youtube.com/channel/UCh2jMEvFpPZMpNWtkWEojwg"))
