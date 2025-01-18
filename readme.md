# Reddit Bot with Groq AI Integration

- AI-powered content generation using Groq
- Automated post scheduling at configurable times
- Rate limiting and usage tracking
- Error handling and logging at `bot.log`

> Actual limits for **llama-3.3-70b-versatile** are *30 per minute* and *1000 per day*, but we're being conservative.

## Prerequisites

- Python 3.12 or higher
- Reddit account and API credentials
- Groq API key

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a Reddit application:
   - Go to https://www.reddit.com/prefs/apps
   - Click `create another app...`
   - Choose ***`script`***
   - Fill in the required information
   - Note down the client ID and client secret

3. Get your Groq API key:
   - Sign up at https://console.groq.com
   - Click `API Keys` (on left navbar, above settings)
   - Create a new API key

4. Configure environment variables:
   Create a `.env` file in the project root with the following:
   ```
   # Reddit API Credentials
   REDDIT_CLIENT_ID=your_client_id
   REDDIT_CLIENT_SECRET=your_client_secret
   REDDIT_USERNAME=your_username
   REDDIT_PASSWORD=your_password

   # Subreddit to post to
   SUBREDDIT=your_target_subreddit

   # Groq API Key
   GROQ_API_KEY=your_groq_api_key
   ```

## Usage

Run the bot: (Post every hour of the day)
```bash
python app.py
```

or

Run for *specific time(s)*:
```bash
python app.py 06:10 12:30 18:45 23:59
```

> [!NOTE]
> [Click here to run your setup](/run.ipynb) 

## Sample Output ([r/ScientificFactsByAI](https://www.reddit.com/r/ScientificFactsByAI/))

**Title**: Unveiling the Mysteries of "Fast Radio Bursts" (FRBs): Unprecedented Insights into the Universe's Most Powerful Events

**Content**:
Hey fellow Redditors and science enthusiasts, today I want to share with you a fascinating aspect of astrophysics that has left scientists baffled for decades - Fast Radio Bursts (FRBs). These brief, intense pulses of energy have been observed coming from distant galaxies, releasing as much energy in a millisecond as the sun does in an entire day.

What's even more intriguing is that researchers have recently discovered a connection between FRBs and magnetars, which are incredibly powerful neutron stars with magnetic fields trillions of times stronger than Earth's. It's believed that the collapse of a magnetar's magnetic field can produce the enormous amount of energy released during an FRB.

But here's the kicker: scientists have found that some FRBs can repeat, and by studying these repeating FRBs, they've uncovered a peculiar pattern. The bursts seem to follow a predictable, periodic pattern, almost like a cosmic lighthouse. This has led researchers to suggest that FRBs could be used as cosmic probes to study the intergalactic medium and even test the fundamental laws of physics.

The implications are mind-boggling: if we can harness the power of FRBs, we could potentially use them to study the universe in unprecedented detail, from the formation of galaxies to the properties of dark matter and dark energy. It's a truly exciting time for astrophysics, and I'd love to hear your thoughts on this phenomenon. Have any of you heard about FRBs before, or have any theories on what could be causing these enigmatic events? Let's dive into the mysteries of the universe together!

Sources:

"Fast Radio Bursts: A Brief Review" (The Astrophysical Journal)

"Repeating Fast Radio Bursts from Magnetars" (Nature Astronomy)

"FRBs as Cosmic Probes" (The Astronomical Journal)

Edit: I'll be happy to answer any questions or provide more information on FRBs in the comments below!

> [!WARNING]
This bot is designed for responsible automation. Please ensure you comply with:
> - Reddit's API terms of service
> - Groq AI's usage policies
> - Your target subreddit's rules and guidelines