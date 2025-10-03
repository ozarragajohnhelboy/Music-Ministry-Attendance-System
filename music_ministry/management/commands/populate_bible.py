from django.core.management.base import BaseCommand
from music_ministry.models import BibleBook, BibleVerse
import json
import os


class Command(BaseCommand):
    help = 'Populate Bible books and verses from JSON data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Path to Bible JSON file',
            default='complete_bible_data.json'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        
        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f'Bible data file not found: {file_path}')
            )
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            bible_data = json.load(f)

        BibleVerse.objects.all().delete()
        BibleBook.objects.all().delete()

        books_created = 0
        verses_created = 0

        for book_data in bible_data:
            book, created = BibleBook.objects.get_or_create(
                name=book_data['name'],
                defaults={
                    'testament': book_data['testament'],
                    'order': book_data['order']
                }
            )
            
            if created:
                books_created += 1

            for chapter_num, chapter_data in book_data['chapters'].items():
                chapter_num = int(chapter_num)
                for verse_num, verse_text in chapter_data.items():
                    verse_num = int(verse_num)
                    BibleVerse.objects.create(
                        book=book,
                        chapter=chapter_num,
                        verse_number=verse_num,
                        text=verse_text
                    )
                    verses_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {books_created} books and {verses_created} verses'
            )
        )
