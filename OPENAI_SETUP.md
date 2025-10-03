# OpenAI Bible Chatbot Setup

## Getting Your OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in to your account
3. Navigate to the API section
4. Create a new API key
5. Copy the API key (it starts with `sk-`)

## Setting Up the Environment

1. Copy the example environment file:

   ```bash
   cp env.example .env
   ```

2. Edit the `.env` file and add your OpenAI API key:

   ```
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```

3. Restart your Django server:
   ```bash
   python manage.py runserver
   ```

## How It Works

The Bible chatbot now uses OpenAI's GPT-3.5-turbo model with the following features:

### ✅ **Bible-Only Responses**

- The AI is specifically trained to only answer Bible-related questions
- If asked about non-Bible topics, it will respond: "I can only answer questions about the Bible and Christian faith. Please ask me about scripture, biblical stories, or spiritual guidance."

### ✅ **Smart Bible Context**

- Automatically searches your complete Bible database for relevant verses
- Provides context from actual scripture when answering questions
- Can find specific verses (e.g., "John 3:16") and explain them

### ✅ **Fallback System**

- If OpenAI is unavailable, it falls back to the local Bible chatbot
- Ensures the chatbot always works, even without internet

### ✅ **Conversation History**

- All conversations are saved to the database
- Users can see their chat history

## Example Questions You Can Ask

- "What does John 3:16 mean?"
- "Tell me about the story of David and Goliath"
- "What does the Bible say about love?"
- "Explain the meaning of the Lord's Prayer"
- "What are the fruits of the Spirit?"
- "Tell me about Jesus' miracles"

## Cost Considerations

- OpenAI charges per token used
- GPT-3.5-turbo is cost-effective for this use case
- Typical cost: ~$0.001-0.002 per conversation
- Monitor your usage in the OpenAI dashboard

## Security

- Your API key is stored securely in environment variables
- Never commit your `.env` file to version control
- The API key is only used for Bible-related conversations

## Troubleshooting

If you get errors:

1. Check that your API key is correct in `.env`
2. Ensure you have credits in your OpenAI account
3. Check your internet connection
4. The system will automatically fall back to the local chatbot if needed
