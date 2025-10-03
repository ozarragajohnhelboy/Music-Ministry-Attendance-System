import re
from django.db.models import Q
from .models import BibleVerse, BibleBook, ChatMessage


class BibleChatbot:
    def __init__(self):
        self.bible_keywords = [
            'bible', 'verse', 'scripture', 'god', 'jesus', 'christ', 'lord', 'faith', 'prayer',
            'worship', 'praise', 'love', 'hope', 'peace', 'joy', 'grace', 'mercy', 'salvation',
            'heaven', 'eternal', 'holy', 'spirit', 'trinity', 'gospel', 'testament', 'old testament',
            'new testament', 'genesis', 'psalms', 'matthew', 'john', 'romans', 'corinthians',
            'ephesians', 'philippians', 'galatians', 'isaiah', 'jeremiah', 'ezekiel', 'daniel'
        ]
    
    def is_bible_related(self, message):
        """Check if the message is Bible-related"""
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in self.bible_keywords)
    
    def search_verses(self, query, limit=5):
        """Search for Bible verses based on query"""
        if not query.strip():
            return []
        
        # Clean the query
        query = query.strip()
        
        # Try to parse book:chapter:verse format
        verse_match = re.match(r'(\w+)\s*(\d+):(\d+)', query)
        if verse_match:
            book_name = verse_match.group(1)
            chapter = int(verse_match.group(2))
            verse_num = int(verse_match.group(3))
            
            try:
                book = BibleBook.objects.get(name__iexact=book_name)
                verses = BibleVerse.objects.filter(
                    book=book,
                    chapter=chapter,
                    verse_number=verse_num
                )
                return list(verses)
            except BibleBook.DoesNotExist:
                pass
        
        # Try to parse book:chapter format
        chapter_match = re.match(r'(\w+)\s*(\d+)', query)
        if chapter_match:
            book_name = chapter_match.group(1)
            chapter = int(chapter_match.group(2))
            
            try:
                book = BibleBook.objects.get(name__iexact=book_name)
                verses = BibleVerse.objects.filter(
                    book=book,
                    chapter=chapter
                ).order_by('verse_number')[:limit]
                return list(verses)
            except BibleBook.DoesNotExist:
                pass
        
        # Search by book name only
        try:
            book = BibleBook.objects.get(name__iexact=query)
            verses = BibleVerse.objects.filter(book=book).order_by('chapter', 'verse_number')[:limit]
            return list(verses)
        except BibleBook.DoesNotExist:
            pass
        
        # Search by text content
        verses = BibleVerse.objects.filter(
            Q(text__icontains=query) | 
            Q(book__name__icontains=query)
        ).order_by('book__order', 'chapter', 'verse_number')[:limit]
        
        return list(verses)
    
    def get_random_verse(self, testament=None):
        """Get a random verse from the Bible"""
        from django.db.models import Count
        from random import randint
        
        queryset = BibleVerse.objects.all()
        if testament:
            queryset = queryset.filter(book__testament=testament)
        
        count = queryset.count()
        if count == 0:
            return None
        
        random_index = randint(0, count - 1)
        return queryset[random_index]
    
    def generate_response(self, message, user):
        """Generate a response to the user's message"""
        message_lower = message.lower()
        
        # Check if it's a Bible-related query
        if not self.is_bible_related(message):
            return (
                "I'm a Bible chatbot! I can help you find Bible verses, "
                "search scriptures, or provide spiritual guidance. Try asking me about "
                "specific verses, books, or topics like 'love', 'faith', or 'hope'.",
                False
            )
        
        # Handle specific commands
        if any(word in message_lower for word in ['random', 'random verse']):
            verse = self.get_random_verse()
            if verse:
                response = f"Here's a random verse for you:\n\n**{verse.reference}**\n\n{verse.text}"
                return response, True
            else:
                return "I don't have any Bible verses available right now.", True
        
        if 'old testament' in message_lower or 'old' in message_lower:
            verse = self.get_random_verse('old')
            if verse:
                response = f"Here's a verse from the Old Testament:\n\n**{verse.reference}**\n\n{verse.text}"
                return response, True
        
        if 'new testament' in message_lower or 'new' in message_lower:
            verse = self.get_random_verse('new')
            if verse:
                response = f"Here's a verse from the New Testament:\n\n**{verse.reference}**\n\n{verse.text}"
                return response, True
        
        # Search for verses
        search_results = self.search_verses(message)
        
        if search_results:
            if len(search_results) == 1:
                verse = search_results[0]
                response = f"**{verse.reference}**\n\n{verse.text}"
            else:
                response = f"I found {len(search_results)} verses:\n\n"
                for verse in search_results:
                    response += f"**{verse.reference}**\n{verse.text}\n\n"
            
            return response, True
        
        # Handle common topics
        topic_responses = {
            'love': "Here are some verses about love:\n\n**1 Corinthians 13:4-8**\nCharity suffereth long, and is kind; charity envieth not; charity vaunteth not itself, is not puffed up. Doth not behave itself unseemly, seeketh not her own, is not easily provoked, thinketh no evil; Rejoiceth not in iniquity, but rejoiceth in the truth; Beareth all things, believeth all things, hopeth all things, endureth all things. Charity never faileth.",
            
            'faith': "Here's a verse about faith:\n\n**Hebrews 11:1**\nNow faith is the substance of things hoped for, the evidence of things not seen.",
            
            'hope': "Here's a verse about hope:\n\n**Romans 15:13**\nNow the God of hope fill you with all joy and peace in believing, that ye may abound in hope, through the power of the Holy Ghost.",
            
            'peace': "Here's a verse about peace:\n\n**Philippians 4:7**\nAnd the peace of God, which passeth all understanding, shall keep your hearts and minds through Christ Jesus.",
            
            'joy': "Here's a verse about joy:\n\n**Nehemiah 8:10**\nThen he said unto them, Go your way, eat the fat, and drink the sweet, and send portions unto them for whom nothing is prepared: for this day is holy unto our Lord: neither be ye sorry; for the joy of the LORD is your strength."
        }
        
        for topic, response in topic_responses.items():
            if topic in message_lower:
                return response, True
        
        # Default response for Bible-related queries
        return (
            "I understand you're asking about the Bible. Could you be more specific? "
            "You can ask for:\n"
            "• A specific verse (e.g., 'John 3:16')\n"
            "• A chapter (e.g., 'Psalms 23')\n"
            "• A book (e.g., 'Matthew')\n"
            "• A topic (e.g., 'love', 'faith', 'hope')\n"
            "• A random verse\n"
            "• Old Testament or New Testament verses",
            True
        )
    
    def save_conversation(self, user, message, response, is_bible_related):
        """Save the conversation to the database"""
        ChatMessage.objects.create(
            user=user,
            message=message,
            response=response,
            is_bible_related=is_bible_related
        )
