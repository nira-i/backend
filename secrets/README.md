# Secrets

This directory holds API keys and other sensitive credentials.
**It is listed in `.gitignore` and must never be committed to source control.**

## Files

### `gemini_api_key.txt`

Contains your Google Gemini API key.

1. Obtain a key from https://aistudio.google.com/app/apikey
2. Create the file:
   ```
   echo "YOUR_API_KEY_HERE" > secrets/gemini_api_key.txt
   ```

The file should contain only the key with no extra whitespace or quotes.
