import re
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi
from agents import Agent, Runner
from ..models.tools import YouTubeTranscriptInput, YouTubeTranscriptOutput

class YouTubeTranscriptExtractor:
    """Extract transcripts from YouTube videos using youtube-transcript-api"""
    
    def extract_video_id(self, url: str) -> str:
        """Extract YouTube video ID from various URL formats and clean UTM parameters"""
        # Remove UTM parameters and other tracking
        url = re.sub(r'[?&]utm_[^=]*=[^&]*', '', url)
        url = re.sub(r'[?&]si=[^&]*', '', url)  # YouTube's tracking parameter
        url = re.sub(r'[?&]feature=[^&]*', '', url)
        url = re.sub(r'[?&]t=[^&]*', '', url)  # Timestamp parameters
        
        # YouTube URL patterns
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # If no pattern matches, try parsing as query parameter
        parsed = urlparse(url)
        if parsed.netloc in ['www.youtube.com', 'youtube.com', 'm.youtube.com']:
            query_params = parse_qs(parsed.query)
            if 'v' in query_params:
                return query_params['v'][0]
        
        raise ValueError(f"Could not extract video ID from URL: {url}")
    
    def find_youtube_urls(self, text: str) -> list:
        """Find all YouTube URLs in text"""
        # Match various YouTube URL formats
        youtube_pattern = r'https?://(?:www\.)?(?:youtube\.com/watch\?[^\s]*v=|youtu\.be/)[a-zA-Z0-9_-]{11}[^\s]*'
        urls = re.findall(youtube_pattern, text)
        return urls
    
    async def extract_transcript(self, input_data: YouTubeTranscriptInput) -> YouTubeTranscriptOutput:
        """Extract transcript from YouTube video"""
        try:
            # Use the provided video URL directly
            video_url = input_data.video_url
            video_id = self.extract_video_id(video_url)
            
            # Get transcript using youtube-transcript-api
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            
            # Format transcript with timestamps (youtube-transcript-api provides start times)
            formatted_segments = []
            for entry in transcript_list:
                # Convert start time to MM:SS or HH:MM:SS format
                start_seconds = int(entry['start'])
                minutes = start_seconds // 60
                seconds = start_seconds % 60
                
                if minutes >= 60:
                    hours = minutes // 60
                    minutes = minutes % 60
                    timestamp = f"[{hours:02d}:{minutes:02d}:{seconds:02d}]"
                else:
                    timestamp = f"[{minutes:02d}:{seconds:02d}]"
                
                formatted_segments.append(f"{timestamp} {entry['text']}")
            
            # Join all segments with newlines for readability
            full_transcript = "\n".join(formatted_segments)
            
            # Try to get video metadata (this requires additional API calls)
            # For now, we'll just use the video ID as title
            video_title = f"YouTube Video {video_id}"
            
            return YouTubeTranscriptOutput(
                transcript=full_transcript,
                video_title=video_title,
                video_id=video_id,
                channel="",  # Would need YouTube Data API for this
                duration_text="",  # Would need YouTube Data API for this
                success=True,
                error_message=""
            )
            
        except Exception as e:
            # Handle all exceptions generically since older version has different exception names
            error_message = str(e)
            
            # Check for specific error patterns
            if "Could not retrieve a transcript" in error_message:
                error_message = "No transcript/captions available for this video. The creator may have disabled captions or YouTube hasn't generated them yet."
            elif "The video is unavailable" in error_message:
                error_message = "Video is unavailable. It may be private, deleted, or restricted in your region."
            
            return YouTubeTranscriptOutput(
                transcript="",
                video_title="",
                video_id=video_id if 'video_id' in locals() else "",
                success=False,
                error_message=error_message
            )

# Create global instance
youtube_extractor = YouTubeTranscriptExtractor()

class YouTubeTranscriptTool:
    """YouTube Transcript Tool using Agent SDK for proper tracing"""
    
    def __init__(self):
        self.agent = Agent(
            name="YouTube Transcript Tool",
            instructions="Extract and process YouTube video transcripts",
            output_type=YouTubeTranscriptOutput
        )
        self.extractor = YouTubeTranscriptExtractor()
    
    async def extract(self, input_data: YouTubeTranscriptInput) -> YouTubeTranscriptOutput:
        """Extract YouTube transcript with proper agent tracing"""
        
        user_prompt = f"""
        Extract transcript from YouTube video:
        - Video URL: {input_data.video_url}
        - Content type: {input_data.item_type}
        """
        
        try:
            # Use Runner.run() for proper Agent SDK tracing
            await Runner.run(self.agent, user_prompt)
            
            # Do the actual extraction
            return await self.extractor.extract_transcript(input_data)
        except Exception as e:
            return YouTubeTranscriptOutput(
                transcript="",
                video_title="",
                video_id="",
                success=False,
                error_message=f"Tool error: {str(e)}"
            )

# Create global instance
youtube_tool_instance = YouTubeTranscriptTool()

async def youtube_transcript_tool(input_data: YouTubeTranscriptInput) -> YouTubeTranscriptOutput:
    """Tool function for YouTube transcript extraction"""
    return await youtube_tool_instance.extract(input_data) 