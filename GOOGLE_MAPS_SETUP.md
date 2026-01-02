# Google Maps Integration Setup Guide

This guide explains how to set up and use the Google Maps Places API integration for address autocomplete and map display features.

## Prerequisites

1. A Google Cloud Platform account
2. A Google Maps API key with the following APIs enabled:
   - Places API
   - Maps Static API
   - Geocoding API

## Setup Instructions

### 1. Get a Google Maps API Key

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to "APIs & Services" > "Credentials"
4. Click "Create Credentials" > "API Key"
5. Copy your new API key
6. Enable the required APIs:
   - Go to "APIs & Services" > "Library"
   - Search for and enable: "Places API", "Maps Static API", and "Geocoding API"

### 2. Configure the API Key

1. Navigate to the `.streamlit/` directory in the project root
2. Open `secrets.toml` file
3. Replace `YOUR_GOOGLE_MAPS_API_KEY_HERE` with your actual API key:

```toml
[google_maps]
api_key = "your-actual-api-key-here"
```

**Important:** Never commit your actual API key to version control. The `secrets.toml` file is already in `.gitignore`.

### 3. Install Dependencies

If you haven't already, install the required dependencies:

```bash
pip install -r requirements.txt
```

## Features

### Address Autocomplete

When adding or editing Real Estate assets:

1. Start typing an address in the address field
2. After typing 3+ characters, address suggestions will appear automatically
3. Select an address from the dropdown to:
   - Auto-fill the complete address
   - Capture latitude and longitude coordinates
   - Display a preview map of the location

### Location Map Display

For Real Estate assets with location data:

1. **Viewing Assets:** Click "View Location Map" to see a map of the property
2. **Editing Assets:** The map preview appears automatically when selecting an address

### Real-time Suggestions

The address autocomplete works in real-time:
- Suggestions appear as you type (no need to finish typing)
- Select any suggestion to get detailed location information
- The map updates immediately when you select an address

## Troubleshooting

### No suggestions appearing

1. **Check API Key:** Ensure your API key is correctly set in `.streamlit/secrets.toml`
2. **Check APIs:** Verify that Places API is enabled in Google Cloud Console
3. **Check Logs:** Look at the application logs for error messages:
   - Errors are logged with descriptive messages
   - Check for authentication or quota issues

### Map not displaying

1. **Check API Key:** Ensure Maps Static API is enabled
2. **Check Coordinates:** Verify that latitude and longitude are stored (edit the asset and select address again)
3. **Check Console:** Browser console may show image loading errors

### API Quota Exceeded

If you see quota errors:

1. Go to Google Cloud Console > "APIs & Services" > "Quotas"
2. Check your API usage
3. Request quota increases or enable billing if needed

## Logging

The application includes comprehensive logging for debugging:

- All API calls are logged with DEBUG level
- Errors are logged with ERROR level including stack traces
- Success operations are logged with INFO level

To view logs, check your console output when running the Streamlit application.

## Cost Considerations

Google Maps APIs have both free tiers and paid usage:

- **Places API Autocomplete:** $2.83 per 1,000 requests (first $200 free monthly)
- **Maps Static API:** $2 per 1,000 requests (first $200 free monthly)
- **Geocoding API:** $5 per 1,000 requests (first $200 free monthly)

For typical usage with a few dozen property lookups per month, you'll likely stay within the free tier.

## Security Best Practices

1. **API Key Restrictions:** In Google Cloud Console, restrict your API key:
   - Add application restrictions (HTTP referrers for web)
   - Add API restrictions (only enable necessary APIs)
   
2. **Never Commit Keys:** Always use `.streamlit/secrets.toml` and never commit actual keys

3. **Monitor Usage:** Regularly check your API usage in Google Cloud Console

## Development vs Production

- **Development:** Use the secrets.toml file locally
- **Production/Streamlit Cloud:** Add secrets through the Streamlit Cloud dashboard under "App settings" > "Secrets"
