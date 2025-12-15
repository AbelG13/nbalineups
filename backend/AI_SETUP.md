# AI Report Setup Guide

This guide explains how to set up the AI-powered pregame reports feature.

## Overview

The AI report feature uses **Google Gemini** (free tier available) to generate intelligent pregame analysis based on:
1. Current injured players
2. Standardized statistical edges (with injuries)
3. Baseline standardized edges (without injuries)

## Setup Instructions

1. Get a Gemini API key:
   - Go to https://makersuite.google.com/app/apikey
   - Sign in with your Google account
   - Click "Create API Key"
   - Copy your API key

2. Create a `.env` file in the `backend` directory:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

3. Install Dependencies:

Make sure you have the required packages installed:

```bash
cd backend
pip install -r requirements.txt
```

The following packages will be installed:
- `google-generativeai` (for Gemini - **required**)
- `python-dotenv` (for loading .env file - **required**)

## Usage

Once set up, the AI reports will be available in the frontend:

1. Navigate to the Pregame Reports page
2. Click "Generate Report" on any game
3. Click "Generate AI Analysis" button
4. The AI will analyze the matchup and provide insights

## API Endpoints

- `GET /ai-report/{game_id}` - Generate AI report for a specific game using Gemini
- `GET /ai-reports` - Generate AI reports for all games today using Gemini

## How It Works

The AI receives three inputs:

1. **Injured Players**: List of currently injured players from `data/injuries25.csv`
2. **Edges with Injuries**: Standardized statistical edges calculated using lineups that exclude injured players
3. **Baseline Edges**: Standardized statistical edges calculated using all available lineups (no injuries)

The AI analyzes:
- How injuries affect each team's rotation
- Changes in statistical profile when injuries are removed
- Relationships between different statistical categories
- Implications for game flow and betting angles

## Troubleshooting

**Error: "No API key configured"**
- Make sure you've created a `.env` file in the `backend` directory
- Verify the API key is correct (no extra spaces or quotes)
- Restart the backend server after creating/updating the `.env` file

**Error: "Failed to generate AI report"**
- Check your API key is valid and has sufficient credits/quota
- Verify your internet connection
- Check the backend console for detailed error messages

**Reports are slow to generate**
- AI API calls can take 5-15 seconds depending on the API provider
- This is normal behavior - be patient while the report generates

