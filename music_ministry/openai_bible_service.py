import os
import openai
from django.conf import settings
from .models import BibleVerse, BibleBook, ChatMessage


class OpenAIBibleService:
    def __init__(self):
        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = openai.OpenAI(api_key=api_key)
        
        # Bible-focused system prompt
        self.system_prompt = """You are a Bible Assistant, a knowledgeable and helpful AI that specializes in providing accurate, thoughtful responses about the Bible and Christian faith. 

Your role is to:
- Answer questions about Bible verses, stories, characters, and teachings
- Provide spiritual guidance based on biblical principles
- Explain biblical concepts and themes
- Help users understand the context and meaning of scripture
- Share insights about Christian faith and practice

Guidelines:
- Always base your responses on biblical truth and Christian doctrine
- Be respectful, compassionate, and encouraging
- When quoting scripture, be accurate and provide references when possible
- If asked about topics outside of the Bible or Christian faith, politely redirect by saying: "I can only answer questions about the Bible and Christian faith. Please ask me about scripture, biblical stories, or spiritual guidance."
- Maintain a warm, supportive tone while being doctrinally sound
- If you're unsure about something, admit it rather than speculate

Remember: You are here to help people grow in their understanding of God's Word and strengthen their faith."""

    def is_bible_related(self, message):
        """Check if the message is Bible-related"""
        bible_keywords = [
            'bible', 'scripture', 'god', 'jesus', 'christ', 'lord', 'faith', 'prayer',
            'worship', 'praise', 'love', 'hope', 'peace', 'joy', 'grace', 'mercy', 
            'salvation', 'heaven', 'eternal', 'holy', 'spirit', 'trinity', 'gospel', 
            'testament', 'old testament', 'new testament', 'genesis', 'psalms', 'matthew', 
            'john', 'romans', 'corinthians', 'ephesians', 'philippians', 'galatians',
            'isaiah', 'jeremiah', 'ezekiel', 'daniel', 'verse', 'chapter', 'book',
            'christian', 'church', 'pastor', 'minister', 'blessing', 'pray', 'amen',
            'sin', 'forgiveness', 'repentance', 'baptism', 'communion', 'sabbath',
            'commandment', 'prophet', 'apostle', 'disciple', 'miracle', 'healing',
            'resurrection', 'crucifixion', 'cross', 'savior', 'redeemer', 'messiah'
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in bible_keywords)

    def get_bible_context(self, message):
        """Get relevant Bible verses for context"""
        try:
            # Search for specific verse references (e.g., "John 3:16")
            import re
            verse_match = re.search(r'(\w+)\s*(\d+):(\d+)', message)
            if verse_match:
                book_name = verse_match.group(1)
                chapter = int(verse_match.group(2))
                verse_num = int(verse_match.group(3))
                
                try:
                    book = BibleBook.objects.get(name__iexact=book_name)
                    verse = BibleVerse.objects.get(
                        book=book,
                        chapter=chapter,
                        verse_number=verse_num
                    )
                    return f"Relevant Scripture: {verse.reference} - {verse.text}"
                except (BibleBook.DoesNotExist, BibleVerse.DoesNotExist):
                    pass
            
            # Search for verses containing keywords
            words = message.lower().split()
            relevant_verses = []
            
            for word in words:
                if len(word) > 3:  # Only search for words longer than 3 characters
                    verses = BibleVerse.objects.filter(text__icontains=word)[:3]
                    for verse in verses:
                        relevant_verses.append(f"{verse.reference}: {verse.text[:100]}...")
            
            if relevant_verses:
                return "Relevant Scriptures:\n" + "\n".join(relevant_verses[:5])
                
        except Exception as e:
            print(f"Error getting Bible context: {e}")
        
        return ""

    def generate_response(self, message, user):
        """Generate response using OpenAI"""
        try:
            # Check if message is Bible-related
            if not self.is_bible_related(message):
                return "I can only answer questions about the Bible and Christian faith. Please ask me about scripture, biblical stories, or spiritual guidance.", False
            
            # Get Bible context
            bible_context = self.get_bible_context(message)
            
            # Prepare messages for OpenAI
            messages = [
                {"role": "system", "content": self.system_prompt}
            ]
            
            if bible_context:
                messages.append({
                    "role": "system", 
                    "content": f"Here is some relevant biblical context for the user's question:\n\n{bible_context}"
                })
            
            messages.append({
                "role": "user", 
                "content": message
            })
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.7,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Save conversation
            self.save_conversation(user, message, response_text, True)
            
            return response_text, True
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            # Fallback to simple response
            return "I can only answer questions about the Bible and Christian faith. Please ask me about scripture, biblical stories, or spiritual guidance.", True

    def save_conversation(self, user, message, response, is_bible_related):
        """Save the conversation to the database"""
        try:
            ChatMessage.objects.create(
                user=user,
                message=message,
                response=response,
                is_bible_related=is_bible_related
            )
        except Exception as e:
            print(f"Error saving conversation: {e}")
